"""Standalone numerical baseline. Reads input only; no recipe or reference imports."""
import argparse
from pathlib import Path
import numpy as np
import gmsh
from scipy.fft import dstn, idstn, fft2, ifft2, fftfreq
from scipy.sparse import diags
from scipy.sparse.linalg import splu
from caeoj.sdk import load_problem, read_constant, read_field, write_result


def grid(problem):
    source=next(c for c in problem.manifest['conditions'] if c['role']=='source')
    domain=problem.manifest['locations'][source['location']]
    ids=problem.arrays[domain['ids']]
    gmsh.initialize([],readConfigFiles=False)
    try:
        gmsh.option.setNumber('General.Terminal',0)
        gmsh.open(str(problem.path.parent/problem.manifest['meshes'][domain['mesh']]['file']))
        tags,coordinates,_=gmsh.model.mesh.getNodes()
        order=np.argsort(tags)
        xy=coordinates.reshape(-1,3)[order,:2][np.searchsorted(tags[order],ids)]
    finally:
        gmsh.finalize()
    xs,ys=np.unique(np.round(xy[:,0],8)),np.unique(np.round(xy[:,1],8))
    ix=np.argmin(abs(xy[:,0,None]-xs[None,:]),axis=1)
    iy=np.argmin(abs(xy[:,1,None]-ys[None,:]),axis=1)
    if len(xs)*len(ys)!=len(ids): raise ValueError('Expected supplied Cartesian grid')
    return xy,xs,ys,ix,iy


def side_name(p,location,xy):
    """Identify a rectangle side by referenced tags and coordinates, not its label."""
    source=next(c for c in p.manifest['conditions'] if c['role']=='source')
    ids=p.arrays[p.manifest['locations'][source['location']]['ids']]
    boundary=p.arrays[p.manifest['locations'][location]['ids']]
    points=xy[np.searchsorted(ids,boundary)]
    if np.ptp(points[:,0])<1e-7:
        return 'left' if abs(points[0,0]-xy[:,0].min())<1e-7 else 'right'
    if np.ptp(points[:,1])<1e-7:
        return 'bottom' if abs(points[0,1]-xy[:,1].min())<1e-7 else 'top'
    raise ValueError('Expected a rectangle boundary')


def output_times(p):
    field=next(iter(p.manifest['outputs'].values()))
    return p.arrays[p.manifest['time_axes'][field['time_axis']]]


def input_values(p):
    params={k:float(read_constant(v)) for k,v in p.manifest['physics']['parameters'].items()}
    conditions=p.manifest['conditions']
    source=next(c for c in conditions if c['role']=='source')
    force=read_field(p,source['data']['value'])[0,0]
    initial=next((c for c in conditions if c['role']=='initial'),None)
    u0=read_field(p,initial['data']['value'])[0] if initial else None
    return params,conditions,force,u0


def channel(p,xy,xs,ys,ix,iy,par,conditions,force,u0):
    periodic=next(c for c in conditions if c['operator']=='periodic')
    axis=0 if side_name(p,periodic['location'],xy) in ('left','right') else 1
    transverse=1-axis
    coordinate=ys if axis==0 else xs
    h=coordinate[1]-coordinate[0]
    nu=par['dynamic_viscosity']/par['density']
    n=len(coordinate)
    walls=[c for c in conditions if c['variable']=='velocity' and c['role']=='boundary']
    values={side_name(p,c['location'],xy):float(read_field(p,c['data']['value'])[0,0,axis]) for c in walls}
    lower=values['bottom' if axis==0 else 'left']
    upper=values['top' if axis==0 else 'right']
    lap=diags([np.ones(n-3),-2*np.ones(n-2),np.ones(n-3)],[-1,0,1],format='csc')*nu/h**2
    load=np.full(n-2,force[axis]);load[0]+=nu*lower/h**2;load[-1]+=nu*upper/h**2
    times=output_times(p)
    profiles=[]
    if u0 is None:
        inner=splu(-lap).solve(load)
        profiles=[np.r_[lower,inner,upper]]
    else:
        tindex=iy if axis==0 else ix
        profile=np.array([u0[np.flatnonzero(tindex==i)[0],axis] for i in range(n)])
        profiles=[profile.copy()]
        inner=profile[1:-1].copy()
        ident=diags([np.ones(n-2)],[0],format='csc')
        cache={}
        for j in range(1,len(times)):
            interval=times[j]-times[j-1]
            target=0.0001*(coordinate[-1]-coordinate[0])**2/nu
            steps=max(1,int(np.ceil(interval/target)))
            dt=interval/steps
            key=round(dt,12)
            if key not in cache:
                cache[key]=(splu(ident-0.5*dt*lap),ident+0.5*dt*lap)
            solve,B=cache[key]
            for step in range(steps):
                # Rannacher startup suppresses unresolved initial boundary layers.
                if j==1 and step==0:
                    be=splu(ident-0.5*dt*lap)
                    inner=be.solve(inner+0.5*dt*load)
                    inner=be.solve(inner+0.5*dt*load)
                else:
                    inner=solve.solve(B@inner+dt*load)
            profiles.append(np.r_[lower,inner,upper])
    tindex=iy if axis==0 else ix
    u=np.zeros((len(times),len(xy),2))
    u[:,:,axis]=np.array(profiles)[:,tindex]
    return {'velocity':u,'pressure':np.zeros((len(times),len(xy),1))}


