"""Retain RC4's source identities while rebinding changed grading assets.

This copies existing provenance, not certificates or claims of new numerical
qualification. Pool descriptors/index are author products; assembly receipts
are only regenerated through the real assembly operation.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from caeoj_tools import data_pool as pool

ROOT=Path('D:/Code/CAE-Bench-OJ');WORK=ROOT/'runs/continuous-scoring'
plan_path=WORK/'plan.json'
plan=json.loads((plan_path if plan_path.exists() else ROOT/'runs/uniform-samples/plan.json').read_text(encoding='utf-8'))
prepared=json.loads((WORK/'preparation.json').read_text(encoding='utf-8'))
record_path=WORK/'provenance-preservation.json'
records=json.loads(record_path.read_text(encoding='utf-8')) if record_path.exists() else []
completed={row['task'] for row in records}
eligible={row['task'] for row in json.loads((WORK/'state.json').read_text(encoding='utf-8'))['tasks']}
for entry,old_record in zip(plan['tasks'],prepared):
    assert entry['task']==old_record['task']
    if not old_record['revised_grading']:continue
    if entry['task'] in completed:continue
    if '--completed-only' in sys.argv and entry['task'] not in eligible:continue
    old=Path(old_record['original_root']);before=pool.manifest(old/'data-manifest.json')
    old_receipt=json.loads((old/'.data-assembly.json').read_text(encoding='utf-8'))
    assert hashlib.sha256(pool.encoded(before)).hexdigest()==old_receipt['selection_sha256']
    origins={}
    for role in ('cases','samples'):
        for choice in before[role].values():
            raw=old_receipt['descriptors'][choice['case']['path']]
            assert hashlib.sha256(raw.encode()).hexdigest()==choice['case']['sha256']
            descriptor=json.loads(raw);case_id=choice['case_id']
            assert descriptor['case_id']==case_id
            if case_id in origins:assert origins[case_id]==descriptor
            origins[case_id]=descriptor
    bundle=WORK/'pools'/entry['task'];selected=pool.manifest(bundle/'selection.json')
    store=pool.LocalStore(bundle/'repository');prefix=selected['repository']['path']
    # pack.py already validated this complete bundle and strictly assembled it.
    # Preserve its inventory while correcting provenance metadata only.
    repository_inventory={p.relative_to(store.root).as_posix() for p in store.root.rglob('*') if p.is_file()}
    index_path=store.get(prefix+'/'+selected['pool']['index'])
    index=json.loads(index_path.read_text(encoding='utf-8'));changed=[]
    for case_id,binding in index['cases'].items():
        descriptor_path=store.get(prefix+'/'+binding['path'])
        assert pool.digest(descriptor_path)==binding['sha256']
        descriptor=json.loads(descriptor_path.read_text(encoding='utf-8'));previous=origins[case_id]
        assert descriptor['case_id']==previous['case_id']
        assert set(descriptor['input']['files'])==set(previous['input']['files'])
        for name in descriptor['input']['files']:assert descriptor['files'][name]==previous['files'][name]
        non_grading=lambda d:{k:v for k,v in d['files'].items() if k!='reference/grading.json'}
        assert non_grading(descriptor)==non_grading(previous),(entry['task'],case_id)
        if descriptor['origin']!=previous['origin']:
            descriptor['origin']=deepcopy(previous['origin'])
            pool.write_json(descriptor_path,descriptor)
            binding['sha256']=pool.digest(descriptor_path);changed.append(case_id)
    if changed:
        pool.write_json(index_path,index)
        # select reads the updated index, so all descriptor bindings are real.
        selected=pool.select(selected,store,[f"{k}={v['case_id']}" for k,v in before['cases'].items()],[],
                             format_samples=[f"{k}={v['case_id']}" for k,v in before['samples'].items()])
        selected['notes']='Offline RC5 continuous-scoring revision; original RC4 source identity retained without re-certification. New descriptors have not been uploaded to HF.'
        pool.write_json(bundle/'selection.json',selected)
        assert repository_inventory=={p.relative_to(store.root).as_posix() for p in store.root.rglob('*') if p.is_file()}
        target=WORK/'stage'/entry['task_path']
        pool.assemble(target,selected,store)
        pool.write_json(target/'data-manifest.json',selected)
        assert pool.verify(target,strict=True)['valid']
        current=ROOT/entry['task_path']
        refreshed=(current/'.data-assembly.json').exists()
        if refreshed:pool.assemble(current,selected,store,update=True)
        pool.write_json(current/'data-manifest.json',selected)
        if refreshed:assert pool.verify(current,strict=True)['valid']
    records.append({'task':entry['task'],'source_identities_preserved':len(origins),
                    'origins_restored':changed,'new_certificate_created':False,
                    'rc4_receipt_sha256':pool.digest(old/'.data-assembly.json'),
                    'all_non_grading_descriptor_assets_unchanged':True,
                    'validation_basis':'Original numerical bundle validation retained; only origin/index bindings changed with unchanged repository inventory. Real select/plan binding checks, assemble/fetch numerical preflight and strict verification run for every changed origin.'})
    pool.write_json(WORK/'provenance-preservation.json',records)
    print(entry['task'],'source identities retained; restored',len(changed),flush=True)
if '--completed-only' not in sys.argv:assert len(records)==80
