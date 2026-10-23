import collections, hashlib, json, pathlib, re, sys
import h5py
import numpy as np

ROOT=pathlib.Path('D:/Code/CAE-Bench-OJ'); BASE=ROOT/'runs/prepublication-review-rc2'
sys.stdout.reconfigure(encoding='utf-8')
# Reuse only the neutral ASCII MSH parser, not previous review conclusions.
namespace={}; source=(BASE/'candidate_structural_check.py').read_text(encoding='utf-8-sig')
exec(source[source.index('TYPES='):source.index('cache={}; results=[]')],dict(pathlib=pathlib,np=np),namespace)
mesh=namespace['mesh']; mesh.__globals__.update(namespace)
plan=json.loads((ROOT/'runs/release-assembly-rc2/plan.json').read_text(encoding='utf-8'))
tasks=[]; issues=[]
def add(task,p,kind,message,evidence=None):
    issues.append(dict(task=task,manifest=str(p),category=kind,message=message,evidence=evidence))
def lines_for(lines,token):
    return [i for i,l in enumerate(lines,1) if token in l]
def js(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
for ti,t in enumerate(plan['tasks']):
    task=t['task']; current=ROOT/t['task_path']; inv=json.loads((BASE/'data-inventory'/f'{task}.json').read_text(encoding='utf-8'))
    dl=(current/'DATA.md').read_text(encoding='utf-8').splitlines(); il=(current/'instruction.md').read_text(encoding='utf-8').splitlines()
    record=dict(task=task,task_path=t['task_path'],cases=inv['case_count'],samples=inv['sample_count'],documents={n:hashlib.sha256((current/n).read_bytes()).hexdigest() for n in ['DATA.md','instruction.md']},claims={},inputs=[])
    claims=record['claims']; cache={}
    def claim(path,value,p,token=None):
        key=path+'='+js(value)
        if key not in claims:
            tok=str(token if token is not None else value)
            claims[key]=dict(json_path=path,value=value,DATA_lines=lines_for(dl,tok),instruction_lines=lines_for(il,tok),manifests=[])
        claims[key]['manifests'].append(str(p))
    for e in inv['inputs']:
        p=pathlib.Path(e['path']); m=e['manifest']; D=m['spatial_dimension']; params=m.get('physics',{}).get('parameters',{}); start=params.get('time_start',params.get('start_time',{})).get('value');end=params.get('time_end',params.get('end_time',{})).get('value')
        if 'time_interval' in m.get('analysis',{}):start=m['analysis']['time_interval']['start'];end=m['analysis']['time_interval']['end']
        rr=dict(manifest=str(p),kind=e['kind'],time_axes={},field_checks=[],mesh_checks=[],condition_branches=[]);record['inputs'].append(rr)
        for k in ['task','spatial_dimension','contract_version','profile']:
            if k in m:claim(k,m[k],p,k if k!='task' else m[k])
        if 'physics'in m:
            claim('physics.model',m['physics']['model'],p)
            for k,v in params.items():claim('physics.parameters.'+k,v,p,k)
        if 'analysis'in m:
            for k,v in m['analysis'].items():claim('analysis.'+k,v,p,k)
        for name,mat in m.get('materials',{}).items():
            for typ,rec in mat.items():
                if isinstance(rec,dict):
                    claim('materials.*.'+typ+'.kind',rec.get('kind'),p,rec.get('kind'))
                    for k,v in rec.get('parameters',{}).items():claim('materials.*.'+typ+'.parameters.'+k,v,p,k)
        for c in m['conditions']:
            branch='/'.join(c[k] for k in ['role','variable','operator']);rr['condition_branches'].append(branch)
            claim('conditions[].role/variable/operator',branch,p,c['operator'])
            for k,v in c['data'].items():claim('conditions['+branch+'].data.'+k,v,p,k)
        with h5py.File(p.parent/m['data_file']) as h:
            ids={n:h[l['ids']][()] for n,l in m['locations'].items()}
            axes={n:h[k][()] for n,k in m['time_axes'].items()};rr['time_axes']={n:a.tolist() for n,a in axes.items()}
            for n,a in axes.items():
                if not np.isfinite(a).all() or not np.all(np.diff(a)>0):add(task,p,'data_conflict','nonfinite/non-increasing time axis',n)
            for n,l in m['locations'].items():
                claim('locations.*.kind/entity/value', {k:v for k,v in l.items() if k not in ['ids','coordinates','mesh','source']},p,l['kind'])
                a=ids[n]
                if not np.all(np.diff(a)>0):add(task,p,'data_conflict','IDs not strictly increasing',n)
                if l['kind']=='points':
                    xyz=h[l['coordinates']][()]
                    rr.setdefault('point_bounds',{})[n]={'N':len(a),'min':xyz.min(axis=0).tolist(),'max':xyz.max(axis=0).tolist()}
            for section in ['fields','outputs']:
                for name,f in m[section].items():
                    for k in ['quantity','unit','kind','value_kind','component_shape','components']:
                        claim(section+'.*.'+k,f[k],p,f[k] if isinstance(f[k],str) else k)
                    expected=[len(axes[f['time_axis']]),len(ids[f['location']]),*f['component_shape']]
                    if section=='outputs':
                        if start is not None and not np.all((axes[f['time_axis']]>=start)&(axes[f['time_axis']]<=end)):add(task,p,'data_conflict','output times outside physical interval',name)
                        continue
                    a=h[f['array']][()]; sample=f.get('sampling'); checks={'name':name,'array':f['array'],'shape':list(a.shape),'expected':expected,'min':float(np.min(a)),'max':float(np.max(a)),'sampling':sample}
                    rr['field_checks'].append(checks)
                    if list(a.shape)!=expected:add(task,p,'data_conflict','input array axes differ from declaration',checks)
                    if not np.isfinite(a).all():add(task,p,'data_conflict','nonfinite field',name)
                    if sample:
                        claim('fields.*.sampling',sample,p,'sampling')
                        if sample['space']=='uniform' and not np.all(a==a[:,0:1]):add(task,p,'data_conflict','sampling uniform but spatial rows differ',name)
                        at=axes[f['time_axis']]
                        if sample['time']=='constant' and len(at)!=1:add(task,p,'data_conflict','constant time sampling has more than one frame',name)
                        if sample['time']in ['linear','previous'] and start is not None and sample['extrapolation']=='forbid' and not(at[0]<=start and at[-1]>=end):add(task,p,'data_conflict','condition sampling does not cover physical interval',name)
                    loc=m['locations'][f['location']]
                    if loc['kind']in ['node','points','entities'] and f['value_kind']!='point':add(task,p,'data_conflict','non-point value_kind on point location',name)
            # Every real MSH location resolves to the actual named entities / groups.
            for mn,md in m['meshes'].items():
                mp=p.parent/md['file'];digest=hashlib.sha256(mp.read_bytes()).hexdigest()
                if digest not in cache:cache[digest]=mesh(mp)
                nd,es,gr=cache[digest]; rr['mesh_checks'].append(dict(name=mn,path=str(mp),node_count=len(nd),element_types=sorted({v['type'] for v in es.values()}),bounds=[np.min(list(nd.values()),axis=0).tolist(),np.max(list(nd.values()),axis=0).tolist()]))
                for ln,l in m['locations'].items():
                    if l['kind']!='mesh' or l['mesh']!=mn:continue
                    chosen=set(nd) if l['entity']=='node' else {k for k,v in es.items() if v['dimension']==l['dimension']}
                    if not set(ids[ln])<=chosen:add(task,p,'data_conflict','location IDs absent from mesh entities',ln)
                    if 'physical_group'in l:
                        pg=l['physical_group'];selected={k for k,v in es.items() if v['dimension']==pg['dimension'] and pg['tag'] in gr.get((v['dimension'],v['entity']),set())}
                        if l['entity']=='node':selected={n for k in selected for n in es[k]['nodes']}
                        if set(ids[ln])!=selected:add(task,p,'data_conflict','IDs not exact Physical Group selection',ln)
                # Fixed-domain moving walls must have zero normal speed on each entity.
                for c in m['conditions']:
                    if c['role']!='boundary' or c['operator']not in ['moving_wall','velocity_wall','gas_wall']:continue
                    l=m['locations'][c['location']]
                    if l.get('entity')!='element':continue
                    ref=c['data'].get('value',c['data'].get('velocity'))
                    if not ref or 'field'not in ref:continue
                    f=m['fields'][ref['field']]
                    if f['location']!=c['location']:continue # Nodal reconstruction belongs to separate consumption evidence.
                    a=h[f['array']][()];maxnormal=0.
                    for j,eid in enumerate(ids[c['location']]):
                        xyz=np.array([nd[n] for n in es[eid]['nodes']]);u=xyz[1]-xyz[0];normal=np.array([u[1],-u[0],0.])if D==2 else np.cross(u,xyz[2]-xyz[0]);normal=normal[:D]/np.linalg.norm(normal)
                        maxnormal=max(maxnormal,float(np.max(np.abs(a[:,j]@normal))))
                    if maxnormal>1e-10:add(task,p,'data_conflict','fixed-domain moving wall has nonzero normal speed',dict(condition=c,maxnormal=maxnormal))
            # Scalar physical input restrictions from public conditions, without solving.
            for c in m['conditions']:
                for key,v in c['data'].items():
                    if 'field'in v:
                        f=m['fields'][v['field']];a=h[f['array']][()];q=c['variable'] if key=='value' else key
                        if t['chapter']=='02-fluid-mechanics' and not task.startswith('cc-') and c['operator']!='outward_heat_flux' and q in ['density','temperature','gap','turbulence_length_scale'] and np.min(a)<=0:add(task,p,'data_conflict','nonpositive required positive input',dict(variable=q,field=v['field'],min=float(np.min(a))))
                        if q in ['alpha','accommodation'] and (np.min(a)<0 or np.max(a)>1):add(task,p,'data_conflict','fraction input outside [0,1]',q)
                        if q=='conformation':
                            if not np.allclose(a,np.swapaxes(a,-1,-2),rtol=0,atol=1e-12)or np.min(np.linalg.eigvalsh(a))<=0:add(task,p,'data_conflict','conformation is not SPD',v['field'])
        # Public tables directly constrain output quantity/kind/unit in fluid families.
        table={}
        for l in dl:
            if l.startswith('|'):
                cells=[x.strip().strip('`') for x in l.split('|')[1:-1]]
                if len(cells)==4:
                    if cells[1]in ['scalar','vector','tensor']:table[cells[0]]=(cells[1],cells[2])
                    elif cells[2]in ['scalar','vector','tensor']:table[cells[0]]=(cells[2],cells[1])
        for name,f in m['outputs'].items():
            if f['quantity']in table and table[f['quantity']]!=(f['kind'],f['unit']):add(task,p,'document_data_conflict','public output quantity table differs from manifest',dict(field=name,actual=[f['kind'],f['unit']],document=table[f['quantity']]))
    record['claim_count']=len(claims);record['issues']=[x for x in issues if x['task']==task];tasks.append(record)
    print(ti,task,'claims',len(claims),'issues',len(record['issues']),flush=True)
    (BASE/'actual-data-review.json').write_text(json.dumps(dict(scope={'tasks':len(tasks),'cases':sum(x['cases']for x in tasks),'samples':sum(x['samples']for x in tasks)},issues=issues,tasks=tasks),ensure_ascii=False,indent=2),encoding='utf-8')
