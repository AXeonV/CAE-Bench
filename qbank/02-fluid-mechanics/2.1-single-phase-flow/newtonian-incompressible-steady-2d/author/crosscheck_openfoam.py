"""Independent OpenFOAM case adapter. Reads frozen contract assets, not Lethe definitions.

Run with the repository Python (gmsh, numpy, h5py) and a sourced OpenFOAM shell.
This only translates data and invokes upstream utilities; it implements no PDE solver.
"""
from pathlib import Path
import argparse, concurrent.futures, hashlib, json, re, subprocess, time
import gmsh
import h5py
import numpy as np


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def header(obj, cls='dictionary'):
    return f'FoamFile {{version 2.0; format ascii; class {cls}; object {obj};}}\n'


def write(p, text):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def vec(v):
    return '('+' '.join(format(float(x), '.17g') for x in v)+')'


def read_input(case):
    j = json.loads((case/'problem.json').read_text())
    with h5py.File(case/j['data_file']) as h:
        arrays = {k: h[k][:] for k in h}
    gmsh.initialize(); gmsh.option.setNumber('General.Terminal', 0)
    gmsh.open(str(case/'mesh.msh'))
    tags, coords, _ = gmsh.model.mesh.getNodes()
    nodes = {int(k): v[:2] for k, v in zip(tags, np.array(coords).reshape(-1, 3))}
    elements = {}
    for dim in (1, 2):
        types, ids, conn = gmsh.model.mesh.getElements(dim)
        for typ, ii, cc in zip(types, ids, conn):
            nn = gmsh.model.mesh.getElementProperties(typ)[3]
            for tag, vs in zip(ii, cc.reshape(-1, nn)):
                elements[int(tag)] = [int(v) for v in vs]
    gmsh.finalize()
    domain = arrays[j['locations']['domain']['ids']]
    triangles = np.array([[nodes[v] for v in elements[int(k)]] for k in domain])
    assert triangles.shape[1:] == (3, 2)
    e1=triangles[:,1]-triangles[:,0];e2=triangles[:,2]-triangles[:,0]
    areas = np.abs(e1[:,0]*e2[:,1]-e1[:,1]*e2[:,0])/2
    # These frozen geometries are unions of complete integer unit squares.
    unit_cells = sorted(set(tuple(int(x) for x in row) for row in np.floor(triangles.mean(axis=1)).astype(int)))
    for x, y in unit_cells:
        mask = np.all(np.floor(triangles.mean(axis=1)).astype(int) == [x, y], axis=1)
        assert abs(areas[mask].sum()-1) < 1e-12
    assert abs(areas.sum()-len(unit_cells)) < 1e-12
    boundaries = {}
    for c in j['conditions']:
        if c['role'] != 'boundary':
            continue
        name = c['location']; loc = j['locations'][name]
        edges = np.array([[nodes[v] for v in elements[int(k)]] for k in arrays[loc['ids']]])
        assert edges.shape[1:] == (2, 2)
        motion = {}
        if c['operator'] == 'moving_wall':
            f = j['fields'][c['data']['velocity']['field']]
            floc = j['locations'][f['location']]
            assert f['sampling']['space'] == 'piecewise_linear'
            motion = {int(k): v for k, v in zip(arrays[floc['ids']], arrays[f['array']][0])}
        values = np.array([[motion.get(v, np.zeros(2)) for v in elements[int(k)]] for k in arrays[loc['ids']]])
        boundaries[name] = dict(operator=c['operator'], edges=edges, values=values)
    affine = np.zeros((3, 2)); fit_error = 0.
    for c in j['conditions']:
        if c['role'] != 'source':
            continue
        assert c['operator'] == 'acceleration'
        f = j['fields'][c['data']['value']['field']]
        loc = j['locations'][f['location']]
        xy = np.array([nodes[int(k)] for k in arrays[loc['ids']]])
        design = np.column_stack((np.ones(len(xy)), xy))
        values = arrays[f['array']][0]
        a = np.linalg.lstsq(design, values, rcond=None)[0]
        fit_error = max(fit_error, float(np.max(np.abs(design@a-values))))
        assert fit_error < 1e-14
        a[np.abs(a) < 1e-15] = 0
        affine += a
    mat = next(iter(j['materials'].values()))
    rho = mat['density']['parameters']['density']['value']
    mu = mat['viscosity']['parameters']['dynamic_viscosity']['value']
    probes = arrays[j['locations']['probes']['coordinates']]
    pin = arrays[j['locations'][j['analysis']['pressure_gauge']['location']]['coordinates']][0]
    assert np.all(pin == probes[0])
    return j, arrays, unit_cells, boundaries, affine, fit_error, rho, mu, probes


