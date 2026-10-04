"""Independent continuum references: exact channel series and periodic vortex."""
import numpy as np
from ghia import U, V, X, Y, DOI, CROSSCHECK


def initial_channel(case, s):
    if case.initial == 'linear':
        return s.copy()
    if case.initial == 'modes':
        return 0.6*np.sin(np.pi*s)-0.3*np.sin(3*np.pi*s)+0.2*np.sin(7*np.pi*s)
    if case.initial == 'plate':
        return np.where((s>0.2)&(s<0.55),0.8,np.where((s>=0.55)&(s<0.8),-0.5,0.0))
    if case.initial == 'pulse':
        return 0.9*np.maximum(1-abs(s-0.35)/0.12,0)
    if case.initial == 'oscillatory':
        return 0.45*np.sin(2*np.pi*s)+0.25*np.sin(9*np.pi*s)-0.15*np.sin(13*np.pi*s)
    if case.initial == 'reverse':
        return 0.7-1.4*s
    if case.initial == 'double_pulse':
        return 0.8*np.maximum(1-abs(s-0.25)/0.1,0)-0.6*np.maximum(1-abs(s-0.7)/0.15,0)
    return np.zeros_like(s)


def vortex(case, xy, times):
    k = 2*np.pi*case.mode/case.size[0]
    velocity, pressure = [], []
    for t in times:
        xx=k*(xy[:,0]-case.origin[0]-case.drift[0]*t)+case.phase[0]
        yy=k*(xy[:,1]-case.origin[1]-case.drift[1]*t)+case.phase[1]
        if case.pattern == 'shear':
            wave=2*np.pi*np.array(case.wave)/case.size[0]
            angle=(xy-np.array(case.origin)-np.array(case.drift)*t)@wave+case.phase[0]
            direction=np.array([wave[1],-wave[0]])/np.linalg.norm(wave)
            speed=case.amplitude*np.sin(angle)*np.exp(-case.nu*(wave@wave)*t)
            velocity.append(np.array(case.drift)+speed[:,None]*direction)
            pressure.append(np.zeros((len(xy),1)))
            continue
        # All streamfunction modes share Laplace eigenvalue 2*k^2.
        # Their nonlinear self-advection is a gradient, giving exact pressure.
        matrix=np.array(case.coefficients or (case.amplitude,0,0,0)).reshape(2,2)
        matrix=matrix*np.exp(-2*case.nu*k*k*t)
        fx=np.column_stack((np.sin(xx),np.cos(xx)))
        fy=np.column_stack((np.sin(yy),np.cos(yy)))
        dx=np.column_stack((np.cos(xx),-np.sin(xx)))
        dy=np.column_stack((np.cos(yy),-np.sin(yy)))
        psi=np.einsum('ni,ij,nj->n',fx,matrix,fy)/k
        u=np.einsum('ni,ij,nj->n',fx,matrix,dy)
        v=-np.einsum('ni,ij,nj->n',dx,matrix,fy)
        velocity.append(np.column_stack((case.drift[0]+u,case.drift[1]+v)))
        p=case.rho*(np.sum(matrix**2)/2-(u*u+v*v+2*k*k*psi*psi)/2)
        pressure.append(p[:,None])
    return np.array(velocity),np.array(pressure)


def cavity_observations(case):
    """Rigid reflections/rotations of published coordinates AND vector components."""
    frames={
        ('top',1):(((1,0),(0,1)),(0,0)),
        ('top',-1):(((-1,0),(0,1)),(1,0)),
        ('bottom',1):(((1,0),(0,-1)),(0,1)),
        ('bottom',-1):(((-1,0),(0,-1)),(1,1)),
        ('left',1):(((0,-1),(1,0)),(1,0)),
        ('left',-1):(((0,-1),(-1,0)),(1,1)),
        ('right',1):(((0,1),(1,0)),(0,0)),
        ('right',-1):(((0,1),(-1,0)),(0,1)),
    }
    matrix,offset=map(np.array,frames[case.lid,case.lid_sign])
    first=np.column_stack((np.full(17,.5),Y))@matrix.T+offset
    second=np.column_stack((X,np.full(17,.5)))@matrix.T+offset
    if matrix[0,0]:
        vertical,horizontal=first,second
        u,v=matrix[0,0]*U,matrix[1,1]*V
    else:
        vertical,horizontal=second,first
        u,v=matrix[0,1]*V,matrix[1,0]*U
    return (np.array(case.origin)+case.size[0]*vertical,
            np.array(case.origin)+case.size[0]*horizontal,
            case.upper*u,case.upper*v,matrix,offset)


