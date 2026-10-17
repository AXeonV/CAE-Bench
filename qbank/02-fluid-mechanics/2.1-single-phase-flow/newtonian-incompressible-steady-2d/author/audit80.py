"""Audit every actual additional input, full reference and production grading plan.

Topology/normals and condition reconstruction are read from final contract assets.
Analytic boundary checks are consistency checks, distinct from solver independence.
"""
from pathlib import Path
from collections import Counter,defaultdict
import argparse,json,tempfile,shutil
import numpy as np
import h5py
from caeoj.sdk import load_problem,load_result
from caeoj.validation import read_mesh
from caeoj.case_grading import grade_case
from analytic80 import exact,quadrature


def audit(source,analytic_records):
    definitions={r['definition']['name']:r['definition'] for r in analytic_records}
    reports=[];coverage=defaultdict(Counter)
    for d in sorted((source/'cases').iterdir()):
        p=load_problem(d/'problem.json');j=p.manifest;a=p.arrays
        r=source/'reference'/d.name/'reference.h5';grading=r.with_name('grading.json');load_result(p,r)
        mesh=read_mesh(d/'mesh.msh',geometry=True);conn=mesh['connectivity'];coords=mesh['node_coordinates']
        cells={k:vs for k,(typ,vs) in conn.items() if typ in (2,3)};edges=defaultdict(list);area=0.
        for cid,vs in cells.items():
            xy=np.array([coords[v][:2] for v in vs]);signed=np.sum(xy[:,0]*np.roll(xy[:,1],-1)-xy[:,1]*np.roll(xy[:,0],-1))/2;assert signed>1e-15
            area+=signed
            for v,w in zip(vs,vs[1:]+vs[:1]):edges[tuple(sorted((v,w)))].append(cid)
        assert len(cells)<=50000 and len(coords)<=100000
        graph=defaultdict(set)
        for adjacent in edges.values():
            assert len(adjacent) in (1,2)
            if len(adjacent)==2:
                v,w=adjacent;graph[v].add(w);graph[w].add(v)
        reached=set();todo=[next(iter(cells))]
        while todo:
            v=todo.pop()
            if v in reached:continue
            reached.add(v);todo.extend(graph[v]-reached)
        assert len(reached)==len(cells)
        exterior={e for e,adjacent in edges.items() if len(adjacent)==1};specified=[];max_boundary_error=0.;operators=Counter()
        definition=definitions.get(d.name)

        def boundary_data(item,key,tag,vs,q):
            ref=item['data'][key]
            if 'value' in ref:return np.full((len(q),1),ref['value'])
            f=j['fields'][ref['field']];loc=j['locations'][f['location']];ids=a[loc['ids']];values=a[f['array']][0]
            by_id={int(k):v for k,v in zip(ids,values)}
            if loc.get('entity')=='element':return np.tile(by_id[tag],(len(q),1))
            x0,x1=[np.array(coords[v][:2]) for v in vs];t=((q-x0)@(x1-x0))/np.dot(x1-x0,x1-x0)
            return (1-t[:,None])*by_id[vs[0]]+t[:,None]*by_id[vs[1]]

        for item in j['conditions']:
            op=item['operator'];operators[op]+=1;coverage['operators'][op]+=1
            if item['role']!='boundary':continue
            loc=j['locations'][item['location']];ids=a[loc['ids']]
            total_shape=0.;boundary_rows=[]
            for tag in ids:
                typ,vs=conn[int(tag)];assert typ==1;edge=tuple(sorted(vs));assert edge in exterior;specified.append(edge)
                xy=np.array([coords[v][:2] for v in vs]);q,w=quadrature(xy);length=w.sum()
                n=np.array([xy[1,1]-xy[0,1],xy[0,0]-xy[1,0]])/length
                centroid=np.mean([coords[v][:2] for v in cells[edges[edge][0]]],axis=0)
                if np.dot(n,xy.mean(axis=0)-centroid)<0:n=-n
                if op=='moving_wall':
                    value=boundary_data(item,'velocity',int(tag),vs,q);assert np.max(np.abs(value@n))<1e-10
                if op=='flow_rate':total_shape+=float(w@boundary_data(item,'shape',int(tag),vs,q)[:,0])
                boundary_rows.append((int(tag),vs,q,w,n))
            if not definition:continue
            for tag,vs,q,w,n in boundary_rows:
                value=exact(definition,q);u=value['velocity'];stress=value['stress'];target=stress@n
                if op=='no_slip':error=np.max(np.abs(u))
                elif op in ('slip','symmetry'):
                    tangent=np.array([-n[1],n[0]]);error=max(np.max(np.abs(u@n)),np.max(np.abs(target@tangent)))
                elif op in ('moving_wall','velocity'):error=np.max(np.abs(u-boundary_data(item,'velocity',tag,vs,q)))
                elif op=='traction':error=np.max(np.abs(target-boundary_data(item,'traction',tag,vs,q)))
                elif op=='pressure_outlet':
                    pressure=boundary_data(item,'pressure',tag,vs,q);error=np.max(np.abs(target+pressure*n));assert np.min(u@n)>-1e-12
                elif op=='flow_rate':
                    rate=boundary_data(item,'rate',tag,vs,q)[0,0];shape=boundary_data(item,'shape',tag,vs,q)[:,0]
                    expected=-rate*float(w@shape/w.sum())*n/total_shape;error=np.max(np.abs(u-expected))
                elif op=='periodic':
                    shift=np.array([item['data']['translation_x']['value'],item['data']['translation_y']['value']]);partner=exact(definition,q+shift)
                    error=max(np.max(np.abs(u-partner['velocity'])),np.max(np.abs(value['pressure']-partner['pressure'])))
                else:raise ValueError(op)
                max_boundary_error=max(max_boundary_error,float(error));assert error<1e-8,(d.name,op,error)
        assert len(specified)==len(set(specified)) and set(specified)==exterior
        positive=grade_case(d/'problem.json',r,grading);assert positive['score']==1,positive
        negatives={};quantities={f['quantity'] for f in j['outputs'].values()}
        with tempfile.TemporaryDirectory() as temp:
            for quantity in sorted(quantities):
                f=next(v for v in j['outputs'].values() if v['quantity']==quantity);key=f['array'];bad=Path(temp)/'bad.h5';shutil.copyfile(r,bad)
                with h5py.File(bad,'r+') as h:
                    values=h[key][:];h[key][...]=values+100*(1+np.abs(values))
                grade=grade_case(d/'problem.json',bad,grading);assert grade['score']==0
                negatives[quantity]=dict(status=grade['status'],score=grade['score'])
            bad=Path(temp)/'missing.h5';shutil.copyfile(r,bad)
            with h5py.File(bad,'r+') as h:del h[next(iter(j['outputs'].values()))['array']]
            missing=grade_case(d/'problem.json',bad,grading);assert missing['score']==0
            negatives['missing_output']=dict(status=missing['status'],score=missing['score'])
        for f in j['outputs'].values():coverage['outputs'][f['quantity']]+=1;coverage['output_value_kind'][f['value_kind']]+=1
        for f in j['fields'].values():coverage['sampling'][f['sampling']['space']]+=1
        for typ,_ in conn.values():coverage['mesh_types'][str(typ)]+=1
        coverage['pressure_representation'][j['analysis']['pressure']['representation']]+=1
        gauge=j['analysis'].get('pressure_gauge');coverage['pressure_constraint'][gauge['kind'] if gauge else 'natural']+=1
        with h5py.File(r) as h:scalars=sum(h[f['array']].size for f in j['outputs'].values())
        assert scalars<=5000000
        reports.append(dict(name=d.name,valid=True,nodes=len(coords),cells=len(cells),area=area,operators=dict(operators),quantities=sorted(quantities),boundary_partition=True,connected=True,scalar_components=scalars,
          analytic_boundary_max_abs_error=max_boundary_error if definition else None,positive=positive,negative_controls=negatives))
        print(d.name,'passed',flush=True)
    assert len(reports)==80,len(reports)
    assert set(coverage['operators'])=={'no_slip','moving_wall','slip','symmetry','velocity','pressure_outlet','traction','flow_rate','periodic','acceleration'}
    assert len(coverage['outputs'])==9
    assert set(coverage['sampling'])=={'uniform','piecewise_constant','piecewise_linear'}
    return dict(cases=reports,coverage={k:dict(v) for k,v in coverage.items()},valid=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('analytic_report',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    report=audit(a.source,json.loads(a.analytic_report.read_text()));a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')