def boundary_at(point, boundaries):
    matches = []
    for name, b in boundaries.items():
        a = b['edges'][:, 0]; d = b['edges'][:, 1]-a
        t = np.einsum('ij,ij->i', point-a, d)/np.einsum('ij,ij->i', d, d)
        dist = np.linalg.norm(a+t[:, None]*d-point, axis=1)
        hits = np.flatnonzero((dist < 1e-9) & (t >= -1e-9) & (t <= 1+1e-9))
        for k in hits:
            value = (1-t[k])*b['values'][k, 0]+t[k]*b['values'][k, 1]
            matches.append((name, value))
    assert matches, point
    assert len({m[0] for m in matches}) == 1, (point, matches)
    assert max(np.linalg.norm(m[1]-matches[0][1]) for m in matches) < 1e-12
    return matches[0]


def prepare(case, out, n, relaxation=.8, relative=0.):
    j, arrays, cells, bs, affine, fit_error, rho, mu, probes = read_input(case)
    vertices = sorted(set((x+dx, y+dy, z) for x, y in cells for dx, dy in ((0,0),(1,0),(1,1),(0,1)) for z in (0,1)))
    vi = {v:k for k,v in enumerate(vertices)}
    blocks = []; patches = {k:[] for k in bs}; patches['frontBack'] = []
    occupied = set(cells)
    for x,y in cells:
        vs = [vi[(x+dx,y+dy,z)] for z in (0,1) for dx,dy in ((0,0),(1,0),(1,1),(0,1))]
        blocks.append('hex '+vec(vs).replace('.0','')+f' ({n} {n} 1) simpleGrading (1 1 1)')
        patches['frontBack'] += [[vs[i] for i in face] for face in ((0,3,2,1),(4,5,6,7))]
        for neighbour, face, mid in [((x,y-1),(0,1,5,4),(x+.5,y)),((x+1,y),(1,2,6,5),(x+1,y+.5)),((x,y+1),(2,3,7,6),(x+.5,y+1)),((x-1,y),(3,0,4,7),(x,y+.5))]:
            if neighbour not in occupied:
                name,_ = boundary_at(np.array(mid),bs)
                patches[name].append([vs[i] for i in face])
    boundary_text = ''
    for k,faces in patches.items():
        typ = 'empty' if k == 'frontBack' else 'wall'
        boundary_text += k+' {type '+typ+'; faces ('+' '.join(vec(f) for f in faces)+');}\n'
    write(out/'system/blockMeshDict', header('blockMeshDict')+'convertToMeters 1;\nvertices ('+' '.join(vec([x,y,z*.1]) for x,y,z in vertices)+');\nblocks ('+'\n'.join(blocks)+');\nedges ();\nboundary ('+boundary_text+');\nmergePatchPairs ();\n')
    write(out/'constant/physicalProperties',header('physicalProperties')+f'viscosityModel constant;\nnu {mu/rho:.17g};\n')
    write(out/'constant/momentumTransport',header('momentumTransport')+'simulationType laminar;\n')
    if np.any(affine):
        expr = [f'({affine[0,k]:.17g}+{affine[1,k]:.17g}*c.x()+{affine[2,k]:.17g}*c.y())' for k in range(2)]
        code = 'const auto& V=mesh().V(); const auto& C=mesh().C(); forAll(V,i) {const vector& c=C[i]; eqn.source()[i] -= V[i]*vector('+','.join(expr)+',0);}'
        write(out/'constant/fvModels',header('fvModels')+'acceleration {type coded; cellZone all; field U; codeAddSup #{'+code+'#};}\n')
    write(out/'system/fvSchemes',header('fvSchemes')+'''ddtSchemes {default steadyState;}
gradSchemes {default Gauss linear;}
divSchemes {default none; div(phi,U) bounded Gauss linear; div(nuEff*dev2(T(grad(U)))) Gauss linear;}
laplacianSchemes {default Gauss linear corrected;}
interpolationSchemes {default linear;}
snGradSchemes {default corrected;}
''')
    write(out/'system/fvSolution',header('fvSolution')+'''solvers
{
 p {solver GAMG; tolerance 1e-11; relTol 0; smoother GaussSeidel;}
 U {solver smoothSolver; smoother symGaussSeidel; tolerance 1e-12; relTol 0;}
}
SIMPLE {nNonOrthogonalCorrectors 0; consistent yes; pRefCell 0; pRefValue 0;
 residualControl {p 1e-9; U 1e-10;}}
relaxationFactors {fields {p 0.7;} equations {U 0.8;}}
'''.replace('relTol 0;',f'relTol {relative};').replace('U 0.8;',f'U {relaxation};'))
    functions = '''gradU {type grad; libs ("libfieldFunctionObjects.so"); field U; result gradU; executeControl writeTime; writeControl writeTime;}
samples {type sets; libs ("libsampling.so"); writeControl writeTime; setFormat raw; interpolationScheme cellPoint;
fields (U p gradU); sets (observations {type points; axis xyz; ordered false; points ('''+ ' '.join(vec([*p,.05]) for p in probes)+''');});}
'''
    write(out/'system/controlDict', header('controlDict')+'''application foamRun; solver incompressibleFluid;
startFrom startTime; startTime 0; stopAt endTime; endTime 10000; deltaT 1;
writeControl timeStep; writeInterval 10000; purgeWrite 1; writeFormat ascii; writePrecision 17;
timeFormat general; timePrecision 12; runTimeModifiable false;
functions {'''+functions+'}\n')
    audit = dict(input_hashes={p.name:sha(p) for p in case.iterdir() if p.is_file()},
                 area=float(len(cells)),unit_cells=cells,n=n,cells=len(cells)*n*n,
                 acceleration_affine=affine.tolist(),source_nodal_fit_error=fit_error,
                 rho=rho,mu=mu,nu=mu/rho,probes=probes.tolist(),
                 pressure_gauge=j['analysis']['pressure_gauge'],
                 boundary_conditions={k:dict(operator=b['operator'],length=float(np.linalg.norm(b['edges'][:,1]-b['edges'][:,0],axis=1).sum())) for k,b in bs.items()})
    write(out/'translation.json',json.dumps(audit,indent=2)+'\n')
    return bs


