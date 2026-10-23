"""Neutral adapter: real upstream reconstruction or full CFD, then output conversion."""
import argparse,csv,json,re,subprocess,tempfile,shutil,sys
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem,write_result
from read_vtk import read
HERE=Path(__file__).resolve().parent
def run(input_path,output_path,driver='/opt/su2-build/bin/reconstruction-driver',executable='/opt/su2-build/SU2_CFD/src/SU2_CFD',artifacts=None):
    p=load_problem(input_path);a=p.arrays;v={k:x['value'] for k,x in p.manifest['physics']['parameters'].items()};d=p.manifest['spatial_dimension']
    if v['operation']==0:
        n=len(a['edge_ids']);tokens=[str(n)]
        for i in range(n):
            tokens.extend(map(str,[d,v['gamma'],v['gas_constant'],v['kappa'],v['relax'],int(v['muscl']),int(v['limiter'])]))
            tokens.extend(map(str,a['displacement'][0,i]))
            for end in [2*i,2*i+1]:
                for k in ['temperature','velocity','pressure','density','enthalpy']:tokens.extend(map(str,a[k][0,end]))
                grad=np.vstack([a['gradient_temperature'][0,end],a['gradient_velocity'][0,end].reshape(d,d),a['gradient_pressure'][0,end]])
                tokens.extend(map(str,grad.flatten()));tokens.extend(map(str,a['limiters'][0,end]))
        r=subprocess.run([driver],input=' '.join(tokens)+'\n',text=True,capture_output=True)
        if r.returncode:sys.stderr.write(r.stderr);raise RuntimeError(f'Reconstruction exited {r.returncode}')
        y=np.array(json.loads(r.stdout),dtype='float64').reshape(2*n,2*d+6)
        out={'temperature':y[None,:,0:1],'velocity':y[None,:,1:d+1],'pressure':y[None,:,d+1:d+2],'density':y[None,:,d+2:d+3],'enthalpy':y[None,:,d+3:d+4],'momentum':y[None,:,d+5:2*d+5],'energy':y[None,:,2*d+5:2*d+6]}
    else:
        with tempfile.TemporaryDirectory(prefix='reconstruction-cfd-') as tmp:
            w=Path(tmp);shutil.copyfile(HERE/'flatplate.su2',w/'mesh.su2')
            cfg=(HERE/'flatplate.cfg').read_text()
            cfg=re.sub(r'^CFL_NUMBER=.*$',f'CFL_NUMBER= {v["cfl"]}',cfg,flags=re.M)
            cfg=re.sub(r'^ITER=.*$',f'ITER= {int(v["iterations"])+100}',cfg,flags=re.M)
            cfg=re.sub(r'^OUTPUT_FILES=.*$','OUTPUT_FILES= (PARAVIEW_ASCII,SURFACE_PARAVIEW_ASCII)',cfg,flags=re.M)
            cfg+='\nVOLUME_FILENAME= observed\nSURFACE_FILENAME= wall\n'
            (w/'config.cfg').write_text(cfg)
            r=subprocess.run([executable,'config.cfg'],cwd=w,text=True,capture_output=True)
            if artifacts is not None:
                artifacts.mkdir(parents=True,exist_ok=True);shutil.copytree(w,artifacts,dirs_exist_ok=True);(artifacts/'stdout.log').write_text(r.stdout);(artifacts/'stderr.log').write_text(r.stderr)
            if r.returncode:sys.stderr.write(r.stdout[-10000:]+r.stderr);raise RuntimeError(f'SU2_CFD exited {r.returncode}')
            _,flow=read(w/'observed.vtk');xyz,wall=read(w/'wall.vtk');order=np.argsort(xyz[:,0])
            with (w/'history.csv').open() as f:
                records=list(csv.DictReader(f,skipinitialspace=True))
            records=[{key.strip():value for key,value in row.items()} for row in records]
            last={k.strip():float(x) for k,x in records[-1].items()}
            res=np.array([last[k] for k in ['rms[Rho]','rms[RhoU]','rms[RhoV]','rms[RhoE]','rms[k]','rms[w]']])
            if res[0]>-10 or res[3]>-7:raise RuntimeError('Full CFD failed published residual bounds')
            if last['Inner_Iter']+1<int(v['iterations'])+100:raise RuntimeError('Full CFD stopped before the required observation steps')
            tail=records[-101:];drag=np.array([float(row['CD']) for row in tail])
            if len(tail)<101 or not np.isfinite(drag).all() or np.ptp(drag)>1e-3*abs(drag[-1]):raise RuntimeError('Drag did not remain stationary over the final 100 steps')
            out={'flow_density':flow['Density'][None],'flow_momentum':flow['Momentum'][None,:,:2],'flow_energy':flow['Energy'][None],'wall_cf':wall['Skin_Friction_Coefficient'][order,0][None,:,None],'residuals':res[None,None,:]}
    if any(not np.isfinite(x).all() for x in out.values()):raise RuntimeError('Nonfinite solver output')
    write_result(output_path,p,out)
if __name__=='__main__':
    s=argparse.ArgumentParser();s.add_argument('--input',type=Path,required=True);s.add_argument('--output',type=Path,required=True);s.add_argument('--driver',default='/opt/su2-build/bin/reconstruction-driver');s.add_argument('--executable',default='/opt/su2-build/SU2_CFD/src/SU2_CFD');s.add_argument('--artifacts',type=Path);o=s.parse_args();run(o.input,o.output,o.driver,o.executable,o.artifacts)
