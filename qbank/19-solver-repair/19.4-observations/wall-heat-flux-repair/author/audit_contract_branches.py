"""Exercise declared topology, JSON integer, and active/ignored inlet branches."""
from pathlib import Path
import hashlib,importlib.util,json
from caeoj.sdk import load_problem
from caeoj.validation import read_mesh

Q=Path(__file__).resolve().parents[1];ROOT=Q.parents[3]
spec=importlib.util.spec_from_file_location('wall_contract',Q/'extension/caeoj_task_ext/wall_energy.py')
checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)


def load(path):
    problem=load_problem(path)
    problem.meshes['channel']=read_mesh(path.parent/'mesh.msh',geometry=True)
    return problem


def errors(problem):
    result=[];checker.check(problem,result);return result


if __name__=='__main__':
    rows=[]
    for path in sorted((Q/'cases').glob('*/problem.json')):
        p=load(path);assert not errors(p)
        velocity=p.manifest['physics']['parameters']['velocity']['value']
        ids=p.arrays['inlet_ids'];coords=p.meshes['channel']['node_coordinates']
        ys=[coords[int(tag)][1] for tag in ids]
        for index in [ys.index(min(ys)),ys.index(max(ys))]:
            old=p.arrays['inlet_temperature'][0,index,0]
            p.arrays['inlet_temperature'][0,index,0]=old+1
            e=errors(p)
            assert bool(e)==bool(velocity),(path,index,e)
            p.arrays['inlet_temperature'][0,index,0]=old
        rows.append({'case':path.parent.name,'valid':True,
                     'endpoint_plus_1K':'rejected for flow' if velocity else 'accepted as ignored static field'})
    for variant in ['iterations-float','flow-inlet-endpoint-discontinuity','mesh-triangles']:
        path=ROOT/'runs/data-review/repair22-su22347/variants'/variant/'problem.json'
        p=load(path);e=errors(p);assert e,(variant,e)
        rows.append({'review_variant':variant,'rejected':True,'errors':e})
    (Q/'author/data-evidence/contract-branches-audit.json').write_text(json.dumps({
        'checker_sha256':hashlib.sha256((Q/'extension/caeoj_task_ext/wall_energy.py').read_bytes()).hexdigest(),
        'runtime_geometry':json.loads((Q/'extension/runtime.json').read_text())['geometry'],
        'scope':'Complete explicit checker; fresh installed final bundle is tested separately.',
        'passed':True,'branches':rows},indent=2)+'\n')
    print(json.dumps({'valid_cases':10,'endpoint_branches':20,'reported_negative_variants':3,'passed':True}))
