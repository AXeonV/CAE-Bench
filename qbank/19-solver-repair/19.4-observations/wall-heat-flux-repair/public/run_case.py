"""Convert declared mesh/boundaries, run actual SU2, and extract native outputs."""
import argparse,csv,subprocess,tempfile,sys
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem,write_result
from caeoj.validation import read_mesh
def write_su2(path,mesh):
    tags=sorted(mesh['nodes']);index={tag:i for i,tag in enumerate(tags)}
    cells=sorted(mesh['elements'][2]);lines=['NDIME= 2',f'NELEM= {len(cells)}']
    for tag in cells:
        typ,conn=mesh['connectivity'][tag]
        if typ!=3:raise ValueError('Expected quadrilaterals')
        lines.append('9 '+' '.join(str(index[i]) for i in conn))
    lines.append(f'NPOIN= {len(tags)}')
    for i,tag in enumerate(tags):
        x,y,_=mesh['node_coordinates'][tag];lines.append(f'{x:.17g} {y:.17g} {i}')
    lines.append('NMARK= 4')
    for group,name in [(1,'hot'),(2,'cold'),(3,'left'),(4,'right')]:
        elements=sorted(mesh['groups'][(1,group)]['elements']);lines.extend([f'MARKER_TAG= {name}',f'MARKER_ELEMS= {len(elements)}'])
        for tag in elements:
            typ,conn=mesh['connectivity'][tag]
            if typ!=1:raise ValueError('Expected edges')
            lines.append('3 '+' '.join(str(index[i]) for i in conn))
    path.write_text('\n'.join(lines)+'\n');return tags,index
