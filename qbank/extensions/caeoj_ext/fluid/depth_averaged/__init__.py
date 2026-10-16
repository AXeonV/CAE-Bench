"""Physical declarations and helpers for depth averaged."""
import numpy as np
from .._declaration_checks import check_declaration
from .._geometry import boundary_geometry

MODELS = {'fluid-reduced-fully-wet-steady-v1': {'slug': 'fully-wet-steady',
                                       'dimension': 2,
                                       'transient': False,
                                       'parameters': {'density': 'kg/m3',
                                                      'gravity': 'm/s2',
                                                      'drag_rate': '1/s'},
                                       'domain': {'bed': ('material',
                                                          'geometry',
                                                          'm',
                                                          'scalar',
                                                          'finite')},
                                       'outputs': ['depth', 'velocity', 'water_flux', 'water_volume'],
                                       'family': 'water',
                                       'boundary_rules': {'water_wall': ('water',
                                                                         {'mode': ('option',
                                                                                   'impermeable')}),
                                                          'water_reservoir': ('water',
                                                                              {'depth': ('scalar',
                                                                                         'm',
                                                                                         'positive'),
                                                                               'velocity': ('vector',
                                                                                            'm/s',
                                                                                            'finite')})},
                                       'required_outputs': ['depth', 'velocity'],
                                       'output_specs': {'depth': ('m', 'scalar'),
                                                        'velocity': ('m/s', 'vector'),
                                                        'water_flux': ('m2/s', 'vector'),
                                                        'water_volume': ('m3', 'scalar')},
                                       'integral_outputs': ['water_volume'],
                                       'boundary_outputs': [],
                                       'thermal_boundary': False,
                                       'wall_velocity_keys': {},
                                       'required_open_ops': ['water_reservoir'],
                                       'exchange_wall_only': False,
                                       'signed_parameters': [],
                                       'nonnegative_parameters': ['drag_rate']},
 'fluid-reduced-fully-wet-transient-v1': {'slug': 'fully-wet-transient',
                                          'dimension': 2,
                                          'transient': True,
                                          'parameters': {'density': 'kg/m3',
                                                         'gravity': 'm/s2',
                                                         'drag_rate': '1/s',
                                                         'start_time': 's',
                                                         'end_time': 's'},
                                          'domain': {'bed': ('material',
                                                             'geometry',
                                                             'm',
                                                             'scalar',
                                                             'finite'),
                                                     'depth': ('initial',
                                                               'assign',
                                                               'm',
                                                               'scalar',
                                                               'positive'),
                                                     'velocity': ('initial',
                                                                  'assign',
                                                                  'm/s',
                                                                  'vector',
                                                                  'finite')},
                                          'outputs': ['depth', 'velocity', 'water_flux', 'water_volume'],
                                          'family': 'water',
                                          'boundary_rules': {'water_wall': ('water',
                                                                            {'mode': ('option',
                                                                                      'impermeable')}),
                                                             'water_reservoir': ('water',
                                                                                 {'depth': ('scalar',
                                                                                            'm',
                                                                                            'positive'),
                                                                                  'velocity': ('vector',
                                                                                               'm/s',
                                                                                               'finite')})},
                                          'required_outputs': ['depth', 'velocity'],
                                          'output_specs': {'depth': ('m', 'scalar'),
                                                           'velocity': ('m/s', 'vector'),
                                                           'water_flux': ('m2/s', 'vector'),
                                                           'water_volume': ('m3', 'scalar')},
                                          'integral_outputs': ['water_volume'],
                                          'boundary_outputs': [],
                                          'thermal_boundary': False,
                                          'wall_velocity_keys': {},
                                          'required_open_ops': [],
                                          'exchange_wall_only': False,
                                          'signed_parameters': ['start_time', 'end_time'],
                                          'nonnegative_parameters': ['drag_rate']},
 'fluid-reduced-wetting-drying-v1': {'slug': 'wetting-drying',
                                     'dimension': 2,
                                     'transient': True,
                                     'parameters': {'density': 'kg/m3',
                                                    'gravity': 'm/s2',
                                                    'drag_rate': '1/s',
                                                    'start_time': 's',
                                                    'end_time': 's'},
                                     'domain': {'bed': ('material', 'geometry', 'm', 'scalar', 'finite'),
                                                'depth': ('initial',
                                                          'assign',
                                                          'm',
                                                          'scalar',
                                                          'nonnegative'),
                                                'velocity': ('initial',
                                                             'assign',
                                                             'm/s',
                                                             'vector',
                                                             'finite')},
                                     'outputs': ['depth', 'velocity', 'water_flux', 'water_volume'],
                                     'family': 'water_dry',
                                     'boundary_rules': {'water_wall': ('water',
                                                                       {'mode': ('option',
                                                                                 'impermeable')}),
                                                        'water_reservoir': ('water',
                                                                            {'depth': ('scalar',
                                                                                       'm',
                                                                                       'positive'),
                                                                             'velocity': ('vector',
                                                                                          'm/s',
                                                                                          'finite')})},
                                     'required_outputs': ['depth', 'velocity'],
                                     'output_specs': {'depth': ('m', 'scalar'),
                                                      'velocity': ('m/s', 'vector'),
                                                      'water_flux': ('m2/s', 'vector'),
                                                      'water_volume': ('m3', 'scalar')},
                                     'integral_outputs': ['water_volume'],
                                     'boundary_outputs': [],
                                     'thermal_boundary': False,
                                     'wall_velocity_keys': {},
                                     'required_open_ops': [],
                                     'exchange_wall_only': False,
                                     'signed_parameters': ['start_time', 'end_time'],
                                     'nonnegative_parameters': ['drag_rate']},
 'fluid-reduced-two-layer-v1': {'slug': 'two-layer',
                                'dimension': 2,
                                'transient': True,
                                'parameters': {'lower_density': 'kg/m3',
                                               'upper_density': 'kg/m3',
                                               'gravity': 'm/s2',
                                               'bottom_drag': '1/s',
                                               'interface_drag': 'kg/(m2.s)',
                                               'start_time': 's',
                                               'end_time': 's'},
                                'domain': {'bed': ('material', 'geometry', 'm', 'scalar', 'finite'),
                                           'lower_depth': ('initial',
                                                           'assign',
                                                           'm',
                                                           'scalar',
                                                           'positive'),
                                           'lower_velocity': ('initial',
                                                              'assign',
                                                              'm/s',
                                                              'vector',
                                                              'finite'),
                                           'upper_depth': ('initial',
                                                           'assign',
                                                           'm',
                                                           'scalar',
                                                           'positive'),
                                           'upper_velocity': ('initial',
                                                              'assign',
                                                              'm/s',
                                                              'vector',
                                                              'finite')},
                                'outputs': ['lower_depth',
                                            'upper_depth',
                                            'lower_velocity',
                                            'upper_velocity',
                                            'water_volume'],
                                'family': 'water_two',
                                'boundary_rules': {'layer_wall': ('layers',
                                                                  {'mode': ('option', 'impermeable')}),
                                                   'layer_inlet': ('layers',
                                                                   {'lower_depth': ('scalar',
                                                                                    'm',
                                                                                    'positive'),
                                                                    'lower_velocity': ('vector',
                                                                                       'm/s',
                                                                                       'finite'),
                                                                    'upper_depth': ('scalar',
                                                                                    'm',
                                                                                    'positive'),
                                                                    'upper_velocity': ('vector',
                                                                                       'm/s',
                                                                                       'finite')}),
                                                   'layer_outflow': ('layers',
                                                                     {'mode': ('option',
                                                                               'supercritical_outflow')})},
                                'required_outputs': ['lower_depth',
                                                     'lower_velocity',
                                                     'upper_depth',
                                                     'upper_velocity'],
                                'output_specs': {'lower_depth': ('m', 'scalar'),
                                                 'upper_depth': ('m', 'scalar'),
                                                 'lower_velocity': ('m/s', 'vector'),
                                                 'upper_velocity': ('m/s', 'vector'),
                                                 'water_volume': ('m3', 'scalar')},
                                'integral_outputs': ['water_volume'],
                                'boundary_outputs': [],
                                'thermal_boundary': False,
                                'wall_velocity_keys': {},
                                'required_open_ops': [],
                                'exchange_wall_only': False,
                                'signed_parameters': ['start_time', 'end_time'],
                                'nonnegative_parameters': ['bottom_drag', 'interface_drag']}}

