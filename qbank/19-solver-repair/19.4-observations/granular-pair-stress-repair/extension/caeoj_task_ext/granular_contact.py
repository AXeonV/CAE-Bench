"""Strict declaration and domain checks for instantaneous spherical contacts."""
import numpy as np
from caeoj.validation import issue
TASK='granular-pair-stress-repair'
MODEL='instantaneous-granular-contact-v1'
V=['x','y','z'];S=['xx','yy','zz','xy','xz','yz']
FIELDS={'position':('position','m',V),'diameter':('diameter','m',['value']),'material_density':('mass_density','kg/m^3',['value']),'velocity':('velocity','m/s',V),'angular_velocity':('angular_velocity','rad/s',V)}
OUTPUTS={'force':('force','N',V),'torque':('torque','N*m',V),'particle_virial':('pair_virial','N*m',S),'pressure_tensor':('configurational_pressure','Pa',S)}
UNITS={'box_length':'m','normal_stiffness':'N/m','tangential_stiffness':'N/m','normal_damping':'1/s','tangential_damping':'1/s','friction':'1','tally_mode':'1'}
PARAMS={'box_length','normal_stiffness','tangential_stiffness','normal_damping','tangential_damping','friction','tally_mode'}
def spec(k,v,output=False):
    quantity,unit,components=v
    d={'array':k,'quantity':quantity,'unit':unit,'location':'system' if k=='pressure_tensor' else 'particles','time_axis':'instant','dtype':'float64','kind':'scalar' if len(components)==1 else 'components','component_shape':[len(components)],'components':components,'value_kind':'point'}
    if not output:d['sampling']={'space':'uniform','time':'constant','extrapolation':'forbid'}
    return d
def output_specs(mode):return {k:spec(k,v,True) for k,v in OUTPUTS.items() if k not in ['particle_virial','pressure_tensor'] or k=='particle_virial' and mode!='global' or k=='pressure_tensor' and mode!='particle'}
def check(p,errors):
    m,a=p.manifest,p.arrays
    def fail(path,expected,actual):errors.append(issue('E_GRANULAR_CONTACT',path,expected,str(actual),'Outside the public granular-contact DATA contract.'))
    decl=m['physics']['parameters'];s={k:v['value'] for k,v in decl.items()}
    if m.get('task')!=TASK or m['spatial_dimension']!=3 or m['geometries'] or m['meshes'] or m['conditions'] or m['physics']['model']!=MODEL or set(s)!=PARAMS:fail('$.physics','exact instantaneous granular declaration',m['physics']);return
    if decl!={k:{'value':s[k],'unit':UNITS[k]} for k in PARAMS}:fail('$.physics.parameters','specified constant units',decl)
    if m['locations']!={'particles':{'kind':'entities','ids':'particle_ids'},'system':{'kind':'entities','ids':'system_ids'}} or not 2<=len(a.get('particle_ids',[]))<=32 or not np.array_equal(a.get('system_ids'),[0]):fail('$.locations','2..32 particles and system_ids=[0]',m['locations'])
    if np.any(a['particle_ids']<1) or np.any(a['particle_ids']>1000000):fail('particle_ids','1..1000000',a['particle_ids'])
    if m['time_axes']!={'instant':'times'} or not np.array_equal(a.get('times'),[0.]):fail('$.time_axes','instant=[0]',m['time_axes'])
    for k,(lo,hi) in {'box_length':(3.,20.),'normal_stiffness':(100.,1e6),'tangential_stiffness':(10.,1e6),'normal_damping':(0.,10.),'tangential_damping':(0.,10.),'friction':(.1,1.)}.items():
        if isinstance(s[k],bool) or not isinstance(s[k],(float,int)) or not np.isfinite(s[k]) or not lo<=s[k]<=hi:fail('$.physics.parameters.'+k,f'{lo}..{hi}',s[k]);return
    if s['tally_mode'] not in [0,1,2]:fail('$.physics.parameters','mode0/1/2',s);return
    if m['fields']!={k:spec(k,v) for k,v in FIELDS.items()} or m['outputs']!=output_specs({0:'global',1:'particle',2:'both'}[s['tally_mode']]):fail('$.fields/outputs','exact field declarations',m['fields'])
    for k,(lo,hi) in {'diameter':(.1,1.5),'material_density':(100.,10000.),'velocity':(-.1,.1),'angular_velocity':(-.2,.2)}.items():
        if np.any(a[k]<lo) or np.any(a[k]>hi):fail('$.fields.'+k,f'{lo}..{hi}',a[k])
    x=a['position'][0];r=a['diameter'][0,:,0]/2;mass=4*np.pi/3*a['material_density'][0,:,0]*r**3
    if np.any(np.abs(x)+r[:,None]+.1>=s['box_length']/2):fail('position','sphere plus .1m margin strictly inside box',x)
    for i in range(len(x)):
        for j in range(i+1,len(x)):
            d=x[i]-x[j];dist=np.linalg.norm(d)
            if dist<.05:fail('position','pair separation >=.05m',dist);continue
            if dist>=r[i]+r[j]:continue
            normal=d/dist;dv=a['velocity'][0,i]-a['velocity'][0,j];vn=dv@normal;meff=mass[i]*mass[j]/(mass[i]+mass[j]);fn=s['normal_stiffness']*(r[i]+r[j]-dist)-meff*s['normal_damping']*vn
            vt=dv-vn*normal-np.cross(r[i]*a['angular_velocity'][0,i]+r[j]*a['angular_velocity'][0,j],normal)
            if fn<=0 or meff*s['tangential_damping']*np.linalg.norm(vt)>.8*s['friction']*fn:fail('contact','repulsive normal and tangential <=.8 Coulomb bound',(i,j,fn))
