"""Existing pimpleFoam annulus producer with equivalent fixed-normal/Robin BC.

On r=R, u_r=cos(theta), omega=0 is equivalent to
du_theta/dr=-(u_theta+sin(theta))/R. directionMixed implements the latter with
alpha=1/(1+R*deltaCoeff); its normal projector fixes U.n to (1,0).n.
This is an existing boundary type, without generated solver or dynamic code.
Initial U is the analytic harmonic-Poisson startup approved for the migration.
"""
import json,os,re,subprocess,time
from pathlib import Path
import numpy as np
from scipy.interpolate import CubicSpline
from catalog import WORK
from cavity_openfoam import foam,setup

def read_list(path):
    text=Path(path).read_text();start=text.index('}',text.index('FoamFile'))+1
    match=re.search(r'\b(\d+)\s*\(',text[start:]);n=int(match.group(1));offset=start+match.end()
    return n,text[offset:text.rfind(')')]

def geometry(path):
    n,body=read_list(path/'points');pts=np.fromstring(body.replace('(',' ').replace(')',' '),sep=' ').reshape(n,3)
    n,body=read_list(path/'faces');faces=[np.fromstring(row,sep=' ',dtype=int) for row in re.findall(r'\d+\s*\(([^)]*)\)',body)]
    if len(faces)!=n:raise ValueError('Wrong face count')
    no,body=read_list(path/'owner');owner=np.fromstring(body,sep=' ',dtype=int)
    nn,body=read_list(path/'neighbour');nei=np.fromstring(body,sep=' ',dtype=int)
    nc=int(max(owner.max(),nei.max())+1);vertices=[set() for _ in range(nc)]
    for j,f in enumerate(faces):
        vertices[owner[j]].update(f)
        if j<nn:vertices[nei[j]].update(f)
    centers=[]
    for ids in vertices:
        xy=np.unique(pts[list(ids),:2],axis=0);mean=xy.mean(axis=0)
        order=np.argsort(np.arctan2(xy[:,1]-mean[1],xy[:,0]-mean[0]));xy=xy[order]-mean;nxt=np.roll(xy,-1,axis=0)
        cross=xy[:,0]*nxt[:,1]-nxt[:,0]*xy[:,1];A2=cross.sum()
        centers.append(np.r_[mean+(np.sum((xy+nxt)*cross[:,None],axis=0)/(3*A2)),0.])
    return pts,faces,owner,np.array(centers)

def mesh_dict(Nr,Nphi):
    points=[]
    for z in (-.05,.05):
        for r in (.5,10):
            points.extend((r*np.cos(j*np.pi/2),r*np.sin(j*np.pi/2),z) for j in range(4))
    vertices='\n'.join('('+ ' '.join(f'{v:.17g}' for v in p)+')' for p in points)
    blocks=[];arcs=[];inner=[];outer=[];empty=[]
    for j in range(4):
        k=(j+1)%4;ids=(j,j+4,k+4,k,j+8,j+12,k+12,k+8)
        blocks.append('hex ('+' '.join(map(str,ids))+f') ({Nr} {Nphi//4} 1) simpleGrading (64 1 1)')
        inner.append(f'({j} {j+8} {k+8} {k})');outer.append(f'({j+4} {k+4} {k+12} {j+12})')
        empty.extend((f'({j} {k} {k+4} {j+4})',f'({j+8} {j+12} {k+12} {k+8})'))
        for zbase,z in ((0,-.05),(8,.05)):
            for radial,r in ((0,.5),(4,10)):
                angle=(j+.5)*np.pi/2
                arcs.append(f'arc {j+zbase+radial} {k+zbase+radial} ({r*np.cos(angle):.17g} {r*np.sin(angle):.17g} {z})')
    return foam('blockMeshDict',f'''convertToMeters 1;
vertices ({vertices}); blocks ({' '.join(blocks)}); edges ({' '.join(arcs)});
boundary (inner {{type wall;faces ({' '.join(inner)});}} outer {{type patch;faces ({' '.join(outer)});}} frontBack {{type empty;faces ({' '.join(empty)});}});mergePatchPairs ();
''')

