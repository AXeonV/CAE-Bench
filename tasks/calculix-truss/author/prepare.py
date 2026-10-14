"""Repackage a published CalculiX truss regression; no solver runs."""
from pathlib import Path
import json
import argparse
import shutil
import sys
import tarfile
import numpy as np
import gmsh
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"src"))
from utils.authoring.fetch import fetch,load_manifest
from caeoj.sdk import load_problem,load_result

def field(array,quantity,location,kind,unit,value_kind):
    return {"array":array,"quantity":quantity,"location":location,"time_axis":"steady",
            "dtype":"float64","kind":kind,"component_shape":[3] if kind=="vector" else [1],
            "components":["x","y","z"] if kind=="vector" else ["value"],
            "unit":unit,"value_kind":value_kind}

def write_mesh(path,nodes,bars,coords):
    gmsh.initialize([],readConfigFiles=False)
    try:
        gmsh.option.setNumber("General.Terminal",0)
        gmsh.model.add("released-truss")
        for tag,coord in zip(nodes,coords):
            gmsh.model.addDiscreteEntity(0,int(tag))
            gmsh.model.mesh.addNodes(0,int(tag),[int(tag)],coord.tolist())
        for i,(bar,a,b) in enumerate(zip(bars,nodes[:-1],nodes[1:]),1):
            gmsh.model.addDiscreteEntity(1,i,[int(a),int(b)])
            gmsh.model.mesh.addElementsByType(i,1,[int(bar)],[int(a),int(b)])
        gmsh.option.setNumber("Mesh.MshFileVersion",4.1)
        gmsh.option.setNumber("Mesh.Binary",0)
        gmsh.write(str(path))
    finally:gmsh.finalize()

