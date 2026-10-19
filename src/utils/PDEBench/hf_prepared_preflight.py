"""Classify frozen prepared bundles without downloading numerical payloads."""
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
    from huggingface_hub import HfApi,hf_hub_download
    from caeoj_tools import data_pool as pool
    from caeoj_tools.data_pool_shards import PartitionStore
    plan=json.loads((OUT/'plan.json').read_text());api=HfApi();repo=plan['repository'];checks=[]
    tasks={'advection':'pdebench-advection-1d','burgers':'pdebench-burgers-1d','compressible':'pdebench-compressible-1d'}
    for q in plan['quarantined_prepared_batches']:
        state=pool.checked_json(hf_hub_download(repo,q['state_path'],repo_type='dataset',revision=q['branch_revision']))
        if state['status']!='prepared' or state['batch_key']!=q['batch_key']:raise ValueError('Frozen checkpoint differs')
        task='qbank/01-prescribed-pdes/pdebench-archive/'+tasks[q['family']]
        prefix=task+'/pool/batches/'+state['transport_sha256']
        present=api.get_paths_info(repo,[prefix+'/transport.json'],repo_type='dataset',revision=q['branch_revision'])
        item={'batch_key':q['batch_key'],'file':q['file'],'first':q['first'],'count':q['count']}
        if not present:
            if api.get_paths_info(repo,[prefix],repo_type='dataset',revision=q['branch_revision']):
                raise ValueError('Partially staged immutable folder requires explicit inspection')
            for revision in (q['branch_revision'],plan['consolidated_revision']):
                view=PartitionStore(pool.HubStore(repo,revision),task,ROOT/'runs/pdebench-cloud-trial/partial-audit'/'absent-check')
                if any(view.lookup(b['case_id']) is not None for b in state['selection']['cases'].values()):
                    raise ValueError('Prepared case is already bound; cannot regenerate')
            item.update(recovery_mode='regenerate_unpublished',entire_batch_folder_absent=True,
                all_case_ids_absent_in_source_and_consolidated_pool=True,
                guard='Whole old bundle and old case IDs absent: preserve old candidate; fresh publication must prove identical pinned sources, source/problem JSON and all source/mapped arrays; complete full remote consumption before acceptance')
        else:
            path=Path(hf_hub_download(repo,prefix+'/transport.json',repo_type='dataset',revision=q['branch_revision']))
            if pool.digest(path)!=state['transport_sha256']:raise ValueError('Prepared transport differs')
            catalog=pool.checked_json(path)
            assets=[e[k] for e in catalog['shards'] for k in ('archive','locator')]+[{'path':x} for x in ('index.json','selection.json','transport.json')]
            info={f.path:f for f in api.get_paths_info(repo,[prefix+'/'+x['path'] for x in assets],repo_type='dataset',revision=q['branch_revision'])}
            for asset in assets:
                f=info[prefix+'/'+asset['path']]
                if 'size_bytes' in asset and f.size!=asset['size_bytes']:raise ValueError('Prepared size differs')
                if '.tar' in asset['path'] and (not f.lfs or f.lfs.sha256!=asset['sha256']):raise ValueError('Prepared TAR identity differs')
            item.update(recovery_mode='import_existing_bundle',assets_present=len(assets),transport_and_tar_hash_metadata_match=True)
        q['recovery_mode']=item['recovery_mode'];checks.append(item)
    result={'passed':True,'checks':checks,'numerical_payload_downloaded':False,'real_cloud_consumption_still_required':True}
    pool.write_json(OUT/'prepared-preflight.json',result);pool.write_json(OUT/'plan.json',plan)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