def setup_annulus(job,Nr,Nphi,dt,env):
    dt,T=setup(job,12,Nr,dt)
    (job/'system/blockMeshDict').write_text(mesh_dict(Nr,Nphi))
    control=(job/'system/controlDict').read_text();control=control[:control.index('functions {')]
    (job/'system/controlDict').write_text(control)
    (job/'constant/transportProperties').write_text(foam('transportProperties','transportModel Newtonian;nu [0 2 -1 0 0 0 0] 0.005;'))
    (job/'0/p').write_text(foam('p','''dimensions [0 2 -2 0 0 0 0];internalField uniform 0;
boundaryField {inner {type fixedFluxPressure;value uniform 0;} outer {type fixedFluxPressure;value uniform 0;} frontBack {type empty;}}
''','volScalarField'))
    with (job/'blockMesh.log').open('w') as log:subprocess.run(['blockMesh','-case',str(job)],stdout=log,stderr=subprocess.STDOUT,env=env,check=True)
    points,faces,owner,C=geometry(job/'constant/polyMesh')
    text=(job/'constant/polyMesh/boundary').read_text();entry=text[text.index('outer'):]
    nfaces=int(re.search(r'nFaces\s+(\d+)',entry)[1]);start=int(re.search(r'startFace\s+(\d+)',entry)[1])
    matrices=[]
    for j in range(start,start+nfaces):
        fc=points[faces[j]].mean(axis=0);n=fc.copy();n[2]=0;n/=np.linalg.norm(n)
        delta=float(np.dot(fc-C[owner[j]],n))
        if delta<=0:raise ValueError('Wrong exterior normal/owner')
        alpha=delta/(10+delta);P=np.outer(n,n);M=P+alpha*(np.eye(3)-P);M[2,2]=1
        matrices.append('('+' '.join(f'{v:.17g}' for v in (M[0,0],M[0,1],M[0,2],M[1,1],M[1,2],M[2,2]))+')')
    r2=C[:,0]**2+C[:,1]**2;A=1/(1-.25/100)
    U=np.column_stack((A*(1-.25*(C[:,0]**2-C[:,1]**2)/r2**2),-A*.5*C[:,0]*C[:,1]/r2**2,np.zeros(len(C))))
    values='\n'.join('('+' '.join(f'{v:.17g}' for v in u)+')' for u in U)
    (job/'0/U').write_text(foam('U',f'''dimensions [0 1 -1 0 0 0 0];
internalField nonuniform List<vector> {len(C)} ({values});
boundaryField {{inner {{type fixedValue;value uniform (0 0 0);}}
outer {{type directionMixed;refValue uniform (1 0 0);refGradient uniform (0 0 0);
valueFraction nonuniform List<symmTensor> {nfaces} ({' '.join(matrices)});value uniform (1 0 0);}}
frontBack {{type empty;}} }}
''','volVectorField'))
    np.savez(job/'mesh-geometry.npz',centers=C)
    return dt,T

def read_vector_field(path):
    text=Path(path).read_text();match=re.search(r'internalField\s+nonuniform\s+List<vector>\s+(\d+)\s*\(',text)
    if match is None:raise ValueError('Expected nonuniform velocity')
    end=text.index('\n)',match.end());data=text[match.end():end]
    a=np.fromstring(data.replace('(',' ').replace(')',' '),sep=' ').reshape(-1,3)
    if len(a)!=int(match[1]):raise ValueError('Wrong cell field count')
    return a

