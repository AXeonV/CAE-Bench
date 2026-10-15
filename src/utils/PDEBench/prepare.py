#!/usr/bin/env python3
"""Clone-to-data entry point. --plan is offline and needs only Python stdlib."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'src'))


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tasks',nargs='+',default=['all'],help='Task names, short family names, or all')
    p.add_argument('--plan',action='store_true',help='Print pinned source plan without network or dependency installation')
    p.add_argument('--catalog',type=Path,default=HERE/'catalog.json')
    p.add_argument('--output-root',type=Path,help='Optional flat output tree; default: each task in its qbank chapter/section')
    p.add_argument('--cache-root',type=Path,default=ROOT/'runs/pdebench')
    p.add_argument('--source-dir',type=Path,help='Read local complete source files (full size and MD5 verified)')
    p.add_argument('--reference-dir',type=Path,help='Import independently audited references, never unreviewed source trajectories')
    p.add_argument('--reference-mode',choices=['official','independent'],default='official',help='Source-aligned numerical audit (default), or independent references where implemented')
    p.add_argument('--refresh-contract',action='store_true',help='Explicitly bind existing frozen source choices to a reviewed revised contract; archive previous selection')
    p.add_argument('--budget-gb',type=float,default=60.,help='Decimal GB managed disk cap')
    p.add_argument('--candidate-pool',type=int,default=64,help='Bounded candidate pool for feature-stratified families')
    p.add_argument('--max-cases',type=int,help='Smoke run: prepare only this many hidden cases, still include both public samples')
    p.add_argument('--timeout',type=int,default=45,help='HTTP connect/read timeout in seconds')
    p.add_argument('--no-bootstrap',action='store_true',help='Require dependencies already installed')
    return p


def bootstrap(args):
    missing=[n for n in ('numpy','gmsh','h5py','requests','yaml','jsonschema','scipy') if importlib.util.find_spec(n) is None]
    if not missing:return
    if args.no_bootstrap:
        raise RuntimeError('Missing '+', '.join(missing)+"; install: python -m pip install -e '.[pdebench]'")
    env=args.cache_root.resolve()/'venv'
    existing=sum(p.stat().st_size for root in [args.cache_root.resolve(),(args.output_root or ROOT/'qbank').resolve()]
                 if root.exists() for p in root.rglob('*') if p.is_file() and not p.is_symlink())
    if existing+512_000_000 > args.budget_gb*1e9:
        raise RuntimeError('Insufficient budget for dependency bootstrap (512 MB reserved); use an existing environment')
    python=env/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    print('Installing preparation dependencies in '+str(env),flush=True)
    if not python.exists(): subprocess.run([sys.executable,'-m','venv',str(env)],check=True)
    with tempfile.TemporaryDirectory(prefix='bootstrap-',dir=args.cache_root.resolve()) as temporary:
        environment=dict(os.environ,TMPDIR=temporary,TMP=temporary,TEMP=temporary)
        subprocess.run([str(python),'-m','pip','install','--no-cache-dir','-e',str(ROOT)+'[pdebench]'],
                       check=True,env=environment)
    command=[str(python),str(Path(__file__).resolve()),*sys.argv[1:],'--no-bootstrap']
    raise SystemExit(subprocess.run(command).returncode)


def acquire_lock(path):
    try:
        return os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError:
        try:
            pid=int(path.read_text().strip())
            if pid<=0:raise ValueError('Invalid lock PID')
            os.kill(pid,0)
        except ProcessLookupError:
            path.unlink()
            return os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        except (ValueError,PermissionError):
            pass
        raise FileExistsError('Another preparation run owns '+str(path)+'; inspect its PID before removing the lock')


def main(argv=None):
    args=parser().parse_args(argv)
    if args.budget_gb<=0 or args.candidate_pool<18 or args.timeout<=0 or (args.max_cases is not None and args.max_cases<1):
        parser().error('budget/timeout/max-cases must be positive; candidate-pool must be at least 18')
    from utils.PDEBench.models import BY_TASK,MODELS,source_files
    chosen=[]
    for name in args.tasks:
        matches=MODELS if name=='all' else [m for m in MODELS if name == m.task]
        if not matches:parser().error('Unknown task: '+name)
        for model in matches:
            if model not in chosen:chosen.append(model)
    catalog=json.loads(args.catalog.read_text())
    plan={'dataset':catalog['dataset'],'version':catalog['version'],'budget_bytes':int(args.budget_gb*1e9),
          'tasks':[{'task':m.task,'sources':len(source_files(m,catalog)),
                    'whole_source_bytes':sum(s['bytes'] for s in source_files(m,catalog)),
                    'strategy':'selected frames via bounded HTTP ranges',
                    'reference':'source-aligned audit and equilibrium correction' if args.reference_mode=='official' else 'independent reference where implemented'} for m in chosen]}
    if args.plan:
        print(json.dumps(plan,ensure_ascii=False,indent=2));return 0
    bootstrap(args)
    from utils.PDEBench.pipeline import prepare_task
    from utils.PDEBench.storage import Budget,PreparationError,atomic_json
    from caeoj.task_paths import task_directory
    runtime=args.cache_root.resolve()
    destinations={m.task: args.output_root.resolve()/m.task if args.output_root is not None
                  else task_directory(m.task,ROOT) for m in chosen}
    for model in chosen:
        task=destinations[model.task]
        canonical=task_directory(model.task,ROOT)
        if task!=canonical:
            task.mkdir(parents=True,exist_ok=True)
            for name in ('instruction.md','DATA.md'):
                source=canonical/name
                target=task/name
                if not target.exists():target.write_bytes(source.read_bytes())
    # Account for the existing managed tree without requiring every unselected
    # task to be present, unique, or readable as an executable task.
    budget=Budget([runtime,args.output_root or ROOT/'qbank'],plan['budget_bytes'])
    reports=[]
    try:
        budget.check()
        # One process owns the shared budget and staged output at a time.
        runtime.mkdir(parents=True,exist_ok=True)
        lock=runtime/'prepare.lock'
        fd=acquire_lock(lock)
    except (PreparationError,FileExistsError) as exc:
        print(str(exc),file=sys.stderr);return 1
    try:
        with os.fdopen(fd,'w') as stream:stream.write(str(os.getpid())+'\n')
        for model in chosen:
            print('Preparing '+model.task,flush=True)
            try:
                result=prepare_task(model,catalog,destinations[model.task],runtime/'cache',runtime/'staging',budget,
                                    args.source_dir,args.candidate_pool,args.timeout,args.max_cases,args.reference_dir,
                                    args.reference_mode,args.refresh_contract)
            except (PreparationError,ValueError,KeyError,OSError) as exc:
                result={'task':model.task,'status':'failed','error':str(exc),'grading_ready':False}
                atomic_json(destinations[model.task]/'author/preparation.json',result)
            reports.append(result)
            atomic_json(runtime/'reports/latest.json',{'plan':plan,'tasks':reports,
                        'managed_bytes':budget.used(),'accounted_peak_bytes':budget.peak})
            print(model.task+': '+result['status'],flush=True)
    finally:
        lock.unlink(missing_ok=True)
    print('Report: '+str(runtime/'reports/latest.json'))
    if any(r['status']=='failed' for r in reports):return 1
    if any(r['status']=='reference_pending' for r in reports):return 2
    return 0


if __name__=='__main__':
    try:raise SystemExit(main())
    except KeyboardInterrupt:
        print('Interrupted; completed cache blocks and cases remain reusable.',file=sys.stderr)
        raise SystemExit(130)
    except (RuntimeError,OSError,ValueError,KeyError,ImportError) as exc:
        print('Preparation failed: '+str(exc),file=sys.stderr)
        raise SystemExit(1)
