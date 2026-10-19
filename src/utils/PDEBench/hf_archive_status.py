"""Read-only full-migration status; never reads source fields or case payloads."""
import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ledger', type=Path, default=Path('runs/pdebench-cloud-trial/budget.json'))
    parser.add_argument('--job-id', required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--settle-terminal', action='store_true', help='Settle only API-verifiable terminal Jobs under the shared ledger lock')
    args = parser.parse_args(argv)
    from huggingface_hub import HfApi, hf_hub_download
    spec = importlib.util.spec_from_file_location('budget_launcher', Path(__file__).with_name('hf_trial_launch.py'))
    launcher = importlib.util.module_from_spec(spec); spec.loader.exec_module(launcher)
    ledger = json.loads(args.ledger.read_text())
    attempts = [a for a in ledger['attempts'] if a.get('job_id') == args.job_id and a.get('phase') == 'archive-full']
    if len(attempts) != 1:
        raise ValueError('Expected exactly one registered full migration Job')
    attempt = attempts[0]
    api = HfApi(); job = api.inspect_job(job_id=args.job_id)
    if args.settle_terminal and job.status.stage in ('COMPLETED', 'ERROR', 'CANCELED', 'CANCELLED'):
        lock = args.ledger.with_suffix('.lock')
        descriptor = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(descriptor)
        try:
            ledger = json.loads(args.ledger.read_text())
            launcher.settle_completed(api, ledger)
            temporary = args.ledger.with_suffix('.settled.tmp')
            temporary.write_text(json.dumps(ledger, indent=2)+'\n')
            temporary.replace(args.ledger)
            attempt = next(a for a in ledger['attempts'] if a.get('job_id') == args.job_id)
        finally:
            lock.unlink(missing_ok=True)
    head = api.repo_info(attempt['repo_id'], repo_type='dataset', revision=attempt['revision']).sha
    path = attempt['prefix']+'/full-report.json'
    metadata = api.get_paths_info(attempt['repo_id'], [path], repo_type='dataset', revision=head)
    report = {}
    if metadata:
        if metadata[0].size > 5*1024**2:
            raise ValueError('Unexpectedly large progress JSON; no download')
        report = json.loads(Path(hf_hub_download(attempt['repo_id'], path, repo_type='dataset', revision=head)).read_text())
    counts = {family: 0 for family in ('advection', 'burgers', 'compressible')}
    for entry in report.get('baseline', [])+report.get('batches', []):
        counts[entry['family']] += entry['cases']
    snapshot = {'observed_at_utc': datetime.now(timezone.utc).isoformat(),
        'job_id': job.id, 'job_url': attempt['job_url'], 'job_status': job.status.stage,
        'job_message': job.status.message, 'hardware': job.flavor,
        'durations': vars(job.durations) if job.durations else None,
        'report_status': report.get('status', 'initializing'),
        'verified_cases': report.get('verified_cases', 0), 'family_verified_cases': counts,
        'target_cases': 250000, 'completed_batches': len(report.get('batches', [])),
        'planned_batches': len(report.get('recipe', {}).get('plan', [])),
        'current_batch': report.get('current_batch'), 'error': report.get('error'),
        'report_revision': head, 'report_path': path,
        'maximum_reserved_full_job_usd': attempt['maximum_reserved_compute_usd'],
        'full_job_lifecycle_compute_upper_bound_usd': attempt.get('api_lifecycle_cost_upper_bound_usd'),
        'cumulative_budget_occupation_usd': round(sum(launcher.effective_reservation(a) for a in ledger['attempts']), 6),
        'cumulative_budget_limit_usd': ledger['budget_usd'], 'invoice_verified': False,
        'source_or_case_payload_downloaded': False}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(snapshot, indent=2)+'\n')
    print(json.dumps(snapshot, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