def foam_list(path):
    text = re.sub(r'/\*.*?\*/|//[^\n]*','',path.read_text(),flags=re.S)
    body = re.search(r'\n\s*\d+\s*\n\s*\((.*)\)\s*$',text,re.S).group(1)
    return body


def set_boundaries(out, bs):
    mesh=out/'constant/polyMesh'
    points=np.array([[float(v) for v in s.split()] for s in re.findall(r'\(([^()]*)\)',foam_list(mesh/'points'))])
    faces=[list(map(int,s.split())) for s in re.findall(r'\d+\(([^()]*)\)',foam_list(mesh/'faces'))]
    boundary=(mesh/'boundary').read_text()
    ub='';pb=''; boundary_checks={}
    for name,content in re.findall(r'(\w+)\s*\{([^{}]*)\}',boundary):
        if name not in bs and name!='frontBack':continue
        if name=='frontBack':
            ub+=name+' {type empty;}\n';pb+=name+' {type empty;}\n';continue
        count=int(re.search(r'nFaces\s+(\d+)',content).group(1));start=int(re.search(r'startFace\s+(\d+)',content).group(1))
        values=[]
        for face in faces[start:start+count]:
            centre=points[face].mean(axis=0)[:2]
            matched,value=boundary_at(centre,bs)
            assert matched==name
            values.append([*value,0])
        assert len(values)==count
        op=bs[name]['operator']
        if op=='slip':ub+=name+' {type slip;}\n'
        else:ub+=name+' {type fixedValue; value nonuniform List<vector> '+str(count)+' ('+' '.join(vec(v) for v in values)+');}\n'
        pb+=name+' {type zeroGradient;}\n'
        boundary_checks[name]=dict(face_count=count,max_speed=float(np.linalg.norm(values,axis=1).max()))
    write(out/'0/U',header('U','volVectorField')+'dimensions [0 1 -1 0 0 0 0]; internalField uniform (0 0 0); boundaryField {\n'+ub+'}\n')
    write(out/'0/p',header('p','volScalarField')+'dimensions [0 2 -2 0 0 0 0]; internalField uniform 0; boundaryField {\n'+pb+'}\n')
    audit=json.loads((out/'translation.json').read_text());audit['mapped_boundary_faces']=boundary_checks
    write(out/'translation.json',json.dumps(audit,indent=2)+'\n')


