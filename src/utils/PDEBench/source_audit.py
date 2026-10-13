"""Source-aligned reference audit, with explicit numerical accuracy limits."""
import numpy as np
import hashlib,json
from pathlib import Path
from scipy.ndimage import map_coordinates
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
from caeoj.sdk import write_result, load_result
from .storage import PreparationError,atomic_json,digest


def transport_residual(velocity,tracer,times,length,substeps):
    """Independent bilinear tracer transport with measured positive velocities."""
    grid=np.indices(tracer[0].shape,dtype=float);state=tracer[0].copy()
    dt=(times[1]-times[0])/substeps;n=state.shape[0]
    for i in range(substeps):
        v=velocity[0]+((i+1)/substeps)*(velocity[1]-velocity[0])
        state=map_coordinates(state,grid-dt*n/length*v.transpose(2,0,1),
                              order=1,mode='nearest',prefilter=False)
    margin=max(1,n//8);crop=(slice(margin,-margin),slice(margin,-margin))
    residual=state[crop]-tracer[1][crop]
    change=tracer[1][crop]-tracer[0][crop]
    return float(np.linalg.norm(residual)/max(np.linalg.norm(change),1e-30))


def audit_ns_domain(model,source,cache,budget,local,timeout):
    """Each shard must distinguish the published unit Box from the current Box."""
    from .sources import open_source,Reader
    key=hashlib.sha256(json.dumps({'source':source,'audit_sha256':digest(Path(__file__))},sort_keys=True).encode()).hexdigest()
    path=cache/'ns-domain'/f"{source['id']}.json"
    if path.exists():
        previous=json.loads(path.read_text())
        if previous.get('identity')==key:return previous
    with open_source(source,cache,budget,local,timeout) as handle:
        reader=Reader(handle,model);coords,times,config=reader.metadata(0,frames=np.array([0,1,2]))
        if len(times)<3:raise PreparationError('Insufficient early NS frames for domain audit')
        frame_int=int(config.get('frame_int',0))
        if not 1<=frame_int<=1000:raise PreparationError('Unsupported NS frame interval')
        budget.check(len(coords[0])*len(coords[1])*8*16)
        values=reader.values(0,np.array([1,2]))
        unit=transport_residual(values['velocity'],values['tracer'][...,0],times[1:3],1.,frame_int)
        large=transport_residual(values['velocity'],values['tracer'][...,0],times[1:3],float(len(coords[0])),frame_int)
        if not unit<.05 or not large>.5:
            raise PreparationError(f'NS domain audit inconclusive: unit Box residual={unit}, grid-size Box residual={large}')
        witness={'identity':key,'source_id':source['id'],'sample_index':0,'frames':[1,2],
                 'unit_box_relative_transport_residual':unit,'grid_size_box_relative_transport_residual':large,
                 'method':'Repeated bilinear transport using linear temporal interpolation between the two released positive velocity frames; boundary margin excluded',
                 'scope':'Distinguishes coordinate scale, not a proof of full NS continuum accuracy or archival source commit'}
        atomic_json(path,witness);return witness


def fhn_initial(coords,values,config):
    sim=config.get('sim',{})
    nx=int(sim['xdim']);ny=int(sim['ydim']);seed=int(sim['seed'])
    if nx<2 or ny<2:raise PreparationError('Invalid original FHN initial grid')
    axes=[]
    for c,n,lo,hi in zip(coords,(nx,ny),(-1.,-1.),(1.,1.)):
        index=np.rint((c-lo)*n/(hi-lo)-.5).astype(int)
        if np.any(index<0) or np.any(index>=n):raise PreparationError('FHN sample outside original grid')
        centers=lo+(index+.5)*(hi-lo)/n
        if not np.allclose(c,centers,rtol=0,atol=2e-7):raise PreparationError('FHN sample is not an original cell center')
        axes.append(index)
    # The released data uses legacy MT19937, unlike current default_rng source.
    # Never guess: all released t=0 samples must match the reconstruction.
    rng=np.random.RandomState(seed)
    fields={}
    for name in ('activator','inhibitor'):
        original=rng.standard_normal(nx*ny).reshape(ny,nx).T.astype(np.float32).astype(np.float64)
        sampled=original[np.ix_(*axes)]
        if not np.array_equal(sampled,values[name][0,...,0]):
            raise PreparationError('FHN legacy initial reconstruction does not reproduce every released t=0 value')
        fields[name]=original[None,...,None]
    return (nx,ny),axes,fields


def darcy_system(coefficient):
    """Arithmetic face coefficients and zero exterior-cell values in the source."""
    shape=coefficient.shape;nx,ny=shape;index=np.arange(nx*ny).reshape(shape)
    diagonal=np.zeros(shape);rows=[];cols=[];entries=[]
    for axis,n in enumerate(shape):
        low=[slice(None),slice(None)];high=low.copy()
        low[axis]=slice(0,-1);high[axis]=slice(1,None)
        low=tuple(low);high=tuple(high)
        face=.5*(coefficient[low]+coefficient[high])*n*n
        diagonal[low]+=face;diagonal[high]+=face
        for a,b in ((low,high),(high,low)):
            rows.extend(index[a].ravel());cols.extend(index[b].ravel());entries.extend(-face.ravel())
        for upper in (False,True):
            edge=[slice(None),slice(None)];edge[axis]=-1 if upper else 0;edge=tuple(edge)
            diagonal[edge]+=coefficient[edge]*n*n
    rows.extend(index.ravel());cols.extend(index.ravel());entries.extend(diagonal.ravel())
    return coo_matrix((entries,(rows,cols)),shape=(nx*ny,nx*ny)).tocsr()


def audit_reference(model,problem,values,coords,config,path):
    shape=tuple(len(c) for c in coords);times=problem.arrays['times']
    arrays={name:values[name].reshape(len(times),-1,c) for name,_,_,c in model.fields}
    metrics={'finite_fields':True,'source_frame_count':len(times),'source_dtype':'published precision converted to float64 without adding accuracy'}
    caveats=['Source discretization and continuum error are not certified; grading tolerance and resources remain uncalibrated.']
    kind='source_aligned_official_numerical_reference'
    if any(not np.isfinite(a).all() for a in arrays.values()):raise PreparationError('Nonfinite source reference')
    if model.model in ('advection_1d','burgers_1d','reaction_diffusion_1d'):
        initial=problem.arrays['initial_state'].reshape(-1)
        parameters=problem.manifest['physics']['parameters']
        if model.model=='advection_1d':
            from .conversion import advection_average
            comparison=advection_average(initial,times,parameters['velocity']['value'])
            comparison_method='exact periodic piecewise-constant cell integrals'
        elif model.model=='burgers_1d':
            from .references import burgers_average
            comparison=burgers_average(initial,times,parameters['diffusion_coefficient']['value'])
            comparison_method='independent Cole–Hopf Gaussian cell integrals'
        else:
            from .references import write_logistic_reference
            refinement=write_logistic_reference(problem,path)
            comparison=load_result(problem,path)['state']
            comparison_method=refinement['method']
            metrics['recomputed_reference']=refinement
            kind='recomputed_source_pde_reference'
            if arrays['state'].min()<-1e-6 or arrays['state'].max()>1+1e-6:
                raise PreparationError('Published logistic state violates [0,1] beyond float32 precision')
        delta=arrays['state']-comparison
        metrics['independent_comparison']={'method':comparison_method,
                  'max_absolute_difference':float(np.max(abs(delta))),
                  'rms_difference':float(np.sqrt(np.mean(delta**2))),
                  'scope':'Numerical source-versus-same-model witness, not a grading tolerance or a universal accuracy assertion'}
        if model.model=='reaction_diffusion_1d':
            averages=arrays['state'][...,0].mean(axis=1)
            metrics['official_last_interval_mean_change']=float(averages[-1]-averages[-2])
            metrics['nominal_last_reaction_mean']=float(parameters['reaction_rate']['value']*np.mean(arrays['state'][-1]*(1-arrays['state'][-1])))
            arrays['state']=comparison
            caveats.append('Official logistic trajectories can plateau away from equilibrium; retain them as rejected numerical candidates, use the independently recomputed same-PDE reference with measured refinement instead.')
    elif model.model=='reaction_diffusion_2d':
        original,axes,fields=fhn_initial(coords,values,config)
        metrics['complete_initial_grid']=list(original)
        metrics['initial_reconstruction']='legacy MT19937; all published initial samples match bitwise at float32 precision'
        sim=config['sim']
        for key,expected in [('Du',.001),('Dv',.005),('k',.005)]:
            if sim.get(key)!=expected:raise PreparationError('Unexpected FHN physical configuration')
        caveats.append('Original float64 random initial values are rounded to released float32 precision; the archival generator commit is not known.')
    elif model.model=='darcy_flow_2d':
        coefficient=values['diffusivity'].reshape(shape)
        strength=problem.manifest['physics']['parameters']['source_strength']['value']
        operator=darcy_system(coefficient);rhs=np.full(coefficient.size,strength)
        official=arrays['state'].reshape(-1)
        source_residual=operator@official-rhs
        # Some published small-source snapshots are not steady. Continue to
        # the exact equilibrium of the published spatial operator independently.
        corrected=spsolve(operator,rhs)
        residual=operator@corrected-rhs
        relative=float(np.linalg.norm(residual)/np.linalg.norm(rhs))
        if not np.isfinite(corrected).all() or relative>1e-9:
            raise PreparationError('Darcy source-operator equilibrium did not pass residual check')
        arrays['state']=corrected.reshape(1,-1,1)
        metrics.update({'official_relative_residual_l2':float(np.linalg.norm(source_residual)/np.linalg.norm(rhs)),
                        'corrected_relative_residual_l2':relative,
                        'correction_max_absolute':float(np.max(abs(corrected-official))),
                        'correction_relative_l2':float(np.linalg.norm(corrected-official)/max(np.linalg.norm(corrected),1e-30))})
        kind='source_operator_equilibrium_reference'
        caveats.append('Steady-state algebraic residual checks the fixed source grid, not mesh convergence of the continuous elliptic solution.')
    elif model.model.startswith('compressible_'):
        rho=arrays['density'][...,0];p=arrays['pressure'][...,0];v=arrays['velocity']
        if rho.min()<=0 or p.min()<=0:raise PreparationError('Nonpositive compressible source state')
        metrics.update({'minimum_density':float(rho.min()),'minimum_pressure':float(p.min()),
                        'saved_pressure_floor_values':int(np.count_nonzero(np.isclose(p,1e-4,rtol=1e-6,atol=0)))})
        energy=p/(5/3-1)+.5*rho*np.sum(v*v,axis=-1)
        metrics['source_viscous_flux']='rho*(eta+(zeta+eta/3)*delta_ij)*partial_j(v_i); energy flux sum_i(v_i*Q_ij)'
        periodic=any(c['operator']=='periodic' for c in problem.manifest['conditions'])
        if periodic:
            mass=rho.mean(axis=1);total_energy=energy.mean(axis=1)
            drift=float(np.max(abs(mass-mass[0]))/mass[0])
            metrics.update({'relative_mass_drift':drift,
                            'relative_energy_drift':float(np.max(abs(total_energy-total_energy[0]))/abs(total_energy[0]))})
            if drift>5e-3:raise PreparationError('Periodic compressible source failed mass-conservation plausibility audit')
        caveats.append('Published primitives are derived from conservative cell states; pressure-floor and split-update errors remain reference uncertainty.')
    elif model.points:
        if config.get('NU')!=.01 or list(config.get('grid_size',[]))!=list(shape):
            raise PreparationError('Unexpected incompressible source configuration')
        metrics.update({'initial_saved_frame':'unprojected raw velocity, preserved at t=0',
                        'source_box':[list(b) for b in model.bounds],
                        'box_evidence':'released domain_size=1, independently discriminated by short-time tracer transport against grid-size Box',
                        'projection_and_transport':'projection at each positive simulation step; advected tracer times static force'})
        caveats.append('Archived generator-version provenance and centered/staggered reconstruction errors remain uncalibrated; no pressure ground truth is provided.')
    elif model.model=='diffusion_sorption_1d':
        sim=config.get('sim',{})
        for key,expected in [('D',.0005),('por',.29),('rho_s',2880),('k_f',.00035),('n_f',.874),('sol',1.)]:
            if sim.get(key)!=expected:raise PreparationError('Unexpected sorption physical configuration')
        metrics['source_boundary']='left exterior value=1; right exterior value=-ell*(last_mean-previous_mean)/h'
        if arrays['concentration'].min()<-1e-6:raise PreparationError('Negative sorption concentration beyond source precision')
    elif model.model=='shallow_water_2d':
        if arrays['depth'].min()<=0:raise PreparationError('Nonpositive shallow-water source depth')
        metrics['minimum_depth']=float(arrays['depth'].min())
    from .conversion import check_reference_initial
    check_reference_initial(model,problem,arrays)
    write_result(path,problem,arrays);load_result(problem,path)
    return {'kind':kind,'audit_scope':'source identity, physical configuration, axes, complete initial data, actual times, structural and model-specific consistency checks',
            'checks':metrics,'limitations':caveats,'continuum_error_certified':False,
            'grading_ready':False}
