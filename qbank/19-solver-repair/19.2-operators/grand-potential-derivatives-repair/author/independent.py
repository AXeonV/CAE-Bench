"""Independent polynomial calculus and exact linear FE integration, in SI units."""
import numpy as np

LOGICAL=['phi','eta0','eta1','eta2','eta3']
PROPERTIES=['void_minimum','solid_minimum','void_response','solid_response']

def evaluate(parameters, phi, eta, potential, concentration):
    p=parameters;eta=np.asarray(eta,dtype=float)
    a=np.array([p[f'equilibrium_linear_{i}'] for i in range(4)])
    b=np.zeros((4,4))
    for i in range(4):
        for j in range(i,4):b[i,j]=b[j,i]=p[f'equilibrium_hessian_{i}{j}']
    ceq=p['equilibrium_constant']+a@eta+.5*eta@b@eta
    g=a+b@eta
    if phi<=0:h,hp,hpp=0.,0.,0.
    elif phi>=1:h,hp,hpp=1.,0.,0.
    else:h=6*phi**5-15*phi**4+10*phi**3;hp=30*phi**2*(phi-1)**2;hpp=60*phi*(2*phi-1)*(phi-1)
    value=np.array([h,(1-h)*ceq,h/(p['atomic_volume']*p['void_energy_coefficient']),(1-h)/(p['atomic_volume']*p['solid_energy_coefficient'])])
    grad=np.zeros((4,5));hessian=np.zeros((4,5,5))
    grad[0,0]=hp;hessian[0,0,0]=hpp
    grad[1,0]=-hp*ceq;grad[1,1:]=(1-h)*g
    hessian[1,0,0]=-hpp*ceq;hessian[1,0,1:]=hessian[1,1:,0]=-hp*g;hessian[1,1:,1:]=(1-h)*b
    for k,denom,sign in [(2,p['atomic_volume']*p['void_energy_coefficient'],1),(3,p['atomic_volume']*p['solid_energy_coefficient'],-1)]:
        grad[k,0]=sign*hp/denom;hessian[k,0,0]=sign*hpp/denom
    result={}
    for i,name in enumerate(PROPERTIES):result[name]=np.array([value[i]]);result[name+'_gradient']=grad[i];result[name+'_hessian']=hessian[i].ravel()
    va=p['atomic_volume'];ks=p['solid_energy_coefficient'];kv=p['void_energy_coefficient'];w=potential
    result.update(void_number_density=np.array([w/(va*va*kv)+1/va]),solid_number_density=np.array([w/(va*va*ks)+ceq/va]),void_grand_potential=np.array([-.5*w*w/(va*va*kv)-w/va]),solid_grand_potential=np.array([-.5*w*w/(va*va*ks)-w*ceq/va]))
    length=p['probe_length'];mass=length*np.array([[2.,1.],[1.,2.]])/6
    result['constraint_residual']=np.full(2,length/2*(concentration-value[0]-value[1]-(value[2]+value[3])*w))
    slopes=-grad[0]-grad[1]-(grad[2]+grad[3])*w
    result['constraint_state_jacobian']=np.stack([s*mass for s in slopes]).ravel()
    result['constraint_potential_jacobian']=(-(value[2]+value[3])*mass).ravel()
    result['constraint_concentration_jacobian']=mass.ravel()
    return result

def reference(problem):
    p={k:v['value'] for k,v in problem.manifest['physics']['parameters'].items()};a=problem.arrays
    states=[evaluate(p,float(a['phi'][0,i,0]),a['eta'][0,i],float(a['potential'][0,i,0]),float(a['concentration'][0,i,0])) for i in range(len(a['program_ids']))]
    return {name:np.stack([s[name] for s in states])[None] for name in states[0]}
