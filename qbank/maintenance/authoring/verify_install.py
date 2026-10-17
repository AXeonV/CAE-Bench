"""Disposable combined public installation check; does not publish or solve cases.

Run with the developer environment. A new venv installs the assembled runtime
normally, then its source tree is renamed and all commands run from another cwd.
May download the declared dependencies during pip installation.
"""
import argparse
from importlib import import_module
import json
from pathlib import Path
import subprocess
import sys
import venv

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tests'))
from caeoj_tools.assembly import runtime_materials
from caeoj_tools.task_paths import task_directory


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--domain',action='append',required=True,
                        help='Domain with tests/<domain>_fixture.py; repeat to combine domains.')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    fixtures={}
    for domain in dict.fromkeys(args.domain):
        if not domain.isidentifier() or not (ROOT/'tests'/f'{domain}_fixture.py').is_file():
            parser.error(f'Unknown fixture domain: {domain}')
        fixture=import_module(f'{domain}_fixture').fixture
        for slug in import_module(f'caeoj_ext.{domain}').models():
            if slug in fixtures:
                parser.error(f'Duplicate task: {slug}')
            fixtures[slug]=fixture
    base=args.output.resolve()
    if not base.is_relative_to(ROOT/'runs'):
        raise SystemExit('Installation evidence must stay under this workspace runs directory.')
    if base.exists():
        raise SystemExit('Use a fresh destination; existing installation evidence is preserved.')
    base.mkdir(parents=True)
    source=base/'assembled'
    runtime_files, runtime=runtime_materials({s:task_directory(s,ROOT) for s in fixtures},ROOT)
    for name,data in runtime_files.items():
        target=source/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(data)
    for slug,fixture in fixtures.items():fixture(base/'fixtures'/slug,slug)
    env=base/'venv'
    venv.create(env,with_pip=True)
    python=env/('Scripts/python.exe' if sys.platform=='win32' else 'bin/python')
    completed=subprocess.run([str(python),'-m','pip','install',str(source)],capture_output=True,encoding='utf-8',errors='backslashreplace')
    (base/'install.log').write_text(completed.stdout+completed.stderr,encoding='utf-8')
    completed.check_returncode()
    source.rename(base/'source-moved-after-install')
    work=base/'different-working-directory'
    work.mkdir()
    rows=[]
    for slug in fixtures:
        task=task_directory(slug,ROOT)
        path=base/'fixtures'/slug/'problem.json'
        output=path.parent/'tool-output.h5'
        script='''import sys,numpy as np
from pathlib import Path
import caeoj
from caeoj.sdk import load_problem,write_result,load_result
p=load_problem(sys.argv[1]);m=p.manifest
assert "site-packages" in str(Path(caeoj.__file__)).lower(),caeoj.__file__
v={s["array"]:np.zeros((len(p.arrays[m["time_axes"][s["time_axis"]]]),len(p.arrays[m["locations"][s["location"]]["ids"]]),*s["component_shape"])) for s in m["outputs"].values()}
write_result(sys.argv[2],p,v);load_result(p,sys.argv[2])
'''
        subprocess.run([str(python),'-I','-c',script,str(path),str(output)],cwd=work,check=True,capture_output=True,encoding='utf-8',errors='backslashreplace')
        from caeoj.case_grading import direct_config
        from caeoj.grading_policy import load_policy
        config=direct_config(load_policy(task/'author/grading-template.json'))
        config['checks'][0]['reference']=output.name
        grading=path.parent/'grading.json';grading.write_text(json.dumps(config))
        commands=[['info','--input',str(path)],['validate-input',str(path)],
                  ['validate-output','--input',str(path),'--output',str(output)],
                  ['grade','--input',str(path),'--output',str(output),'--grading',str(grading)]]
        for args in commands:
            r=subprocess.run([str(python),'-I','-m','caeoj',*args],cwd=work,capture_output=True,encoding='utf-8',errors='backslashreplace')
            rows.append(dict(task=slug,command=args[0],returncode=r.returncode))
            if r.returncode: raise RuntimeError(r.stdout+r.stderr)
        bad=path.parent/'bad-output.h5';bad.write_bytes(b'not HDF5')
        for candidate,reference,code in [(bad,output,1),(output,bad,2)]:
            config['checks'][0]['reference']=reference.name
            grading.write_text(json.dumps(config))
            r=subprocess.run([str(python),'-I','-m','caeoj','grade','--input',str(path),'--output',str(candidate),'--grading',str(grading)],cwd=work,capture_output=True,encoding='utf-8',errors='backslashreplace')
            assert r.returncode==code,(r.stdout,r.stderr)
            rows.append(dict(task=slug,command='bad-candidate' if code==1 else 'bad-reference',returncode=code))
    summary=dict(runtime_id=runtime['id'],task_count=len(fixtures),normal_install=True,source_moved=True,
                 different_cwd=True,isolated_python=True,commands=rows,
                 scope='synthetic array/declaration fixtures only; no numerical or physical reference verification',
                 public_files=list(sorted(runtime_files)),dependencies=runtime['dependencies'])
    (base/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:summary[k] for k in ('runtime_id','task_count','normal_install','source_moved')},indent=2))


if __name__=='__main__':main()
