"""Read-only structural checks for direct-child qbank problem statements.

Checks ordinary inline Markdown file links (not anchors, reference-style links or
HTML), the candidate's three-document link boundary, strict JSON fenced blocks
and topic document presence. Public sample assets may be linked. Never runs a
solver, fetches URLs, reads numerical data or judges physics/review readiness.
"""
import argparse
import json
import math
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit


FENCE = re.compile(r'^```([^\n]*)\n(.*?)^```\s*$', re.M | re.S)
LINK = re.compile(r'\]\((<[^>]+>|[^\s)]+)(?:\s+"[^"]*")?\)')
DEFAULT_CONTRACT = Path(__file__).resolve().parents[4] / 'docs/CONTRACT.md'


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate key: {key}')
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError(f'non-finite JSON constant: {value}')


def finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f'number exceeds finite float range: {value}')
    return number


def inspect(section, contract=DEFAULT_CONTRACT):
    section, contract = Path(section).resolve(), Path(contract).resolve()
    errors = []
    topics = []
    documents = sorted(section.rglob('*.md'))
    json_blocks = 0
    links = 0
    for topic in sorted(p for p in section.iterdir() if p.is_dir()):
        if not any((topic / name).is_file() for name in ('instruction.md', 'DATA.md')):
            continue
        topics.append(topic.name)
        for name in ('instruction.md', 'DATA.md'):
            if not (topic / name).is_file():
                errors.append({'file': str(topic / name), 'issue': 'missing_topic_document'})
    if not topics:
        errors.append({'file': str(section), 'issue': 'no_direct_child_topics'})
    candidate_files = {section / topic / name for topic in topics
                       for name in ('instruction.md', 'DATA.md')}
    for path in documents:
        try:
            text = path.read_text(encoding='utf-8')
        except (OSError, UnicodeError) as exc:
            errors.append({'file': str(path), 'issue': 'unreadable_document', 'detail': str(exc)})
            continue
        for block in FENCE.finditer(text):
            if block.group(1).strip() != 'json':
                continue
            json_blocks += 1
            try:
                json.loads(block.group(2), object_pairs_hook=unique_object,
                           parse_constant=reject_constant, parse_float=finite_float)
            except ValueError as exc:
                errors.append({'file': str(path), 'line': text.count('\n', 0, block.start()) + 1,
                               'issue': 'invalid_json_block', 'detail': str(exc)})
        prose = FENCE.sub('', text)
        for match in LINK.finditer(prose):
            target = match.group(1).strip('<>')
            url = urlsplit(target)
            candidate = path in candidate_files
            if url.scheme or url.netloc:
                if candidate:
                    errors.append({'file': str(path), 'issue': 'external_candidate_link',
                                   'target': target})
                continue
            if not url.path:
                continue
            links += 1
            destination = (path.parent / unquote(url.path)).resolve()
            if not destination.exists():
                errors.append({'file': str(path), 'issue': 'missing_link_target', 'target': target})
            if candidate:
                allowed = {path.parent / 'instruction.md', path.parent / 'DATA.md', contract}
                sample_asset = destination.suffix.lower() != '.md' and any(
                    destination.is_relative_to(path.parent / folder)
                    for folder in ('examples', 'samples'))
                if destination not in allowed and not sample_asset:
                    errors.append({'file': str(path), 'issue': 'extra_candidate_dependency',
                                   'target': target})
    data_files = []
    for topic in topics:
        for folder in ('examples', 'references', 'cases', 'samples'):
            base = section / topic / folder
            if base.is_dir():
                data_files.extend(str(p.relative_to(section)) for p in sorted(base.rglob('*'))
                                  if p.is_file() and p.name != '.gitkeep')
    return {'section': str(section), 'contract': str(contract),
            'topics': topics, 'documents': len(documents),
            'json_blocks': json_blocks, 'local_file_links': links, 'errors': errors,
            'data_directory_files': data_files,
            'static_checks': 'failed' if errors else 'passed',
            'planning_alignment': 'not_evaluated', 'candidate_review': 'not_evaluated',
            'data_validation': 'not_evaluated', 'physics_validation': 'not_evaluated',
            'notice': 'Only structural/link checks; plain-text dependencies, anchors, full Markdown syntax and physical self-sufficiency are not validated.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--section', type=Path, required=True)
    parser.add_argument('--contract', type=Path, default=DEFAULT_CONTRACT,
                        help='Shared CONTRACT.md; defaults to this repository contract')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    section = args.section.resolve()
    if not section.is_dir():
        parser.error('--section must be an existing directory')
    if not args.contract.is_file():
        parser.error('--contract must be an existing file')
    if args.output and args.output.resolve().is_relative_to(section):
        parser.error('write the report outside the section directory')
    result = inspect(section, args.contract)
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding='utf-8')
        print(json.dumps({'report': str(args.output), 'topics': len(result['topics']),
                          'static_checks': result['static_checks']}, ensure_ascii=False))
    else:
        print(encoded, end='')
    return 1 if result['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
