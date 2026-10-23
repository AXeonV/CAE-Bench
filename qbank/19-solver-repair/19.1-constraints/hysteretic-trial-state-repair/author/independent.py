import numpy as np
EPS=np.finfo(float).eps
CHECKPOINTS=('committed','returned','accepted','continued','rolled_back','reset')
def envelope(e,pos,neg):
    if e==0:return 0.,pos[0][0]/pos[0][1]
    points=pos if e>0 else neg
    f0=x0=0.
    for f,x in points:
        slope=(f-f0)/(x-x0)
        if abs(e)<=abs(x):return f0+slope*(e-x0),slope
        f0,x0=f,x
    return f+slope*(e-x),slope

def reference(program):
    pos,neg=program['positive'],program['negative'];e=stress=energy=0.;tangent=pos[0][0]/pos[0][1]
    def step(target):
        nonlocal e,stress,tangent,energy
        if abs(target-e)<EPS:return
        s,k=envelope(target,pos,neg)
        energy+=.5*(stress+s)*(target-e);e,stress,tangent=target,s,k
    for target in program['history']:step(target)
    committed=[e,stress,tangent,energy]
    step(e+program['delta']);returned=[e,stress,tangent,energy]
    # getEnergy exposes committed work: before commit it remains its old value.
    observed_return=[e,stress,tangent,committed[3]]
    for target in program['continuation']:step(target)
    continued=[e,stress,tangent,energy]
    return np.array([committed,observed_return,returned,continued,continued,[0.,0.,pos[0][0]/pos[0][1],0.]])

def serialize(programs):
    lines=[str(len(programs))]
    for p in programs:
        lines.append(' '.join(map(str,[p['kind'],len(p['positive']),len(p['negative']),*p['pinch'],p['beta']])))
        for side in ('positive','negative'):lines.append(' '.join(format(x,'.17g') for pair in p[side] for x in pair))
        for key in ('history','probes'):lines.append(' '.join([str(len(p[key])),*[format(x,'.17g') for x in p[key]]]))
        lines.append(format(p['delta'],'.17g'))
        lines.append(' '.join([str(len(p['continuation'])),*[format(x,'.17g') for x in p['continuation']]]))
        lines.append(format(p['rollback_probe'],'.17g'))
    return '\n'.join(lines)+'\n'
