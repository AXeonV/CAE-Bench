"""Convert one instantaneous contact state to/from the actual LAMMPS executable."""
import argparse, subprocess, tempfile, sys
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem, write_result

def run(input_path, output_path, executable='/opt/lammps-build/lmp'):
    p=load_problem(input_path);a=p.arrays;s={k:v['value'] for k,v in p.manifest['physics']['parameters'].items()};s['newton_pair']='off';s['tally_mode']={0:'global',1:'particle',2:'both'}[s['tally_mode']];ids=a['particle_ids'];n=len(ids);half=s['box_length']/2
    with tempfile.TemporaryDirectory() as temp:
        d=Path(temp)
        lines=['Instantaneous sphere state','',f'{n} atoms','1 atom types','']
        for axis in ['x','y','z']:lines.append(f'{-half:.17g} {half:.17g} {axis}lo {axis}hi')
        lines+=['','Atoms # sphere','']
        for i,k in enumerate(ids):lines.append(' '.join(map(str,[int(k),1,a['diameter'][0,i,0],a['material_density'][0,i,0],*a['position'][0,i]])))
        lines+=['','Velocities','']
        for i,k in enumerate(ids):lines.append(' '.join(map(str,[int(k),*a['velocity'][0,i],*a['angular_velocity'][0,i]])))
        (d/'atoms.data').write_text('\n'.join(lines)+'\n')
        mode=s['tally_mode'];global_on=mode in ['global','both'];atom_on=mode in ['particle','both']
        script=['units si','atom_style sphere','boundary f f f','newton '+s['newton_pair'],'read_data atoms.data','comm_modify vel yes',f"pair_style gran/hooke/history/kk {s['normal_stiffness']:.17g} {s['tangential_stiffness']:.17g} {s['normal_damping']:.17g} {s['tangential_damping']:.17g} {s['friction']:.17g} 1",'pair_coeff * *','neighbor 0.05 bin','neigh_modify delay 0 every 1 check yes','thermo 1']
        if global_on:script+=['compute P all pressure NULL pair','thermo_style custom step '+' '.join(f'c_P[{i}]' for i in range(1,7))]
        else:script+=['thermo_style custom step']
        if atom_on:script+=['compute S all stress/atom NULL pair']
        columns='id fx fy fz tqx tqy tqz'+(' '+' '.join(f'c_S[{i}]' for i in range(1,7)) if atom_on else '')
        script+=['dump D all custom 1 dump.txt '+columns,'dump_modify D sort id format float %.17g','run 0']
        if global_on:script+=['print "'+' '.join(f'$(c_P[{i}]:%.17g)' for i in range(1,7))+'" file global.txt screen no']
        (d/'input.lmp').write_text('\n'.join(script)+'\n')
        r=subprocess.run([executable,'-k','on','-sf','kk','-pk','kokkos','neigh','half','newton',s['newton_pair'],'-in','input.lmp'],cwd=d,text=True,capture_output=True)
        if r.returncode:sys.stderr.write(r.stdout+r.stderr);raise RuntimeError(f'LAMMPS exited {r.returncode}')
        raw=(d/'dump.txt').read_text().splitlines();start=next(i for i,l in enumerate(raw) if l.startswith('ITEM: ATOMS'))+1
        data=np.array([[float(t) for t in row.split()] for row in raw[start:start+n]])
        lookup={int(row[0]):row for row in data};data=np.array([lookup[int(k)] for k in ids])
        outputs={'force':data[None,:,1:4],'torque':data[None,:,4:7]}
        if atom_on:outputs['particle_virial']=-data[None,:,7:13]
        if global_on:outputs['pressure_tensor']=np.loadtxt(d/'global.txt').reshape(1,1,6)
        write_result(output_path,p,outputs)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--executable',default='/opt/lammps-build/lmp');a=p.parse_args();run(a.input,a.output,a.executable)
