"""Extract the published COMSOL values verbatim; no solver or interpolation."""
from pathlib import Path
import json
import argparse
import shutil
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from utils.authoring.fetch import fetch, load_manifest
from caeoj.sdk import load_problem, load_result

def prepare(cache=None, mode="sample", cases=(), allow_all=False):
    task = Path(__file__).resolve().parent.parent
    known = {"source-001","source-002","source-003"}
    if mode == "all" and not allow_all: raise ValueError("all requires --allow-all")
    if mode == "selected" and not cases: raise ValueError("selected requires --case")
    if mode != "selected" and cases: raise ValueError("--case requires selected mode")
    if set(cases)-known: raise ValueError("Unknown case ID")
    chosen = known if mode == "all" else set(cases) if mode == "selected" else {"source-001"}

    manifest = load_manifest(task / "author/source-manifest.json")
    report = fetch(manifest, cache or ROOT / "runs/authoring-cache/pinnacle-poisson-cg")
    raw = Path(report["sources"][0]["path"])
    rows = np.loadtxt(raw, comments="%", dtype=np.float64)
    if rows.shape != (1246, 3) or not np.isfinite(rows).all():
        raise ValueError("Unexpected released COMSOL table")
    times = np.array([0.0], dtype=np.float64)
    params = {key:{"value":value,"unit":"m"} for key,value in
              {"x_min":-.5,"x_max":.5,"y_min":-.5,"y_max":.5}.items()}
    for i,(x,y) in enumerate([(-.3,-.3),(-.3,.3),(.3,-.3),(.3,.3)],1):
        for name,value in (("x",x),("y",y),("r",.1)):
            params[f"hole_{i}_{name}"]={"value":value,"unit":"m"}
    params.update({key:{"value":value,"unit":"1"} for key,value in
                   {"outer_value":1.0,"inner_value":0.0}.items()})
    field={"array":"state","quantity":"dimensionless_potential","location":"observations",
           "time_axis":"steady","dtype":"float64","kind":"scalar","component_shape":[1],
           "components":["value"],"unit":"1","value_kind":"point"}
    problem={"task":"pinnacle-poisson-cg","spatial_dimension":2,"data_file":"input.npz",
             "geometries":{},"meshes":{},"locations":{"observations":{"kind":"points",
             "ids":"probe_ids","coordinates":"probe_coordinates"}},"time_axes":{"steady":"times"},
             "fields":{},"outputs":{"state":field},"conditions":[],
             "physics":{"model":"laplace_square_four_holes","parameters":params}}
    selections = {"source-001":np.arange(0,64), "source-002":np.arange(64,655),
                  "source-003":np.arange(655,1246)}
    for name, indices in selections.items():
        if name not in chosen: continue
        case = task / "cases" / name
        case.mkdir(parents=True,exist_ok=True)
        ids = indices.astype(np.int64)
        np.savez(case/"input.npz",probe_ids=ids,probe_coordinates=rows[indices,:2],times=times)
        (case/"problem.json").write_text(json.dumps(problem,indent=2)+"\n",encoding="utf-8")
        reference = task/"reference"/name/"reference.npz"
        reference.parent.mkdir(parents=True,exist_ok=True)
        np.savez(reference,probe_ids=ids,times=times,state=rows[indices,2][None,:,None])
        load_result(load_problem(case/"problem.json"),reference)
    if "source-001" in chosen:
        sample = task/"samples/source-001"
        (sample/"input").mkdir(parents=True,exist_ok=True)
        (sample/"output").mkdir(parents=True,exist_ok=True)
        for name in ("problem.json","input.npz"):
            shutil.copyfile(task/"cases/source-001"/name,sample/"input"/name)
        shutil.copyfile(task/"reference/source-001/reference.npz",sample/"output/result.npz")
        load_result(load_problem(sample/"input/problem.json"),sample/"output/result.npz")
    pending=task/"author/pending/radius-variant"
    pending.mkdir(parents=True,exist_ok=True)
    pending_problem=json.loads(json.dumps(problem))
    pending_problem["physics"]["parameters"]["hole_1_r"]["value"]=0.11
    (pending/"problem.json").write_text(json.dumps(pending_problem,indent=2)+"\n")
    # Interior independent locations; no reference is supplied for this modified PDE.
    coords=np.array([[0.,0.],[.1,0.],[0.,.1]],dtype=np.float64)
    np.savez(pending/"input.npz",probe_ids=np.arange(3,dtype=np.int64),
             probe_coordinates=coords,times=times)
    load_problem(pending/"problem.json")
    (pending/"status.json").write_text(json.dumps({"status":"pending_reference",
        "reason":"Changed radius has no published source output; excluded from scored cases",
        "solver_executed":False},indent=2)+"\n")
    report.update({"mode":mode,"generated_cases":sorted(chosen),"cases":len(chosen),"samples":int("source-001" in chosen),"case_rows":{k:len(v) for k,v in selections.items() if k in chosen},"source_rows":1246,"pending_inputs":1,
        "reference_status":"source_extracted","solver_executed":False,"interpolation":False,
        "validation":"generated cases and pending input structure valid; sample checked when selected",
        "source_publicly_accessible":True,"confidential_benchmark":False})
    (task / "author/preparation-report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report))
if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode",choices=("sample","selected","all"),default="sample")
    parser.add_argument("--case","--cases",action="append",default=[])
    parser.add_argument("--allow-all",action="store_true")
    parser.add_argument("--cache")
    args=parser.parse_args()
    prepare(args.cache,args.mode,args.case,args.allow_all)

