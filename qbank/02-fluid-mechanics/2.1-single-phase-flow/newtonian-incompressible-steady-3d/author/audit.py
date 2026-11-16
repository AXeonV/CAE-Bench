"""Audit every generated input; native numerical qualification stays separate."""
import argparse
from collections import Counter
import hashlib
from pathlib import Path

import gmsh
import numpy as np

from supplement import TASK_DIR, catalog, save, settings, lid_values, tangential_load
from caeoj.sdk import load_problem, load_result, boundary_geometry


def audit(generated):
    cases={c['name']:c for c in catalog()}
    paths=sorted((generated/'cases').glob('*/problem.json'))
    assert {p.parent.name for p in paths}==set(cases), 'Expected all 100 configured inputs'
    counts={name:Counter() for name in ('boundary','sampling','pressure','gauge','mesh','output','location','source_count')}
    rows=[]
    for path in paths:
        p=load_problem(path);m=p.manifest;c=cases[path.parent.name]
        assert m['task']==TASK_DIR.name
        assert not any(s['role']=='initial' for s in m['conditions'])
        boundary=[s for s in m['conditions'] if s['role']=='boundary']
        source=[s for s in m['conditions'] if s['role']=='source']
        material=next(iter(m['materials'].values()))
        assert material['density']['parameters']['density']['value']==c['density']
        assert material['viscosity']['parameters']['dynamic_viscosity']['value']==c['viscosity']
        expected_bcs,_,acc,H=settings(c)
        def values(reference):
            if 'value' in reference:return np.array([[reference['value']]])
            field=m['fields'][reference['field']]
            return p.arrays[field['array']][0]
        def coordinates(location):
            s=m['locations'][location];mesh=p.meshes['main']
            if s.get('entity')=='node':return np.array([mesh['node_coordinates'][int(i)] for i in p.arrays[s['ids']]])
            if s.get('dimension')==2:return boundary_geometry(p,location)[0]
            return np.array([np.mean([mesh['node_coordinates'][j] for j in mesh['connectivity'][int(i)][1]],axis=0) for i in p.arrays[s['ids']]])
        # Check actual condition->field->array data against the native case
        # definition. Two solvers reading the same catalog alone cannot do this.
        for s in boundary:
            b=int(s['location'].removeprefix('face'));assert s['operator']==expected_bcs[b]
            if s['operator'] in ('moving_wall','velocity'):
                field=m['fields'][s['data']['velocity']['field']]
                x=coordinates(field['location']);logical=((x-c['origin'])@np.array(c['rotation']))/c['lengths']
                assert np.allclose(values(s['data']['velocity']),lid_values(c,b,logical),rtol=1e-12,atol=1e-13)
            if s['operator'] in ('pressure_outlet','traction'):
                key='pressure' if s['operator']=='pressure_outlet' else 'traction';v=s['data'][key]
                location=m['fields'][v['field']]['location'] if 'field' in v else s['location']
                x=coordinates(location);pressure=c['pressure_value']+c['density']*((x-c['origin'])@acc)
                if key=='traction':
                    normal=np.array(c['rotation'])[:,(b-1)//2]*(1 if b%2==0 else -1)
                    expected_value=-pressure[:,None]*normal+tangential_load(c,b)
                else:expected_value=pressure[:,None]
                assert np.allclose(values(v),expected_value,rtol=1e-12,atol=1e-11)
            if s['operator']=='flow_rate':
                assert np.allclose(values(s['data']['rate']),c['speed']*c['lengths'][1]*c['lengths'][2])
                shape=values(s['data']['shape']);assert np.all(shape>0) and np.all(shape==shape.flat[0])
            if s['operator']=='periodic':
                translation=np.array([s['data']['translation_'+a]['value'] for a in 'xyz'])
                expected_translation=np.array(c['rotation'])[:,(b-1)//2]*c['lengths'][(b-1)//2]*(1 if b%2 else -1)
                assert np.allclose(translation,expected_translation)
        if np.linalg.norm(H)>0:
            assert source
            first=m['fields'][source[0]['data']['value']['field']];x=coordinates(first['location'])
        else:x=np.zeros((1,3))+c['origin']
        expected_acc=acc+(x-c['origin'])@H.T
        actual_acc=sum((values(s['data']['value']) for s in source),np.zeros_like(expected_acc))
        assert np.allclose(actual_acc,expected_acc,rtol=1e-12,atol=1e-13)
        counts['boundary'].update({s['operator'] for s in boundary})
        counts['sampling'].update({s['sampling']['space'] for s in m['fields'].values()})
        counts['pressure'].update([m['analysis']['pressure']['representation']])
        counts['gauge'].update([m['analysis'].get('pressure_gauge',{}).get('kind','natural')])
        counts['mesh'].update([c['input_mesh']]);counts['source_count'].update([str(len(source))])
        counts['output'].update({s['quantity'] for s in m['outputs'].values()})
        counts['location'].update({('mesh_'+s['entity'] if s['kind']=='mesh' else s['kind']) for s in m['locations'].values()})
        flux=np.zeros(3);surface_volume=0.;boundary_ids=[]
        for condition in boundary:
            loc=condition['location'];xyz,normal,area=boundary_geometry(p,loc)
            assert np.all(area>0)
            flux+=(normal*area[:,None]).sum(axis=0)
            surface_volume+=float(np.sum(np.sum(xyz*normal,axis=1)*area))/3
            boundary_ids.extend(map(int,p.arrays[m['locations'][loc]['ids']]))
        assert len(boundary_ids)==len(set(boundary_ids)), 'Repeated boundary condition facet'
        expected=np.prod(c['lengths'])*(1-{'box':0.,'obstacle':.25**3,'two-obstacles':2*.25**3,'baffle':.25*.5*.5,'off-center':.25*.25*.5}[c['geometry']])
        assert np.linalg.norm(flux)<1e-9*max(c['lengths'])**2
        assert np.isclose(surface_volume,expected,rtol=1e-10,atol=1e-12), (path.parent.name,surface_volume,expected)
        gmsh.initialize([],readConfigFiles=False)
        try:
            gmsh.option.setNumber('General.Terminal',0);gmsh.open(str(path.parent/'mesh.msh'))
            volume=0.;minimum=float('inf');elements=0
            for typ,tags,_ in zip(*gmsh.model.mesh.getElements(3)):
                points,weights=gmsh.model.mesh.getIntegrationPoints(int(typ),'Gauss2')
                _,det,_=gmsh.model.mesh.getJacobians(int(typ),points)
                minimum=min(minimum,float(det.min()));elements+=len(tags)
                volume+=float(np.sum(det.reshape(-1,len(weights))@weights))
            assert minimum>0, 'Inverted or degenerate input cell'
            assert np.isclose(volume,expected,rtol=1e-10,atol=1e-12)
            assert elements<=50000
        finally:gmsh.finalize()
        reference=generated/'reference'/path.parent.name/'reference.h5'
        if reference.exists():load_result(p,reference)
        independent=reference.with_name('independent.h5')
        if independent.exists():load_result(p,independent)
        rows.append(dict(case=path.parent.name,input_files={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(path.parent.iterdir()) if f.is_file()},volume=volume,min_jacobian=minimum,cells=elements,reference_structure_checked=reference.exists(),independent_structure_checked=independent.exists()))
    return dict(input_count=len(rows),input_audit='pass',counts={k:dict(v) for k,v in counts.items()},cases=rows,
                limits=['Input/geometry and result structure audit; not numerical certification or a resource benchmark.',
                        'Coverage counts describe this batch and do not prove every legal boundary or sampling combination is tested.'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generated',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=audit(args.generated);save(args.output,result)
    print(f'Input audit: {result["input_count"]} passed')
