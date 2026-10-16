"""Solid-mechanics declaration checks; no solver or reference construction.

The public contract remains each task's instruction/DATA plus CONTRACT.
"""
from functools import lru_cache
from importlib.resources import files
from itertools import combinations
import json
import numpy as np


@lru_cache(maxsize=1)
def models():
    return json.loads(files(__package__).joinpath('models.json').read_text(encoding='utf-8'))


def elastic_constants(young_modulus, poisson_ratio):
    """Return 3D Lame constants (lambda, mu), in the modulus's input units."""
    if not (np.isfinite(young_modulus) and np.isfinite(poisson_ratio) and
            young_modulus > 0 and -1 < poisson_ratio < .5):
        raise ValueError('Require E > 0 and -1 < nu < 0.5')
    return (young_modulus*poisson_ratio/((1+poisson_ratio)*(1-2*poisson_ratio)),
            young_modulus/(2*(1+poisson_ratio)))


def check(problem, errors):
    """Called only after core structure, references and array validation pass."""
    from caeoj.validation import issue
    m, arrays = problem.manifest, problem.arrays
    slug = m.get('physics', {}).get('model', '').removeprefix('solid-').removesuffix('-v1')
    cfg = models().get(slug)
    def fail(path, expected, actual, message='Solid declaration does not match the public contract.'):
        # Keep diagnostics finite and JSON-serializable; do not include large arrays.
        if isinstance(actual, np.ndarray): actual = actual.tolist() if actual.size < 20 else list(actual.shape)
        errors.append(issue('E_SOLID', path, expected, actual, message))
    if cfg is None:
        fail('$.physics.model', 'supported solid model/version', m.get('physics')); return
    d, top = cfg['dimension'], cfg['topology']
    if m['spatial_dimension'] != d: fail('$.spatial_dimension', d, m['spatial_dimension'])
    if 'task' in m and m['task'] != slug: fail('$.task', slug, m['task'])
    if any(k in m for k in ('profile', 'analysis', 'materials', 'contract_version')):
        fail('$', 'physics-only solid declaration', 'mixed profile')
    params = m['physics'].get('parameters', {})
    if set(params) != set(cfg['parameters']):
        fail('$.physics.parameters', sorted(cfg['parameters']), sorted(params)); return
    p = {}
    for key, spec in cfg['parameters'].items():
        x = params[key]
        value = x.get('value')
        if set(x) != {'value', 'unit'} or x.get('unit') != spec['unit'] or type(value) not in (int, float):
            fail('$.physics.parameters.'+key, spec['unit']+' finite scalar', x); continue
        low, high = spec['lower'], spec['upper']
        if ((low is not None and (value < low if spec['closed'] else value <= low)) or
                (high is not None and value > high)):
            fail('$.physics.parameters.'+key, spec, x)
        p[key] = value
    if errors: return
    if 'mode_count' in p and type(p['mode_count']) is not int:
        fail('$.physics.parameters.mode_count.value', 'integer', p['mode_count'])
    history = cfg['mode'] == 'history'
    if history and p['end_time'] <= p['start_time']:
        fail('$.physics.parameters.end_time', '> start_time', p['end_time']); return
    if slug == 'gradient-damage' and p['residual_stiffness'] >= 1:
        fail('$.physics.parameters.residual_stiffness', '< 1', p['residual_stiffness'])
    if 'normal_x' in p:
        normal = np.array([p.get('normal_'+axis, 0) for axis in 'xyz'][:d])
        if abs(np.linalg.norm(normal)-1) > 1e-10: fail('$.physics.parameters', 'unit plane/interface normal', normal)
    if slug == 'cohesive-interface' and 2*p['fracture_energy']/p['peak_traction'] <= p['peak_traction']/p['interface_stiffness']:
        fail('$.physics.parameters', 'delta_f > delta_0', p)
    locs = m['locations']
    def ids(loc): return set(map(int, arrays[loc['ids']]))
    mesh = None; exterior = {}; boundary_nodes = set(); cells = set(); nodes = set()
    if top:
        if set(m['meshes']) != {'main'}:
            fail('$.meshes', 'one main mesh', list(m['meshes'])); return
        mesh = problem.meshes['main']; cells = mesh['elements'].get(top, set())
        nodes = {node for tag in cells for node in mesh['connectivity'][tag][1]}
        for name, entity, tags in [('domain', 'node', nodes), ('cells', 'element', cells)]:
            loc = locs.get(name, {})
            if (loc.get('kind') != 'mesh' or loc.get('mesh') != 'main' or loc.get('entity') != entity or
                    ids(loc) != tags or (entity == 'element' and loc.get('dimension') != top)):
                fail('$.locations.'+name, 'complete '+entity+' support on main', loc)
        if errors: return
        if mesh['dimension'] != top or not cells or nodes != mesh['nodes']:
            fail('$.meshes.main', 'nonempty declared topology and no unused nodes', mesh['dimension'])
        counts = {}; owner = {}
        for tag in cells:
            typ, conn = mesh['connectivity'][tag]
            if typ != {1:1, 2:2, 3:4}[top]:
                fail('$.meshes.main', 'first-order simplices', typ); continue
            x = np.array([mesh['node_coordinates'][n][:d] for n in conn])
            if np.linalg.matrix_rank(x[1:]-x[0]) != top:
                fail('$.meshes.main', 'nondegenerate elements', tag)
            for face in combinations(conn, top):
                face = tuple(sorted(face)); counts[face] = counts.get(face, 0)+1; owner[face] = tag
        if slug!='elastic-truss' and any(v > 2 for v in counts.values()): fail('$.meshes.main', 'manifold domain', 'nonmanifold facets')
        faces = {face for face, count in counts.items() if count == 1}
        if slug=='elastic-truss': faces={(n,) for n in nodes}
        for tag in mesh['elements'].get(top-1, set()):
            typ, conn = mesh['connectivity'][tag]; face = tuple(sorted(conn))
            if typ != {1:15, 2:1, 3:2}[top]:
                fail('$.meshes.main', 'linear boundary simplex', typ)
            if face in faces:
                if face in exterior.values(): fail('$.meshes.main', 'one exported element per boundary facet', tag)
                exterior[tag] = face
        if set(exterior.values()) != faces:
            fail('$.meshes.main', 'all exterior facets exported', len(exterior))
        boundary_nodes = set(n for face in faces for n in face)
        if len(cells) > cfg['limits']['cells'] or len(nodes) > cfg['limits']['nodes']:
            fail('$.meshes.main', cfg['limits'], [len(cells),len(nodes)])
        if slug == 'elastic-beam':
            degree = {n:0 for n in nodes}
            for tag in cells:
                for n in mesh['connectivity'][tag][1]: degree[n] += 1
            if sorted(degree.values()).count(1) != 2 or any(x not in (1,2) for x in degree.values()):
                fail('$.meshes.main','single unbranched beam','invalid node degrees')
    else:
        site = locs.get('sites', {})
        if m['meshes'] or m['geometries'] or site.get('kind') != 'points':
            fail('$.locations.sites', 'independent sites without meshes/geometries', site); return
        if len(ids(site)) > cfg['limits']['nodes']: fail('$.locations.sites','bounded number of sites',len(ids(site)))
    if errors: return

    def support(name, where):
        loc = locs[name]
        if where in ('sum','mean'):
            source = locs.get(loc.get('source'), {})
            return (loc.get('kind') == 'aggregate' and loc.get('operation') == where and
                    source.get('kind') == 'mesh' and source.get('mesh') == 'main' and
                    source.get('entity') == 'element' and source.get('dimension') == top and ids(source) == cells)
        if where == 'sites': return name == 'sites'
        if loc.get('kind') != 'mesh' or loc.get('mesh') != 'main': return False
        tags = ids(loc)
        if where == 'nodes': return loc['entity'] == 'node' and tags <= nodes
        if where == 'ends': return loc['entity'] == 'node' and len(tags)==1 and tags <= boundary_nodes
        if where == 'cells': return loc['entity']=='element' and loc['dimension']==top and tags <= cells
        if where in ('facets','contact','interface'):
            return loc['entity']=='element' and loc['dimension']==top-1 and tags <= set(exterior)
        return False
    # Reject extra locations whose geometry semantics are not covered in DATA.
    for name, loc in locs.items():
        allowed = ('nodes','cells','facets','sum','mean') if top else ('sites',)
        if not any(support(name,w) for w in allowed): fail('$.locations.'+name, 'supported location', loc)
    for name,key in m['time_axes'].items():
        t = arrays[key]
        if len(t)>cfg['limits']['frames']: fail('$.time_axes.'+name,'frame limit',len(t))
        if not history and not np.array_equal(t,[0.]): fail('$.time_axes.'+name,'[0.0]',t)
    output_axis = 'response' if history else 'steady'
    if output_axis not in m['time_axes']:
        fail('$.time_axes', 'output axis '+output_axis, list(m['time_axes'])); return
    if history:
        t = arrays[m['time_axes'][output_axis]]
        if t[0] < p['start_time'] or t[-1] > p['end_time']:
            fail('$.time_axes.'+output_axis,'within start/end interval',t)

    refs=set(); seen={}; used_boundary={}; contact=set(); interface=set(); interface_plus=set(); fixed_nodes=set(); facet_loads=set(); cyclic_axes=set()
    def typed_value(value, spec, locname, role, path):
        if 'value' in value:
            if not top and role == 'source':
                fail(path, 'cycle-block field reference, including constant histories', value); return None
            if spec['kind'] != 'scalar' or value['unit'] != spec['unit']:
                fail(path, 'scalar constant in '+spec['unit'], value); return None
            return np.asarray([value['value']])
        if set(value) != {'field'}:
            fail(path,'typed constant or field',value); return None
        name = value['field']; refs.add(name); field=m['fields'][name]
        expected=dict(unit=spec['unit'],kind=spec['kind'],quantity=spec['quantity'],dtype='float64',location=locname)
        for key,x in expected.items():
            if field.get(key) != x: fail('$.fields.'+name+'.'+key,x,field.get(key))
        loc=locs[locname]; vk='point' if loc.get('kind')=='points' or loc.get('entity')=='node' else 'average'
        if field['value_kind']!=vk: fail('$.fields.'+name+'.value_kind',vk,field['value_kind'])
        space='uniform' if not top else 'piecewise_linear' if loc.get('entity')=='node' else 'piecewise_constant'
        t=arrays[m['time_axes'][field['time_axis']]]; values=arrays[field['array']]
        initial=role=='initial'
        time='constant'
        if history and not initial and len(t)>1: time='previous' if not top else 'linear'
        sampling=dict(space=space,time=time,extrapolation='forbid')
        if field.get('sampling')!=sampling:fail('$.fields.'+name+'.sampling',sampling,field.get('sampling'))
        if history:
            if initial:
                if len(t)!=1 or t[0]!=p['start_time']:fail('$.fields.'+name+'.time_axis','single start_time',t)
            elif len(t)>1:
                if t[0]!=p['start_time'] or t[-1]!=p['end_time']:fail('$.fields.'+name+'.time_axis','full interval endpoints',t)
                if not top:
                    cyclic_axes.add(field['time_axis'])
                    if not np.array_equal(values[-1],values[-2]):fail('$.fields.'+name,'last frame repeats preceding block',name)
            elif not top:fail('$.fields.'+name+'.time_axis','at least two block frames',t)
            elif t[0]!=p['start_time']:fail('$.fields.'+name+'.time_axis','single constant stored at start_time',t)
        if slug=='elastic-transient' and spec['quantity']=='displacement' and not initial and len(t)>2:
            slopes=np.diff(values,axis=0)/np.diff(t).reshape((-1,)+(1,)*(values.ndim-1))
            if not np.allclose(slopes,slopes[0],rtol=1e-12,atol=1e-14):fail('$.fields.'+name,'globally affine displacement history',name)
        return values

    zero_start=slug in ('hyperelastic-solid','frictionless-contact','frictional-contact','j2-plasticity','linear-viscoelastic','power-law-creep','gradient-damage','cohesive-interface')
    values_by_op={}
    for i,c in enumerate(m['conditions']):
        path=f'$.conditions[{i}]';op=c['operator'];rule=cfg['rules'].get(op)
        if rule is None: fail(path+'.operator',list(cfg['rules']),op);continue
        role,var,where,data,_=rule;locname=c['location'];loc=locs[locname];tags=ids(loc)
        if c['role']!=role or c['variable']!=var:fail(path,'correct role and variable',[c['role'],c['variable']])
        if not support(locname,where):
            fail(path+'.location',where,locname); continue
        if where=='cells' and tags!=cells:fail(path+'.location','all cells',locname)
        if role=='initial' and locname!=('domain' if top else 'sites'):fail(path+'.location','domain or sites',locname)
        if role=='boundary' and where=='nodes' and slug!='elastic-truss' and not tags<=boundary_nodes:
            fail(path+'.location','boundary nodes',locname)
        seen[op]=seen.get(op,0)+1
        if (where in ('cells','sites') or role=='initial') and seen[op]>1:fail(path,'one record for operator',op)
        if role=='boundary':
            previous=used_boundary.setdefault(op,set())
            if previous & tags:fail(path+'.location','nonoverlapping records',locname)
            previous.update(tags)
        if set(c['data'])!=set(data):fail(path+'.data',list(data),list(c['data']));continue
        opvalues={}
        for key,spec in data.items():
            value=c['data'][key]
            if 'option' in spec:
                if value!={'option':spec['option']}:fail(path+'.data.'+key,spec,value)
            elif 'location' in spec:
                partner=locs.get(value.get('location'),{})
                if set(value)!={'location'} or not partner or not support(value['location'],'facets'):
                    fail(path+'.data.'+key,'partner facets',value);continue
                partner_tags=ids(partner)
                if tags & (interface | interface_plus) or partner_tags & (interface | interface_plus):
                    fail(path+'.data.'+key, 'each interface facet paired once', value)
                interface.update(tags); interface_plus.update(partner_tags)
                # Match facets by their complete vertex coordinates, not tag order.
                def signatures(tagset):
                    return {tuple(sorted(tuple(mesh['node_coordinates'][n]) for n in exterior[tag])) for tag in tagset}
                if signatures(tags)!=signatures(partner_tags) or tags & partner_tags:
                    fail(path+'.data.'+key,'geometrically coincident distinct interface facets',value)
                minus_nodes={n for tag in tags for n in exterior[tag]}; plus_nodes={n for tag in partner_tags for n in exterior[tag]}
                if minus_nodes & plus_nodes:fail(path+'.data.'+key,'distinct interface node tags',value)
                # The normal is geometric, independent of exported segment order.
                for side, tagset, sign in [('minus', tags, 1), ('plus', partner_tags, -1)]:
                    for tag in tagset:
                        face = exterior[tag]
                        x = np.array([mesh['node_coordinates'][n][:d] for n in face])
                        conn = mesh['connectivity'][owner[face]][1]
                        center = np.mean([mesh['node_coordinates'][n][:d] for n in conn], axis=0)
                        tangent = x[1] - x[0]
                        if (abs(tangent @ normal) > 1e-10*np.linalg.norm(tangent) or
                                sign*((x.mean(axis=0)-center) @ normal) <= 0):
                            fail(path+'.data.'+key, 'normal outward from minus and inward to plus',
                                 {'side': side, 'facet': tag})
            else:
                result=typed_value(value,spec,locname,role,path+'.data.'+key)
                if result is None:continue
                opvalues[key]=result
                if spec['quantity'] in ('area','rigidity','crack_length') and np.any(result<=0):fail(path+'.data.'+key,'positive values',value)
                if spec['quantity'] in ('stress_amplitude','cycle_rate','stress_range') and np.any(result<0):fail(path+'.data.'+key,'nonnegative values',value)
                if spec['quantity']=='mean_stress' and np.any(result>=p['ultimate_strength']):fail(path+'.data.'+key,'mean < ultimate_strength',value)
                if op=='initial_length' and np.any(result>=p['width']):fail(path+'.data.'+key,'length < width',value)
                if op in ('plate_clamp','fixed') or (slug=='elastic-buckling' and op=='displacement'):
                    if np.any(result!=0):fail(path+'.data.'+key,'homogeneous zero value',value)
                if zero_start and spec['quantity'].split('_')[0] in ('displacement','traction','body') and np.any(result[0]!=0):
                    fail(path+'.data.'+key,'zero load/displacement at start',value)
        values_by_op.setdefault(op,[]).append(opvalues)
        if op in ('displacement','displacement_real','fixed','clamp'):fixed_nodes.update(tags)
        if top>=2 and op in ('displacement','displacement_real','displacement_imag','fixed'):
            covered={tag for tag,face in exterior.items() if set(face)<=tags}
            if set(n for tag in covered for n in exterior[tag])!=tags:
                fail(path+'.location','vertices of a union of complete exterior facets',locname)
        if op.startswith('traction'):facet_loads.update(tags)
        if op=='rigid_plane':contact.update(tags)
    if refs != set(m['fields']):fail('$.fields','exactly condition-referenced input fields',sorted(set(m['fields'])-refs))
    for op in cfg['required']:
        if op not in seen: fail('$.conditions','required '+op,'missing')
    if top and not fixed_nodes and slug not in ('elastic-plate',):
        fail('$.conditions','support displacement/fixed/clamp record','missing')
    if slug=='elastic-beam' and seen.get('clamp')!=1:fail('$.conditions','one clamped endpoint',seen.get('clamp',0))
    if slug=='elastic-plate' and used_boundary.get('plate_clamp',set())!=set(exterior):fail('$.conditions','all plate edges clamped','incomplete')
    if not top and len(cyclic_axes)!=1:fail('$.fields','one shared cycle block axis',sorted(cyclic_axes))
    if slug=='elastic-harmonic':
        for op in ('displacement','traction'):
            if used_boundary.get(op+'_real',set())!=used_boundary.get(op+'_imag',set()):fail('$.conditions','matched real/imag '+op+' coverage','mismatch')
        # real and imaginary displacements are the fixed boundary support.
        if used_boundary.get('displacement_real'): fixed_nodes.update(used_boundary['displacement_real'])
    if slug=='elastic-transient' and not errors:
        initial={c['variable']:c for c in m['conditions'] if c['role']=='initial'}
        domain_order={tag:i for i,tag in enumerate(arrays[locs['domain']['ids']])}
        for c in m['conditions']:
            if c['operator']!='displacement':continue
            field=m['fields'][c['data']['value']['field']]
            boundary_values=arrays[field['array']]
            t=arrays[m['time_axes'][field['time_axis']]]
            speed=(boundary_values[1]-boundary_values[0])/(t[1]-t[0]) if len(t)>1 else np.zeros_like(boundary_values[0])
            rows=[domain_order[tag] for tag in arrays[locs[c['location']]['ids']]]
            for variable,expected in [('displacement',boundary_values[0]),('velocity',speed)]:
                initial_field=m['fields'][initial[variable]['data']['value']['field']]
                values=arrays[initial_field['array']][0,rows]
                if not np.allclose(values,expected,rtol=1e-12,atol=1e-14):
                    fail('$.conditions','compatible initial and prescribed boundary '+variable,'incompatible')
    if contact:
        cnodes={n for tag in contact for n in exterior[tag]}
        if cnodes & fixed_nodes or contact & facet_loads:fail('$.conditions','contact disjoint from displacement and traction','overlap')
        x=np.array([mesh['node_coordinates'][n] for n in cnodes])
        if np.any(x @ normal > p['plane_offset']+1e-12):fail('$.conditions','initial nonpenetration','penetrating nodes')
    if top>=2 and facet_loads:
        for tag in facet_loads:
            if set(exterior[tag])<=fixed_nodes:fail('$.conditions','no whole-facet traction/Dirichlet overlap',tag)
    all_interface = interface | interface_plus
    if all_interface & facet_loads:fail('$.conditions','no external interface traction on either side','overlap')
    if any(set(exterior[tag]) <= fixed_nodes for tag in all_interface):
        fail('$.conditions','no whole-facet interface/Dirichlet overlap on either side','overlap')
    present=set(); total_input=sum(arrays[f['array']].size for f in m['fields'].values());total_output=0
    for name,spec in m['outputs'].items():
        q=spec['quantity'];entry=cfg['output_specs'].get(q);path='$.outputs.'+name
        if entry is None:fail(path+'.quantity',cfg['outputs'],q);continue
        present.add(q);where=entry['where'];kind=entry['kind']
        if not support(spec['location'],where):fail(path+'.location',where,spec['location'])
        if where in ('contact','interface'):
            selected_tags=contact if where=='contact' else interface
            if not ids(locs[spec['location']])<=selected_tags:fail(path+'.location',where+' candidate subset',spec['location'])
        if kind=='spectrum':
            kind='components';k=p['mode_count']
            if type(k) is int and (spec['component_shape']!=[k] or spec['components']!=['f'+str(i+1) for i in range(k)]):
                fail(path,'spectrum f1..fk',spec['components'])
        for key,x in dict(unit=entry['unit'],kind=kind,dtype='float64',time_axis=output_axis).items():
            if spec.get(key)!=x:fail(path+'.'+key,x,spec.get(key))
        vk='integral' if where=='sum' else 'point' if where in ('nodes','sites') else 'average'
        if spec['value_kind']!=vk:fail(path+'.value_kind',vk,spec['value_kind'])
        total_output+=len(arrays[m['time_axes'][spec['time_axis']]])*len(arrays[locs[spec['location']]['ids']])*int(np.prod(spec['component_shape']))
    if present!=set(cfg['outputs']):fail('$.outputs','all required quantities',sorted(present))
    if max(total_input,total_output)>cfg['limits']['components']:fail('$.fields/outputs','component limit',max(total_input,total_output))