def periodic(p,xy,xs,ys,ix,iy,par,u0):
    nx,ny=len(xs)-1,len(ys)-1
    lx,ly=xs[-1]-xs[0],ys[-1]-ys[0]
    nu=par['dynamic_viscosity']/par['density']
    rho=par['density']
    full=np.zeros((len(ys),len(xs),2));full[iy,ix]=u0
    state=np.moveaxis(full[:-1,:-1],-1,0)
    kx=2*np.pi*fftfreq(nx,d=lx/nx)[None,:]
    ky=2*np.pi*fftfreq(ny,d=ly/ny)[:,None]
    k2=kx*kx+ky*ky
    inv=np.divide(1,k2,out=np.zeros_like(k2),where=k2>0)
    mask=(abs(kx)<2*np.pi/lx*nx/3)&(abs(ky)<2*np.pi/ly*ny/3)

    def nonlinear(hat):
        values=ifft2(hat,axes=(-2,-1)).real
        dx=ifft2(1j*kx*hat,axes=(-2,-1)).real
        dy=ifft2(1j*ky*hat,axes=(-2,-1)).real
        return fft2(values[0]*dx+values[1]*dy,axes=(-2,-1))*mask

    def rhs(hat):
        nh=nonlinear(hat)
        dot=kx*nh[0]+ky*nh[1]
        projected=nh-np.stack((kx*dot*inv,ky*dot*inv))
        return -projected-nu*k2*hat

    def snapshot(hat):
        values=ifft2(hat,axes=(-2,-1)).real
        nh=nonlinear(hat)
        pressure=ifft2(rho*1j*(kx*nh[0]+ky*nh[1])*inv).real
        # Duplicate periodic endpoints for the supplied Gmsh nodes.
        return np.column_stack((values[0,iy%ny,ix%nx],values[1,iy%ny,ix%nx])),pressure[iy%ny,ix%nx,None]

    hat=fft2(state,axes=(-2,-1))*mask
    results,pressures=[],[]
    times=output_times(p)
    maxspeed=max(float(np.max(abs(state))),0.1)
    # RK4's diffusion stability interval extends to 2.78; keep margin for advection.
    limit=min(0.8/(nu*np.max(k2)),0.3*min(lx/nx,ly/ny)/maxspeed)
    current=0.0
    for output_time in times:
        if output_time>current:
            steps=max(1,int(np.ceil((output_time-current)/limit)))
            dt=(output_time-current)/steps
            for _ in range(steps):
                a=rhs(hat);b=rhs(hat+dt*a/2);c=rhs(hat+dt*b/2);d=rhs(hat+dt*c)
                hat=hat+dt/6*(a+2*b+2*c+d)
            current=output_time
        values,pressure=snapshot(hat)
        if output_time==0: values=u0.copy()
        results.append(values);pressures.append(pressure)
    return {'velocity':np.array(results),'pressure':np.array(pressures)}


