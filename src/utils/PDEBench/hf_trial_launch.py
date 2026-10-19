#!/usr/bin/env python3
"""Submit a cloud source probe with a durable, cumulative USD reservation.

Only code and API metadata pass through this process. The worker reads arrays.
Unknown submission outcomes retain their reservation and are never auto-retried.
"""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
import zipfile
import io
import re


def runtime_payload(root):
    """Inventory code and this new contract only; never include arrays or secrets."""
    content = io.BytesIO()
    with zipfile.ZipFile(content, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(root/'pyproject.toml', 'pyproject.toml')
        for package in ('caeoj', 'caeoj_tools'):
            for path in sorted((root/'src'/package).rglob('*')):
                if path.is_file() and path.suffix in ('.py', '.json') and '__pycache__' not in path.parts:
                    archive.write(path, path.relative_to(root).as_posix())
        for name in ('__init__.py', 'conversion.py', 'storage.py', 'models.py'):
            archive.write(root/'src/utils/PDEBench'/name, 'support/utils/PDEBench/'+name)
        archive.writestr('support/utils/__init__.py', '')
        archive.write(root/'src/utils/PDEBench/hf_preflight.py', 'support/hf_preflight.py')
        archive.write(root/'src/utils/PDEBench/hf_readiness.py', 'support/hf_readiness.py')
        archive.write(root/'src/utils/PDEBench/hf_migrate.py', 'support/hf_migrate.py')
        docker = (root/'src/utils/harbor/environment/Dockerfile').read_text()
        libraries = sorted({name for name in re.findall(r'\blib[a-z0-9+.-]+\b', docker)
                            if not name.endswith('-dev')})
        archive.writestr('support/gmsh-system-packages.json', json.dumps(libraries))
        archive_tasks = root/'qbank/01-prescribed-pdes/pdebench-archive'
        if archive_tasks.exists():
            for path in sorted(archive_tasks.rglob('*')):
                if path.is_file() and path.name in ('instruction.md', 'DATA.md', 'data-manifest.json'):
                    archive.write(path, path.relative_to(root).as_posix())
        task = root/'qbank/01-prescribed-pdes/1.3-scalar-transport/linear-periodic-transport-1d'
        for name in ('instruction.md','DATA.md','author/grading-template.json','data-manifest.json','judge-config.json','harbor/task.toml'):
            archive.write(task/name, (task/name).relative_to(root).as_posix())
        archive.write(root/'docs/CONTRACT.md', 'docs/CONTRACT.md')
    return base64.b64encode(content.getvalue()).decode('ascii')


def reservation_usd(hardware, seconds):
    ceilings={'cpu-upgrade':500,'cpu-basic':167}
    if hardware['name'] not in ceilings or hardware['unit_label'] != 'minute':
        raise ValueError('Trial only permits the two minute-billed CPU flavors')
    rate = hardware['unit_cost_micro_usd'] / 1_000_000
    if not 0 < hardware['unit_cost_micro_usd'] <= ceilings[hardware['name']]:
        raise ValueError('CPU price increased; review budget before submitting')
    # One extra billed minute reserved for startup/rounding uncertainty.
    return round((math.ceil(seconds / 60) + 1) * rate, 6)


def effective_reservation(attempt):
    """Unknown/active jobs keep their full hold; terminal API bounds replace it."""
    bound=attempt.get('api_lifecycle_cost_upper_bound_usd')
    if attempt.get('status') in ('completed','error','canceled','cancelled') and isinstance(bound,(int,float)) and bound>0:
        return bound
    return attempt['maximum_reserved_compute_usd']


def settle_completed(api,ledger):
    """Use the full server lifecycle, including non-billed time and a minute.

    This is a conservative compute bound, not a claim to have read an invoice.
    Only this launcher's non-exposed CPU Jobs can release their reservation.
    """
    for attempt in ledger['attempts']:
        if 'api_lifecycle_cost_upper_bound_usd' in attempt or not attempt.get('job_id'):continue
        info=api.inspect_job(job_id=attempt['job_id'])
        if info.status.stage not in ('COMPLETED','ERROR','CANCELED','CANCELLED'):continue
        expected=attempt.get('hardware','cpu-upgrade')
        ceilings={'cpu-upgrade':500,'cpu-basic':167}
        rate=attempt.get('hardware_unit_cost_micro_usd',500 if expected=='cpu-upgrade' else None)
        if (expected not in ceilings or info.flavor!=expected or not isinstance(rate,(int,float))
                or not 0<rate<=ceilings[expected] or (getattr(info,'expose_urls',None) or getattr(info,'ssh_url',None))
                or info.finished_at is None):continue
        elapsed=(info.finished_at-info.created_at).total_seconds()
        if elapsed<0:raise ValueError('Invalid server lifecycle timestamps')
        attempt.update(status=info.status.stage.lower(),
            api_lifecycle_cost_upper_bound_usd=round((math.ceil(elapsed/60)+1)*rate/1_000_000,6))


def worker_path(phase,reference_only=False):
    if phase=='benchmark-export':return Path(__file__).with_name('hf_benchmark_export.py')
    if phase in ('archive-pilot','archive-full'):return Path(__file__).with_name('hf_archive_migrate.py')
    name='hf_burgers_preflight.py' if reference_only else ('hf_source_probe.py' if phase=='source' else 'hf_cost_calibration.py' if phase=='calibration' else 'hf_transport_trial.py')
    return Path(__file__).with_name(name)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-id', default='jimzhouzzy2006/CAE-Bench-OJ')
    parser.add_argument('--revision', default='pdebench-migration-trial-20261018')
    parser.add_argument('--prefix', default='migration-trials/pdebench/2026-10-18/source-probe')
    parser.add_argument('--ledger', type=Path, default=Path('runs/pdebench-cloud-trial/budget.json'))
    parser.add_argument('--per-file', type=int, default=10)
    parser.add_argument('--phase', choices=('source', 'transport', 'preflight','readiness','migration-prep','migration','calibration','archive-pilot','archive-full','benchmark-export'), default='source')
    parser.add_argument('--export-plan',type=Path)
    parser.add_argument('--baseline-revision', help='Fixed direct-archive pilot commit used by full migration')
    parser.add_argument('--source-revision', help='Fixed completed source-probe commit for transport phase')
    parser.add_argument('--submit', action='store_true')
    parser.add_argument('--reference-only', action='store_true', help='Preflight only: bounded Burgers published-formula diagnostic')
    parser.add_argument('--resume',action='store_true',help='Readiness only: resume using cloud checkpoint in a fresh Job')
    parser.add_argument('--calibration-mode',choices=('mechanical','references','auxiliary','cns-focus'))
    parser.add_argument('--source-file')
    parser.add_argument('--batch-start',type=int,default=0)
    parser.add_argument('--batch-count',type=int,default=1000)
    parser.add_argument('--hardware',choices=('cpu-upgrade','cpu-basic'),default='cpu-upgrade')
    args = parser.parse_args(argv)
    if args.phase=='benchmark-export' and (not args.export_plan or not args.export_plan.is_file()):parser.error('Export requires a frozen selection plan')
    if args.hardware=='cpu-basic' and args.phase not in ('migration-prep','migration','archive-pilot','archive-full','benchmark-export'):
        parser.error('CPU Basic calibration is limited to the actual migration pipeline')
    if args.phase=='archive-full' and (args.hardware!='cpu-basic' or not args.baseline_revision
            or not re.fullmatch('[0-9a-f]{40}',args.baseline_revision)):
        parser.error('Full migration requires CPU Basic and a fixed baseline commit')
    if args.phase=='calibration' and not args.calibration_mode:parser.error('Calibration requires --calibration-mode')
    if args.resume and args.phase!='readiness':parser.error('--resume requires readiness')
    if args.phase in ('migration','migration-prep') and (not args.source_file or not 1<=args.batch_count<=1000 or args.batch_start<0 or args.batch_start+args.batch_count>10000):
        parser.error('Migration requires a source file and valid 1..1000-row span within 10000')
    if args.reference_only and args.phase != 'preflight':
        parser.error('--reference-only requires --phase preflight')
    if not 1 <= args.per_file <= 100:
        parser.error('per-file must be 1..100')
    if args.phase=='archive-pilot' and not 0<=args.batch_start<=10000-args.per_file:
        parser.error('Archive pilot requires a valid source span within 10000 rows')
    if args.phase!='source' and not args.source_revision:
        parser.error('Transport phase requires a fixed --source-revision')
    from huggingface_hub import HfApi, get_token
    api = HfApi()
    owner = api.whoami()['name']  # Authenticate before making any mutation.
    if not args.repo_id.startswith(owner+'/'):
        parser.error('Trial destination must belong to the authenticated account')
    hardware = next(vars(x) for x in api.list_jobs_hardware() if x.name == args.hardware)
    seconds = 1800 if args.phase in ('readiness','migration-prep','calibration','archive-pilot') else 3600
    if args.phase=='archive-full':seconds=72*3600
    if args.phase=='benchmark-export':seconds=600
    if args.phase=='calibration' and args.calibration_mode=='cns-focus':seconds=600
    reserve = reservation_usd(hardware, seconds)
    if args.phase == 'preflight':
        # Additional Starting/rounding margin; new campaign has its own USD .10 cap.
        reserve = .04
    if args.phase in ('readiness','migration-prep','calibration'):reserve=.02
    if args.phase=='calibration' and args.calibration_mode=='cns-focus':reserve=.01
    if args.hardware=='cpu-basic':reserve=round(math.ceil((seconds+600)/60)*hardware['unit_cost_micro_usd']/1_000_000,6)
    worker=worker_path(args.phase,args.reference_only)
    specification = {'hardware': hardware['name'], 'timeout_seconds': seconds,
                     'hardware_unit_cost_micro_usd':hardware['unit_cost_micro_usd'],
                     'maximum_reserved_compute_usd': reserve, 'total_budget_usd': 1.0,
                     'repo_id': args.repo_id, 'revision': args.revision, 'prefix': args.prefix,
                     'per_file': args.per_file, 'worker_sha256': hashlib.sha256(worker.read_bytes()).hexdigest(),
                     'phase': args.phase, 'source_revision': args.source_revision,
                     'reference_only': args.reference_only}
    specification['resume']=args.resume
    if args.phase=='benchmark-export':specification['export_plan_sha256']=hashlib.sha256(args.export_plan.read_bytes()).hexdigest()
    if args.phase=='archive-full':specification.update(baseline_revision=args.baseline_revision,
        target_source_rows=250000,source_batch_max_records=1000,reused_pilot_rows=400)
    if args.phase=='archive-pilot':specification['batch_start']=args.batch_start
    if args.phase=='calibration':specification['calibration_mode']=args.calibration_mode
    if args.phase in ('migration','migration-prep'):
        specification.update(source_file=args.source_file,batch_start=args.batch_start,batch_count=args.batch_count)
    if not args.submit:
        print(json.dumps(specification, indent=2))
        return 0
    args.ledger.parent.mkdir(parents=True, exist_ok=True)
    lock = args.ledger.with_suffix('.lock')
    fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.close(fd)
        ledger = json.loads(args.ledger.read_text()) if args.ledger.exists() else {'budget_usd': 1.0, 'attempts': []}
        if ledger['budget_usd'] != 1.0:
            raise ValueError('Unexpected budget ledger')
        if any(a.get('status') == 'submission_pending' for a in ledger['attempts']):
            raise ValueError('Resolve the previous unknown submission before retrying')
        settle_completed(api,ledger)
        if args.phase=='archive-full' and any(a.get('phase')=='archive-full' and a.get('status') in ('submitted','submission_pending') for a in ledger['attempts']):
            raise ValueError('A full migration Job is already active or unresolved')
        if sum(effective_reservation(a) for a in ledger['attempts']) + reserve > 1.0:
            raise ValueError('Cumulative worst-case compute reservation would exceed USD 1')
        if args.phase == 'preflight' and sum(effective_reservation(a) for a in ledger['attempts'] if a.get('phase')=='preflight') + reserve > .1 + 1e-9:
            raise ValueError('Preflight campaign reservation would exceed USD 0.10')
        if args.phase in ('readiness','migration-prep','calibration','archive-pilot') and sum(effective_reservation(a) for a in ledger['attempts'] if a.get('phase') in ('readiness','migration-prep','calibration','archive-pilot'))+reserve>.1+1e-9:
            raise ValueError('Readiness campaign reservation would exceed USD 0.10')
        api.repo_info(args.repo_id, repo_type='dataset')
        branch_options={'revision':args.baseline_revision} if args.phase=='archive-full' else {}
        api.create_branch(args.repo_id, branch=args.revision, repo_type='dataset', exist_ok=True,**branch_options)
        attempt = {**specification, 'created_at': datetime.now(timezone.utc).isoformat(),
                   'status': 'submission_pending'}
        ledger['attempts'].append(attempt)
        args.ledger.write_text(json.dumps(ledger, indent=2)+'\n')
        token = get_token()
        if not token:
            raise ValueError('No usable local HF credential')
        script_args = ['--repo-id', args.repo_id, '--revision', args.revision, '--prefix', args.prefix]
        if args.phase == 'source':
            script_args += ['--per-file', str(args.per_file)]
        else:
            script_args += ['--source-revision', args.source_revision,
                            '--source-prefix', 'migration-trials/pdebench/2026-10-18/source-probe']
            if args.phase=='calibration':script_args+=['--calibration-mode',args.calibration_mode]
            if args.phase=='archive-pilot':script_args+=['--per-file',str(args.per_file),'--batch-start',str(args.batch_start)]
            if args.phase=='archive-full':script_args+=['--full','--hard-timeout-seconds',str(seconds),'--baseline-revision',args.baseline_revision]
            if args.phase == 'preflight': script_args += ['--preflight']
            if args.phase=='readiness':
                script_args+=['--readiness']
                if args.resume:script_args+=['--resume']
            if args.phase in ('migration','migration-prep'):
                script_args+=['--migrate','--source-file',args.source_file,'--batch-start',str(args.batch_start),'--batch-count',str(args.batch_count)]
        with tempfile.TemporaryDirectory(prefix='caeoj-job-code-') as temporary:
            staged = worker
            if args.phase in ('transport','preflight','readiness','migration','migration-prep','archive-pilot','archive-full','benchmark-export'):
                root = Path(__file__).resolve().parents[3]
                staged = Path(temporary)/worker.name
                payload = runtime_payload(root)
                attempt['runtime_zip_sha256'] = hashlib.sha256(base64.b64decode(payload)).hexdigest()
                staged_script, replacements = re.subn(r'^RUNTIME_ZIP = .*$', lambda _: 'RUNTIME_ZIP = '+repr(payload), worker.read_text(), flags=re.MULTILINE)
                if replacements != 1:raise ValueError('Expected exactly one runtime payload assignment')
                staged.write_text(staged_script)
                if args.phase=='benchmark-export':
                    encoded=base64.b64encode(args.export_plan.read_bytes()).decode()
                    staged.write_text(re.sub(r'^EXPORT_PLAN = .*$',lambda _: 'EXPORT_PLAN = '+repr(encoded),staged.read_text(),flags=re.MULTILINE))
            if args.phase=='calibration' and args.calibration_mode=='auxiliary':
                formula=worker.with_name('hf_burgers_preflight.py').read_bytes()
                staged=Path(temporary)/worker.name
                staged.write_text(worker.read_text().replace("FORMULA_PY = ''",'FORMULA_PY = '+repr(base64.b64encode(formula).decode())))
                attempt['formula_code_sha256']=hashlib.sha256(formula).hexdigest()
            attempt['submitted_script_sha256'] = hashlib.sha256(staged.read_bytes()).hexdigest()
            args.ledger.write_text(json.dumps(ledger, indent=2)+'\n')
            job = api.run_uv_job(str(staged), flavor=hardware['name'], timeout=seconds,
                                 script_args=script_args, secrets={'HF_TOKEN': token},
                                 name='caeoj-pdebench-'+args.phase,
                                 labels={'caeoj-purpose': 'pdebench-migration-trial', 'budget-usd': '1'})
        attempt.update(status='submitted', job_id=job.id, job_url=job.url)
        args.ledger.write_text(json.dumps(ledger, indent=2)+'\n')
        observed=api.inspect_job(job_id=job.id).flavor
        attempt['observed_hardware']=observed
        if observed!=hardware['name']:
            api.cancel_job(job_id=job.id)
            attempt['status']='canceled_hardware_mismatch'
            args.ledger.write_text(json.dumps(ledger, indent=2)+'\n')
            raise RuntimeError('Actual Job hardware differs from budgeted hardware; canceled and retained full reservation')
        args.ledger.write_text(json.dumps(ledger, indent=2)+'\n')
        print(json.dumps(attempt, indent=2))
    finally:
        lock.unlink(missing_ok=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
