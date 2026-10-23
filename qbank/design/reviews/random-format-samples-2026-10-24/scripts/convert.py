import hashlib
import importlib.util
import json
from pathlib import Path
import shutil

from caeoj_tools import data_pool as pool
from caeoj_tools.format_examples import randomize_example
from caeoj.validation import validate_output

ROOT = Path('D:/Code/CAE-Bench-OJ')
WORK = ROOT / 'runs/uniform-samples'
STAGE = WORK / 'stage'
TARGETS = {'smoke-test', 'case-grading-test', 'heat-conduction-steady-2d', 'heat-conduction-transient-2d'}
plan = json.loads((ROOT / 'runs/prepublication-review-rc2/reviewed-plan.json').read_text(encoding='utf-8'))
STAGE.mkdir()
for name in ['src', 'qbank/extensions']:
    shutil.copytree(ROOT / name, STAGE / name, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.egg-info'))
for name in ['LICENSE', 'pyproject.toml', 'README.md', 'docs/CONTRACT.md', 'docs/GRADING.md']:
    p = STAGE / name
    p.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / name, p)
spec = importlib.util.spec_from_file_location('uniform_publisher', ROOT / 'src/utils/publish_dist.py')
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)
records = []
for entry in plan['tasks']:
    if entry['task'] not in TARGETS:
        continue
    original = Path(entry['source_root']) / entry['task_path']
    before = pool.manifest(original / 'data-manifest.json')
    prepared = WORK / 'prepared' / entry['task']
    for name in before['cases']:
        shutil.copytree(original / 'cases' / name, prepared / 'cases' / name)
        shutil.copytree(original / 'reference' / name, prepared / 'reference' / name)
    randomized = []
    for index, name in enumerate(before['samples']):
        sample = prepared / 'samples' / name
        shutil.copytree(original / 'samples' / name / 'input', sample / 'input')
        randomized.append({'sample': name, **randomize_example(sample, seed=2026102400 + len(records) * 10 + index)})
    bundle = WORK / 'pools' / entry['task']
    pool.pack(prepared, bundle, before)
    pool.validate_bundle(bundle)
    packed = pool.manifest(bundle / 'selection.json')
    for role in ['cases', 'samples']:
        assert {k: v['case_id'] for k, v in before[role].items()} == {k: v['case_id'] for k, v in packed[role].items()}
    store = pool.LocalStore(bundle / 'repository')
    selected = pool.select(packed, store, [f"{k}={v['case_id']}" for k, v in before['cases'].items()], [],
                           format_samples=[f"{k}={v['case_id']}" for k, v in before['samples'].items()])
    selected['notes'] = 'Offline RC4 format-only samples; numerical test assets unchanged. This descriptor revision has not been uploaded to HF; use the recorded local pool or the self-contained RC.'
    target = STAGE / entry['task_path']
    target.mkdir(parents=True)
    for name in ['instruction.md', 'DATA.md', 'judge-config.json', 'harbor/task.toml']:
        p = ROOT / entry['task_path'] / name
        if p.exists():
            q = target / name
            q.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, q)
    pool.write_json(target / 'data-manifest.json', selected)
    pool.assemble(target, selected, store)
    strict = pool.verify(target, strict=True)
    assert strict['valid']
    formal_hashes = {}
    for prefix in ['cases', 'reference']:
        for p in (original / prefix).rglob('*'):
            if p.is_file():
                key = p.relative_to(original).as_posix()
                assert (target / key).read_bytes() == p.read_bytes(), key
                formal_hashes[key] = pool.digest(p)
    for name in before['samples']:
        assert not (target / 'samples' / name / 'reference').exists()
        assert validate_output(target / 'samples' / name / 'input/problem.json', target / 'samples' / name / 'output/result.h5')['valid']
    public = publisher.publish(entry['task'], output=WORK / 'public', root=STAGE)
    # The current working tree consumes the same verified pool, not an edited receipt.
    current = ROOT / entry['task_path']
    pool.write_json(current / 'data-manifest.json', selected)
    pool.assemble(current, selected, store)
    assert pool.verify(current, strict=True)['valid']
    record = {'task': entry['task'], 'samples': randomized, 'case_ids_retained': True,
              'formal_input_reference_sha256': formal_hashes, 'formal_bytes_unchanged': True,
              'descriptor_bindings_changed': before['cases'] != selected['cases'],
              'pool': str(bundle), 'hf_uploaded': False, 'strict': strict,
              'public': public, 'manifest_sha256': pool.digest(target / 'data-manifest.json')}
    pool.write_json(current / 'author/data-evidence/random-format-samples-2026-10-24.json', record)
    records.append(record)
    entry.update(source_root=str(STAGE), public_archive=public['archive'],
                 public_archive_sha256=pool.digest(Path(public['archive'])))
    entry['limitations'] = [n for n in entry['limitations'] if not n.startswith('No original-source manifest changed')]
    entry['limitations'].append('Public samples are random format-only examples; local pool descriptors were regenerated without changing original test input/grading/reference bytes. New pool revision not uploaded to HF.')
    pool.write_json(WORK / 'conversion-report.json', records)
    print(entry['task'], 'converted', len(randomized), 'random samples', flush=True)
assert len(records) == 4
plan.update(release_id='caeoj-qbank-20261024-rc4')
plan['capabilities']['public_sample_policy'] = 'random-format-only'
plan['release_notes'].append('本版82题的96个公开样例角色统一为随机格式输出，只保证格式，不保证数值答案正确；公开样例不提供reference/数值判分材料。')
plan['release_notes'].append('4题7例由原数值样例转换为随机格式样例；正式case ID、输入及原评分／参考资产字节保持。新的样例描述在离线池与本包中，未上传HF。')
pool.write_json(WORK / 'plan.json', plan)
print('COMPLETE 82 tasks; all96 samples format-only', flush=True)
