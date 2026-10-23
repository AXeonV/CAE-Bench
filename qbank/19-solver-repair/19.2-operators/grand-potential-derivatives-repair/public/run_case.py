"""Declare independent actual MOOSE material/FE programs and convert native outputs."""
import argparse,os,subprocess,tempfile
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem,write_result
from native_result import residual_and_jacobian,csv_rows,dof_groups

LOGICAL=['phi','eta0','eta1','eta2','eta3']
PROPERTIES={'void_minimum':'hv_c_min','solid_minimum':'hs_c_min','void_response':'hv_over_kVa','solid_response':'hs_over_kVa','void_number_density':'rhov','solid_number_density':'rhos','void_grand_potential':'omegav','solid_grand_potential':'omegas'}
MOOSE='/opt/moose-source/modules/phase_field/phase_field-opt'
PETSC_OPTIONS=['-snes_test_jacobian','-snes_test_jacobian_view','::ascii_matlab','-snes_monitor_residual','::ascii_matlab','-snes_force_iteration','-snes_type','ksponly','-ksp_type','preonly','-pc_type','none','-snes_convergence_test','skip']
def names_for(variant):
    values=['phi','eta0','eta1','eta2','eta3','w','c','T'] if variant==0 else ['pore_state','grain_a','grain_b','grain_c','grain_d','mu_state','fraction_state','thermal_state']
    return dict(zip([*LOGICAL,'potential','concentration','temperature'],values))
def number(value):return format(float(value),'.17g')
def block(name,parameters):return ' ['+name+']\n'+''.join('  '+k+' = '+str(v)+'\n' for k,v in parameters.items())+' []\n'
def quoted(items):return "'"+' '.join(items)+"'"
def prepare(problem,directory):
    p={k:v['value'] for k,v in problem.manifest['physics']['parameters'].items()};a=problem.arrays;n=len(a['program_ids']);count=int(p['grain_count']);length=p['probe_length'];names=names_for(p['variable_name_set']);active=[names['phi'],*[names['eta'+str(i)] for i in range(count)]]
    s='[Mesh]\n'
    for i in range(n):s+=block('segment'+str(i),{'type':'GeneratedMeshGenerator','dim':1,'nx':1,'xmin':number(3*i*length),'xmax':number((3*i+1)*length),'subdomain_ids':i+1})
    s+=block('collection',{'type':'MeshCollectionGenerator','inputs':quoted(['segment'+str(i) for i in range(n)])})+'[]\n[Functions]\n'
    states={'phi':a['phi'][0,:,0],'potential':a['potential'][0,:,0],'concentration':a['concentration'][0,:,0],'temperature':a['temperature'][0,:,0]}
    states.update({'eta'+str(j):a['eta'][0,:,j] for j in range(4)})
    for key,values in states.items():
        expression=number(values[-1])
        for i in reversed(range(n-1)):expression='if(x<'+number((3*i+2)*length)+','+number(values[i])+','+expression+')'
        s+=block('initial_'+key,{'type':'ParsedFunction','expression':"'"+expression+"'"})
    s+='[]\n[Variables]\n'
    for key in [*LOGICAL,'potential','concentration']:s+=block(names[key],{})
    s+='[]\n[AuxVariables]\n'+block(names['temperature'],{})+'[]\n[ICs]\n'
    for key in states:s+=block('state_'+key,{'type':'FunctionIC','variable':names[key],'function':'initial_'+key})
    s+='[]\n[Materials]\n'+block('constants',{'type':'GenericConstantMaterial','prop_names':"'ks kv'",'prop_values':quoted([number(p['solid_energy_coefficient']),number(p['void_energy_coefficient'])])})
    terms=[number(p['equilibrium_constant'])]
    for i in range(count):
        var=names['eta'+str(i)];terms.append('('+number(p[f'equilibrium_linear_{i}'])+')*'+var)
        for j in range(i,count):terms.append('('+number(p[f'equilibrium_hessian_{i}{j}']*(.5 if i==j else 1))+')*'+var+'*'+names['eta'+str(j)])
    s+=block('equilibrium',{'type':'DerivativeParsedMaterial','property_name':'ceq','coupled_variables':quoted([names['eta'+str(i)] for i in range(count)]),'expression':"'"+'+'.join(terms)+"'",'derivative_order':2,'enable_jit':'false'})
    s+=block('grand_potential',{'type':'GrandPotentialSinteringMaterial','etas':quoted([names['eta'+str(i)] for i in range(count)]),'chemical_potential':names['potential'],'void_op':names['phi'],'Temperature':names['temperature'],'solid_energy_coefficient':'ks','void_energy_coefficient':'kv','equilibrium_vacancy_concentration':'ceq','atomic_volume':number(p['atomic_volume']),'surface_energy':number(p['surface_energy']),'grainboundary_energy':number(p['grainboundary_energy']),'int_width':number(p['interface_width']),'surface_switch_value':number(p['surface_switch_value']),'solid_energy_model':'PARABOLIC','mass_conservation':'true' if p['strict_mass_conservation'] else 'false'})+'[]\n[Kernels]\n'
    for key in [*LOGICAL,'potential']:
        s+=block('anchor_'+key,{'type':'Reaction','variable':names[key]})
        s+=block('anchor_force_'+key,{'type':'BodyForce','variable':names[key],'function':'initial_'+key})
    s+=block('concentration',{'type':'Reaction','variable':names['concentration']})
    for key in ['void_response','solid_response']:s+=block(key,{'type':'MatReaction','variable':names['concentration'],'v':names['potential'],'reaction_rate':PROPERTIES[key],'args':quoted(active)})
    for key in ['void_minimum','solid_minimum']:s+=block(key,{'type':'MatBodyForce','variable':names['concentration'],'material_property':PROPERTIES[key],'coupled_variables':quoted(active)})
    s+='[]\n[Postprocessors]\n';columns=[]
    for i in range(n):
        for field,prop in PROPERTIES.items():
            selectors=[('',[],0)]
            if field in ['void_minimum','solid_minimum','void_response','solid_response']:
                selectors += [('_gradient',[names[v]],j) for j,v in enumerate(LOGICAL)]
                selectors += [('_hessian',[names[v],names[w]],5*j+k) for j,v in enumerate(LOGICAL) for k,w in enumerate(LOGICAL)]
            for suffix,derivatives,component in selectors:
                column=f'p{i}_{field}{suffix}_{component}';output=field+suffix
                columns.append({'column':column,'output':output,'program':i,'component':component})
                s+=block(column,{'type':'RepairDerivativeAverage' if suffix else 'ElementAverageMaterialProperty','mat_prop':prop,'block':i+1,'execute_on':'INITIAL',**({'derivatives':quoted(derivatives)} if suffix else {})})
    s+='[]\n[VectorPostprocessors]\n'+block('dofs',{'type':'RepairDofMap','variables':quoted([names[k] for k in [*LOGICAL,'potential','concentration']]),'execute_on':'INITIAL'})+'[]\n[Preconditioning]\n'+block('full',{'type':'SMP','full':'true'})+'[]\n[Executioner]\n type = Steady\n solve_type = NEWTON\n automatic_scaling = false\n[]\n[Outputs]\n console = false\n file_base = result\n'+block('csv',{'type':'CSV','precision':17,'execute_on':'INITIAL'})+'[]\n'
    (directory/'case.i').write_text(s,encoding='utf-8',newline='\n')
    return columns,names,length
