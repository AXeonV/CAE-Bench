"""Pinned, bounded per-task source retrieval; never performs conversion or solving.

Manifest v1: {"version":1,"sources":[{"id":"...", "url":"https://...",
"path":"raw/file", "sha256":"64 lowercase hex", "size_bytes":123,
"sample":true, "mapping":{... source-to-OJ extraction declaration ...}}]}.
sample selects explicitly marked sources; selected requires IDs; all requires
allow_all=True. A mapping is retained as provenance, never executed.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import time
import shutil
import subprocess
import tempfile
import os
from urllib.parse import urlparse
import urllib.request


def safe_path(root, relative):
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise ValueError("Invalid relative path")
    parts = relative.split("/")
    if any(p in ("", ".", "..") or ":" in p for p in parts):
        raise ValueError("Unsafe relative path")
    root = Path(root).absolute()
    path = root.joinpath(*parts)
    for parent in (root, *path.parents, path):
        if parent.is_symlink():
            raise ValueError("Symlink in managed path")
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("Path escapes cache")
    return path


def sha256(path, deadline=None):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            if deadline is not None and time.monotonic() >= deadline:
                raise TimeoutError("Time budget exceeded during cache verification")
            h.update(block)
    return h.hexdigest()


def load_manifest(path):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out: raise ValueError("Duplicate manifest key")
            out[key] = value
        return out
    manifest = json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=pairs,
                          parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    if manifest.get("version") != 1 or not isinstance(manifest.get("sources"), list):
        raise ValueError("Expected source manifest version 1")
    ids, paths = set(), set()
    for source in manifest["sources"]:
        if not isinstance(source, dict): raise ValueError("Source must be an object")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", source.get("id", "")):
            raise ValueError("Invalid source id")
        if source["id"] in ids or source.get("path") in paths: raise ValueError("Duplicate source")
        ids.add(source["id"]); paths.add(source["path"])
        safe_path(Path.cwd(), source["path"])
        if not re.fullmatch(r"[0-9a-f]{64}", source.get("sha256", "")):
            raise ValueError("A fixed SHA256 is required")
        if type(source.get("size_bytes")) is not int or source["size_bytes"] <= 0:
            raise ValueError("A positive pinned size is required")
        url = urlparse(source.get("url", ""))
        if url.scheme not in ("http", "https") or not url.netloc or url.username or url.password:
            raise ValueError("Expected public HTTP(S) URL")
        if not isinstance(source.get("mapping"), dict) or not source["mapping"]:
            raise ValueError("Explicit source-to-OJ mapping required")
        if type(source.get("sample", False)) is not bool: raise ValueError("sample must be boolean")
    if any(path + ".part" in paths for path in paths):
        raise ValueError("Source path collides with managed partial file")
    return manifest


def curl_download(source, part, deadline, byte_budget, timeout):
    """Run curl as argv; curl itself enforces total wall time and pinned size."""
    used = 0
    restarted = False
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0: raise TimeoutError("Time budget exceeded")
        offset = part.stat().st_size if part.exists() else 0
        required = source["size_bytes"] - offset
        if required > byte_budget - used: raise ValueError("Fallback exceeds transfer budget")
        args = ["curl", "--fail", "--silent", "--show-error", "--location",
                "--proto", "=http,https", "--proto-redir", "=http,https",
                "--max-time", str(remaining), "--connect-timeout", str(min(timeout, remaining)),
                "--max-filesize", str(source["size_bytes"]), "--header", "Accept-Encoding: identity",
                "--output", str(part), "--write-out", "%{size_download}"]
        if offset: args.extend(["--continue-at", str(offset)])
        header_fd, header_name = tempfile.mkstemp(prefix=".curl-headers-", dir=part.parent)
        os.close(header_fd)
        args.extend(["--dump-header", header_name])
        args.append(source["url"])
        try:
            result = subprocess.run(args, capture_output=True, text=True, timeout=remaining)
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError("curl exceeded total time budget") from exc
        finally:
            header_text = Path(header_name).read_text(encoding="iso-8859-1")
            Path(header_name).unlink(missing_ok=True)
        try: received = int(float(result.stdout.strip() or "0"))
        except ValueError as exc: raise ValueError("Invalid curl transfer accounting") from exc
        used += received
        if used > byte_budget: raise ValueError("curl transfer budget exceeded")
        if time.monotonic() >= deadline: raise TimeoutError("Time budget exceeded")
        if offset and result.returncode in (33, 36):
            blocks = [block for block in header_text.split("\n\n") if block.strip()]
            if blocks and re.match(r"HTTP/\S+ 206(?: |$)", blocks[-1]):
                raise ValueError("Server returned incompatible resumed range")
        if result.returncode == 28: raise TimeoutError("curl exceeded total time budget")
        if result.returncode == 0:
            if offset:
                blocks = [block for block in header_text.split("\n\n") if block.strip()]
                final = blocks[-1] if blocks else ""
                expected = f"bytes {offset}-{source['size_bytes']-1}/{source['size_bytes']}"
                found = re.search(r"(?im)^content-range:\s*(.*?)\s*$", final)
                if not found or found.group(1) != expected or not re.match(r"HTTP/\S+ 206(?: |$)", final):
                    raise ValueError("Unexpected curl resumed Content-Range")
            return used
        # libcurl refuses unsupported or incompatible resumed ranges (33/36).
        # It never appends a full 200 response to the existing partial file.
        if offset and result.returncode in (33, 36) and not restarted:
            if source["size_bytes"] > byte_budget - used:
                raise ValueError("Safe full restart exceeds remaining transfer budget")
            part.unlink(missing_ok=True)
            restarted = True
            continue
        raise OSError("curl download failed: " + result.stderr.strip()[:500])


def fetch(manifest, cache, mode="sample", selected=(), allow_all=False,
          max_bytes=256 * 1024**2, max_seconds=300, timeout=30, transport="auto"):
    if transport not in ("auto", "urllib", "curl"): raise ValueError("Unknown transport")
    chosen_transport = "curl" if transport == "curl" or (transport == "auto" and shutil.which("curl")) else "urllib"
    if chosen_transport == "curl" and not shutil.which("curl"): raise ValueError("curl not installed")
    if mode not in ("sample", "selected", "all"): raise ValueError("Unknown mode")
    if mode == "all" and not allow_all: raise ValueError("all requires explicit allow_all")
    if mode != "selected" and selected: raise ValueError("IDs require selected mode")
    if mode == "selected" and not selected: raise ValueError("selected requires source IDs")
    sources = manifest["sources"]
    known = {s["id"] for s in sources}
    if set(selected) - known: raise ValueError("Unknown selected source")
    chosen = [s for s in sources if mode == "all" or
              (mode == "sample" and s.get("sample", False)) or
              (mode == "selected" and s["id"] in selected)]
    if not chosen: raise ValueError("No sources selected")
    if max_bytes <= 0 or max_seconds <= 0 or timeout <= 0: raise ValueError("Positive budgets required")
    # Pinned final size bounds storage including existing partial files.
    if sum(s["size_bytes"] for s in chosen) > max_bytes:
        raise ValueError("Selected source sizes exceed byte budget")
    start, transferred, results = time.monotonic(), 0, []
    deadline = start + max_seconds
    for source in chosen:
        if time.monotonic() >= deadline: raise TimeoutError("Time budget exceeded")
        path = safe_path(cache, source["path"])
        part = safe_path(cache, source["path"] + ".part")
        path.parent.mkdir(parents=True, exist_ok=True)
        size = source["size_bytes"]
        if path.exists():
            if path.stat().st_size != size or sha256(path, deadline) != source["sha256"]:
                raise ValueError("Cached checksum mismatch: " + source["id"])
            results.append({"id":source["id"], "path":str(path), "cache_hit":True,
                            "size_bytes":size, "sha256":source["sha256"], "mapping":source["mapping"]})
            continue
        offset = part.stat().st_size if part.exists() else 0
        if offset > size: raise ValueError("Oversized partial file")
        if offset < size:
            if chosen_transport == "curl":
                transferred += curl_download(source, part, deadline, max_bytes-transferred, timeout)
            else:
                remaining = max_seconds - (time.monotonic() - start)
                if remaining <= 0: raise TimeoutError("Time budget exceeded")
                headers = {"Accept-Encoding":"identity"}
                if offset: headers["Range"] = f"bytes={offset}-"
                request = urllib.request.Request(source["url"], headers=headers)
                with urllib.request.urlopen(request, timeout=min(timeout, remaining)) as response:
                    status = response.status
                    if offset and status == 206:
                        expected = f"bytes {offset}-{size-1}/{size}"
                        if response.headers.get("Content-Range") != expected:
                            raise ValueError("Unexpected resumed Content-Range")
                    elif status == 200:
                        offset = 0  # Range unsupported: restart, still inside transfer budget.
                    else:
                        raise ValueError("Unexpected HTTP status")
                    length = response.headers.get("Content-Length")
                    if length is not None and int(length) != size - offset:
                        raise ValueError("Remote length differs from pinned size")
                    with part.open("ab" if offset else "wb") as stream:
                        written = offset
                        while True:
                            if time.monotonic() - start >= max_seconds: raise TimeoutError("Time budget exceeded")
                            # urllib exposes the TLS socket through this response stream.
                            # Bound every blocking read by the remaining global deadline.
                            sock = getattr(getattr(response.fp, "raw", None), "_sock", None)
                            if sock is not None: sock.settimeout(min(timeout, max(0.001, deadline-time.monotonic())))
                            block = response.read1(min(1024 * 1024, size - written + 1))
                            if time.monotonic() >= deadline: raise TimeoutError("Time budget exceeded")
                            if not block: break
                            transferred += len(block); written += len(block)
                            if transferred > max_bytes or written > size:
                                raise ValueError("Download byte budget or pinned size exceeded")
                            stream.write(block)
        if part.stat().st_size != size or sha256(part, deadline) != source["sha256"]:
            raise ValueError("Downloaded size/SHA256 mismatch: " + source["id"])
        part.replace(path)
        results.append({"id":source["id"], "path":str(path), "cache_hit":False,
                        "size_bytes":size, "sha256":source["sha256"], "mapping":source["mapping"]})
    if time.monotonic() >= deadline: raise TimeoutError("Time budget exceeded")
    return {"mode":mode, "transport":chosen_transport, "downloaded_bytes":transferred, "elapsed_seconds":time.monotonic()-start,
            "sources":results}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transport",choices=("auto","urllib","curl"),default="auto")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--cache", required=True)
    parser.add_argument("--mode", choices=("sample", "selected", "all"), default="sample")
    parser.add_argument("--source", action="append", default=[])
    parser.add_argument("--allow-all", action="store_true")
    parser.add_argument("--max-bytes", type=int, default=256 * 1024**2)
    parser.add_argument("--max-seconds", type=float, default=300)
    args = parser.parse_args(argv)
    try:
        report = fetch(load_manifest(args.manifest), args.cache, args.mode, args.source,
                       args.allow_all, args.max_bytes, args.max_seconds, transport=args.transport)
    except (OSError, ValueError, TimeoutError, KeyError, TypeError) as exc:
        print(json.dumps({"ok":False, "error":str(exc)}))
        return 1
    print(json.dumps({"ok":True, **report}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
