"""Independent continuum solution and boundary energy audit; author only."""
import numpy as np
from caeoj.validation import read_mesh
def audit(p,z):
    v={k:x['value'] for k,x in p.manifest['physics']['parameters'].items()};mesh=read_mesh(p.path.parent/'mesh.msh',geometry=True);a=p.arrays
    xy=np.array([mesh['node_coordinates'][int(tag)][:2] for tag in a['node_ids']]);wallxy=np.array([mesh['node_coordinates'][int(tag)][:2] for tag in a['wall_ids']]);L=xy[:,0].max();H=xy[:,1].max()
    k=v['conductivity'];Th=v['bottom_temperature'];Tc=v['top_temperature'];U=v['velocity'];rho=v['density'];cp=v['heat_capacity'];A=0.
    if U:
        inletxy=np.array([mesh['node_coordinates'][int(tag)][:2] for tag in a['inlet_ids']]);sine=np.sin(np.pi*inletxy[:,1]/H)
        A=float(np.dot(a['inlet_temperature'][0,:,0]-(Th+(Tc-Th)*inletxy[:,1]/H),sine)/np.dot(sine,sine))
    elif v['boundary_mode']==1:Th=Tc+v['bottom_heat_flux']*H/k
    def exact(x,y):
        T=Th+(Tc-Th)*y/H;Ty=np.full_like(x,(Tc-Th)/H);Tx=np.zeros_like(x)
        if U:
            alpha=k/(rho*cp);kn=np.pi/H;d=np.sqrt(U*U+4*alpha*alpha*kn*kn);rp=(U+d)/(2*alpha);rn=-2*alpha*kn*kn/(U+d);r=rn/rp;den=1-r*np.exp((rn-rp)*L)
            e=np.exp(rn*x);f=np.exp(rn*L+rp*(x-L));X=(e-r*f)/den;Xp=rn*(e-f)/den
            T=T+A*np.sin(kn*y)*X;Ty=Ty+A*kn*np.cos(kn*y)*X;Tx=A*np.sin(kn*y)*Xp
        return T,Tx,Ty
    target,_,_=exact(xy[:,0],xy[:,1]);_,_,dy=exact(wallxy[:,0],wallxy[:,1]);q=k*dy*np.where(wallxy[:,1]<H/2,1.,-1.)
    Tdiff=z['temperature'][0,:,0]-target;qdiff=z['wall_heat_flux'][0,:,0]-q
    result={'temperature_max_abs_error_K':float(max(abs(Tdiff))),'temperature_rms_error_K':float(np.sqrt(np.mean(Tdiff**2))),
            'velocity_max_abs_error':float(np.max(abs(z['velocity']-np.array([[[U,0.]]])))),
            'wall_q_max_abs_error_W_m2':float(max(abs(qdiff))),'wall_q_relative_l2_error':float(np.linalg.norm(qdiff)/max(np.linalg.norm(q),1e-30))}
    physical= result['temperature_max_abs_error_K']<(1. if U else 1e-4) and result['velocity_max_abs_error']<1e-8
    if U:physical &= result['wall_q_relative_l2_error']<.025
    else:physical &= result['wall_q_max_abs_error_W_m2']<.001
    # Continuous full energy balance, including axial diffusion.
    xx=np.linspace(0,L,10001);yy=np.linspace(0,H,10001);exact_rates=[]
    for y,sign in [(0.,1.),(H,-1.)]:
        _,_,dY=exact(xx,np.full_like(xx,y));exact_rates.append(float(np.trapezoid(sign*k*dY,xx)))
    t0,tx0,_=exact(np.zeros_like(yy),yy);tL,txL,_=exact(np.full_like(yy,L),yy)
    exact_open=float(np.trapezoid(rho*cp*U*(tL-t0)-k*(txL-tx0),yy))
    rates=[float(z['bottom_heat_rate'][0,0,0]),float(z['top_heat_rate'][0,0,0])]
    result.update(continuum_wall_heat_rates_W=exact_rates,actual_wall_heat_rates_W=rates,
                  continuum_open_heat_rate_W=exact_open,continuum_balance_W=exact_open+sum(exact_rates))
    if not U:physical &= max(abs(np.array(rates)-exact_rates))<.001
    else:
        # Second-order one-sided derivative of actual fields at open boundaries;
        # its truncation error is reported, not confused with exact FV balance.
        ys=np.unique(xy[:,1]);left=[];right=[];dl=[];dr=[]
        for y in ys:
            ix=np.flatnonzero(xy[:,1]==y);ix=ix[np.argsort(xy[ix,0])];x=xy[ix,0];T=z['temperature'][0,ix,0]
            left.append(T[0]);right.append(T[-1]);dl.append(np.polyfit(x[:3]-x[0],T[:3],2)[1]);dr.append(np.polyfit(x[-3:]-x[-1],T[-3:],2)[1])
        numerical_open=float(np.trapezoid(rho*cp*U*(np.array(right)-left)-k*(np.array(dr)-dl),ys))
        imbalance=numerical_open+sum(rates);scale=sum(abs(x) for x in rates)
        result.update(actual_open_heat_rate_estimate_W=numerical_open,actual_boundary_balance_estimate_W=imbalance,relative_boundary_balance_estimate=abs(imbalance)/scale)
        physical &= abs(imbalance)/scale<.05
    result['passed']=bool(physical);return result