def command(args, out, log):
    start=time.monotonic()
    with (out/log).open('w') as f:
        proc=subprocess.run(args,cwd=out,stdout=f,stderr=subprocess.STDOUT)
    return dict(command=args,returncode=proc.returncode,seconds=time.monotonic()-start,log_sha256=sha(out/log))


def run(case,out,n,relaxation=.8,relative=0.,initial_level=None):
    if (out/'execution.json').exists():
        previous=json.loads((out/'execution.json').read_text())
        if previous['solver']['returncode']==0 and previous['converged']:return previous
    if initial_level is not None and n>initial_level:
        initial=out.parent/f'n{initial_level}'
        deadline=time.monotonic()+3600
        while not (initial/'execution.json').exists():
            if time.monotonic()>deadline:raise TimeoutError(str(initial))
            time.sleep(1)
        proof=json.loads((initial/'execution.json').read_text())
        assert proof['converged'] and proof['solver']['returncode']==0
    bs=prepare(case,out,n,relaxation,relative)
    execution={}
    execution['mesh']=command(['blockMesh'],out,'blockMesh.log')
    if execution['mesh']['returncode']!=0:raise RuntimeError(str(out/'blockMesh.log'))
    set_boundaries(out,bs)
    execution['check_mesh']=command(['checkMesh'],out,'checkMesh.log')
    if initial_level is not None and n>initial_level:
        initial=out.parent/f'n{initial_level}'
        proof=json.loads((initial/'execution.json').read_text())
        assert proof['converged'] and proof['solver']['returncode']==0
        execution['initialization']=command(['mapFields',str(initial.resolve()),'-consistent','-sourceTime','latestTime','-mapMethod','cellPointInterpolate'],out,'mapFields.log')
        assert execution['initialization']['returncode']==0
        # Retain mapped internal guesses, then reapply the exact frozen wall data.
        prefixes={q:(out/'0'/q).read_text().split('boundaryField')[0] for q in ('U','p')}
        set_boundaries(out,bs)
        for q,prefix in prefixes.items():
            field=out/'0'/q
            write(field,prefix+'boundaryField'+field.read_text().split('boundaryField',1)[1])
        execution['initialization']['source_level']=initial_level
        execution['initialization']['source_execution_sha256']=sha(initial/'execution.json')
    execution['solver']=command(['foamRun'],out,'solver.log')
    log=(out/'solver.log').read_text()
    execution['converged']='SIMPLE solution converged' in log or 'SIMPLE: converged' in log
    execution['last_time']=re.findall(r'^Time = (.*)$',log,re.M)[-1:]
    write(out/'execution.json',json.dumps(execution,indent=2)+'\n')
    print(str(out),execution,flush=True)
    if execution['solver']['returncode']!=0:raise RuntimeError(str(out/'solver.log'))
    return execution


def main():
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('root',type=Path)
    p.add_argument('--levels',nargs='+',type=int,default=[16,32]);p.add_argument('--names',nargs='+');p.add_argument('--workers',type=int,default=1)
    p.add_argument('--relaxation',type=float,default=.8);p.add_argument('--linear-relative',type=float,default=0.)
    p.add_argument('--initial-level',type=int)
    a=p.parse_args()
    cases=sorted(c for c in (a.source/'cases').iterdir() if c.name!='lid-square' and (not a.names or c.name in a.names))
    # gmsh global state is deliberately prepared serially; separate processes allow independent runs.
    if a.workers>1:
        with concurrent.futures.ProcessPoolExecutor(a.workers) as pool:
            futures=[pool.submit(run,c,a.root/c.name/f'n{n}',n,a.relaxation,a.linear_relative,a.initial_level) for c in cases for n in a.levels]
            for f in futures:f.result()
    else:
        for c in cases:
            for n in a.levels:run(c,a.root/c.name/f'n{n}',n,a.relaxation,a.linear_relative,a.initial_level)


if __name__=='__main__':main()