def reduced_parameters(problem):
    """Return declared SI constants, with no defaulting or conversion."""
    return {k:v['value'] for k,v in problem.manifest['physics']['parameters'].items()}


def _check_parameters(cfg, p, fail):
    if 'lower_density' in p and p['lower_density']<=p.get('upper_density',0):
        fail('$.physics.parameters','lower_density > upper_density',p,'Stable density ordering required.')

def _check_boundary(cfg, p, op, data, values, problem, loc, requirements, fail, path):
    m = problem.manifest
    if op=='layer_inlet':
        axes={m['fields'][x['field']]['time_axis'] for x in data.values() if 'field' in x}
        if len(axes)>1:fail(path+'.data','one shared field time axis',sorted(axes),'Two-layer inlet state samples must be synchronized.')
        valid=len(axes)<=1 and all(('field' not in data[key] or m['fields'][data[key]['field']]['kind']==('vector' if key.endswith('velocity') else 'scalar')) for key in requirements)
        if valid:
            _,normals,_=boundary_geometry(problem,loc)
            vl=values('lower_velocity');vu=values('upper_velocity')
            hl=values('lower_depth');hu=values('upper_depth')
            frames=max(vl.shape[0],vu.shape[0]);count=len(normals)
            hl=np.broadcast_to(hl,(frames,count,1));hu=np.broadcast_to(hu,(frames,count,1))
            for frame in range(frames):
                for face,n in enumerate(normals):
                    try:
                        speeds=layer_characteristic_speeds(float(hl[frame,face,0]),float(hu[frame,face,0]),
                            float(np.dot(vl[frame,face],n)),float(np.dot(vu[frame,face],n)),p['gravity'],p['upper_density']/p['lower_density'])
                        if np.any(speeds>=0):raise ValueError('Every normal characteristic must enter the domain')
                    except ValueError as exc:fail(path+'.data','strictly supercritical hyperbolic inflow',data,str(exc))

def layer_characteristic_speeds(lower_depth, upper_depth, lower_normal_velocity, upper_normal_velocity, gravity, density_ratio):
    """Four normal gravity-wave speeds, plus two tangential advection speeds."""
    hl,hu,vl,vu,g,r=lower_depth,upper_depth,lower_normal_velocity,upper_normal_velocity,gravity,density_ratio
    a=np.array([[vl,0,hl,0],[0,vu,0,hu],[g,r*g,vl,0],[g,g,0,vu]],dtype=float)
    wave=np.linalg.eigvals(a)
    if np.any(np.abs(wave.imag)>1e-10):raise ValueError('Two-layer state is not hyperbolic')
    return np.r_[wave.real,vl,vu]


def check(problem, errors):
    if problem.manifest.get('physics', {}).get('model') in MODELS:
        check_declaration(problem, errors, MODELS, _check_parameters, _check_boundary)

check_fluid_reduced = check
