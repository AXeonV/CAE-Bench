"""Read-only independent consolidated descriptor/source coverage verification."""
import hashlib
import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'qbank/design/reviews/pdebench-low-commit-20261019'


def main():
    global OUT
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path);args=parser.parse_args()
    if args.out:OUT=args.out.resolve()
    from huggingface_hub import hf_hub_download
    from caeoj_tools import data_pool as pool
    from caeoj_tools.data_pool_shards import PartitionStore
    receipt=json.loads((OUT/'merge-receipt.json').read_text());audit=json.loads((OUT/'audit.json').read_text())
    if receipt['status']!='completed':raise ValueError('Merge not yet completed')
    repo=audit['repository'];revision=receipt['final_revision']
    source=pool.checked_json(hf_hub_download(repo,'migration-trials/pdebench/2026-10-18/source-probe/report.json',repo_type='dataset',revision=audit['source_revision']))
    sources={s['file']:s for s in source['sources']};actual=set();counts={};case_ids=set()
    for family,task in [('advection','pdebench-advection-1d'),('burgers','pdebench-burgers-1d'),('compressible','pdebench-compressible-1d')]:
        prefix='qbank/01-prescribed-pdes/pdebench-archive/'+task
        view=PartitionStore(pool.HubStore(repo,revision),prefix,ROOT/'runs/pdebench-cloud-trial/partial-audit'/('check-'+family))
        n=0
        for key in view.index['partitions']:
            for cid,binding in view.partition(key).items():
                descriptor=binding['descriptor'];identity=descriptor['origin']['certificate_identity'];file=identity['source_file'];raw=sources[file]
                if (hashlib.sha256(pool.encoded(descriptor)).hexdigest()!=binding['sha256'] or descriptor['case_id']!=cid
                    or not binding['input_complete'] or not binding['reference_complete'] or cid in case_ids):
                    raise ValueError('Descriptor identity/completeness differs')
                if (raw['family']!=family or identity['source_repository']!=raw['repo_id']
                    or identity['source_revision']!=raw['revision'] or identity['source_sha256']!=raw['source_lfs_sha256']):
                    raise ValueError('Pinned source identity differs')
                row=(file,identity['sample_index'])
                if row in actual:raise ValueError('Repeated source row across consolidated pools')
                actual.add(row);case_ids.add(cid);n+=1
        if n!=view.index['case_count'] or n!=audit['family_verified_cases'][family]:raise ValueError('Root membership differs')
        counts[family]=n
    expected={(file,i) for file,rows in audit['coverage'].items() for i in rows}
    if actual!=expected or len(actual)!=audit['verified_cases']:raise ValueError('Consolidated source coverage differs from accepted checkpoints')
    result={'valid':True,'fixed_revision':revision,'verified_cases':len(actual),'family_counts':counts,
        'descriptor_sha_case_id_and_completeness_checked':True,'unique_sources_match_audited_coverage':True,
        'source_repository_revision_and_sha_metadata_checked':True,'independent_full_source_file_checksums_recomputed':False,
        'fresh_numerical_consumption_performed':False,'numerical_payload_downloaded':False,
        'source_field_validation_basis':'Prior verified batch fixed-commit consumption receipts; copied blob and descriptor identity retained'}
    pool.write_json(OUT/'consolidated-check.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':main()
