"""Bounded, resumable HTTP range access; no implicit whole-file download."""
from collections import OrderedDict
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
import time

import requests
from urllib3.exceptions import HTTPError as TransportError


class PreparationError(RuntimeError):
    pass


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".write-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def digest(path, algorithm="sha256"):
    h = hashlib.new(algorithm)
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


class Budget:
    """Account for existing managed files plus outstanding disk reservations."""
    def __init__(self, roots, limit):
        unique = []
        for root in sorted({Path(p).resolve() for p in roots}, key=lambda p: len(p.parts)):
            if not any(root.is_relative_to(parent) for parent in unique):
                unique.append(root)
        self.roots, self.limit = unique, int(limit)
        self.reserved = 0
        self.peak = self.used()

    def used(self):
        return sum(p.stat().st_size for root in self.roots if root.exists()
                   for p in root.rglob("*") if p.is_file() and not p.is_symlink())

    def check(self, extra=0):
        used = self.used() + self.reserved + int(extra)
        self.peak = max(self.peak, used)
        if used > self.limit:
            raise PreparationError(f"Managed disk budget exceeded: {used} > {self.limit} bytes")
        existing = next((p for p in self.roots if p.exists()), Path.cwd())
        if extra > shutil.disk_usage(existing).free:
            raise PreparationError("Insufficient free disk space")


