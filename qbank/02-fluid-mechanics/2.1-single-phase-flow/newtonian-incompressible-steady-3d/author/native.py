"""Native solver configuration and postprocessing for supplement.py.

FlowSolver and simpleFoam perform all physical solves. The small user-function
hooks below only load prescribed boundary/source tables into their native APIs.
"""
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

import numpy as np
from scipy.interpolate import RegularGridInterpolator

from supplement import (FACE_NODES, ELMER_IMAGE, FOAM_IMAGE, box_grid, settings,
                        lid_values, transform, save, tangential_load)


def input_lid(c,problem,b,logical):
    """Reconstruct the actual declared P1 triangle field; no analytic substitution."""
    if c['family']!='cavity':return lid_values(c,b,logical)
    condition=next(x for x in problem.manifest['conditions'] if x['location']==f'face{b}')
    field=problem.manifest['fields'][condition['data']['velocity']['field']]
    loc=problem.manifest['locations'][field['location']]
    values=dict(zip(map(int,problem.arrays[loc['ids']]),problem.arrays[field['array']][0]))
    mesh=problem.meshes['main'];axes=[a for a in range(3) if a!=(b-1)//2]
    results=np.full((len(logical),3),np.nan)
    for tag in problem.arrays[problem.manifest['locations'][f'face{b}']['ids']]:
        typ,ids=mesh['connectivity'][int(tag)];assert typ==2
        xyz=np.array([mesh['node_coordinates'][i] for i in ids])
        uv=((xyz-np.asarray(c['origin']))@np.asarray(c['rotation']))/np.asarray(c['lengths'])
        xy=uv[:,axes]
        basis=np.vstack([xy.T,np.ones(3)])
        bary=np.linalg.solve(basis,np.vstack([logical[:,axes].T,np.ones(len(logical))])).T
        inside=np.min(bary,axis=1)>=-1e-9
        results[inside]=bary[inside]@np.array([values[i] for i in ids])
    if np.any(~np.isfinite(results)):raise ValueError('Native boundary table extends outside declared triangles')
    return results


def tables(c,problem,points,logical,faces):
    velocities=np.zeros_like(points);bcs,lids,acc,H=settings(c)
    for b in lids:
        ids=np.unique([i for _,f in faces[b] for i in f]);velocities[ids]=input_lid(c,problem,b,logical[ids])
    accel=acc+(points-np.asarray(c['origin']))@H.T
    pressure=c['density']*((points-np.asarray(c['origin']))@acc)
    return np.column_stack([velocities,accel,pressure])


def elmer(c,problem,folder,n):
    folder.mkdir(parents=True,exist_ok=True);mesh=folder/'mesh';mesh.mkdir(exist_ok=True)
    points,cells,faces,_,logical=box_grid(c,n);bcs,lids,acc,H=settings(c)
    data=tables(c,problem,points,logical,faces)
    with (folder/'native_values.dat').open('w') as f:
        f.write(str(len(points))+'\n')
        np.savetxt(f,np.column_stack([np.arange(1,len(points)+1),data]),fmt=['%d']+['%.17g']*7)
    rows=[(b,o,q) for b,group in faces.items() for o,q in group]
    natural=any(v in ('traction','pressure_outlet') for v in bcs.values())
    (mesh/'mesh.header').write_text(f'{len(points)} {len(cells)} {len(rows)+(not natural)}\n3\n808 {len(cells)}\n404 {len(rows)}\n101 {int(not natural)}\n')
    (mesh/'mesh.nodes').write_text(''.join(f'{i} -1 '+ ' '.join(f'{x:.17g}' for x in p)+'\n' for i,p in enumerate(points,1)))
    (mesh/'mesh.elements').write_text(''.join(f'{i} 1 808 '+' '.join(map(str,h+1))+'\n' for i,h in enumerate(cells,1)))
    boundaries=''.join(f'{i} {b} {o+1} 0 404 '+' '.join(str(v+1) for v in q)+'\n' for i,(b,o,q) in enumerate(rows,1))
    if not natural:boundaries+=f'{len(rows)+1} 99 1 0 101 1\n'
    (mesh/'mesh.boundary').write_text(boundaries)
    functions='''MODULE PrescribedValues
 USE DefUtils
 IMPLICIT NONE
 REAL(KIND=dp), ALLOCATABLE, SAVE :: Data(:,:)
CONTAINS
 FUNCTION Lookup(Node,k) RESULT(v)
 INTEGER :: Node,k,n,i,j,unit
 REAL(KIND=dp) :: v
 IF (.NOT.ALLOCATED(Data)) THEN
   OPEN(NEWUNIT=unit,FILE="native_values.dat",STATUS="old",ACTION="read")
   READ(unit,*) n
   ALLOCATE(Data(7,n))
   DO i=1,n
     READ(unit,*) j,Data(:,i)
     IF (j/=i) STOP "Invalid native I/O node mapping"
   END DO
   CLOSE(unit)
 END IF
 v=Data(k,Node)
 END FUNCTION
END MODULE
'''
    for name,k in [('VX',1),('VY',2),('VZ',3),('AX',4),('AY',5),('AZ',6),('PEXT',7)]:
        functions+=f'''FUNCTION {name}(Model,Node,Time) RESULT(v)
 USE PrescribedValues
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: Node
 REAL(KIND=dp) :: Time,v
 v=Lookup(Node,{k})
END FUNCTION
'''
    for b in range(1,7):
        normal=np.asarray(c['rotation'])[:,(b-1)//2]*(1 if b%2==0 else -1)
        for a in range(3):
            functions+=f'''FUNCTION T{b}{a}(Model,Node,Time) RESULT(v)
 USE PrescribedValues
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: Node
 REAL(KIND=dp) :: Time,v
 v=-Lookup(Node,7)*({normal[a]:.17e}_dp)+({tangential_load(c,b)[a]:.17e}_dp)
END FUNCTION
'''
    (folder/'NativeValues.f90').write_text(functions)
    sif=f'''Header
 CHECK KEYWORDS Warn
 Mesh DB "." "mesh"
 Results Directory "."
End
Simulation
 Max Output Level = 5
 Coordinate System = Cartesian 3D
 Simulation Type = Steady state
 Steady State Max Iterations = 1
 Output File = "flow.result"
 Set Dirichlet BCs by BC Numbering = True
End
Body 1
 Equation = 1
 Material = 1
 Body Force = 1
End
Equation 1
 Active Solvers(2) = 1 2
End
Material 1
 Density = {c['density']:.17g}
 Viscosity = {c['viscosity']:.17g}
End
Body Force 1
 Flow BodyForce 1 = Variable Time
   Real Procedure "NativeValues" "AX"
 Flow BodyForce 2 = Variable Time
   Real Procedure "NativeValues" "AY"
 Flow BodyForce 3 = Variable Time
   Real Procedure "NativeValues" "AZ"
End
Solver 1
 Equation = Navier-Stokes
 Procedure = "FlowSolve" "FlowSolver"
 Variable = Flow Solution[Velocity:3 Pressure:1]
 Variable DOFs = 4
 Flow Model = Full
 Stabilization Method = Stabilized
 Linear System Solver = Iterative
 Linear System Iterative Method = BiCGStab
 Linear System Preconditioning = ILU1
 Linear System Max Iterations = 3000
 Linear System Convergence Tolerance = 1e-11
 Nonlinear System Max Iterations = 100
 Nonlinear System Convergence Tolerance = 1e-9
 Nonlinear System Convergence Measure = Solution
 Nonlinear System Convergence Absolute = Logical True
 Nonlinear System Norm Dofs = 4
 Nonlinear System Newton After Iterations = 5
 Nonlinear System Newton After Tolerance = 1e-3
 Nonlinear System Relaxation Factor = 0.7
End
Solver 2
 Exec Solver = After Simulation
 Equation = ResultOutput
 Procedure = "ResultOutputSolve" "ResultOutputSolver"
 Output File Name = "solution"
 Vtu Format = Logical True
 Binary Output = Logical False
End
'''
    for b,group in faces.items():
        if not group:continue
        op=bcs[b];sif+=f'Boundary Condition {b}\n Target Boundaries(1) = {b}\n'
        if op=='no_slip':sif+=' Velocity 1 = Real 0\n Velocity 2 = Real 0\n Velocity 3 = Real 0\n'
        elif op in ('velocity','flow_rate','moving_wall'):
            for i,name in enumerate(('VX','VY','VZ'),1):sif+=f' Velocity {i} = Variable Time\n   Real Procedure "NativeValues" "{name}"\n'
        elif op in ('slip','symmetry'):sif+=' Normal-Tangential Velocity = Logical True\n Velocity 1 = Real 0\n'
        elif op=='periodic' and b%2:
            partner=b+1;shift=-np.asarray(c['rotation'])[:,(b-1)//2]*c['lengths'][(b-1)//2]
            sif+=f' Periodic BC = {partner}\n Periodic BC Translate(3) = '+ ' '.join(map(str,shift))+'\n'
            sif+=''.join(f' Periodic BC Velocity {i} = Logical True\n' for i in (1,2,3))+' Periodic BC Pressure = Logical True\n'
        elif op in ('pressure_outlet','traction'):
            # These cases prescribe a purely normal total traction. Pressure is
            # offset only for conditioning and restored in every requested output.
            sif+=' Flow Force BC = Logical True\n'
            for a in range(3):sif+=f' Pressure {a+1} = Variable Time\n   Real Procedure "NativeValues" "T{b}{a}"\n'
        sif+='End\n'
    if not natural:sif+='Boundary Condition 8\n Target Boundaries(1) = 99\n Pressure = Real 0\nEnd\n'
    (folder/'flow.sif').write_text(sif)
    (folder/'run.sh').write_text('set -eu\nelmerf90 NativeValues.f90 -o NativeValues.so > compile.log 2>&1\nElmerSolver flow.sif > flow.log 2>&1\n')


def foam(c,problem,folder,n):
    folder.mkdir(parents=True,exist_ok=True)
    for d in ('0','constant/polyMesh','system'):(folder/d).mkdir(parents=True,exist_ok=True)
    points,cells,boundaries,internal,logical=box_grid(c,n);bcs,lids,acc,H=settings(c)
    conservative=c['family'] in ('hydrostatic','couette','plug')
    # Exact pressure variable substitution for conservative body acceleration:
    # p/rho = q + Phi, grad(Phi)=a. This is the usual hydrostatic-pressure
    # separation, not a prescribed solution for q or velocity.
    if conservative:
        save(folder/'constant/pressure_transform.json',dict(definition='p = rho*(q+Phi)',acceleration=acc.tolist(),hessian=H.tolist(),origin=c['origin']))
        acc=np.zeros(3);H=np.zeros((3,3))
    def initial_pressure(xyz):
        if c['family'] not in ('hydrostatic','couette','plug'):return np.zeros(len(xyz))
        x=np.asarray(xyz)-np.asarray(c['origin'])
        return x@acc+.5*np.einsum('ni,ij,nj->n',x,H,x)
    def write(name,kind,body):
        (folder/name).write_text(f'FoamFile\n{{version 2.0;format ascii;class {kind};object {Path(name).name};}}\n'+body)
    def vector(v):return '('+' '.join(f'{x:.17g}' for x in v)+')'
    def values(v):
        v=np.asarray(v)
        if v.ndim==1:return 'nonuniform List<scalar>\n'+str(len(v))+'\n(\n'+'\n'.join(f'{x:.17g}' for x in v)+'\n)'
        return 'nonuniform List<vector>\n'+str(len(v))+'\n(\n'+'\n'.join(map(vector,v))+'\n)'
    write('constant/polyMesh/points','vectorField',str(len(points))+'\n(\n'+'\n'.join(map(vector,points))+'\n)\n')
    fcs=[q for _,_,q in internal];owners=[o for o,_,_ in internal];patches=[];ub='';pb=''
    for b,group in boundaries.items():
        if not group:continue
        op=bcs[b];start=len(fcs);fcs.extend(q for _,q in group);owners.extend(o for o,_ in group)
        patch_type='cyclic' if op=='periodic' else 'symmetryPlane' if op=='symmetry' else 'patch' if op in ('pressure_outlet','traction','velocity','flow_rate') else 'wall'
        p=f'b{b}\n{{type {patch_type};nFaces {len(group)};startFace {start};'
        if op=='periodic':
            shift=np.asarray(c['rotation'])[:,(b-1)//2]*c['lengths'][(b-1)//2]*(1 if b%2 else -1)
            p+=f'neighbourPatch b{b+1 if b%2 else b-1};transform translational;separationVector {vector(shift)};'
        patches.append(p+'}\n')
        centers=np.array([points[list(q)].mean(axis=0) for _,q in group]);uv=np.array([logical[list(q)].mean(axis=0) for _,q in group])
        normal=np.asarray(c['rotation'])[:,(b-1)//2]*(1 if b%2==0 else -1)
        def wall_pressure():
            if c['family'] in ('hydrostatic','couette','plug'):
                # For these equilibrium/parallel-flow families the normal
                # momentum equation reduces to dp/dn = rho*a.n. Supply the
                # corresponding native kinematic-pressure Neumann data; the
                # velocity/pressure fields are still solved by simpleFoam.
                gradient=(acc+(centers-np.asarray(c['origin']))@H.T)@normal
                return 'type fixedGradient;gradient '+values(gradient)+';value '+values(initial_pressure(centers))+';'
            return 'type fixedFluxPressure;value '+values(initial_pressure(centers))+';'
        if op in ('no_slip','moving_wall','velocity','flow_rate'):
            v=input_lid(c,problem,b,uv) if b in lids else np.zeros((len(group),3))
            ub+=f'b{b} {{type fixedValue;value '+values(v)+';}\n';pb+=f'b{b} {{'+wall_pressure()+'}\n'
        elif op in ('slip','symmetry','periodic'):
            typ='cyclic' if op=='periodic' else 'symmetryPlane' if op=='symmetry' else 'slip'
            ub+=f'b{b} {{type {typ};}}\n'
            ptype='cyclic' if op=='periodic' else 'symmetryPlane' if op=='symmetry' else 'fixedFluxPressure'
            pb+=f'b{b} {{'+(wall_pressure() if ptype=='fixedFluxPressure' else f'type {ptype};')+'}\n'
        else:
            # In these plug/hydrostatic/Couette families the prescribed state has
            # zero normal velocity gradient and precisely the declared tangential
            # traction. This mapping is not a general traction-outlet adapter.
            pext=(centers-np.asarray(c['origin']))@acc
            ub+=f'b{b} {{type zeroGradient;}}\n';pb+=f'b{b} {{type fixedValue;value '+values(pext)+';}\n'
    write('constant/polyMesh/faces','faceList',str(len(fcs))+'\n(\n'+''.join('4('+' '.join(map(str,q))+')\n' for q in fcs)+')\n')
    for name,v in [('owner',owners),('neighbour',[q for _,q,_ in internal])]:write('constant/polyMesh/'+name,'labelList',str(len(v))+'\n(\n'+'\n'.join(map(str,v))+'\n)\n')
    write('constant/polyMesh/boundary','polyBoundaryMesh',str(len(patches))+'\n(\n'+''.join(patches)+')\n')
    write('system/controlDict','dictionary','''application simpleFoam;
startFrom startTime;startTime 0;stopAt endTime;endTime 2000;deltaT 1;
writeControl timeStep;writeInterval 100;purgeWrite 2;writeFormat ascii;writePrecision 16;
writeCompression off;timeFormat general;timePrecision 10;runTimeModifiable false;
''')
    write('system/fvSchemes','dictionary','''ddtSchemes {default steadyState;}
gradSchemes {default Gauss linear;}
divSchemes {default none;div(phi,U) bounded Gauss linearUpwind grad(U);div((nuEff*dev2(T(grad(U))))) Gauss linear;}
laplacianSchemes {default Gauss linear corrected;}
interpolationSchemes {default linear;}
snGradSchemes {default corrected;}
''')
    fv_solution='''solvers {
p {solver PCG;preconditioner DIC;tolerance 1e-11;relTol 0;}
U {solver smoothSolver;smoother symGaussSeidel;tolerance 1e-12;relTol 0;}}
SIMPLE {nNonOrthogonalCorrectors 1;pRefCell 0;pRefValue 0;
residualControl {p 1e-9;U 1e-10;}}
relaxationFactors {fields {p 0.3;} equations {U 0.7;}}
'''
    cell_centers=points[cells].mean(axis=1);p_initial=initial_pressure(cell_centers)
    fv_solution=fv_solution.replace('pRefValue 0;',f'pRefValue {p_initial[0]:.17g};')
    write('system/fvSolution','dictionary',fv_solution)
    write('constant/transportProperties','dictionary',f'transportModel Newtonian;\nnu [0 2 -1 0 0 0 0] {c["viscosity"]/c["density"]:.17g};\n')
    write('constant/turbulenceProperties','dictionary','simulationType laminar;\n')
    write('0/U','volVectorField','dimensions [0 1 -1 0 0 0 0];\ninternalField uniform (0 0 0);\nboundaryField {\n'+ub+'}\n')
    write('0/p','volScalarField','dimensions [0 2 -2 0 0 0 0];\ninternalField '+values(p_initial)+';\nboundaryField {\n'+pb+'}\n')
    if np.linalg.norm(H)==0:
        write('constant/fvOptions','dictionary','bodyAcceleration {type vectorSemiImplicitSource;active true;selectionMode all;volumeMode specific;injectionRateSuSp {U ('+vector(acc)+' 0);}}\n')
    else:
        centers=points[cells].mean(axis=1);acceleration=acc+(centers-np.asarray(c['origin']))@H.T
        (folder/'acceleration.dat').write_text(str(len(cells))+'\n(\n'+'\n'.join(map(vector,acceleration))+'\n)\n')
        write('constant/fvOptions','dictionary','''bodyAcceleration {
type coded;active true;selectionMode all;fields (U);name prescribedAcceleration;
codeInclude #{
 #include "IFstream.H"
#};
codeCorrect #{ #};
codeConstrain #{ #};
codeAddSup #{
 IFstream stream("acceleration.dat");vectorField a(stream);
 if (a.size()!=mesh().nCells()) {FatalErrorInFunction << "source table length" << exit(FatalError);}
 eqn.source() -= mesh().V()*a;
#};}
''')
    (folder/'run.sh').write_text('set -eu\ncheckMesh > mesh.log 2>&1\nsimpleFoam > flow.log 2>&1\n')


def read_foam(path,count):
    text=Path(path).read_text();m=re.search(r'internalField\s+nonuniform\s+List<\w+>\s+(\d+)\s*\((.*?)\)\s*;',text,re.S)
    if m:return np.fromstring(m[2].replace('(',' ').replace(')',' '),sep=' ').reshape(int(m[1]),-1)
    m=re.search(r'internalField\s+uniform\s+([^;]+);',text)
    if not m:raise ValueError('Missing native internalField')
    return np.tile(np.fromstring(m[1].replace('(',' ').replace(')',' '),sep=' '),(count,1))


class NativeField:
    def __init__(self,c,folder,n,solver):
        self.c=c;self.R=np.asarray(c['rotation']);self.origin=np.asarray(c['origin']);self.lengths=np.asarray(c['lengths'])
        self.potential_pressure=solver=='openfoam' and c['family'] in ('hydrostatic','couette','plug')
        points,cells,faces,_,logical=box_grid(c,n);self.points=points;self.cells=cells;self.solver=solver;self.faces=faces
        if solver=='elmer':
            tree=ET.parse(folder/'mesh/solution_t0001.vtu')
            xyz=np.fromstring(tree.find('.//Points/DataArray').text,sep=' ').reshape(-1,3)
            fields={a.get('Name').lower():np.fromstring(a.text,sep=' ').reshape(len(xyz),-1) for a in tree.findall('.//PointData/DataArray')}
            data=np.column_stack([fields['velocity'],fields['pressure']])
            measured=(xyz-self.origin)@self.R
            local=np.rint(measured/self.lengths*n)/n*self.lengths
            if np.max(abs(local-measured))>1e-6*max(self.lengths):raise ValueError('VTU coordinates do not match the configured native grid')
            local=np.round(local,11)
            center_local=np.round((points[cells].mean(axis=1)-self.origin)@self.R,11)
        else:
            times=[p for p in folder.iterdir() if p.is_dir() and re.fullmatch(r'[0-9.]+',p.name) and float(p.name)>0]
            latest=max(times,key=lambda p:float(p.name))
            self.latest=latest
            data=np.column_stack([read_foam(latest/'U',len(cells)),read_foam(latest/'p',len(cells))*c['density']])
            xyz=points[cells].mean(axis=1);local=np.round((xyz-self.origin)@self.R,11);center_local=local
        self.axes=[np.unique(local[:,a]) for a in range(3)]
        # Preserve obstacle gaps in the structured lattice; never interpolate
        # across the hole with a Delaunay triangulation.
        if c['geometry']!='box':self.axes=[np.round(np.linspace(0,self.lengths[a],n+1) if solver=='elmer' else (np.arange(n)+.5)*self.lengths[a]/n,11) for a in range(3)]
        dense=np.full(tuple(len(a) for a in self.axes)+(4,),np.nan)
        index=tuple(np.searchsorted(self.axes[a],local[:,a]) for a in range(3));dense[index]=data
        self.interpolator=RegularGridInterpolator(self.axes,dense,bounds_error=False,fill_value=None)
        # The native pressure pin is purely numerical. Restore the problem's
        # explicit global pressure constraint; this is not grader alignment.
        bcs,_,_,_=settings(c)
        if any(v in ('traction','pressure_outlet') for v in bcs.values()):self.shift=c['pressure_value']
        elif c['gauge_kind']=='mean':
            mean=float(self.interpolator(center_local)[:,3].mean())
            if self.potential_pressure:
                _,_,acc,H=settings(c);center=self.R@(self.lengths/2);cov=self.R@np.diag(self.lengths**2/12)@self.R.T
                mean+=c['density']*(center@acc+.5*(center@H@center+np.trace(H@cov)))
            self.shift=c['pressure_value']-mean
        else:
            point=self.lengths[None,:]*.125
            mean=float(self.interpolator(point)[0,3])
            if self.potential_pressure:mean+=self.pressure_potential(point@self.R.T+self.origin)[0]
            self.shift=c['pressure_value']-mean
        self.boundary_trace={}
        if solver=='openfoam':
            text=(self.latest/'U').read_text();bcs,_,_,_=settings(c)
            for b,op in bcs.items():
                if not faces[b] or op not in ('no_slip','moving_wall','velocity','flow_rate'):continue
                match=re.search(r'\bb'+str(b)+r'\s*\{(.*?)\}',text,re.S)
                if not match:raise ValueError('Native prescribed patch missing')
                uniform=re.search(r'value\s+uniform\s+\((.*?)\)',match[1],re.S)
                if uniform:v=np.fromstring(uniform[1],sep=' ')[None]
                else:
                    match=re.search(r'value\s+nonuniform\s+List<vector>\s+\d+\s*\((.*?)\)\s*;',match[1],re.S)
                    if not match:raise ValueError('Native velocity boundary data missing')
                    v=np.fromstring(match[1].replace('(',' ').replace(')',' '),sep=' ').reshape(-1,3)
                if np.max(abs(v-v[0]))<1e-14:self.boundary_trace[b]=v[0]
        self.native_seconds=None

    def boundary_flow(self,location):
        """Use the native conservative face flux, not cell-center extrapolation."""
        assert self.solver=='openfoam'
        b=int(location.removeprefix('face'));text=(self.latest/'phi').read_text()
        match=re.search(r'\bb'+str(b)+r'\s*\{(.*?)\}',text,re.S)
        if not match:raise ValueError('Missing native boundary phi')
        value=re.search(r'value\s+uniform\s+([^;]+);',match[1])
        if value:return float(value[1])*len(self.faces[b])
        value=re.search(r'value\s+nonuniform\s+List<scalar>\s+(\d+)\s*\((.*?)\)\s*;',match[1],re.S)
        if not value:raise ValueError('Unsupported native phi boundary encoding')
        v=np.fromstring(value[2],sep=' ')
        if len(v)!=len(self.faces[b]):raise ValueError('Native phi patch length mismatch')
        return float(v.sum())

    def values(self,xyz):
        local=np.round((np.asarray(xyz)-self.origin)@self.R,11)
        result=self.interpolator(local);result[:,3]+=self.shift
        if self.potential_pressure:result[:,3]+=self.pressure_potential(xyz)
        for b,trace in self.boundary_trace.items():
            axis=(b-1)//2;plane=0 if b%2 else self.lengths[axis]
            on_patch=abs(local[:,axis]-plane)<1e-9*max(self.lengths)
            result[on_patch,:3]=trace
        if not np.all(np.isfinite(result)):raise ValueError('Observation touches an unresolved obstacle stencil')
        return result

    def pressure_potential(self,xyz):
        _,_,acc,H=settings(self.c);x=np.asarray(xyz)-self.origin
        return self.c['density']*(x@acc+.5*np.einsum('ni,ij,nj->n',x,H,x))

    def gradient(self,xyz):
        xyz=np.asarray(xyz);local=(xyz-self.origin)@self.R
        derivatives=[]
        for a in range(3):
            h=self.lengths[a]*1e-5;plus=local.copy();minus=local.copy();plus[:,a]+=h;minus[:,a]-=h
            derivatives.append((self.interpolator(plus)[:,:3]-self.interpolator(minus)[:,:3])/(2*h))
        return np.stack(derivatives,axis=-1)@self.R.T


class AnalyticField:
    """Classical equilibrium/parallel-flow verification, never the producer."""
    solver='analytic'
    def __init__(self,c):
        self.c=c;self.points,self.cells,*_=box_grid(c,12)
        self.R=np.asarray(c['rotation']);self.L=np.asarray(c['lengths']);self.origin=np.asarray(c['origin'])
        self.bcs,self.lids,self.acc,self.H=settings(c)
        if c['family']=='periodic-duct' and not (c['geometry']=='box' and self.bcs[5] in ('slip','symmetry')):raise ValueError('No analytic family for this duct')
        if c['family']=='cavity':raise ValueError('No analytic cavity reference')
        if np.linalg.norm(self.H)>0:raise ValueError('Quadratic pressure face quadrature requires separate verification')
    def values(self,xyz):
        X=np.asarray(xyz)-self.origin;xi=X@self.R;eta=xi[:,1]/self.L[1]
        phi=X@self.acc+.5*np.einsum('ni,ij,nj->n',X,self.H,X)
        if self.c['family']=='periodic-duct':u=6*self.c['speed']*eta[:,None]*(1-eta[:,None])*self.R[:,0]+eta[:,None]*(self.R@np.array(self.lids.get(4,[0,0,0])));phi*=0
        elif self.c['family']=='couette':
            low=self.R@np.array(self.lids.get(3,[0,0,0]));high=self.R@np.array(self.lids.get(4,[0,0,0]));u=low+eta[:,None]*(high-low)
        elif self.c['family']=='plug':u=np.tile(self.R[:,0]*self.c['speed'],(len(X),1))
        else:u=np.zeros_like(X)
        if not any(op in ('traction','pressure_outlet') for op in self.bcs.values()):
            if self.c['gauge_kind']=='mean':
                center=self.R@(self.L/2);cov=self.R@np.diag(self.L**2/12)@self.R.T
                ref=center@self.acc+.5*(center@self.H@center+np.trace(self.H@cov))
            else:
                point=self.R@(self.L*.125);ref=point@self.acc+.5*point@self.H@point
            if self.c['family']=='periodic-duct':ref=0.
            phi-=ref
        return np.column_stack([u,self.c['pressure_value']+self.c['density']*phi])
    def gradient(self,xyz):
        n=len(xyz);eta=((np.asarray(xyz)-self.origin)@self.R)[:,1]/self.L[1]
        if self.c['family']=='couette':
            delta=self.R@(np.asarray(self.lids.get(4,[0,0,0]))-np.asarray(self.lids.get(3,[0,0,0])))
            return np.tile(np.outer(delta,self.R[:,1])/self.L[1],(n,1,1))
        if self.c['family']=='periodic-duct':
            top=self.R@np.asarray(self.lids.get(4,[0,0,0]));slope=(6*self.c['speed']*(1-2*eta)[:,None]*self.R[:,0]+top)/self.L[1]
            return np.einsum('ni,j->nij',slope,self.R[:,1])
        return np.zeros((n,3,3))


def outputs(c,problem,native):
    from caeoj.sdk import boundary_geometry
    result={}
    for spec in problem.manifest['outputs'].values():
        loc=problem.manifest['locations'][spec['location']];quantity=spec['quantity']
        if loc['kind']!='aggregate':
            if loc['kind']=='points':xyz=problem.arrays[loc['coordinates']]
            elif loc['entity']=='node':xyz=np.array([problem.meshes['main']['node_coordinates'][int(i)] for i in problem.arrays[loc['ids']]])
            elif loc['dimension']==2:xyz,normal,area=boundary_geometry(problem,spec['location'])
            else:
                from scipy.spatial import ConvexHull
                mesh=problem.meshes['main'];centers=[]
                for i in problem.arrays[loc['ids']]:
                    p=np.array([mesh['node_coordinates'][t] for t in mesh['connectivity'][int(i)][1]])
                    middle=p.mean(axis=0);hull=ConvexHull(p);tri=p[hull.simplices]
                    v=np.abs(np.linalg.det(tri-middle))/6
                    centers.append(np.sum((tri.sum(axis=1)+middle)/4*v[:,None],axis=0)/v.sum())
                xyz=np.array(centers)
            values=native.values(xyz)
            if quantity=='velocity':v=values[:,:3]
            elif quantity=='pressure':v=values[:,3,None]
            elif quantity=='density':v=np.full((len(xyz),1),c['density'])
            elif quantity=='dynamic_viscosity':v=np.full((len(xyz),1),c['viscosity'])
            elif quantity=='traction':
                grad=native.gradient(xyz);stress=-values[:,3,None,None]*np.eye(3)+c['viscosity']*(grad+grad.transpose(0,2,1));v=np.einsum('nij,nj->ni',stress,normal)
            else:
                grad=native.gradient(xyz);D=(grad+grad.transpose(0,2,1))/2;v=np.sqrt(2*np.sum(D*D,axis=(1,2)))[:,None]
        else:
            assert loc['kind']=='aggregate'
            if loc['operation']=='mean':
                xyz=native.points[native.cells].mean(axis=1)
                v=np.array([[native.values(xyz)[:,3].mean()]])
                result[spec['array']]=v[None]
                continue
            xyz,normal,area=boundary_geometry(problem,loc['source'])
            values=native.values(xyz)
            if quantity in ('volume_flow','mass_flow'):
                value=native.boundary_flow(loc['source']) if native.solver=='openfoam' else np.sum(np.sum(values[:,:3]*normal,axis=1)*area)
                v=np.array([[value*(c['density'] if quantity=='mass_flow' else 1)]])
            else:
                grad=native.gradient(xyz);stress=-values[:,3,None,None]*np.eye(3)+c['viscosity']*(grad+grad.transpose(0,2,1))
                traction=np.einsum('nij,nj->ni',stress,normal);v=-np.sum(traction*area[:,None],axis=0)[None]
        result[spec['array']]=np.asarray(v,dtype='float64')[None]
    return result


def execute(solvers,sid,folder,timeout=600):
    image=ELMER_IMAGE if sid=='elmer' else FOAM_IMAGE
    cmd=['python3',str(solvers/'solver.py'),'run',sid,'--image-id',image,'--workdir',str(folder.resolve()),'--cpus','1','--memory','2g','--timeout',str(timeout),'--','sh','run.sh']
    start=__import__('time').monotonic()
    with (folder/'execution.log').open('w') as stream:
        process=subprocess.run(cmd,stdout=stream,stderr=subprocess.STDOUT)
    elapsed=__import__('time').monotonic()-start
    if process.returncode:raise RuntimeError(f'{sid} failed with {process.returncode}: {folder}/execution.log')
    proof=convergence(sid,folder)
    return dict(solver=sid,image_id=image,wall_seconds=elapsed,command=cmd,**proof,
                raw_sha256={str(p.relative_to(folder)):__import__('hashlib').sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file() and (p.suffix=='.vtu' or p.name in ('U','p','flow.log','flow.sif','fvOptions','fvSchemes','fvSolution','native_values.dat')) and 'dynamicCode' not in p.parts})


def convergence(sid,folder):
    log=(folder/'flow.log').read_text()
    stationarity=None
    if sid=='openfoam' and 'SIMPLE solution converged' not in log:
        times=sorted((p for p in folder.iterdir() if p.is_dir() and re.fullmatch(r'[0-9.]+',p.name) and float(p.name)>0),key=lambda p:float(p.name))
        if len(times)<2:raise RuntimeError('No independent steady-iteration snapshots')
        du=float(np.max(np.abs(read_foam(times[-1]/'U',1)-read_foam(times[-2]/'U',1))))
        dp=float(np.max(np.abs(read_foam(times[-1]/'p',1)-read_foam(times[-2]/'p',1))))
        continuity=re.findall(r'continuity errors : sum local = ([0-9.Ee+\-]+)',log)
        if du>1e-10 or dp>1e-10 or not continuity or float(continuity[-1])>1e-9:raise RuntimeError('simpleFoam steady convergence not established')
        stationarity=dict(velocity_max_change=du,kinematic_pressure_max_change=dp,continuity=float(continuity[-1]),iterations=[float(p.name) for p in times[-2:]])
    if sid=='elmer':
        change=re.findall(r'Relative Change\s*:\s*([0-9.Ee+\-]+)',log)
        norms=re.findall(r'Result Norm\s*:\s*([0-9.Ee+\-]+)',log)
        if not change or float(change[-1])>1e-8:raise RuntimeError('Elmer nonlinear convergence not established')
    return dict(stationarity=stationarity,
                absolute_solution_change=float(change[-1]) if sid=='elmer' else None,
                solution_norm=float(norms[-1]) if sid=='elmer' else None)


def input_fingerprint(folder,sid):
    import hashlib
    if sid=='elmer':names=['flow.sif','NativeValues.f90','native_values.dat','run.sh']+[str(p.relative_to(folder)) for p in (folder/'mesh').glob('mesh.*')]
    else:names=['run.sh','0/U','0/p']+[str(p.relative_to(folder)) for directory in ('system','constant') for p in (folder/directory).rglob('*') if p.is_file()]
    if (folder/'acceleration.dat').exists():names.append('acceleration.dat')
    return {n:hashlib.sha256((folder/n).read_bytes()).hexdigest() for n in sorted(names)}


def raw_fingerprint(folder):
    import hashlib
    return {str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file() and (p.suffix=='.vtu' or p.name in ('U','p','flow.log')) and 'dynamicCode' not in p.parts}


def reusable_run(folder,sid,case_jobs):
    """Reuse only completed native executions with byte-identical native inputs."""
    import json
    wanted=input_fingerprint(folder,sid);image=ELMER_IMAGE if sid=='elmer' else FOAM_IMAGE
    for prior in sorted(case_jobs.glob('*/'+folder.name)):
        if not (prior/'execution.log').exists():continue
        try:
            if input_fingerprint(prior,sid)!=wanted:continue
            match=re.search(r'run record: (.+)',(prior/'execution.log').read_text())
            if not match:continue
            record=json.loads((Path(match[1].strip())/'record.json').read_text())
            if record.get('exit_code')!=0 or record['image_id']!=image:continue
            if any(record.get('inputs_sha256',{}).get(k)!=v for k,v in wanted.items()):continue
            if not (prior/'flow.log').is_file():continue
            proof=convergence(sid,prior)
            return prior,dict(solver=sid,image_id=image,wall_seconds=record['seconds'],command=record['command'],reused_native_run=record['id'],native_input_sha256=wanted,raw_sha256=raw_fingerprint(prior),**proof)
        except (OSError,ValueError,KeyError,RuntimeError):continue
    return None
