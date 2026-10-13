"""Deterministic selection, atomic case preparation, and explicit reference status."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

import h5py
import numpy as np

from caeoj.sdk import load_problem, load_result
from .conversion import build_input, input_identity, write_analytic_reference
from .models import parameters, public_sources, source_files
from .sources import Reader, check_initial, feature, frame_indices, open_source
from .storage import PreparationError, atomic_json, digest


VERSION = 1


def tool_hash():
    h=hashlib.sha256()
    for name in ('models.py','sources.py','conversion.py','pipeline.py','storage.py'):
        h.update(name.encode());h.update((Path(__file__).parent/name).read_bytes())
    return h.hexdigest()


def contract_hash(task):
    h=hashlib.sha256()
    for name in ('instruction.md','DATA.md'):
        h.update(name.encode());h.update((Path(task)/name).read_bytes())
    return h.hexdigest()


def spread(candidates, count, key='gradient'):
    ordered=sorted(candidates,key=lambda c:(c[key],c['source_id'],c['index']))
    if len(ordered)<count:
        raise PreparationError(f"Candidate group has {len(ordered)} trajectories; needs {count}")
    indices=frame_indices(len(ordered),count)
    return [ordered[int(i)] for i in indices]


def select(model, sources, cache, budget, local, pool, timeout, max_cases=None):
    candidates=[]
    file_by_id={s['id']:s for s in sources}
    inspect_sources=sources
    if max_cases is not None and not (model.grouped or model.points):
        wanted={s['id'] for s in public_sources(model,sources)}
        remaining=max_cases
        for s in sources:
            if remaining<=0:break
            wanted.add(s['id'])
            remaining-=1 if s['filename'].startswith('Sod') else model.hidden_per_file
        inspect_sources=[s for s in sources if s['id'] in wanted]
    for source in inspect_sources:
        print(f"  inspect {source['filename']}",flush=True)
        with open_source(source,cache,budget,local,timeout) as handle:
            reader=Reader(handle,model)
            count=min(reader.count,pool if model.grouped or model.points else max(8,model.hidden_per_file+2))
            for index in range(count):
                coords,times,config=reader.metadata(index)
                values=reader.values(index,np.array([0],dtype=np.int64))
                check_initial(model,values)
                magnitude,gradient=feature(model,values)
                fingerprint=hashlib.sha256()
                for key in sorted(values): fingerprint.update(key.encode());fingerprint.update(values[key].tobytes())
                candidates.append({'source_id':source['id'],'index':index,'magnitude':magnitude,
                                   'gradient':gradient,'initial_sha256':fingerprint.hexdigest()})
    public=[]
    if model.grouped or model.points:
        public=spread(candidates,2,key='magnitude')
    else:
        for index,source in enumerate(public_sources(model,sources)):
            eligible=[c for c in candidates if c['source_id']==source['id'] and c not in public]
            ordered=sorted(eligible,key=lambda c:(c['gradient'],c['index']))
            if not ordered: raise PreparationError("No separate public trajectory available")
            public.append(ordered[0 if index==0 else -1])
    public_keys={(c['source_id'],c['index']) for c in public}
    # Identical inputs are also excluded from hidden/public overlap.
    public_hashes={c['initial_sha256'] for c in public}
    remaining=[c for c in candidates if (c['source_id'],c['index']) not in public_keys
               and c['initial_sha256'] not in public_hashes]
    hidden=[]
    if model.grouped or model.points:
        if model.model in ('diffusion_sorption_1d','shallow_water_2d'):
            ordered=sorted(remaining,key=lambda c:(c['magnitude'],c['index']))
            groups=[list(a) for a in np.array_split(np.array(ordered,dtype=object),4)]
        else:
            med_m=np.median([c['magnitude'] for c in remaining])
            med_g=np.median([c['gradient'] for c in remaining])
            groups=[[] for _ in range(4)]
            for c in remaining:
                if model.points:
                    group=2*int(c['magnitude']>=med_m)+int(c['gradient']>=med_g)
                else:
                    group=2*int(c['gradient']>=med_g)+int(c['magnitude']>=med_m)
                groups[group].append(c)
        for number,group in enumerate(groups):
            needed=4 if max_cases is None else max(0,min(4,max_cases-len(hidden)))
            if needed:hidden.extend([{**c,'group':number+1} for c in spread(group,needed)])
    else:
        for number,source in enumerate(sources):
            if max_cases is not None and len(hidden)>=max_cases:break
            group=[c for c in remaining if c['source_id']==source['id']]
            needed=1 if source['filename'].startswith('Sod') else model.hidden_per_file
            if max_cases is not None:needed=min(needed,max_cases-len(hidden))
            # A single published Sod trajectory cannot become three independent tests.
            if len(group)<needed:
                raise PreparationError(f"{source['filename']}: only {len(group)} distinct hidden candidates, needs {needed}")
            hidden.extend([{**c,'group':number+1} for c in spread(group,needed)])
    entries=[{**c,'kind':'sample','id':f'{i+1:02d}','variant':0} for i,c in enumerate(public)]
    group_counts={}
    for i,c in enumerate(hidden):
        group=c['group'];variant=group_counts.get(group,0)%2
        group_counts[group]=group_counts.get(group,0)+1
        entries.append({**c,'kind':'case','id':f'{i+1:03d}','variant':variant})
    if max_cases is not None: entries=[e for e in entries if e['kind']=='sample' or int(e['id'])<=max_cases]
    return entries


def install_directory(staged, target):
    """Atomic rename with rollback; never merge stale arrays into a new case."""
    target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
    backup=target.with_name('.'+target.name+'.previous')
    if backup.exists():
        if target.exists(): raise PreparationError(f"Interrupted installation needs inspection: {backup}")
        backup.rename(target)
    if target.exists(): target.rename(backup)
    try: Path(staged).rename(target)
    except BaseException:
        if backup.exists(): backup.rename(target)
        raise
    if backup.exists(): shutil.rmtree(backup)


def save_selected(path,model,source,index,coords,times,frames,values,config,budget):
    payload=sum(v.nbytes for v in values.values())+sum(c.nbytes for c in coords)+times.nbytes
    budget.check(payload+65536)
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix('.partial.h5')
    with h5py.File(temporary,'w') as out:
        out.attrs['source_id']=source['id'];out.attrs['sample_index']=index
        out.attrs['config']=json.dumps(config,ensure_ascii=False)
        for key,val in values.items(): out.create_dataset(key,data=val)
        out.create_dataset('times',data=times)
        out.create_dataset('frame_indices',data=frames)
        for axis,coord in zip('xyz',coords): out.create_dataset(axis+'-coordinate',data=coord)
    os.replace(temporary,path)
    atomic_json(path.with_suffix('.json'),{'sha256':digest(path),'source':source,
                'integrity_scope':'selected_payload_sha256; range blocks checked; full-source MD5 only for local full files'})


def selected(path,model,source,index,cache,budget,local,timeout,requested):
    cert=path.with_suffix('.json')
    if path.exists() and cert.exists():
        info=json.loads(cert.read_text())
        if info['source']==source and digest(path)==info['sha256']:
            with h5py.File(path,'r') as handle:
                coords=[handle[a+'-coordinate'][...] for a in 'xyz'[:model.dimension]]
                values={k:handle[k][...] for k in handle if k not in {'times','frame_indices',*[a+'-coordinate' for a in 'xyz']}}
                return coords,handle['times'][...],handle['frame_indices'][...],values,json.loads(handle.attrs['config'])
    with open_source(source,cache,budget,local,timeout) as handle:
        reader=Reader(handle,model)
        coords,times,config=reader.metadata(index)
        frames=frame_indices(len(times),requested)
        shape=tuple(len(c) for c in coords)
        # Preflight selected source payload + input + reference + mesh/staging duplicate.
        components=sum(f[3] for f in model.fields)+(3 if model.points else 1 if model.model=='darcy_flow_2d' else 0)
        estimate=int(np.prod(shape))*(requested*components*8*4+600)
        budget.check(estimate)
        values=reader.values(index,frames)
        if any(not np.isfinite(v).all() for v in values.values()):
            raise PreparationError("Nonfinite selected source trajectory")
        save_selected(path,model,source,index,coords,times[frames],frames,values,config,budget)
        return coords,times[frames],frames,values,config


def prepare_entry(model,source,entry,task,cache,staging,budget,local,timeout,reference_root=None):
    public=entry['kind']=='sample'
    requested=5 if public else 9
    payload=cache/'selections'/str(source['id'])/f"{entry['index']}-{requested}.h5"
    coords,times,frames,values,config=selected(payload,model,source,entry['index'],cache,budget,local,timeout,requested)
    initial={k:v[0:1] for k,v in values.items()}
    check_initial(model,initial)
    shape=tuple(len(c) for c in coords)
    budget.check(int(np.prod(shape))*(len(times)*sum(f[3] for f in model.fields)*8*3+600))
    if model.model=='darcy_flow_2d': times=np.array([0.])
    else:
        maximum=2 if model.model in ('advection_1d','burgers_1d') or (model.dimension==1 and source['filename'].startswith('Sod')) else 500 if model.model=='diffusion_sorption_1d' else 5 if model.model=='reaction_diffusion_2d' else 4.995 if model.points else 1
        if times[-1] > maximum+1e-6: raise PreparationError("Source time is outside task contract")
    contract=contract_hash(task)
    build_key=hashlib.sha256(json.dumps({'version':VERSION,'tool_sha256':tool_hash(),'entry':entry,'contract':contract,
                             'payload':digest(payload)},sort_keys=True).encode()).hexdigest()
    target=task/'samples'/entry['id'] if public else task/'cases'/entry['id']
    record_path=task/'author'/'prepared'/f"{entry['kind']}-{entry['id']}.json"
    reusable=False
    if record_path.exists():
        previous=json.loads(record_path.read_text())
        expected=previous.get('files',{})
        reusable=(previous.get('build_key')==build_key and expected and
                  all((task/name).is_file() and digest(task/name)==sha for name,sha in expected.items()))
        if reusable and not reference_root: return {**previous,'reused':True}
        if reusable and reference_root and previous.get('status')=='reference_prepared':
            external=Path(reference_root)/model.task/entry['kind']/entry['id']
            if not (external/'reference.npz').exists() and not (external/'evidence.json').exists():
                return {**previous,'reused':True}
    elif target.exists() and any(p.is_file() and p.name!='.gitkeep' for p in target.rglob('*')):
        raise PreparationError(f"Refusing to replace an existing case not owned by this tool: {target}")
    staging.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=staging,prefix='convert-') as temporary:
        stage=Path(temporary)
        input_dir=stage/'input'
        if reusable:
            shutil.copytree(target/'input' if public else target,input_dir)
            problem=load_problem(input_dir/'problem.json')
        else:
            problem=build_input(model,source,coords,times,values,input_dir,entry['variant'])
        identity=input_identity(problem)
        certificate={'source_id':source['id'],'source_md5':source['md5'],
                     'sample_index':entry['index'],'frame_indices':frames.tolist(),
                     'shape':list(shape),'source_axes':'y,x transposed to x,y' if model.model=='reaction_diffusion_2d' else 'x,y,z in C order',
                     'contract_sha256':contract,'input_files':identity,'build_key':build_key,
                     'tool_version':VERSION,'tool_sha256':tool_hash(),'status':'reference_pending',
                     'source_coordinate_axes':[c.tolist() for c in coords],
                     'coordinate_interpretation':'ordered source samples assigned to task cell averages; no claim of source continuum equivalence' if not model.points else 'centred source samples interpreted on task unit square; source-domain audit pending'}
        ref_dir=stage/'reference';ref_dir.mkdir()
        reference=ref_dir/'reference.npz'
        candidate=ref_dir/'official-candidate.npz'
        from caeoj.sdk import write_result
        write_result(candidate,problem,{name:values[name].reshape(len(times),-1,c)
                                        for name,_,_,c in model.fields})
        certificate['official_candidate']={'filename':'official-candidate.npz',
                'sha256':digest(candidate),'status':'unreviewed_do_not_grade',
                'meaning':'converted source values; not asserted to solve this continuous task'}
        if model.model=='advection_1d':
            certificate['evidence']=write_analytic_reference(problem,reference)
            certificate['status']='reference_prepared'
        elif reference_root:
            external=Path(reference_root)/model.task/entry['kind']/entry['id']
            supplied=external/'reference.npz';evidence=external/'evidence.json'
            if supplied.exists()!=evidence.exists():
                raise PreparationError('External reference.npz and evidence.json must both exist')
            if supplied.exists() and evidence.exists():
                audit=json.loads(evidence.read_text())
                if (audit.get('status')!='audited' or audit.get('contract_sha256')!=contract or
                    audit.get('input_files')!=identity or audit.get('reference_sha256')!=digest(supplied) or
                    not audit.get('method') or not audit.get('error_evidence')):
                    raise PreparationError("External reference evidence does not bind to this exact input/contract")
                imported=load_result(problem,supplied)
                if not model.points:
                    for output,initial,_,_ in model.fields:
                        if initial and not np.array_equal(imported[output][0:1],problem.arrays[initial]):
                            raise PreparationError('Reviewed reference t=0 does not match the contracted initial averages')
                shutil.copyfile(supplied,reference)
                # Preserve reviewer provenance; do not call supplied assertions
                # a proof or an independently measured error by this tool.
                certificate['evidence']={**audit,'kind':'external_review_assertion'}
                certificate['status']='reference_prepared'
        if reference.exists(): certificate['reference_sha256']=digest(reference)
        atomic_json(ref_dir/'certificate.json',certificate)
        if public:
            sample=stage/'sample';sample.mkdir();input_dir.rename(sample/'input')
            output=sample/'output';output.mkdir()
            if reference.exists(): shutil.copyfile(reference,output/'result.npz')
            install_directory(sample,target)
            private=task/'author'/'sample-certificates'/entry['id']
            install_directory(ref_dir,private)
        else:
            install_directory(input_dir,target)
            install_directory(ref_dir,task/'reference'/entry['id'])
        files={str(p.relative_to(task)):digest(p) for p in target.rglob('*') if p.is_file()}
        private=task/'author'/'sample-certificates'/entry['id'] if public else task/'reference'/entry['id']
        files.update({str(p.relative_to(task)):digest(p) for p in private.rglob('*') if p.is_file()})
        record={'kind':entry['kind'],'id':entry['id'],'status':certificate['status'],
                'build_key':build_key,'files':files,'input_files':identity,'shape':list(shape),
                'estimated_output_bytes':int(np.prod(shape))*len(times)*sum(f[3] for f in model.fields)*8}
        atomic_json(record_path,record)
        budget.check()
        return record


def prepare_task(model,catalog,task,cache,staging,budget,local=None,pool=64,timeout=45,
                 max_cases=None,reference_root=None):
    sources=source_files(model,catalog)
    if not sources: raise PreparationError("No pinned sources for task")
    selection_path=task/'author'/'selection.json'
    identity=hashlib.sha256(json.dumps({'catalog':catalog,'contract':contract_hash(task),
                      'pool':pool,'max_cases':max_cases,'version':VERSION},sort_keys=True).encode()).hexdigest()
    if selection_path.exists():
        selection=json.loads(selection_path.read_text())
        if selection.get('identity')!=identity:
            raise PreparationError("Frozen selection differs from this catalog/contract/options; use a separate output root")
        entries=selection['entries']
    else:
        entries=select(model,sources,cache,budget,local,pool,timeout,max_cases)
        selection={'version':VERSION,'identity':identity,'task':model.task,'status':'frozen',
                   'source_files':sources,'entries':entries}
        atomic_json(selection_path,selection)
    file_by_id={s['id']:s for s in sources}
    records=[]
    for entry in entries:
        print(f"  prepare {entry['kind']} {entry['id']}",flush=True)
        records.append(prepare_entry(model,file_by_id[entry['source_id']],entry,task,cache,staging,
                                     budget,local,timeout,reference_root))
    pending=sum(r['status']=='reference_pending' for r in records)
    report={'task':model.task,'status':'reference_pending' if pending else 'references_prepared',
            'samples':sum(r['kind']=='sample' for r in records),
            'cases':sum(r['kind']=='case' for r in records),'pending_references':pending,
            'records':records,'partial_selection':max_cases is not None,
            'grading_ready':False,
            'remaining':['Calibrate error thresholds and execution resources; no judge-config generated']}
    if any(r['estimated_output_bytes']>128*1024**2 for r in records):
        report['remaining'].append('Current Harbor output-size limit is 128 MiB; high-dimensional outputs require an audited change')
    atomic_json(task/'author'/'preparation.json',report)
    return report