def cavity(p,xy,xs,ys,par,conditions):
    nx,ny=len(xs)-1,len(ys)-1
    hx,hy=(xs[-1]-xs[0])/nx,(ys[-1]-ys[0])/ny
    nu=par['dynamic_viscosity']/par['density']
    walls={side_name(p,c['location'],xy):read_field(p,c['data']['value'])[0]
           for c in conditions if c['role']=='boundary' and c['variable']=='velocity'}
    speed=max(float(np.max(abs(values))) for values in walls.values())
    boundary={side:values[np.argmax(np.linalg.norm(values,axis=1))] for side,values in walls.items()}
    psi=np.zeros((ny+1,nx+1));omega=np.zeros_like(psi)
    eigen=2*(np.cos(np.pi*np.arange(1,nx)/nx)-1)[None,:]/hx**2
    eigen=eigen+2*(np.cos(np.pi*np.arange(1,ny)/ny)-1)[:,None]/hy**2

    def poisson(w):
        result=np.zeros_like(w)
        result[1:-1,1:-1]=idstn(dstn(-w[1:-1,1:-1],type=1,norm='ortho')/eigen,type=1,norm='ortho')
        return result

    def evaluate(w):
        stream=poisson(w)
        w=w.copy()
        w[0,1:-1]=-2*stream[1,1:-1]/hy**2+2*boundary['bottom'][0]/hy
        w[-1,1:-1]=-2*stream[-2,1:-1]/hy**2-2*boundary['top'][0]/hy
        w[1:-1,0]=-2*stream[1:-1,1]/hx**2-2*boundary['left'][1]/hx
        w[1:-1,-1]=-2*stream[1:-1,-2]/hx**2+2*boundary['right'][1]/hx
        u=np.zeros_like(w);v=np.zeros_like(w)
        u[1:-1,1:-1]=(stream[2:,1:-1]-stream[:-2,1:-1])/(2*hy)
        v[1:-1,1:-1]=-(stream[1:-1,2:]-stream[1:-1,:-2])/(2*hx)
        u[0,1:-1],v[0,1:-1]=boundary['bottom']
        u[-1,1:-1],v[-1,1:-1]=boundary['top']
        u[1:-1,0],v[1:-1,0]=boundary['left']
        u[1:-1,-1],v[1:-1,-1]=boundary['right']
        wx=(w[1:-1,2:]-w[1:-1,:-2])/(2*hx)
        wy=(w[2:,1:-1]-w[:-2,1:-1])/(2*hy)
        lap=(w[1:-1,2:]-2*w[1:-1,1:-1]+w[1:-1,:-2])/hx**2
        lap+=(w[2:,1:-1]-2*w[1:-1,1:-1]+w[:-2,1:-1])/hy**2
        return stream,u,v,nu*lap-u[1:-1,1:-1]*wx-v[1:-1,1:-1]*wy

    dt=min(0.2*min(hx,hy)/max(speed,0.1),0.2/(nu*(1/hx**2+1/hy**2)))
    length=xs[-1]-xs[0]
    max_steps=int(np.ceil(80*length/max(speed,0.1)/dt))
    stable=0
    for step in range(max_steps):
        _,_,_,a=evaluate(omega)
        trial=omega.copy();trial[1:-1,1:-1]+=dt*a
        _,_,_,b=evaluate(trial)
        delta=dt*(a+b)/2
        omega[1:-1,1:-1]+=delta
        if not np.isfinite(omega).all(): raise RuntimeError('Cavity integration diverged')
        if step%50==0:
            residual=float(np.max(abs(delta)))/dt
            stable=stable+1 if residual<1e-6*max(speed,0.1)**2/length**2 else 0
            if stable>=3: break
    else:
        raise RuntimeError('Cavity did not reach steady state')
    _,u,v,_=evaluate(omega)
    # General probe coordinates, bilinear interpolation of the numerical grid.
    def sample(values,name):
        loc=p.manifest['outputs'][name]['location']
        coordinates=p.arrays[p.manifest['locations'][loc]['coordinates']]
        from scipy.interpolate import RegularGridInterpolator
        return RegularGridInterpolator((ys,xs),values)(coordinates[:,[1,0]])[None,:,None]
    return {'u_centerline':sample(u,'u_centerline'),'v_centerline':sample(v,'v_centerline')}


def solve_values(p):
    xy,xs,ys,ix,iy=grid(p)
    par,conditions,force,u0=input_values(p)
    count=sum(c['operator']=='periodic' for c in conditions)
    if count==2:
        values=periodic(p,xy,xs,ys,ix,iy,par,u0)
    elif count==1:
        values=channel(p,xy,xs,ys,ix,iy,par,conditions,force,u0)
    else:
        values=cavity(p,xy,xs,ys,par,conditions)
    return {p.manifest['outputs'][name]['array']:value for name,value in values.items()}


def solve(input_path,output_path):
    p=load_problem(input_path)
    write_result(output_path,p,solve_values(p))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();solve(args.input,args.output)