def channel_reference(case, xy, times, initial):
    transverse = 1-case.axis
    h = case.size[transverse]
    y = xy[:,transverse]-case.origin[transverse]
    base = case.lower+(case.upper-case.lower)*y/h+case.acceleration*y*(h-y)/(2*case.nu)
    if initial is None:
        values = base[None,:]
        certificate = {'type':'steady_channel_exact'}
    else:
        # Exact integrals of the specified continuous piecewise-linear initial profile.
        ys = np.unique(y)
        u0 = np.array([initial[np.argmin(abs(y-s)),case.axis] for s in ys])
        n = np.arange(1,1025,dtype=np.float64)
        k = n*np.pi/h
        slope = np.diff(u0)/np.diff(ys)
        yl, yr = ys[:-1,None],ys[1:,None]
        integrals = (-u0[1:,None]*np.cos(yr*k)+u0[:-1,None]*np.cos(yl*k))/k
        integrals += slope[:,None]*(np.sin(yr*k)-np.sin(yl*k))/k**2
        b0=2/h*integrals.sum(axis=0)
        bs=2/(n*np.pi)*(case.lower-case.upper*(-1)**n)
        bs+=2*case.acceleration*h*h/case.nu/(n*np.pi)**3*(1-(-1)**n)
        coeff=b0-bs
        values=[]
        for t in times:
            if t == 0:
                values.append(initial[:,case.axis].copy())
            else:
                values.append(base+np.sin(y[:,None]*k)@(coeff*np.exp(-case.nu*k*k*t)))
        values=np.array(values)
        positive=times[times>0]
        # Bound omitted coefficients by 2*sup|u0-base| and an integral Gaussian tail.
        from scipy.special import erfc
        a=case.nu*(np.pi/h)**2*positive.min()
        maximum=max(abs(case.lower),abs(case.upper))
        if case.acceleration:
            critical=h/2+(case.upper-case.lower)*case.nu/(case.acceleration*h)
            if 0<critical<h:
                maximum=max(maximum,abs(case.lower+(case.upper-case.lower)*critical/h+
                    case.acceleration*critical*(h-critical)/(2*case.nu)))
        tail=2*(np.max(abs(u0))+maximum)*np.sqrt(np.pi)/(2*np.sqrt(a))*erfc(np.sqrt(a)*1024)
        certificate={'type':'piecewise_linear_initial_sine_series','modes':1024,
                     'absolute_tail_bound':float(tail),'initial_interpretation':'linear transverse profile'}
    velocity=np.zeros((len(times),len(xy),2))
    velocity[:,:,case.axis]=values
    return {'velocity':velocity,'pressure':np.zeros((len(times),len(xy),1))},certificate


def reference(case, xy, times, initial=None):
    if case.family == 'cavity':
        _,_,u,v,matrix,offset=cavity_observations(case)
        return {'u_centerline':u[None,:,None],
                'v_centerline':v[None,:,None]}, {
                    'type':'published_steady_centerlines','Re':100,'source':DOI,
                    'tables':['I','II'],'crosscheck':CROSSCHECK,
                    'rounding':'coordinates 4 decimals; velocities 5 decimals',
                    'no_full_field_or_pressure_reference':True,
                    'coordinate_transform':{'matrix':matrix.tolist(),'offset':offset.tolist()}}
    if case.family == 'periodic':
        u,p=vortex(case,xy,times)
        return {'velocity':u,'pressure':p},{'type':'advected_periodic_shear' if case.pattern=='shear'
            else 'advected_decaying_periodic_vortex','pattern':case.pattern,
            'coefficients':case.coefficients,'wave':case.wave,
            'amplitude':case.amplitude,'drift':case.drift,'mode':case.mode,'phase':case.phase}
    return channel_reference(case,xy,times,initial)
