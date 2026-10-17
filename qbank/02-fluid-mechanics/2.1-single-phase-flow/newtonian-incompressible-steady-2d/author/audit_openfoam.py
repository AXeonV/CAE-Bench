"""Audit frozen actual inputs and all independent output levels against DATA/CONTRACT."""
from pathlib import Path
import argparse, hashlib, json
import numpy as np
from caeoj.sdk import load_problem,load_result
from caeoj.validation import read_mesh

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def audit(source,evidence,task,output=None):
    rows=json.loads((evidence/'comparison.json').read_text());reports=[]
    for row in rows:
        inp=source/'cases'/row['name'];problem=load_problem(inp/'problem.json');j=problem.manifest;arr=problem.arrays
        mesh=read_mesh(inp/'mesh.msh',geometry=True)
        assert {p.name:sha(p) for p in inp.iterdir() if p.is_file()}==row['input_hashes']
        ref=source/'reference'/row['name']
        assert {p.name:sha(p) for p in ref.iterdir() if p.is_file()}==row['reference_hashes']
        xy=mesh['node_coordinates'];connectivity=mesh['connectivity']
        edge_count={};area=0.
        for tag in arr[j['locations']['domain']['ids']]:
            typ,conn=connectivity[int(tag)];assert typ==2
            p=np.array([xy[v][:2] for v in conn]);a=p[1]-p[0];b=p[2]-p[0]
            cross=a[0]*b[1]-a[1]*b[0];assert cross>0;area+=cross/2
            for a,b in zip(conn,conn[1:]+conn[:1]):
                key=tuple(sorted((a,b)));edge_count[key]=edge_count.get(key,0)+1
        external={k for k,v in edge_count.items() if v==1};assigned=[];lengths={}
        for cond in j['conditions']:
            if cond['role']!='boundary':continue
            name=cond['location'];length=0.
            for tag in arr[j['locations'][name]['ids']]:
                typ,conn=connectivity[int(tag)];assert typ==1;assigned.append(tuple(sorted(conn)))
                a,b=[np.array(xy[v][:2]) for v in conn];length+=float(np.linalg.norm(b-a))
                if cond['operator']=='moving_wall':
                    field=j['fields'][cond['data']['velocity']['field']]
                    values={int(k):v for k,v in zip(arr[j['locations'][field['location']]['ids']],arr[field['array']][0])}
                    normal=np.array([-(b-a)[1],(b-a)[0]])
                    assert all(abs(np.dot(values[v],normal))<1e-12 for v in conn)
            lengths[name]=length
        assert len(assigned)==len(set(assigned)) and set(assigned)==external
        gauge=j['analysis']['pressure_gauge'];assert gauge['kind']=='point' and gauge['value']['value']==0
        pin=arr[j['locations'][gauge['location']]['coordinates']][0]
        assert np.array_equal(pin,arr['probe_xy'][0])
        levels=[]
        for level in row['levels']:
            run=evidence/'runs'/row['name']/f'n{level}';tr=json.loads((run/'translation.json').read_text())
            assert sha(run/'result.h5')==row['levels'][level]['result_sha256']
            assert sha(run/'observations.xy')==row['levels'][level]['sample_sha256']
            initialization=row['levels'][level].get('initialization')
            if initialization:
                initial=evidence/'runs'/row['name']/f'n{initialization["source_level"]}'/'execution.json'
                assert sha(initial)==initialization['source_execution_sha256']
            assert tr['input_hashes']==row['input_hashes']
            assert abs(tr['area']-area)<1e-12 and tr['cells']==round(area)*int(level)**2
            assert set(tr['boundary_conditions'])==set(lengths)==set(tr['mapped_boundary_faces'])
            for name,length in lengths.items():
                cond=next(c for c in j['conditions'] if c['location']==name)
                assert tr['boundary_conditions'][name]['operator']==cond['operator']
                assert abs(tr['boundary_conditions'][name]['length']-length)<1e-12
                assert tr['mapped_boundary_faces'][name]['face_count']==round(length*int(level))
                if cond['operator']!='moving_wall':assert tr['mapped_boundary_faces'][name]['max_speed']==0
            affine=np.array(tr['acceleration_affine']);actual=np.zeros((len(arr['node_ids']),2))
            for cond in j['conditions']:
                if cond['role']=='source':
                    field=j['fields'][cond['data']['value']['field']]
                    assert j['locations'][field['location']]['ids']=='node_ids'
                    actual+=arr[field['array']][0]
            coords=np.array([xy[int(k)][:2] for k in arr['node_ids']]);fit=np.column_stack((np.ones(len(coords)),coords))@affine
            assert np.max(np.abs(fit-actual))<1e-14
            load_result(problem,run/'result.h5')
            levels.append(dict(level=int(level),contract_valid=True,geometry_and_boundary_mapping=True,acceleration_max_error=float(np.max(np.abs(fit-actual)))))
        reports.append(dict(alias=row['alias'],name=row['name'],case_id=row['case_id'],input_and_reference_immutable=True,
                            area=area,all_actual_exterior_edges_covered_once=True,moving_wall_tangency=True,
                            pressure_gauge=pin.tolist(),observations=len(arr['probe_ids']),levels=levels))
    assert len(reports)==19
    report=dict(valid=True,cases=reports,scope='All 19 frozen inputs and every OpenFOAM output level; standard cavity 010 excluded.',
                specification_hashes={p.name:sha(p) for p in [task/'instruction.md',task/'DATA.md',Path('docs/CONTRACT.md'),task/'data-manifest.json']},
                mappings={'geometry':'DATA 清单与数组；CONTRACT 网格与位置','boundaries':'DATA 边界、输入场采样','source':'DATA 初态及体加速度、输入场采样','pressure':'DATA 分析声明、压力点基准','outputs':'DATA 输出、CONTRACT 结果数组'},
                limitations='This audit establishes representation/consumption equivalence; numerical conclusions are separately recorded in comparison.json and report.md.')
    output=output or evidence/'interface-audit.json'
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('All 19 inputs and all independent outputs audited')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('evidence',type=Path);p.add_argument('task',type=Path);p.add_argument('--output',type=Path);a=p.parse_args();audit(a.source,a.evidence,a.task,a.output)