def prepare(cache=None, mode="sample", cases=(), allow_all=False):
    task=Path(__file__).resolve().parent.parent
    known = {"source-001","source-002"}
    if mode == "all" and not allow_all: raise ValueError("all requires --allow-all")
    if mode == "selected" and not cases: raise ValueError("selected requires --case")
    if mode != "selected" and cases: raise ValueError("--case requires selected mode")
    if set(cases)-known: raise ValueError("Unknown case ID")
    chosen = known if mode == "all" else set(cases) if mode == "selected" else {"source-001"}

    report=fetch(load_manifest(task/"author/source-manifest.json"),
                 cache or ROOT/"runs/authoring-cache/calculix-truss")
    with tarfile.open(report["sources"][0]["path"],"r:bz2") as archive:
        base="./CalculiX/ccx_2.20/test/"
        texts={}
        for name in ("truss.inp","truss.dat.ref"):
            member=archive.getmember(base+name)
            if not member.isfile() or member.size>100000:raise ValueError("Unexpected tar member")
            texts[name]=archive.extractfile(member).read().decode("ascii")
    inp=texts["truss.inp"]
    for pin in ("1, 0, 0, 0","2, 5, 0, 5","3, 0, 0, 10",
                "1,1,2","2,2,3","1E7,.3",".0625","2,1,1."):
        if pin not in inp:raise ValueError("Released deck changed")
    rows=[]
    for line in texts["truss.dat.ref"].splitlines():
        parts=line.split()
        if len(parts)==8:rows.append([float(x) for x in parts])
    rows=np.array(rows,dtype=np.float64)
    if rows.shape!=(16,8):raise ValueError("Unexpected stress output")
    coords=np.array([[0.,0.,0.],[5.,0.,5.],[0.,0.,10.]])
    values=[]
    checks={}
    for e in (1,2):
        subset=rows[rows[:,0]==e]
        if not np.array_equal(subset[:,1],np.arange(1,9)):raise ValueError("Missing source GP")
        tang=coords[e]-coords[e-1];tang/=np.linalg.norm(tang)
        projections=[]
        for row in subset:
            xx,yy,zz,xy,xz,yz=row[2:]
            tensor=np.array([[xx,xy,xz],[xy,yy,yz],[xz,yz,zz]])
            projections.append(float(tang@tensor@tang))
        if not np.allclose(projections,projections[0],rtol=0,atol=1e-12):
            raise ValueError("Source integration-point axial values differ")
        values.append(projections[0])
        checks[str(e)]={"integration_points":8,"max_projection_difference":float(
            np.max(np.abs(np.array(projections)-projections[0]))),
            "selection":"first published GP; no averaging or interpolation"}
    for name,nodes,bars,mesh_name in (
        ("source-001",np.array([1,2,3],dtype=np.int64),np.array([1,2],dtype=np.int64),"mesh.msh"),
        ("source-002",np.array([10,20,30],dtype=np.int64),np.array([101,202],dtype=np.int64),"renumbered.msh")):
        if name not in chosen: continue
        case=task/"cases"/name;case.mkdir(parents=True,exist_ok=True)
        write_mesh(case/mesh_name,nodes,bars,coords)
        arrays={"node_ids":nodes,"bar_ids":bars,"support_ids":nodes[[0,2]],
                "roller_ids":nodes[[1]],"load_ids":nodes[[1]],
                "times":np.array([1.0]),"applied_force":np.array([[[1.,0.,0.]]])}
        np.savez(case/"input.npz",**arrays)
        locations={key:{"kind":"mesh","mesh":"main","entity":"node","ids":ids}
            for key,ids in (("nodes","node_ids"),("supports","support_ids"),
                            ("roller","roller_ids"),("loaded","load_ids"))}
        locations["bars"]={"kind":"mesh","mesh":"main","entity":"element","dimension":1,"ids":"bar_ids"}
        problem={"task":"calculix-truss","spatial_dimension":3,"data_file":"input.npz",
            "geometries":{},"meshes":{"main":{"file":mesh_name}},"locations":locations,
            "time_axes":{"steady":"times"},"fields":{"applied_force":field(
                "applied_force","force","loaded","vector","N","point")},
            "outputs":{"axial_stress":field("axial_stress","axial_stress","bars","scalar","Pa","average")},
            "physics":{"model":"linear_axial_truss","parameters":{
                "young_modulus":{"value":1e7,"unit":"Pa"},
                "cross_section_area":{"value":.0625,"unit":"m2"},
                "poisson_ratio":{"value":.3,"unit":"1"}}},
            "conditions":[{"role":"boundary","variable":"displacement","location":"supports",
                 "operator":"all_components_dirichlet","data":{"value":{"value":0.,"unit":"m"}}},
                {"role":"boundary","variable":"displacement","location":"roller",
                 "operator":"y_dirichlet","data":{"value":{"value":0.,"unit":"m"}}},
                {"role":"source","variable":"displacement","location":"loaded",
                 "operator":"nodal_force","data":{"force":{"field":"applied_force"}}}]}
        (case/"problem.json").write_text(json.dumps(problem,indent=2)+"\n")
        ref=task/"reference"/name/"reference.npz";ref.parent.mkdir(parents=True,exist_ok=True)
        np.savez(ref,bar_ids=bars,times=arrays["times"],axial_stress=np.array(values)[None,:,None])
        load_result(load_problem(case/"problem.json"),ref)
    if "source-001" in chosen:
        sample=task/"samples/source-001"
        (sample/"input").mkdir(parents=True,exist_ok=True);(sample/"output").mkdir(parents=True,exist_ok=True)
        for name in ("problem.json","input.npz","mesh.msh"):
            shutil.copyfile(task/"cases/source-001"/name,sample/"input"/name)
        shutil.copyfile(task/"reference/source-001/reference.npz",sample/"output/result.npz")
        load_result(load_problem(sample/"input/problem.json"),sample/"output/result.npz")
    for name,key,value in (("material-variant","young_modulus",2e7),("force-variant",None,2.)):
        pending=task/"author/pending"/name;pending.mkdir(parents=True,exist_ok=True)
        source=task/"cases"/sorted(chosen)[0]
        p=json.loads((source/"problem.json").read_text())
        with np.load(source/"input.npz") as data:a={k:data[k].copy() for k in data.files}
        if key:p["physics"]["parameters"][key]["value"]=value
        else:a["applied_force"][0,0,0]=value
        mesh_file=p["meshes"]["main"]["file"]
        for old_mesh in ("mesh.msh", "renumbered.msh"):
            if old_mesh != mesh_file: (pending/old_mesh).unlink(missing_ok=True)
        shutil.copyfile(source/mesh_file,pending/mesh_file)
        (pending/"problem.json").write_text(json.dumps(p,indent=2)+"\n")
        np.savez(pending/"input.npz",**a);load_problem(pending/"problem.json")
        (pending/"status.json").write_text(json.dumps({"status":"pending_reference",
            "reason":"Modified model has no published reference; excluded from cases",
            "solver_executed":False},indent=2)+"\n")
    report.update({"mode":mode,"generated_cases":sorted(chosen),"cases":len(chosen),"samples":int("source-001" in chosen),"pending_inputs":2,"source_members_bytes":{
        "truss.inp":len(inp),"truss.dat.ref":len(texts["truss.dat.ref"])},"projection_checks":checks,
        "reference_status":"source_extracted_projection","solver_executed":False,
        "interpolation":False,"validation":"generated cases and pending inputs valid; sample checked when selected",
        "units":"OJ declares consistent SI interpretation; source deck itself has no unit declaration",
        "license_status":"source data redistribution unconfirmed; draft remains blocked"})
    (task/"author/preparation-report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report))
if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode",choices=("sample","selected","all"),default="sample")
    parser.add_argument("--case","--cases",action="append",default=[])
    parser.add_argument("--allow-all",action="store_true")
    parser.add_argument("--cache")
    args=parser.parse_args()
    prepare(args.cache,args.mode,args.case,args.allow_all)

