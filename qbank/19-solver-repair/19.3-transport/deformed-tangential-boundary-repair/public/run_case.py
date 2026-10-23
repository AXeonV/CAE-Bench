"""Build declared native ASPECT input and read its native fixed Cartesian PointValues."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import numpy as np
from caeoj.sdk import load_problem, write_result

def configuration(m, points, directory):
    p={k:v['value'] for k,v in m['physics']['parameters'].items()}
    d=m['spatial_dimension']; family={'deformed-tangential-parallel-v1': 0, 'deformed-tangential-wedge-v1': 1, 'deformed-tangential-annulus-v1': 2}[m['physics']['model']]
    W=p.get('width'); H=p.get('height')
    if family==2:
        geometry=f'''  set Model name = spherical shell
  subsection Spherical shell
    set Inner radius = {p['inner_radius']}
    set Outer radius = {p['outer_radius']}
    set Opening angle = 360
  end'''
        temperature_boundaries='bottom, top'
        material_boundaries=f'''  set Tangential velocity boundary indicators = top
  set Prescribed velocity boundary indicators = bottom: function'''
        velocity=f"{-p['angular_speed']}*y; {p['angular_speed']}*x"
        mesh=''; gravity='radial constant'; gravity_section='Radial constant'
    else:
        geometry=f'''  set Model name = box
  subsection Box
    set X extent = {W}
    set Y extent = {H if d==2 else p['depth']}
    set X repetitions = 2
'''+(f"    set Z extent = {H}\n" if d==3 else '')+'  end'
        temperature_boundaries='bottom, top, left, right'+(', front, back' if d==3 else '')
        if family==0:
            material_boundaries='  set Tangential velocity boundary indicators = top, bottom\n  set Prescribed velocity boundary indicators = left: function, right: function'+(', front: function, back: function' if d==3 else '')
            velocity=f"{p['velocity_x']}; {p['rate_x']*p['velocity_x']}*t" if d==2 else f"{p['velocity_x']}; {p['velocity_y']}; {p['rate_x']*p['velocity_x']+p['rate_y']*p['velocity_y']}*t"
            mesh_velocity=f"0; {p['rate_x']}*x" if d==2 else f"0; 0; {p['rate_x']}*x+{p['rate_y']}*y"
            deforming='top: boundary function, bottom: boundary function'
        else:
            material_boundaries='  set Tangential velocity boundary indicators = top, left, right\n  set Prescribed velocity boundary indicators = bottom: function'
            velocity=f"{p['peak_velocity']}*(1-(2*x/{W}-1)^2); 0"
            mesh_velocity=f"0; {p['rate_x']}*(x-{W}/2)"
            deforming='top: boundary function'
        mesh=f'''subsection Mesh deformation
  set Mesh deformation boundary indicators = {deforming}
  set Additional tangential mesh velocity boundary indicators = left,right'''+(',front,back' if d==3 else '')+f'''
  subsection Boundary function
    set Variable names = {','.join(['x','y','z'][:d])},t
    set Function expression = {mesh_velocity}
  end
end
'''
        gravity='vertical'; gravity_section='Vertical'
    point_text='; '.join(','.join(format(float(v),'.17g') for v in row) for row in points)
    return f'''set Dimension = {d}
set End time = {p['end_time']}
set Maximum time step = {p['time_step']}
set Use years instead of seconds = false
set Adiabatic surface temperature = {p['temperature']}
set CFL number = 1e6
set Pressure normalization = surface
set Output directory = {directory}
subsection Geometry model
{geometry}
end
subsection Boundary temperature model
  set Fixed temperature boundary indicators = {temperature_boundaries}
  set List of model names = initial temperature
end
subsection Initial temperature model
  set List of model names = function
  subsection Function
    set Function expression = {p['temperature']}
  end
end
subsection Boundary velocity model
{material_boundaries}
  subsection Function
    set Variable names = {','.join(['x','y','z'][:d])},t
    set Function expression = {velocity}
  end
end
{mesh}subsection Gravity model
  set Model name = {gravity}
  subsection {gravity_section}
    set Magnitude = 0
  end
end
subsection Material model
  set Model name = simple
  subsection Simple model
    set Reference density = {p['density']}
    set Thermal conductivity = 1
    set Thermal expansion coefficient = 0
    set Reference specific heat = 1
    set Viscosity = {p['viscosity']}
    set Reference temperature = {p['temperature']}
  end
end
subsection Mesh refinement
  set Initial adaptive refinement = 0
  set Initial global refinement = {int(p['refinement'])}
  set Time steps between mesh refinement = 0
end
subsection Postprocess
  set List of postprocessors = point values
  subsection Point values
    set Evaluation points = {point_text}
    set Time between point values output = 0
    set Use natural coordinates = false
  end
end
subsection Solver parameters
  subsection Stokes solver parameters
    set Linear solver tolerance = 1e-10
    set Stokes solver type = block AMG
  end
end
'''

def native(m, arrays, executable, work):
    work=Path(work); work.mkdir(parents=True,exist_ok=True)
    (work/'input.prm').write_text(configuration(m,arrays['probe_coordinates'],work/'native'))
    env=os.environ.copy()
    # Native ASPECT is a single rank process in this task. The official OpenMPI
    # singleton option avoids starting a supporting daemon for unused spawning.
    env['OMPI_MCA_ess_singleton_isolated']='1'
    env['OMP_NUM_THREADS']='1';env['OPENBLAS_NUM_THREADS']='1'
    r=subprocess.run([str(executable),str(work/'input.prm')],text=True,capture_output=True,env=env)
    (work/'stdout.log').write_text(r.stdout); (work/'stderr.log').write_text(r.stderr)
    if r.returncode:
        sys.stderr.write(r.stdout[-12000:]+r.stderr[-12000:]);raise RuntimeError(f'ASPECT exited {r.returncode}')
    rows=np.loadtxt(work/'native'/'point_values.txt',comments='#',ndmin=2)
    d=m['spatial_dimension']; n=len(arrays['probe_ids']); times=arrays['times']
    if rows.shape!=(len(times)*n,2*d+3):raise ValueError(f'Native PointValues shape {rows.shape} does not match requested times/points')
    rows=rows.reshape(len(times),n,-1)
    # GNUPlot-style native PointValues uses six significant figures. No interpolation.
    if not np.allclose(rows[:,:,0],times[:,None],rtol=5e-6,atol=1e-12):raise ValueError('Native output times differ from requested frames')
    if not np.allclose(rows[:,:,1:1+d],arrays['probe_coordinates'][None],rtol=5e-6,atol=1e-12):raise ValueError('Native fixed Cartesian points changed identity')
    return {'velocity':rows[:,:,1+d:1+2*d].copy(),'pressure':rows[:,:,1+2*d:2+2*d].copy()}

def run(input_path,output_path,executable='/opt/aspect-build/aspect-release'):
    p=load_problem(input_path)
    with tempfile.TemporaryDirectory(prefix='aspect-fixed-points-') as tmp:
        fields=native(p.manifest,p.arrays,executable,Path(tmp))
        write_result(output_path,p,fields)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--executable',default='/opt/aspect-build/aspect-release');a=ap.parse_args();run(a.input,a.output,a.executable)
