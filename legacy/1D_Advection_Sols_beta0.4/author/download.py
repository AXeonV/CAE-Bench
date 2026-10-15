"""Read complete selected trajectories from the official public HDF5 file."""
import hashlib
import io
import json
from pathlib import Path

import h5py
import requests

TASK = Path(__file__).resolve().parents[1]
DEFAULT = TASK.parents[1]/'runs/pdebench-official/advection-beta0.4-official.h5'
URL = 'https://darus.uni-stuttgart.de/api/access/datafile/133110'


class RangeReader(io.RawIOBase):
    def __init__(self):
        self.session = requests.Session()
        response = self.session.get(URL, headers={'Range':'bytes=0-7'}, timeout=60)
        response.raise_for_status()
        if response.status_code != 206:
            raise RuntimeError('Official server must support byte ranges')
        self.url = response.url
        self.size = int(response.headers['Content-Range'].split('/')[-1])
        self.position = 0
        self.blocks = {}

    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.position
    def seek(self, offset, whence=0):
        self.position = (0 if whence == 0 else self.position if whence == 1 else self.size)+offset
        if self.position < 0: raise ValueError('Negative file offset')
        return self.position
    def read(self, size=-1):
        end = self.size if size < 0 else min(self.position+size, self.size)
        parts = []
        while self.position < end:
            start = self.position//1048576*1048576
            if start not in self.blocks:
                stop = min(start+1048576, self.size)-1
                response = self.session.get(self.url, headers={'Range':f'bytes={start}-{stop}'}, timeout=90)
                response.raise_for_status()
                if response.status_code != 206 or response.headers.get('Content-Range') != f'bytes {start}-{stop}/{self.size}':
                    raise RuntimeError('Invalid byte-range response')
                if len(response.content) != stop-start+1: raise RuntimeError('Incomplete range')
                self.blocks[start] = response.content
            block = self.blocks[start]
            stop = min(end, start+len(block))
            parts.append(block[self.position-start:stop-start])
            self.position = stop
        return b''.join(parts)
    def readinto(self, buffer):
        data = self.read(len(buffer)); buffer[:len(data)] = data; return len(data)
    def close(self):
        self.session.close(); super().close()


def verify(path):
    provenance = json.loads((TASK/'author/SOURCE.json').read_text())
    with h5py.File(path, 'r') as source:
        if float(source.attrs['beta']) != 0.4:
            raise ValueError('Unexpected official beta attribute')
        for key in ('x-coordinate', 't-coordinate'):
            values = source[key][...]
            if hashlib.sha256(values.tobytes()).hexdigest() != provenance['coordinates'][key]:
                raise ValueError('Official coordinates changed: '+key)
        if source['tensor'].shape != (12,201,1024) or source['tensor'].dtype.name != 'float32':
            raise ValueError('Expected 12 complete official float32 samples')
        for record in provenance['samples']:
            if hashlib.sha256(source['tensor'][record['sample_index']].tobytes()).hexdigest() != record['sha256']:
                raise ValueError('Official trajectory changed: '+str(record['sample_index']))
    return Path(path)


def download(destination=DEFAULT):
    destination = Path(destination)
    if destination.exists(): return verify(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix('.partial.h5')
    try:
        with RangeReader() as reader, h5py.File(reader, 'r') as source, h5py.File(temporary, 'w') as local:
            if source['tensor'].shape != (10000,201,1024): raise ValueError('Unexpected official tensor shape')
            for key in ('x-coordinate','t-coordinate'): local.create_dataset(key,data=source[key][...])
            for key,value in source.attrs.items(): local.attrs[key]=value
            tensor = local.create_dataset('tensor',shape=(12,201,1024),dtype='float32')
            for index in range(12):
                tensor[index] = source['tensor'][index,...]
                print(f'Downloaded complete official sample {index}',flush=True)
        verify(temporary)
        temporary.replace(destination)
    finally:
        if temporary.exists(): temporary.unlink()
    return destination


if __name__ == '__main__': download()
