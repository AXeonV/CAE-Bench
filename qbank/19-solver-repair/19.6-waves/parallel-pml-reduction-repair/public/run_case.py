"""Convert public mesh/loads to genuine SPECFEM input and return raw solver samples."""
import argparse, os, re, subprocess, tempfile
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem,write_result
from caeoj.validation import read_mesh

BUILD=Path('/opt/specfem-repair-build/upstream')
HERE=Path(__file__).resolve().parent

def values(problem):
    result={k:v['value'] for k,v in problem.manifest['physics']['parameters'].items()}
    result['wave_branch']={'parallel-scalar-sh-v1':0,'parallel-scalar-acoustic-potential-v1':1}[problem.manifest['physics']['model']]
    return result

def prepare(problem,dest):
    """Pure serialization; no PDE or answer is evaluated here."""
    dest=Path(dest); data=dest/'DATA';data.mkdir(parents=True,exist_ok=True)
    (dest/'OUTPUT_FILES').mkdir(exist_ok=True)
    p=values(problem);a=problem.arrays
    mesh=read_mesh(problem.path.parent/problem.manifest['meshes']['domain']['file'],geometry=True)
    node_ids=sorted(mesh['nodes']);node_index={tag:i+1 for i,tag in enumerate(node_ids)}
    cells=[mesh['connectivity'][int(tag)][1] for tag in a['cell_ids']]
    points=mesh['node_coordinates'];pml=a['pml_region'][0,:,0]
    def write(name,rows,header=True):
        lines=([str(len(rows))] if header else [])+[' '.join(str(x) for x in row) for row in rows]
        (data/name).write_bytes(('\n'.join(lines)+'\n').encode())
    write('nodes',[(points[tag][0],points[tag][1]) for tag in node_ids])
    write('mesh',[tuple(node_index[n] for n in row) for row in cells])
    write('materials',[(1,)]*len(cells),False)
    # External horizontal faces of z-PML elements are SPECFEM absorbing faces.
    edge_count={}
    for row in cells:
        for k in range(4):
            edge=tuple(sorted((row[k],row[(k+1)%4])));edge_count[edge]=edge_count.get(edge,0)+1
    absorbing=[]
    for i,row in enumerate(cells):
        if pml[i]==0:continue
        for k,side in [(0,1),(2,3)]:
            n1,n2=row[k],row[(k+1)%4]
            if edge_count[tuple(sorted((n1,n2)))]==1:
                absorbing.append((i+1,2,node_index[n1],node_index[n2],side))
    write('absorbing',absorbing);write('pml',[(i+1,int(v)) for i,v in enumerate(pml) if v])
    write('free',[])
    template=(HERE/'Par_file.template').read_text()
    settings=dict(title='Parallel scalar wave propagation',NPROC=p['processes'],partitioning_method=1,
        ngnod=4,NSTEP=len(a['times']),DT=p['time_step'],P_SV='.false.' if p['wave_branch']==0 else '.true.',
        NSOURCES=len(a['source_ids']),initialfield='.false.',use_existing_STATIONS='.true.',
        record_at_surface_same_vertical='.false.',PML_BOUNDARY_CONDITIONS='.true.' if np.any(pml) else '.false.',
        STACEY_ABSORBING_CONDITIONS='.false.',read_external_mesh='.true.',nbmodels=1,
        mesh_file='./DATA/mesh',nodes_coords_file='./DATA/nodes',materials_file='./DATA/materials',
        free_surface_file='./DATA/free',absorbing_surface_file='./DATA/absorbing',absorbing_cpml_file='./DATA/pml',
        output_color_image='.false.',output_postscript_snapshot='.false.',OUTPUT_ENERGY='.false.',
        seismotype=1 if p['wave_branch']==0 else 6,USE_TRICK_FOR_BETTER_PRESSURE='.false.',
        save_binary_seismograms_single='.false.',save_binary_seismograms_double='.false.',
        NSTEP_BETWEEN_OUTPUT_INFO=100000,NELEM_PML_THICKNESS=3)
    for k,v in settings.items():template=re.sub(r'^'+k+r'\s*=.*$',f'{k} = {v}',template,flags=re.M)
    template=re.sub(r'^1 1 .*$',f'1 1 {p["density"]} {p["p_speed"]} {p["s_speed"]} 0 0 9999 9999 0 0 0 0 0 0',template,flags=re.M)
    template=re.sub(r'^[234] 1 .*\n','',template,flags=re.M)
    (data/'Par_file').write_bytes(template.encode())
    source_template=(HERE/'SOURCE.template').read_text();sources=[]
    for xy,amp in zip(a['source_coordinates'],a['source_amplitude'][0,:,0]):
        item=source_template
        for k,v in dict(xs=xy[0],zs=xy[1],f0=p['frequency'],factor=amp).items():
            item=re.sub(r'^'+k+r'\s*=.*$',f'{k} = {v}',item,flags=re.M)
        sources.append(item)
    (data/'SOURCE').write_bytes(('\n'.join(sources)+'\n').encode())
    (data/'STATIONS').write_bytes(('\n'.join(f'R{i:04d} AA {xy[0]:.17g} {xy[1]:.17g} 0 0' for i,xy in enumerate(a['probe_coordinates']))+'\n').encode())

def execute(problem,dest,build=BUILD,native_timeout=None):
    p=values(problem);env=dict(os.environ)
    env.update(OMPI_ALLOW_RUN_AS_ROOT='1',OMPI_ALLOW_RUN_AS_ROOT_CONFIRM='1')
    for exe in ['xmeshfem2D','xspecfem2D']:
        command=['mpirun','--oversubscribe','--bind-to','none','-np',str(p['processes']),str(build/'bin'/exe)]
        if native_timeout is not None:command=['timeout','--signal=TERM','--kill-after=2s',str(native_timeout)+'s',*command]
        result=subprocess.run(command,cwd=dest,env=env,capture_output=True,text=True)
        (Path(dest)/(exe+'.log')).write_text(result.stdout+'\n'+result.stderr)
        if result.returncode:raise RuntimeError(f'{exe} exit {result.returncode}:\n{result.stdout[-24000:]}\n{result.stderr[-8000:]}')
    traces=[]
    suffix='BXY.semd' if p['wave_branch']==0 else 'PRE.semp'
    for i in range(len(problem.arrays['probe_ids'])):
        raw=np.loadtxt(Path(dest)/'OUTPUT_FILES'/f'AA.R{i:04d}.{suffix}')
        if raw.shape!=(len(problem.arrays['times']),2):raise ValueError('SPECFEM sample count changed')
        if not np.allclose(raw[:,0],problem.arrays['times'],rtol=0,atol=5e-8):raise ValueError('SPECFEM sample times changed')
        traces.append(raw[:,1])
    return np.stack(traces,axis=1)[:,:,None].astype('float64')

def run(input_path,output_path):
    problem=load_problem(input_path)
    with tempfile.TemporaryDirectory(prefix='specfem-case-') as tmp:
        prepare(problem,tmp);result=execute(problem,tmp)
    write_result(output_path,problem,{'wave_response':result})

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--input',required=True,type=Path);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();run(args.input,args.output)
