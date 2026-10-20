"""Input/output adapter for unmodified OpenCFD icoFoam; not a CFD solver.

Run on Titan with the caeoj venv. All results remain unvalidated candidates.
Reads only fully prescribed closed-cavity designs. No HF/benchmark code.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

import h5py
import numpy as np

IMAGE = "sha256:d6e27c56bb5f598bc93597fdf671d6e9d06534b1851885f1b093e3cc627ea67e"
SOCKET = "unix:///home/zhouzhiyu/code/docker/qbank/maintenance/solver-images/local/daemon/run/docker.sock"


def put(p, s):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(s,encoding="utf-8")


def save(p, x): put(p,json.dumps(x,ensure_ascii=False,indent=2)+"\n")
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def header(cls, obj): return f"FoamFile {{ version 2.0; format ascii; class {cls}; object {obj}; }}\n"
def vector(x): return "("+" ".join(f"{v:.15g}" for v in x)+")"


def prepare_native(path, p):
    d=p["spatial_dimension"]; lx,ly,lz=p["length_m"]; nx,ny,nz=p["target_cells_xyz"]
    hole=p["obstacle_xy_fraction"]
    xs=np.array([0,.4,.6,1])*lx if hole else np.array([0,.5,1])*lx
    ys=np.array([0,.3,.5,1])*ly if hole else np.array([0,1])*ly
    zs=np.array([0,lz]); verts=[]; lookup={}
    def v(i,j,k):
        key=(i,j,k)
        if key not in lookup: lookup[key]=len(verts);verts.append([xs[i],ys[j],zs[k]])
        return lookup[key]
    active={(i,j) for i in range(len(xs)-1) for j in range(len(ys)-1) if not(hole and i==1 and j==1)}
    patch={k:[] for k in ["left","right","bottom","top_left","top_right","front","back","obstacle"]}
    blocks=[]
    for j in range(len(ys)-1):
        for i in range(len(xs)-1):
            if (i,j) not in active: continue
            ids=[v(i,j,0),v(i+1,j,0),v(i+1,j+1,0),v(i,j+1,0),v(i,j,1),v(i+1,j,1),v(i+1,j+1,1),v(i,j+1,1)]
            counts=[max(1,round(nx*(xs[i+1]-xs[i])/lx)),max(1,round(ny*(ys[j+1]-ys[j])/ly)),nz]
            blocks.append("hex "+vector(ids)+" "+vector(counts)+" simpleGrading (1 1 1)")
            for neighbour, face, outer in [((i-1,j),[0,4,7,3],"left"),((i+1,j),[1,2,6,5],"right"),((i,j-1),[0,1,5,4],"bottom"),((i,j+1),[3,7,6,2],"top_left" if (xs[i]+xs[i+1])/2 < lx/2 else "top_right")]:
                if neighbour in active: continue
                is_hole=0<=neighbour[0]<len(xs)-1 and 0<=neighbour[1]<len(ys)-1
                patch["obstacle" if is_hole else outer].append([ids[k] for k in face])
            patch["front"].append([ids[k] for k in [0,3,2,1]])
            patch["back"].append([ids[k] for k in [4,5,6,7]])
    patch={k:v for k,v in patch.items() if v}
    chunks=[header("dictionary","blockMeshDict"),"scale 1;\nvertices\n(\n"+"\n".join(vector(v) for v in verts)+"\n);", "blocks\n(\n"+"\n".join(blocks)+"\n);\nedges ();\nboundary\n("]
    for name,faces in patch.items():
        typ="empty" if d==2 and name in ("front","back") else "wall"
        chunks.append(name+" { type "+typ+"; faces ("+" ".join(vector(v) for v in faces)+"); }")
    chunks.append(");\nmergePatchPairs ();\n")
    put(path/"system/blockMeshDict","\n".join(chunks))
    history=p["wall_speed_multiplier_linear_table"]; speeds=p["wall_velocity_vectors_m_s"]
    ubc=[];pbc=[]
    for name in patch:
        empty=d==2 and name in ("front","back")
        if empty:
            ubc.append(name+" { type empty; }"); pbc.append(name+" { type empty; }");continue
        pbc.append(name+" { type zeroGradient; }")
        if name in speeds:
            table=" ".join(f"({t:.15g} {vector(np.array(speeds[name])*a)})" for t,a in history)
            ubc.append(name+" { type uniformFixedValue; uniformValue table ("+table+"); value uniform (0 0 0); }")
        else: ubc.append(name+" { type fixedValue; value uniform (0 0 0); }")
    put(path/"0/U",header("volVectorField","U")+"dimensions [0 1 -1 0 0 0 0];\ninternalField uniform (0 0 0);\nboundaryField {\n"+"\n".join(ubc)+"\n}\n")
    put(path/"0/p",header("volScalarField","p")+"dimensions [0 2 -2 0 0 0 0];\ninternalField uniform 0;\nboundaryField {\n"+"\n".join(pbc)+"\n}\n")
    nu=p["dynamic_viscosity_Pa_s"]/p["density_kg_m3"]
    put(path/"constant/transportProperties",header("dictionary","transportProperties")+f"transportModel Newtonian;\nnu [0 2 -1 0 0 0 0] {nu:.15g};\n")
    end=p["time_interval_s"][1]; dt=p["native_dt_s"]
    put(path/"system/controlDict",header("dictionary","controlDict")+f"application icoFoam; startFrom startTime; startTime 0; stopAt endTime; endTime {end}; deltaT {dt}; writeControl runTime; writeInterval {end/4:.15g}; purgeWrite 0; writeFormat ascii; writePrecision 16; writeCompression off; timeFormat general; timePrecision 12; runTimeModifiable false;\n")
    put(path/"system/fvSchemes",header("dictionary","fvSchemes")+"ddtSchemes { default Euler; } gradSchemes { default Gauss linear; } divSchemes { default none; div(phi,U) Gauss linear; } laplacianSchemes { default Gauss linear corrected; } interpolationSchemes { default linear; } snGradSchemes { default corrected; } fluxRequired { default no; p; }\n")
    put(path/"system/fvSolution",header("dictionary","fvSolution")+"solvers { p { solver PCG; preconditioner DIC; tolerance 1e-9; relTol 0; } U { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-9; relTol 0; } } PISO { nCorrectors 2; nNonOrthogonalCorrectors 0; pRefCell 0; pRefValue 0; }\n")


def foam_list(path):
    s=path.read_text();s=re.sub(r"/\*.*?\*/|//[^\n]*","",s,flags=re.S)
    if "FoamFile" in s: s=s[s.index("}",s.index("FoamFile"))+1:]
    m=re.search(r"\b(\d+)\s*\(",s)
    if not m: raise ValueError(f"missing list: {path}")
    return int(m[1]),s[m.end():s.rfind(")")]


def native_mesh(path, d):
    mesh=path/"constant/polyMesh"
    n,s=foam_list(mesh/"points")
    xyz=np.array([[float(x) for x in v.split()] for v in re.findall(r"\(([^()]+)\)",s)])
    assert len(xyz)==n
    n,s=foam_list(mesh/"faces");faces=[[int(x) for x in v.split()] for v in re.findall(r"\d+\s*\(([^()]*)\)",s)];assert len(faces)==n
    n,s=foam_list(mesh/"owner");owner=np.fromstring(s,sep=" ",dtype=int);assert len(owner)==n
    n,s=foam_list(mesh/"neighbour");nei=np.fromstring(s,sep=" ",dtype=int);assert len(nei)==n
    cells=[set() for _ in range(max(owner.max(),nei.max(initial=-1))+1)]
    for face,c in zip(faces,owner): cells[c].update(face)
    for face,c in zip(faces,nei): cells[c].update(face)
    # Preserve native cell order. Geometry is Cartesian hexes; no averaging between cells.
    coords=[];lut={}
    def node(x):
        x=tuple(float(a) for a in x[:d])
        if x not in lut: lut[x]=len(coords)+1;coords.append(x+(0.,) if d==2 else x)
        return lut[x]
    conn=[];vol=[]
    for c in cells:
        a=xyz[list(c)];low=a.min(axis=0);high=a.max(axis=0)
        assert len(c)==8
        pattern=[(0,0,0),(1,0,0),(1,1,0),(0,1,0)]
        if d==3: pattern += [(0,0,1),(1,0,1),(1,1,1),(0,1,1)]
        conn.append([node(np.where(mask,high,low)) for mask in pattern])
        vol.append(np.prod((high-low)[:d]))
    s=(mesh/"boundary").read_text();patches={}
    for name,body in re.findall(r"(\w+)\s*\{([^{}]+)\}",s):
        st=re.search(r"startFace\s+(\d+)",body);nn=re.search(r"nFaces\s+(\d+)",body)
        if not(st and nn): continue
        if d==2 and name in ("front","back"):continue
        group=[]
        for f in faces[int(st[1]):int(st[1])+int(nn[1])]:
            ids=list(dict.fromkeys(node(xyz[k]) for k in f))
            assert len(ids)==(2 if d==2 else 4)
            group.append(ids)
        patches[name]=group
    return np.array(coords),conn,patches,np.array(vol)


def field(path, c, n):
    s=path.read_text();m=re.search(r"internalField\s+uniform\s+([^;]+);",s)
    if m:
        a=np.fromstring(m[1].strip("() "),sep=" ");return np.tile(a,(n,1))
    m=re.search(r"internalField\s+nonuniform\s+List<\w+>\s+(\d+)\s*\((.*?)\)\s*;",s,re.S)
    if not m:raise ValueError(f"unreadable {path}")
    a=np.fromstring(m[2].replace("("," ").replace(")"," "),sep=" ").reshape(-1,c)
    assert len(a)==n==int(m[1]);return a


def gmsh(path, xyz, conn, patches, d):
    """Export actual native cells and patch faces as MSH4.1 ASCII."""
    # Entities carry physical groups; all nodes classified on the fluid entity.
    lo=xyz.min(axis=0);hi=xyz.max(axis=0);bb=" ".join(str(x) for x in [*lo,*hi]); groups=[]; tag=len(conn)+1; ids={}
    for g,(name,faces) in enumerate(patches.items(),2):
        start=tag;group=[]
        for f in faces:group.append(f"{tag} "+" ".join(map(str,f)));tag+=1
        ids[name]=np.arange(start,tag,dtype=np.int64);groups.append((g,group))
    n=len(xyz); lines=["$MeshFormat","4.1 0 8","$EndMeshFormat","$Entities"]
    lines.append(f"0 {len(groups) if d==2 else 0} {1 if d==2 else len(groups)} {1 if d==3 else 0}")
    for g,_ in groups:lines.append(f"{g} {bb} 1 {g} 0")
    lines.append(f"1 {bb} 1 1 0")
    lines+= ["$EndEntities","$Nodes",f"1 {n} 1 {n}",f"{d} 1 0 {n}", "\n".join(str(i) for i in range(1,n+1)),"\n".join(" ".join(map(str,x)) for x in xyz),"$EndNodes","$Elements",f"{len(groups)+1} {tag-1} 1 {tag-1}",f"{d} 1 {3 if d==2 else 5} {len(conn)}"]
    lines += [str(i+1)+" "+" ".join(map(str,c)) for i,c in enumerate(conn)]
    for g,rows in groups:lines+=[f"{d-1} {g} {1 if d==2 else 3} {len(rows)}",*rows]
    lines += ["$EndElements"]
    put(path,"\n".join(lines)+"\n");return ids


def convert(job, entry, task, grading):
    p=entry["prescription"];d=p["spatial_dimension"];native=job/"native"
    xyz,conn,patches,vol=native_mesh(native,d);n=len(conn)
    inp=job/"input";inp.mkdir(exist_ok=True);ref=job/"reference";ref.mkdir(exist_ok=True)
    ids=gmsh(inp/"mesh.msh",xyz,conn,patches,d)
    def loc(key,dim):return {"kind":"mesh","mesh":"main","entity":"element","dimension":dim,"ids":key}
    def desc(name,quantity,location,axis,unit,c,sampling=None):
        v={"array":name,"quantity":quantity,"location":location,"time_axis":axis,"dtype":"float64","kind":"scalar" if c==1 else "vector","component_shape":[c],"components":["value"] if c==1 else list("xyz"[:c]),"unit":unit,"value_kind":"average"}
        if sampling:v["sampling"]=sampling
        return v
    locations={"domain":loc("cell_ids",d)};fields={};conditions=[]
    times=p["output_times_s"];ht=np.array(p["wall_speed_multiplier_linear_table"])
    with h5py.File(inp/"input.h5","w") as f:
        f["cell_ids"]=np.arange(1,n+1,dtype=np.int64);f["t0"]=np.array([0.]);f["times"]=np.array(times);f["history_times"]=ht[:,0]
        f["initial_u"]=np.zeros((1,n,d))
        fields["initial_u"]=desc("initial_u","velocity","domain","initial","m/s",d,{"space":"uniform","time":"constant","extrapolation":"forbid"})
        conditions.append({"role":"initial","variable":"velocity","operator":"assign","location":"domain","data":{"value":{"field":"initial_u"}}})
        for name,a in ids.items():
            f[name+"_ids"]=a;locations[name]=loc(name+"_ids",d-1)
            if name not in p["wall_velocity_vectors_m_s"]:
                conditions.append({"role":"boundary","variable":"flow","operator":"no_slip","location":name,"data":{}});continue
            key=name+"_u";velocity=np.array(p["wall_velocity_vectors_m_s"][name][:d]);a=ht[:,1,None,None]*np.tile(velocity,(1,len(a),1));f[key]=a
            fields[key]=desc(key,"velocity",name,"history","m/s",d,{"space":"uniform","time":"linear","extrapolation":"forbid"})
            conditions.append({"role":"boundary","variable":"flow","operator":"moving_wall","location":name,"data":{"velocity":{"field":key}}})
    problem={"task":task,"spatial_dimension":d,"contract_version":2,"profile":"cfd-2.1","data_file":"input.h5","geometries":{},"meshes":{"main":{"file":"mesh.msh"}},"locations":locations,"time_axes":{"initial":"t0","requested":"times","history":"history_times"},"fields":fields,"conditions":conditions,"outputs":{"u":desc("velocity","velocity","domain","requested","m/s",d),"p":desc("pressure","pressure","domain","requested","Pa",1)},"analysis":{"type":"transient","compressibility":"incompressible","flow_regime":"laminar","temperature":{"value":300,"unit":"K"},"pressure":{"representation":"gauge","reference_pressure":{"value":101325,"unit":"Pa"}},"time_interval":{"start":0,"end":p["time_interval_s"][1]},"pressure_gauge":{"kind":"mean","location":"domain","value":{"value":0,"unit":"Pa"}}},"materials":{"fluid":{"region":"domain","density":{"kind":"constant","parameters":{"density":{"value":p["density_kg_m3"],"unit":"kg/m3"}}},"viscosity":{"kind":"newtonian","parameters":{"dynamic_viscosity":{"value":p["dynamic_viscosity_Pa_s"],"unit":"Pa.s"}}}}}}
    save(inp/"problem.json",problem);save(ref/"grading.json",grading)
    us=[];ps=[];native_times={round(float(x.name),12):x for x in native.iterdir() if x.is_dir() and re.fullmatch(r"[0-9.eE+-]+",x.name)}
    for t in times:
        td=native_times[round(t,12)];u=field(td/"U",3,n)[:,:d];pressure=field(td/"p",1,n)*p["density_kg_m3"]
        pressure-=np.sum(pressure[:,0]*vol)/np.sum(vol)
        # Only storage completeness/finite-value checks, not an accuracy validation.
        if not(np.isfinite(u).all() and np.isfinite(pressure).all()):raise ValueError("nonfinite output")
        us.append(u);ps.append(pressure)
    with h5py.File(ref/"reference.h5","w") as f:
        f["cell_ids"]=np.arange(1,n+1,dtype=np.int64);f["times"]=np.array(times);f["velocity"]=np.array(us);f["pressure"]=np.array(ps)
    return {"cells":n,"output_frames":len(times),"output_quantities":["velocity","pressure"],"reference_sha256":digest(ref/"reference.h5"),"input_sha256":{x.name:digest(x) for x in inp.iterdir()},"validation":"not_performed","native_to_contract":"same native cell order; 2D empty extrusion removed; p multiplied by rho then volume-mean gauge applied"}


def run_one(root, record, entry):
    job=root/"cases"/entry["design_id"];status=job/"status.json"
    if status.exists():return json.loads(status.read_text())
    if entry["status"]!="numerically_specified_pending_native_adapter":raise ValueError("unfrozen design")
    p=entry["prescription"];job.mkdir(parents=True,exist_ok=False);save(job/"design.json",entry)
    prepare_native(job/"native",p)
    name="ch02ten-"+hashlib.sha256(entry["design_id"].encode()).hexdigest()[:12]
    cmd=["docker","--host",SOCKET,"run","--name",name,"--network","none","--cpus","1","--memory","1g","--user",f"{__import__('os').getuid()}:{__import__('os').getgid()}","-e","HOME=/tmp","-v",f"{job.resolve()}:/work","-w","/work/native",IMAGE,"bash","-c","source /usr/lib/openfoam/openfoam2512/etc/bashrc && blockMesh > ../blockMesh.log 2>&1 && icoFoam > ../icoFoam.log 2>&1"]
    save(job/"execution.json",{"command":cmd,"image":IMAGE,"start_unix":time.time(),"producer":"unmodified OpenCFD icoFoam","numerical_validation":False})
    state={"design_id":entry["design_id"],"status":"running","container":name};save(status,state)
    try:
        cp=subprocess.run(cmd,capture_output=True,text=True,timeout=1800)
        put(job/"docker.stdout",cp.stdout);put(job/"docker.stderr",cp.stderr)
        if cp.returncode:raise RuntimeError(f"native solver exit {cp.returncode}; see native logs")
        g=record["grading_template"]
        state.update(convert(job,entry,record["task"],g));state["status"]="unvalidated_candidate"
    except Exception as e:
        # Timeout is not permission to kill or restart a possibly active solver.
        state.update(status="needs_attention",error=str(e))
    state["finished_unix"]=time.time();save(status,state);return state


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--root",type=Path,required=True);ap.add_argument("--snapshot",type=Path,required=True);ap.add_argument("--execute",action="store_true");args=ap.parse_args()
    records=[]
    for p in args.snapshot.glob("qbank/02-fluid-mechanics/*/*/author/chapter02-ten-20261020/design.json"):
        r=json.loads(p.read_text())
        g=p.parents[1]/"grading-template.json"
        r["grading_template"]=json.loads(g.read_text());records.append(r)
    assert len(records)==63 and sum(len(r["proposed_cases"]) for r in records)==630
    ready=[(r,e) for r in records for e in r["proposed_cases"] if "prescription" in e]
    if not args.execute:print(json.dumps({"numerically_specified":len(ready),"remaining_design_work":630-len(ready),"executed":0}));return
    raise SystemExit("Batch execution is intentionally locked until the complete design phase is resolved. No solver launched.")


if __name__=="__main__":main()
