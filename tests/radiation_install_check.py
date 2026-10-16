"""Explicit disposable ordinary-install audit; run manually, not during unit discovery.

python tests/radiation_install_check.py --work runs/authoring/chapter-15/install
All staged numerical files are protocol fixtures, not formal data or references.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import sys
import venv

from radiation_fixture import fixture
from caeoj_ext.radiation import models
from caeoj_tools.assembly import runtime_materials
from caeoj_tools.task_paths import task_directory

ROOT = Path(__file__).resolve().parents[1]

PROBE = '''
from pathlib import Path
import json, sys
import numpy as np
import caeoj, caeoj_ext.radiation
from caeoj.sdk import load_problem, write_result
from caeoj.runtime import descriptor, RuntimeSupportError
from caeoj.cli import main
base=Path(sys.argv[1]); stage=Path(sys.argv[2]); site=Path(sys.prefix).resolve()
assert Path(caeoj.__file__).resolve().is_relative_to(site)
assert Path(caeoj_ext.radiation.__file__).resolve().is_relative_to(site)
assert not stage.exists(), 'staged source must have been moved before probe'
for path in sorted(base.glob('fixtures/*/problem.json')):
    p=load_problem(path); m=p.manifest; result=path.parent/'result.h5'
    fields={s['array']:np.zeros((len(p.arrays[m['time_axes'][s['time_axis']]]),
        len(p.arrays[m['locations'][s['location']]['ids']]),*s['component_shape']))
        for s in m['outputs'].values()}
    write_result(result,p,fields)
    assert main(['info','--input',str(path)])==0
    assert main(['validate-input',str(path)])==0
    assert main(['validate-output','--input',str(path),'--output',str(result)])==0
    grading=base/'policies'/m['task']/'grading.json'
    assert main(['grade','--input',str(path),'--output',str(result),'--reference',str(result),'--grading',str(grading)])==0
    bad=json.loads(path.read_text()); name=next(iter(bad['fields'])); bad['fields'][name]['unit']='wrong'
    invalid=path.parent/'bad.json'; invalid.write_text(json.dumps(bad))
    assert main(['validate-input',str(invalid)])==1
    assert main(['grade','--input',str(invalid),'--output',str(result),'--reference',str(result),'--grading',str(grading)])==2
    invalid.unlink()
# SDK and CLI shared installed support; deliberately remove required trusted support in memory.
catalog=descriptor(); saved=catalog['extensions'].pop('radiation.nuclear')
try:
    try: load_problem(path)
    except RuntimeSupportError: pass
    else: raise AssertionError('missing extension silently accepted')
finally: catalog['extensions']['radiation.nuclear']=saved
print('ORDINARY_INSTALL_AUDIT_PASSED')
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--work', required=True)
    args = parser.parse_args()
    work = Path(args.work).resolve()
    if not work.is_relative_to(ROOT/'runs'):
        raise ValueError('work must be under repository runs/')
    work.mkdir(parents=True, exist_ok=True)
    if any(work.iterdir()):
        raise ValueError('work must be a new empty directory')
    files, runtime = runtime_materials({s:task_directory(s,ROOT) for s in models()},ROOT)
    for name in files:
        assert not any(x in name for x in ('caeoj_tools', 'maintenance', '/author/', '/cases/', '/reference/'))
    stage = work/'public-runtime'
    for name, payload in files.items():
        path = stage/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(payload)
    for slug in models():
        fixture(work/'fixtures'/slug,slug)
        policy = work/'policies'/slug/'grading.json'; policy.parent.mkdir(parents=True,exist_ok=True)
        policy.write_bytes((task_directory(slug,ROOT)/'grading.json').read_bytes())
    environment = work/'environment'; venv.EnvBuilder(with_pip=True).create(environment)
    py = environment/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    env = os.environ.copy(); env.pop('PYTHONPATH',None)
    with (work/'pip-install.log').open('w',encoding='utf-8') as log:
        subprocess.run([str(py),'-m','pip','install',str(stage)],cwd=work,env=env,
                       stdout=log,stderr=subprocess.STDOUT,check=True)
    # Both paths are verified descendants of runs; never overwrite an existing target.
    moved = work/'public-source-moved'
    assert stage.resolve().is_relative_to(work) and moved.resolve().is_relative_to(work)
    assert not moved.exists()
    stage.rename(moved)
    with (work/'probe.log').open('w',encoding='utf-8') as log:
        subprocess.run([str(py),'-I','-c',PROBE,str(work),str(stage)],cwd=work,env=env,
                       stdout=log,stderr=subprocess.STDOUT,check=True)
    summary = dict(runtime_id=runtime['id'], tasks=list(models()),
                   public_files={name:hashlib.sha256(data).hexdigest() for name,data in files.items()},
                   ordinary_install=True, isolated_imports=True, source_moved=True,
                   platform=sys.platform, python=sys.version, formal_data=False)
    (work/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k!='public_files'}))


if __name__ == '__main__':
    main()
