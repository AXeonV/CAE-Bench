"""Read native final coupled termination per step; not an accuracy check."""
import json
import math
import re

def assess(job):
    plan=json.loads((job/'parallel-numerical-plan.json').read_text())
    log=(job/'solver.log').read_text(errors='replace')
    steps=re.split(r'Time:\s*\d+/\d+:[^\n]*',log)[1:]
    bad=[];peak=0.
    for i,part in enumerate(steps):
        last={}
        for it,norm,rel,name in re.findall(r'ComputeChange:\s+SS \(ITER=\s*(\d+)\) \(NRM,RELC\): \(\s*(\S+)\s+(\S+)\s*\) :: ([^\n]+)',part):
            last[name.strip()]=float(rel.replace('D','E'))
        if not {'navier-stokes','heat equation'}.issubset(last) or any(not math.isfinite(v) or v<0 or v>1e-6 for v in last.values()):bad.append(i+1)
        peak=max(peak,*last.values()) if last else peak
    complete=len(steps)==plan['native_time_steps'] and not bad and 'ELMER SOLVER FINISHED AT:' in log
    return {'native_coupled_termination_complete':complete,'expected_steps':plan['native_time_steps'],'observed_steps':len(steps),'bad_final_coupled_steps':bad,'maximum_final_relative_change':peak,'threshold':1e-6,'scope':'Native termination bookkeeping only. Inner iteration caps followed by converged outer coupling do not reject the final step. No spatial/time/statistical accuracy verification.'}