def config(v):
    text=f'''SOLVER= INC_NAVIER_STOKES
MATH_PROBLEM= DIRECT
RESTART_SOL= NO
INC_DENSITY_MODEL= CONSTANT
INC_ENERGY_EQUATION= YES
INC_DENSITY_INIT= {v['density']}
INC_VELOCITY_INIT= ({v['velocity']},0.,0.)
INC_TEMPERATURE_INIT= {(v['bottom_temperature']+v['top_temperature'])/2}
INC_NONDIM= REFERENCE_VALUES
INC_DENSITY_REF= 1.0
INC_VELOCITY_REF= 1.0
INC_TEMPERATURE_REF= 300.0
FLUID_MODEL= CONSTANT_DENSITY
SPECIFIC_HEAT_CP= {v['heat_capacity']}
VISCOSITY_MODEL= CONSTANT_VISCOSITY
MU_CONSTANT= {v['viscosity']}
CONDUCTIVITY_MODEL= CONSTANT_CONDUCTIVITY
THERMAL_CONDUCTIVITY_CONSTANT= {v['conductivity']}
'''
    if v['boundary_mode']==0:text+=f"MARKER_ISOTHERMAL= (hot,{v['bottom_temperature']},cold,{v['top_temperature']})\n"
    else:text+=f"MARKER_ISOTHERMAL= (cold,{v['top_temperature']})\nMARKER_HEATFLUX= (hot,{v['bottom_heat_flux']})\n"
    if v['velocity']==0:text+='MARKER_SYM= (left,right)\n'
    else:
        U=v['velocity'];text+=f'''INC_INLET_TYPE= VELOCITY_INLET
INC_OUTLET_TYPE= PRESSURE_OUTLET
MARKER_INLET= (left,300.,{U},1.,0.,0.)
MARKER_OUTLET= (right,0.)
SPECIFIED_INLET_PROFILE= YES
INLET_FILENAME= inlet.dat
SURFACE_MOVEMENT= (MOVING_WALL,MOVING_WALL)
MARKER_MOVING= (hot,cold)
SURFACE_MOTION_ORIGIN= (0.,0.,0.,0.,0.,0.)
SURFACE_TRANSLATION_RATE= ({U},0.,0.,{U},0.,0.)
'''
    text+=f'''MARKER_MONITORING= (hot,cold)
MARKER_PLOTTING= (hot,cold)
NUM_METHOD_GRAD= WEIGHTED_LEAST_SQUARES
CFL_NUMBER= {v['cfl']}
CFL_ADAPT= NO
ITER= {int(v['iterations'])}
CONV_FIELD= (RMS_TEMPERATURE)
CONV_RESIDUAL_MINVAL= -8
CONV_STARTITER= 10
LINEAR_SOLVER= FGMRES
LINEAR_SOLVER_PREC= ILU
LINEAR_SOLVER_ERROR= 1e-10
LINEAR_SOLVER_ITER= 30
CONV_NUM_METHOD_FLOW= FDS
MUSCL_FLOW= NO
TIME_DISCRE_FLOW= EULER_IMPLICIT
MESH_FILENAME= mesh.su2
MESH_FORMAT= SU2
TABULAR_FORMAT= CSV
SCREEN_OUTPUT= (INNER_ITER,RMS_PRESSURE,RMS_TEMPERATURE,TOTAL_HEATFLUX)
SCREEN_WRT_FREQ_INNER= 100
HISTORY_OUTPUT= (ITER,RMS_RES,HEAT,HEAT_SURF)
VOLUME_OUTPUT= (COORDINATES,SOLUTION,PRIMITIVE,HEAT_FLUX)
OUTPUT_FILES= (CSV,SURFACE_CSV,RESTART_ASCII)
OUTPUT_WRT_FREQ= 30000
OUTPUT_PRECISION= 15
''';return text
def run(input_path,output_path,executable):
    p=load_problem(input_path);a=p.arrays;v={k:x['value'] for k,x in p.manifest['physics']['parameters'].items()};mesh=read_mesh(p.path.parent/'mesh.msh',geometry=True)
    with tempfile.TemporaryDirectory(prefix='wall-energy-') as tmp:
        w=Path(tmp);tags,index=write_su2(w/'mesh.su2',mesh);(w/'config.cfg').write_text(config(v))
        if v['velocity']>0:
            lines=['NMARK= 1','MARKER_TAG= left',f'NROW= {len(a["inlet_ids"])}','NCOL= 6','# COORD-X COORD-Y TEMPERATURE VELOCITY NORMAL-X NORMAL-Y']
            for tag,T in zip(a['inlet_ids'],a['inlet_temperature'][0,:,0]):
                x,y,_=mesh['node_coordinates'][int(tag)];lines.append(f'{x:.17g} {y:.17g} {T:.17g} {v["velocity"]:.17g} 1 0')
            (w/'inlet.dat').write_text('\n'.join(lines)+'\n')
        r=subprocess.run([executable,'config.cfg'],cwd=w,text=True,capture_output=True)
        if r.returncode:sys.stderr.write(r.stdout[-10000:]+r.stderr);raise RuntimeError(f'SU2 exited {r.returncode}')
        flow=np.genfromtxt(w/'restart.csv',delimiter=',',names=True);wall=np.genfromtxt(w/'surface.csv',delimiter=',',names=True)
        flow=flow[np.argsort(flow['PointID'])];by_id={int(row['PointID']):row for row in wall}
        q=np.array([by_id[index[int(tag)]]['Heat_Flux'] for tag in a['wall_ids']])
        with (w/'history.csv').open() as f:records=list(csv.DictReader(f,skipinitialspace=True))
        last={k.strip():float(value) for k,value in records[-1].items()};res=last['rms[T]']
        if res>-8:raise RuntimeError(f'Temperature residual {res} exceeds -8')
        out={'temperature':flow['Temperature'][None,:,None]*300.,'velocity':np.column_stack([flow['Velocity_x'],flow['Velocity_y']])[None],
             'pressure':flow['Pressure'][None,:,None],'wall_heat_flux':q[None,:,None],
             'bottom_heat_rate':np.array([[[last['HF(hot)']]]]),'top_heat_rate':np.array([[[last['HF(cold)']]]]),'temperature_residual':np.array([[[res]]])}
        if any(not np.isfinite(z).all() for z in out.values()):raise RuntimeError('Nonfinite CFD output')
        write_result(output_path,p,out)
if __name__=='__main__':
    s=argparse.ArgumentParser();s.add_argument('--input',type=Path,required=True);s.add_argument('--output',type=Path,required=True);s.add_argument('--executable',default='/opt/su2-build/SU2_CFD/src/SU2_CFD');v=s.parse_args();run(v.input,v.output,v.executable)
