"""Fetch the pinned public inputs/reference producers, without executing benchmark clients."""
from __future__ import annotations
import concurrent.futures
import hashlib
import json
from pathlib import Path
import time
import urllib.request

REVISION = "e37e8b61fbb1f3532dcfd2f2e8ab67e7c91c3ee2"
REPO = "NLR-Theseus/cfdllmbench"
ROOT = Path(__file__).resolve().parents[4]
WORK = ROOT / "runs/cfdcodebench-local-20261019"

def get(url: str) -> bytes:
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "CAE-Bench-OJ-reference-audit"}), timeout=60) as response:
                return response.read()
        except Exception:
            if attempt == 3:
                raise
            time.sleep(attempt + 1)
    raise AssertionError("unreachable")

def main() -> None:
    tree = json.loads(get(f"https://api.github.com/repos/{REPO}/git/trees/{REVISION}?recursive=1"))
    prefix = "CFDCodeBench/PDE_Benchmark/"
    paths = [x["path"] for x in tree["tree"] if x["type"] == "blob" and (
        x["path"] in ["LICENSE", "CFDCodeBench/README.md"] or
        any(x["path"].startswith(prefix + p) for p in ["prompt/", "solution/", "results/solution/"]))]
    def fetch(path: str) -> dict:
        output = WORK / "upstream" / path
        output.parent.mkdir(parents=True, exist_ok=True)
        payload = output.read_bytes() if output.exists() else get(f"https://raw.githubusercontent.com/{REPO}/{REVISION}/{path}")
        output.write_bytes(payload)
        return {"path": path, "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        files = list(pool.map(fetch, paths))
    record = {"repository": REPO, "revision": REVISION, "files": files}
    (WORK / "upstream-manifest.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps({"files": len(files), "bytes": sum(x["bytes"] for x in files), "work": str(WORK)}))

if __name__ == "__main__":
    main()