def convert(job,Nr,Nphi):
    # OpenFOAM may write the final accumulated time as 9.999999999999897.
    # Select only the requested terminal time within roundoff; never use an
    # arbitrary latest checkpoint as if it were the requested final field.
    candidates=[]
    for path in job.iterdir():
        if not path.is_dir():continue
        try:t=float(path.name)
        except ValueError:continue
        if abs(t-10.)<=1e-10 and (path/'U').is_file():candidates.append(path)
    if len(candidates)!=1:raise ValueError('Need exactly one complete t=10 velocity field, within roundoff')
    final=candidates[0]
    C=np.load(job/'mesh-geometry.npz')['centers'];U=read_vector_field(final/'U')
    (job/'conversion-source.json').write_text(json.dumps(dict(requested_time=10.,actual_time=float(final.name),source_directory=final.name,time_tolerance=1e-10),indent=2))
    r=np.hypot(C[:,0],C[:,1]);phi=np.arctan2(C[:,1],C[:,0])%(2*np.pi)
    # Discover tensor coordinates from actual geometry; do not guess cell order.
    sector=np.floor(phi/(2*np.pi)*Nphi).astype(int)%Nphi
    R=[];UR=[];UT=[];angles=[]
    for j in range(Nphi):
        rows=np.flatnonzero(sector==j);rows=rows[np.argsort(r[rows])]
        if len(rows)!=Nr:raise ValueError('Non-tensor polar cells')
        ph=phi[rows];angles.append(ph.mean());R.append(r[rows])
        UR.append(U[rows,0]*np.cos(ph)+U[rows,1]*np.sin(ph));UT.append(-U[rows,0]*np.sin(ph)+U[rows,1]*np.cos(ph))
    radii=np.mean(R,axis=0);angles=np.array(angles)
    if np.max(np.abs(np.array(R)-radii))>1e-7:raise ValueError('Radial cell geometry is not separable')
    if np.max(np.abs(np.diff(angles)-2*np.pi/Nphi))>1e-7:raise ValueError('Nonuniform azimuth geometry')
    ur=np.array(UR);ut=np.array(UT)
    k=np.fft.fftfreq(Nphi,d=1/Nphi)[:,None]
    ur_theta=np.fft.ifft(1j*k*np.fft.fft(ur,axis=0),axis=0).real
    # Inner velocity is the prescribed no-slip trace. The Robin exterior trace
    # is reconstructed using the same coefficient and geometry as the FV BC.
    h=10-radii[-1];outer_ut=(10*ut[:,-1]-h*np.sin(angles))/(10+h)
    knots=np.r_[.5,radii,10]
    ut_full=np.column_stack((np.zeros(Nphi),ut,outer_ut))
    derivative=CubicSpline(knots,knots[None,:]*ut_full,axis=1).derivative()
    omega=derivative(radii)/radii-ur_theta/radii
    wall_omega=derivative(.5)/.5 # no-slip trace has zero tangential derivative of ur
    omega_full=np.column_stack((wall_omega,omega,np.zeros(Nphi)))
    psi_spline=CubicSpline(knots,ut_full,axis=1).antiderivative()
    faces=.5+9.5*(.5-.5*np.cos(np.linspace(0,np.pi,65)));queryr=(faces[1:]+faces[:-1])/2
    queryphi=(np.arange(64)+.5)*2*np.pi/64
    phase=np.exp(1j*(queryphi[:,None]-angles[0])*np.fft.fftfreq(Nphi,d=1/Nphi)[None,:])
    psi=20-(psi_spline(queryr)-psi_spline(.5)[:,None])
    vort=CubicSpline(knots,omega_full,axis=1)(queryr)
    out={name:(phase@(np.fft.fft(value,axis=0)/Nphi)).real.T.ravel() for name,value in [('psi',psi),('omega',vort)]}
    residual=psi_spline(10)-psi_spline(.5)+10*np.sin(angles)
    np.savez(job/'native.npz',**out,time=10.,conversion_version=2,outer_streamfunction_reconstruction_rms=float(np.sqrt(np.mean(residual**2))))

def main():
    extra=subprocess.check_output(['bash','-lc','source /usr/share/openfoam/etc/bashrc >/dev/null 2>&1;env -0'])
    env={**os.environ,**dict(v.decode().split('=',1) for v in extra.split(b'\0') if b'=' in v),'OMP_NUM_THREADS':'1'}
    for Nr,Nphi,dt in ((64,96,.004),(128,192,.002),(256,384,.001)):
        job=WORK/'cylinder-openfoam'/f'R{Nr}-P{Nphi}';job.mkdir(parents=True,exist_ok=True)
        record=job/'process.json'
        if record.exists() and json.loads(record.read_text()).get('returncode')==0:
            if not (job/'native.npz').exists():convert(job,Nr,Nphi)
            continue
        dt,T=setup_annulus(job,Nr,Nphi,dt,env);started=time.time()
        with (job/'solver.log').open('w') as log:
            p=subprocess.Popen(['pimpleFoam','-noFunctionObjects','-case',str(job)],stdout=log,stderr=subprocess.STDOUT,env=env)
            data=dict(status='running',pid=p.pid,started_unix=started,Nr=Nr,Nphi=Nphi,dt=dt)
            record.write_text(json.dumps(data,indent=2));rc=p.wait()
        data.update(status='finished',returncode=rc,wall_seconds=time.time()-started);record.write_text(json.dumps(data,indent=2));print(json.dumps(data),flush=True)
        if rc:break
        convert(job,Nr,Nphi)

if __name__=='__main__':main()
