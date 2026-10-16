"""Collect DATA.md audit evidence without loading numerical fields or solving PDEs."""
import argparse
import json
from pathlib import Path
import h5py

from caeoj.validation import read_json


def relative_file(base, name):
    if not isinstance(name, str) or not name:
        raise ValueError('Expected a nonempty package-relative file name')
    candidate = (base / name).resolve()
    if not candidate.is_relative_to(base.resolve()):
        raise ValueError('File reference escapes the input package')
    return candidate


def hdf5_headers(path):
    arrays = []
    with h5py.File(path, 'r') as data:
        for key in data:
            if not isinstance(data.get(key, getlink=True), h5py.HardLink):
                raise ValueError(f'Expected a self-contained dataset: {key}')
            dataset = data[key]
            if not isinstance(dataset, h5py.Dataset) or dataset.shape is None:
                raise ValueError(f'Expected a dataset with a non-null dataspace: {key}')
            arrays.append({'key': key, 'dtype': str(dataset.dtype),
                           'shape': list(dataset.shape), 'chunks': dataset.chunks,
                           'compression': dataset.compression})
    return arrays


def inspect_file(path, reader):
    if not path.is_file():
        return {'path': str(path), 'status': 'missing'}
    try:
        return {'path': str(path), 'status': 'read', 'content': reader(path)}
    except (OSError, ValueError, EOFError) as exc:
        return {'path': str(path), 'status': 'unreadable', 'error': str(exc)}


def mesh_header(path):
    with path.open('rb') as stream:
        return [stream.readline(1024).decode('ascii').strip() for _ in range(2)]


def inventory(task):
    inputs = []
    paths = sorted((task / 'cases').glob('*/problem.json'))
    paths += sorted((task / 'samples').glob('*/input/problem.json'))
    for path in paths:
        entry = {'path': str(path), 'kind': 'sample' if path.is_relative_to(task / 'samples') else 'case'}
        try:
            manifest = read_json(path)
            if not isinstance(manifest, dict):
                raise ValueError('Manifest must be a JSON object')
            entry['manifest'] = manifest
            data = relative_file(path.parent, manifest.get('data_file'))
            entry['arrays'] = inspect_file(data, hdf5_headers)
            entry['meshes'] = []
            for name, mesh in manifest.get('meshes', {}).items():
                file = relative_file(path.parent, mesh.get('file'))
                entry['meshes'].append({'mesh': name, **inspect_file(file, mesh_header)})
            if entry['kind'] == 'sample':
                output = path.parent.parent / 'output/result.h5'
                entry['sample_output'] = inspect_file(output, hdf5_headers)
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            entry['inventory_error'] = str(exc)
        inputs.append(entry)
    gaps = []
    for entry in inputs:
        if 'inventory_error' in entry:
            gaps.append({'input': entry['path'], 'error': entry['inventory_error']})
        files = [entry.get('arrays'), entry.get('sample_output'), *entry.get('meshes', [])]
        for file in filter(None, files):
            if file['status'] != 'read':
                gaps.append({'input': entry['path'], **file})
    if not inputs:
        gaps.append({'error': 'No case or sample problem.json files found'})
    documents = {name: (task / name).is_file() for name in ('instruction.md', 'DATA.md')}
    for name, present in documents.items():
        if not present:
            gaps.append({'error': f'Missing task document: {name}'})
    return {'task': str(task), 'documents': documents,
            'input_count': len(inputs), 'case_count': sum(i['kind'] == 'case' for i in inputs),
            'sample_count': sum(i['kind'] == 'sample' for i in inputs),
            'gaps': gaps, 'inputs': inputs,
            'notice': 'Evidence inventory only; not schema validation or a DATA.md audit verdict.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    task = args.task.resolve()
    if not task.is_dir():
        parser.error('Task directory does not exist')
    if args.output.resolve().is_relative_to(task):
        parser.error('Write audit evidence outside the task directory')
    result = inventory(task)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'inventory': str(args.output), 'inputs': result['input_count'],
                      'gaps': len(result['gaps']), 'audit_verdict': 'not_evaluated'}))


if __name__ == '__main__':
    main()