def extract(problem,directory,text,columns,names,length):
    n=len(problem.arrays['program_ids']);values={key:np.empty((1,n,int(np.prod(v['component_shape']))),dtype=float) for key,v in problem.manifest['outputs'].items()}
    rows=csv_rows(directory/'result.csv')
    if len(rows)!=1 or float(rows[0]['time'])!=0:raise ValueError('Expected one initial material observation')
    for col in columns:values[col['output']][0,col['program'],col['component']]=float(rows[0][col['column']])
    r,jac=residual_and_jacobian(text);groups=dof_groups(directory/'result_dofs_0000.csv',n,length,{k:v for k,v in names.items() if k!='temperature'})
    if len(r)!=14*n:raise ValueError('Unexpected native nonlinear system size')
    for i,dofs in enumerate(groups):
        row=dofs['concentration'];values['constraint_residual'][0,i]=r[row]
        values['constraint_state_jacobian'][0,i]=np.stack([jac[np.ix_(row,dofs[v])] for v in LOGICAL]).ravel()
        for key in ['potential','concentration']:values['constraint_'+key+'_jacobian'][0,i]=jac[np.ix_(row,dofs[key])].ravel()
    return values
def run(input_path,output_path):
    problem=load_problem(input_path)
    with tempfile.TemporaryDirectory() as tmp:
        directory=Path(tmp);columns,names,length=prepare(problem,directory)
        command='source /environment && exec '+MOOSE+' -i case.i '+' '.join(PETSC_OPTIONS)
        result=subprocess.run(['/bin/bash','-lc',command],cwd=directory,env=os.environ.copy(),capture_output=True,text=True)
        if result.returncode:raise RuntimeError(f'Actual MOOSE process failed {result.returncode}: {result.stdout[-2000:]} {result.stderr[-2000:]}')
        values=extract(problem,directory,result.stdout,columns,names,length)
    write_result(output_path,problem,values)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--input',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();run(args.input,args.output)
