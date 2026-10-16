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
from .conversion import build_input, input_identity, write_analytic_reference, check_reference_initial
from .models import parameters, public_sources, source_files
from .sources import Reader, check_initial, feature, frame_indices, open_source
from .storage import PreparationError, atomic_json, digest


VERSION = 1


def tool_hash():
    h=hashlib.sha256()
    for name in ('models.py','sources.py','conversion.py','pipeline.py','storage.py','references.py','source_audit.py'):
        h.update(name.encode());h.update((Path(__file__).parent/name).read_bytes())
    # A storage/SDK change also invalidates byte-bound preparation records.
    for name in ('storage.py', 'sdk.py', 'validation.py', 'problem.schema.json'):
        h.update(('caeoj/' + name).encode())
        h.update((Path(__file__).parents[2] / 'caeoj' / name).read_bytes())
    return h.hexdigest()


def contract_hash(task):
    h=hashlib.sha256()
    for name in ('instruction.md','DATA.md'):
        h.update(name.encode());h.update((Path(task)/name).read_bytes().replace(b'\r\n',b'\n'))
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
        inventory_path=cache/'candidates'/model.task/f"{source['id']}.json"
        inventory_key=hashlib.sha256(json.dumps({'source':source,'model':model.model,
                         'reader_sha256':digest(Path(__file__).with_name('sources.py'))},sort_keys=True).encode()).hexdigest()
        inventory={}
        if inventory_path.exists():
            try:
                previous=json.loads(inventory_path.read_text())
                if previous.get('identity')==inventory_key:inventory=previous
            except (ValueError,OSError):pass
        cached={c['index']:c for c in inventory.get('entries',[])}
        requested=pool if model.grouped or model.points else max(8,model.hidden_per_file+2)
        if local is None and inventory.get('count') and all(i in cached for i in range(min(inventory['count'],requested))):
            candidates.extend(cached[i] for i in range(min(inventory['count'],requested)))
            continue
        with open_source(source,cache,budget,local,timeout) as handle:
            reader=Reader(handle,model)
            count=min(reader.count,requested)
            for index in range(count):
                if index in cached:
                    candidates.append(cached[index]);continue
                coords,times,config=reader.metadata(index, frames=np.array([0])) if model.points else reader.metadata(index)
                values=reader.values(index,np.array([0],dtype=np.int64))
                check_initial(model,values)
                magnitude,gradient=feature(model,values)
                fingerprint=hashlib.sha256()
                for key in sorted(values): fingerprint.update(key.encode());fingerprint.update(values[key].tobytes())
                candidate={'source_id':source['id'],'index':index,'magnitude':magnitude,
                           'gradient':gradient,'initial_sha256':fingerprint.hexdigest()}
                candidates.append(candidate);cached[index]=candidate
                budget.check(65536)
                atomic_json(inventory_path,{'identity':inventory_key,'count':reader.count,
                                           'entries':[cached[i] for i in sorted(cached)]})
                if count>8 and (index+1)%8==0:
                    print(f"    initial candidates {index+1}/{count}",flush=True)
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
    # Preserve the versioned empty-directory markers when materializing data.
    if target.exists():
        for marker in target.rglob('.gitkeep'):
            destination=Path(staged)/marker.relative_to(target)
            destination.parent.mkdir(parents=True,exist_ok=True)
            destination.touch()
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
        if model.points:
            frames=frame_indices(reader.h['velocity'].shape[1],requested)
            coords,times,config=reader.metadata(index,frames=frames)
            selected_times=times
        else:
            coords,times,config=reader.metadata(index)
            frames=frame_indices(len(times),requested)
            selected_times=times[frames]
        shape=tuple(len(c) for c in coords)
        # Preflight selected source payload + input + reference + mesh/staging duplicate.
        components=sum(f[3] for f in model.fields)+(3 if model.points else 1 if model.model=='darcy_flow_2d' else 0)
        estimate=int(np.prod(shape))*(requested*components*8*4+600)
        budget.check(estimate)
        values=reader.values(index,frames)
        if any(not np.isfinite(v).all() for v in values.values()):
            raise PreparationError("Nonfinite selected source trajectory")
        save_selected(path,model,source,index,coords,selected_times,frames,values,config,budget)
        return coords,selected_times,frames,values,config


