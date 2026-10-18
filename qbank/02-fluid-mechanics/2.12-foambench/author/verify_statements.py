"""Audit source identity and public document structure, without making cases."""
import hashlib
import json
from pathlib import Path
import re

from source_snapshot import INDEX, read_source


def audit():
    section = Path(__file__).resolve().parent.parent
    source = {kind: read_source(kind) for kind in ['basic', 'advanced']}
    assert len(INDEX['tasks']) == 126
    assert len({t['task'] for t in INDEX['tasks']}) == 126
    assert len({(t['source_split'], t['source_id']) for t in INDEX['tasks']}) == 126
    assert {t['source_id'] for t in INDEX['tasks'] if t['source_split'] == 'basic'} == set(source['basic'])
    assert {t['source_id'] for t in INDEX['tasks'] if t['source_split'] == 'advanced'} == set(source['advanced'])
    result = []
    json_blocks = 0
    links = 0
    for index, task in enumerate(INDEX['tasks'], 1):
        assert task['number'] == f'2.12.{index}'
        folder = section / task['task']
        prompt = source[task['source_split']][task['source_id']]['usr_requirement']
        assert hashlib.sha256(prompt.encode()).hexdigest() == task['prompt_sha256']
        record_path = folder / 'author/source.json'
        record = json.loads(record_path.read_text(encoding='utf-8'))
        assert record.get('prompt', record.get('original_prompt')) == prompt
        assert INDEX['revision'] in record.values(), f'{task["task"]}: unpinned provenance'
        key = record.get('source_id', record.get('source_key', record.get('upstream_key')))
        assert key == task['source_id'], task['task']
        files = {}
        for name in ['instruction.md', 'DATA.md']:
            path = folder / name
            raw = path.read_bytes()
            text = raw.decode('utf-8')
            for block in re.findall(r'```json\s*\n(.*?)\n```', text, re.S):
                json.loads(block)
                json_blocks += 1
            for link in re.findall(r'\]\(([^)]+)\)', text):
                if not link.startswith(('https://', 'http://', '#')):
                    target = link.split('#')[0]
                    assert (folder / target).resolve().is_file(), f'{path}: {link}'
                    links += 1
            if name == 'instruction.md':
                assert f'2.12.{index} ' in text.splitlines()[0]
                assert 'solve.py' in text and '--input' in text and '--output' in text
            else:
                assert task['task'] in text
            files[name] = hashlib.sha256(raw).hexdigest()
        files['author/source.json'] = hashlib.sha256(record_path.read_bytes()).hexdigest()
        result.append({'number': task['number'], 'task': task['task'], 'files': files})
    return {'tasks': len(result), 'basic': 110, 'advanced': 16, 'local_links': links,
            'json_blocks': json_blocks, 'source_revision': INDEX['revision'],
            'status': 'document/source checks only; no data or numerical certification', 'coverage': result}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f"{result['tasks']} tasks: source identity, public links, JSON fragments and entry points verified")