class RangeReader(io.RawIOBase):
    def __init__(self, source, cache, budget, block_size=1024 * 1024,
                 memory_blocks=4, timeout=45, retries=5, cache_bytes=64 * 1024**2):
        super().__init__()
        self.source, self.budget = source, budget
        self.url = source["url"]
        self.size = int(source["bytes"])
        self.position, self.block_size = 0, block_size
        self.memory_blocks, self.timeout, self.retries = memory_blocks, timeout, retries
        self.cache_bytes = cache_bytes
        self.cache = Path(cache) / str(source["id"])
        self.budget.check(4096)
        self.cache.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.memory = OrderedDict()
        self.transferred = 0
        self.hits = 0
        self.identity_path = self.cache / "identity.json"
        identity = {"url": self.url, "bytes": self.size, "md5": source["md5"]}
        if self.identity_path.exists():
            old = json.loads(self.identity_path.read_text())
            if any(old.get(k) != v for k, v in identity.items()):
                raise PreparationError("Cached source identity does not match pinned catalog")
            self.etag = old.get("etag")
        else:
            self.etag = None
            atomic_json(self.identity_path, identity)

    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.position

    def seek(self, offset, whence=0):
        if whence not in (0, 1, 2): raise ValueError("Invalid whence")
        position = (0, self.position, self.size)[whence] + offset
        if position < 0: raise ValueError("Negative offset")
        self.position = position
        return position

    def _fetch(self, start, end):
        last = None
        for attempt in range(self.retries):
            try:
                headers = {"Range": f"bytes={start}-{end}", "Accept-Encoding": "identity"}
                if self.etag: headers["If-Match"] = self.etag
                with self.session.get(self.url, headers=headers, timeout=self.timeout, stream=True) as response:
                    response.raise_for_status()
                    wanted = f"bytes {start}-{end}/{self.size}"
                    if response.status_code != 206 or response.headers.get("Content-Range") != wanted:
                        raise PreparationError("Server did not return the requested byte range; refusing full download")
                    etag = response.headers.get("ETag")
                    if self.etag and etag != self.etag:
                        raise PreparationError("Remote source changed since cached ranges were obtained")
                    content = response.raw.read(end - start + 2)
                    if len(content) != end - start + 1:
                        raise PreparationError("Truncated or oversized range response")
                    if self.etag is None and etag:
                        self.etag = etag
                        atomic_json(self.identity_path, {"url": self.url, "bytes": self.size,
                                                        "md5": self.source["md5"], "etag": etag})
                    self.transferred += len(content)
                    return content
            except (requests.RequestException,TransportError,OSError) as exc:
                last = exc
                # A DNS/proxy reconnect or interrupted TLS session must not
                # reuse a stale connection pool on the next attempt.
                self.session.close();self.session=requests.Session()
                if attempt + 1 < self.retries: time.sleep(min(2**attempt, 10))
        raise PreparationError(f"Cannot read source {self.source['id']}: {last}")

    def _block(self, start):
        if start in self.memory:
            self.memory.move_to_end(start)
            self.hits += 1
            return self.memory[start]
        path = self.cache / f"{start}.bin"
        cert = path.with_suffix(".json")
        size = min(self.block_size, self.size - start)
        data = None
        if path.exists() and cert.exists():
            candidate = path.read_bytes()
            try: info = json.loads(cert.read_text())
            except (OSError,ValueError): info = {}
            if len(candidate) == size and hashlib.sha256(candidate).hexdigest() == info.get("sha256"):
                data = candidate
                self.hits += 1
        if data is None:
            # Per-source disk LRU bounds the resumable range cache.
            blocks = sorted(self.cache.glob("*.bin"), key=lambda p: p.stat().st_mtime)
            occupied = sum(p.stat().st_size for p in blocks)
            for old in blocks:
                if occupied + size <= self.cache_bytes: break
                occupied -= old.stat().st_size
                old.unlink()
                old.with_suffix(".json").unlink(missing_ok=True)
            if size > self.cache_bytes:
                raise PreparationError("Range block is larger than cache limit")
            self.budget.check(size + 4096)
            data = self._fetch(start, start + size - 1)
            temporary = path.with_suffix(".partial")
            temporary.write_bytes(data)
            os.replace(temporary, path)
            atomic_json(cert, {"sha256": hashlib.sha256(data).hexdigest()})
        else:
            os.utime(path, None)
        self.memory[start] = data
        while len(self.memory) > self.memory_blocks: self.memory.popitem(last=False)
        return data

    def _prefetch(self,start,end):
        """Coalesce only blocks that a large current read actually needs.

        Preserve the existing block granularity and checksums, rather than
        increasing overfetch for tiny HDF5 header/initial-field reads.
        """
        count=min(4,self.memory_blocks,self.cache_bytes//self.block_size,
                  (end-start)//self.block_size)
        if count<2:return
        starts=[start+i*self.block_size for i in range(count)]
        if any(i in self.memory or (self.cache/f'{i}.bin').exists() for i in starts):return
        stop=min(self.size,start+count*self.block_size)
        self.budget.check(stop-start+count*4096)
        data=self._fetch(start,stop-1)
        occupied=sum(p.stat().st_size for p in self.cache.glob('*.bin'))
        for old in sorted(self.cache.glob('*.bin'),key=lambda p:p.stat().st_mtime):
            if occupied+len(data)<=self.cache_bytes:break
            occupied-=old.stat().st_size
            old.unlink();old.with_suffix('.json').unlink(missing_ok=True)
        for i in starts:
            block=data[i-start:min(i-start+self.block_size,len(data))]
            path=self.cache/f'{i}.bin';temporary=path.with_suffix('.partial')
            temporary.write_bytes(block);os.replace(temporary,path)
            atomic_json(path.with_suffix('.json'),{'sha256':hashlib.sha256(block).hexdigest()})
            self.memory[i]=block
        while len(self.memory)>self.memory_blocks:self.memory.popitem(last=False)

    def readinto(self, buffer):
        end = min(self.position + len(buffer), self.size)
        written = 0
        while self.position < end:
            start = self.position // self.block_size * self.block_size
            self._prefetch(start,end)
            block = self._block(start)
            offset = self.position - start
            count = min(end - self.position, len(block) - offset)
            buffer[written:written+count] = block[offset:offset+count]
            self.position += count
            written += count
        return written

    def close(self):
        if not self.closed:
            # Budget/identity checks can fail partway through __init__.
            if hasattr(self,'session'):self.session.close()
            if hasattr(self,'memory'):self.memory.clear()
        super().close()