def prepare_entry(model,source,entry,task,cache,staging,budget,local,timeout,reference_root=None,reference_mode='independent'):
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
    build_key=hashlib.sha256(json.dumps({'version':VERSION,'reference_mode':reference_mode,'tool_sha256':tool_hash(),'entry':entry,'contract':contract,
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
            if not (external/'reference.h5').exists() and not (external/'evidence.json').exists():
                return {**previous,'reused':True}
    else:
        definition=target/'input/problem.json' if public else target/'problem.json'
        existing=[p for p in target.rglob('*') if p.is_file() and p.name!='.gitkeep']
        # Fresh clones contain versioned definitions but not local ownership
        # records or numerical payloads. Only this known metadata-only state
        # may be hydrated without an existing preparation record.
        if any(p!=definition for p in existing):
            raise PreparationError(f"Refusing to replace an existing case not owned by this tool: {target}")
    staging.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=staging,prefix='convert-') as temporary:
        stage=Path(temporary)
        input_dir=stage/'input'
        if reusable:
            shutil.copytree(target/'input' if public else target,input_dir)
            problem=load_problem(input_dir/'problem.json')
        else:
            if model.model=='reaction_diffusion_2d':budget.check(int(config['sim']['xdim'])*int(config['sim']['ydim'])*600)
            problem=build_input(model,source,coords,times,values,input_dir,entry['variant'],config=config)
            definition=target/'input/problem.json' if public else target/'problem.json'
            if definition.is_file():
                if json.loads(definition.read_text())!=problem.manifest:
                    raise PreparationError(f'Existing problem definition differs from the frozen source conversion; preserving {definition}')
                # Keep the versioned definition byte-for-byte (including its
                # formatting), then bind the certificate to those actual bytes.
                shutil.copyfile(definition,input_dir/'problem.json')
                problem=load_problem(input_dir/'problem.json')
        identity=input_identity(problem)
        certificate={'source_id':source['id'],'source_md5':source['md5'],
                     'sample_index':entry['index'],'frame_indices':frames.tolist(),
                     'shape':list(shape),'source_axes':'y,x transposed to x,y' if model.model=='reaction_diffusion_2d' else 'x,y,z in C order',
                     'contract_sha256':contract,'input_files':identity,'build_key':build_key,
                     'tool_version':VERSION,'tool_sha256':tool_hash(),'status':'reference_pending',
                     'source_coordinate_axes':[c.tolist() for c in coords],
                     'coordinate_interpretation':'source cell averages; FHN uses reconstructed full initial grid and a subset of original output cells' if not model.points else 'source centered samples on the published unit Box, checked against short-time tracer transport'}
        ref_dir=stage/'reference';ref_dir.mkdir()
        reference=ref_dir/'reference.h5'
        candidate=ref_dir/'official-candidate.h5'
        from caeoj.sdk import write_result
        write_result(candidate,problem,{name:values[name].reshape(len(times),-1,c)
                                        for name,_,_,c in model.fields})
        certificate['official_candidate']={'filename':'official-candidate.h5',
                'sha256':digest(candidate),'status':'unreviewed_do_not_grade',
                'meaning':'converted source values; not asserted to solve this continuous task'}
        if reference_mode=='official' and not reference_root:
            from .source_audit import audit_reference
            certificate['evidence']=audit_reference(model,problem,values,coords,config,reference)
            if model.points:
                from .source_audit import audit_ns_domain
                certificate['evidence']['checks']['domain_witness']=audit_ns_domain(model,source,cache,budget,local,timeout)
            certificate['status']='reference_prepared'
            certificate['official_candidate']['status']='audited_source_snapshot_not_exact_truth'
            if model.model=='darcy_flow_2d':certificate['official_candidate']['status']='source_snapshot_not_used_as_steady_answer'
            if model.model=='reaction_diffusion_1d':certificate['official_candidate']['status']='source_trajectory_replaced_after_same_pde_comparison'
        elif model.model=='advection_1d':
            certificate['evidence']=write_analytic_reference(problem,reference)
            certificate['status']='reference_prepared'
        elif reference_root:
            external=Path(reference_root)/model.task/entry['kind']/entry['id']
            supplied=external/'reference.h5';evidence=external/'evidence.json'
            if supplied.exists()!=evidence.exists():
                raise PreparationError('External reference.h5 and evidence.json must both exist')
            if supplied.exists() and evidence.exists():
                audit=json.loads(evidence.read_text())
                if (audit.get('status')!='audited' or audit.get('contract_sha256')!=contract or
                    audit.get('input_files')!=identity or audit.get('reference_sha256')!=digest(supplied) or
                    not audit.get('method') or not audit.get('error_evidence')):
                    raise PreparationError("External reference evidence does not bind to this exact input/contract")
                imported=load_result(problem,supplied)
                check_reference_initial(model,problem,imported)
                shutil.copyfile(supplied,reference)
                # Preserve reviewer provenance; do not call supplied assertions
                # a proof or an independently measured error by this tool.
                certificate['evidence']={**audit,'kind':'external_review_assertion'}
                certificate['status']='reference_prepared'
        if not reference.exists() and model.model=='burgers_1d':
            from .references import write_burgers_reference
            certificate['evidence']=write_burgers_reference(problem,reference)
            certificate['status']='reference_prepared'
        if not reference.exists() and model.model=='reaction_diffusion_1d':
            from .references import write_logistic_reference
            certificate['evidence']=write_logistic_reference(problem,reference)
            certificate['status']='reference_prepared'
        if reference.exists(): certificate['reference_sha256']=digest(reference)
        atomic_json(ref_dir/'certificate.json',certificate)
        if public:
            sample=stage/'sample';sample.mkdir();input_dir.rename(sample/'input')
            output=sample/'output';output.mkdir()
            if reference.exists(): shutil.copyfile(reference,output/'result.h5')
            install_directory(sample,target)
            private=task/'reference'/'sample-certificates'/entry['id']
            install_directory(ref_dir,private)
        else:
            install_directory(input_dir,target)
            install_directory(ref_dir,task/'reference'/entry['id'])
        files={str(p.relative_to(task)):digest(p) for p in target.rglob('*') if p.is_file()}
        private=task/'reference'/'sample-certificates'/entry['id'] if public else task/'reference'/entry['id']
        files.update({str(p.relative_to(task)):digest(p) for p in private.rglob('*') if p.is_file()})
        record={'kind':entry['kind'],'id':entry['id'],'status':certificate['status'],
                'build_key':build_key,'files':files,'input_files':identity,'shape':list(shape),
                'estimated_output_bytes':int(np.prod(shape))*len(times)*sum(f[3] for f in model.fields)*8}
        atomic_json(record_path,record)
        budget.check()
        return record


def prepare_task(model,catalog,task,cache,staging,budget,local=None,pool=64,timeout=45,
                 max_cases=None,reference_root=None,reference_mode='independent',refresh_contract=False):
    sources=source_files(model,catalog)
    if not sources: raise PreparationError("No pinned sources for task")
    selection_path=task/'author/data-evidence/reference'/'selection.json'
    identity=hashlib.sha256(json.dumps({'catalog':catalog,'contract':contract_hash(task),
                      'pool':pool,'max_cases':max_cases,'version':VERSION},sort_keys=True).encode()).hexdigest()
    options={'pool':pool,'max_cases':max_cases}
    if selection_path.exists():
        selection=json.loads(selection_path.read_text())
        if selection.get('identity')!=identity:
            if not refresh_contract or selection.get('source_files')!=sources or selection.get('options',options)!=options:
                raise PreparationError("Frozen selection differs from this catalog/contract/options; use a separate output root or explicit --refresh-contract for a reviewed contract revision")
            archive=task/'author/data-evidence/reference/history'/('selection-'+selection['identity']+'.json')
            atomic_json(archive,selection)
            selection={**selection,'identity':identity,'options':options,
                       'contract_sha256':contract_hash(task),'previous_identity':selection['identity']}
            atomic_json(selection_path,selection)
        entries=selection['entries']
    else:
        entries=select(model,sources,cache,budget,local,pool,timeout,max_cases)
        selection={'version':VERSION,'identity':identity,'task':model.task,'status':'frozen',
                   'source_files':sources,'entries':entries,'options':options,'contract_sha256':contract_hash(task)}
        atomic_json(selection_path,selection)
    file_by_id={s['id']:s for s in sources}
    records=[];errors=[]
    for entry in entries:
        print(f"  prepare {entry['kind']} {entry['id']}",flush=True)
        try:
            records.append(prepare_entry(model,file_by_id[entry['source_id']],entry,task,cache,staging,
                                         budget,local,timeout,reference_root,reference_mode))
        except (PreparationError,ValueError,KeyError,OSError) as exc:
            errors.append({'kind':entry['kind'],'id':entry['id'],'error':str(exc)})
            print(f"    failed: {exc}",flush=True)
    pending=sum(r['status']=='reference_pending' for r in records)
    report={'task':model.task,'status':'failed' if errors else 'reference_pending' if pending else 'references_prepared',
            'samples':sum(r['kind']=='sample' for r in records),
            'cases':sum(r['kind']=='case' for r in records),'pending_references':pending,
            'records':records,'errors':errors,'partial_selection':max_cases is not None,
            'grading_ready':False,
            'remaining':['Calibrate error thresholds and execution resources; no judge-config generated']}
    if any(r['estimated_output_bytes']>128*1024**2 for r in records):
        report['remaining'].append('Current Harbor output-size limit is 128 MiB; high-dimensional outputs require an audited change')
    atomic_json(task/'author'/'preparation.json',report)
    return report
