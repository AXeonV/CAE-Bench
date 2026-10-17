"""Audit every actual input/output and exercise the production grading chain."""
from pathlib import Path
from collections import Counter,defaultdict
import argparse,json,tempfile,shutil
import h5py
import numpy as np
from caeoj.sdk import load_problem,load_result
from caeoj.validation import read_mesh
from caeoj.case_grading import grade_case


def audit(source):
    reports=[]
    for entry in sorted((source/'cases').iterdir()):
        if not entry.is_dir():continue
        problem=load_problem(entry/'problem.json');m=problem.manifest
        reference=source/'reference'/entry.name/'reference.h5'
        grading=reference.with_name('grading.json')
        load_result(problem,reference)
        mesh=read_mesh(entry/'mesh.msh',geometry=True)
        cells={tag:conn for tag,(typ,conn) in mesh['connectivity'].items() if typ==2}
        edges=defaultdict(list)
        area=0.
        for tag,conn in cells.items():
            coords=np.array([mesh['node_coordinates'][v][:2] for v in conn])
            a=coords[1]-coords[0];b=coords[2]-coords[0]
            cross=a[0]*b[1]-a[1]*b[0]
            assert cross>0
            area+=cross/2
            for a,b in zip(conn,conn[1:]+conn[:1]):edges[tuple(sorted((a,b)))].append(tag)
        assert all(len(v) in (1,2) for v in edges.values())
        external={edge for edge,neighbors in edges.items() if len(neighbors)==1}
        specified=[];operators=Counter()
        graph=defaultdict(set)
        for neighbors in edges.values():
            if len(neighbors)==2:
                a,b=neighbors;graph[a].add(b);graph[b].add(a)
        reached=set();todo=[next(iter(cells))]
        while todo:
            tag=todo.pop()
            if tag in reached:continue
            reached.add(tag);todo.extend(graph[tag]-reached)
        assert len(reached)==len(cells)
        for condition in m['conditions']:
            operators[condition['operator']]+=1
            if condition['role']!='boundary':continue
            loc=m['locations'][condition['location']]
            ids=problem.arrays[loc['ids']]
            for tag in ids:
                typ,conn=mesh['connectivity'][int(tag)]
                assert typ==1
                specified.append(tuple(sorted(conn)))
                if condition['operator']=='moving_wall':
                    field=m['fields'][condition['data']['velocity']['field']]
                    values=problem.arrays[field['array']][0]
                    nodes=problem.arrays[m['locations'][field['location']]['ids']]
                    by_id={int(i):v for i,v in zip(nodes,values)}
                    a,b=[mesh['node_coordinates'][i][:2] for i in conn]
                    normal=np.array([-(b-a)[1],(b-a)[0]])
                    assert all(abs(np.dot(by_id[i],normal))<1e-12 for i in conn)
        assert len(specified)==len(set(specified)) and set(specified)==external
        positive=grade_case(entry/'problem.json',reference,grading)
        assert positive['score']==1,positive
        negatives={}
        with tempfile.TemporaryDirectory() as temp:
            for quantity,shift in [('velocity',.1),('pressure',10.),('shear_rate',1.)]:
                bad=Path(temp)/f'{quantity}.h5';shutil.copyfile(reference,bad)
                with h5py.File(bad,'r+') as h:h[quantity][...]=h[quantity][...]+shift
                result=grade_case(entry/'problem.json',bad,grading)
                assert result['score']==0,result
                negatives[quantity]=dict(status=result['status'],score=result['score'])
            bad=Path(temp)/'missing.h5';shutil.copyfile(reference,bad)
            with h5py.File(bad,'r+') as h:del h['velocity']
            result=grade_case(entry/'problem.json',bad,grading)
            assert result['score']==0,result
            negatives['missing_velocity']=dict(status=result['status'],score=result['score'])
        reports.append(dict(name=entry.name,valid=True,nodes=len(mesh['nodes']),triangles=len(cells),area=float(area),
                            boundary_edges=len(external),connected=True,boundary_partition=True,wall_motion_tangent=True,
                            probes=len(problem.arrays['probe_ids']),operators=dict(operators),
                            outputs=list(m['outputs']),positive=dict(status=positive['status'],score=positive['score']),negative_controls=negatives))
        print(entry.name,'passed',flush=True)
    assert len(reports)==20
    return reports


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);args=p.parse_args()
    reports=audit(args.source)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(reports,indent=2)+'\n')
