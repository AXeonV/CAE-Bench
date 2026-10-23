"""Independent closed-simplex projection by enumerating active barycentric supports.
Validation only; formal reference must be produced by the pinned actual preCICE library.
"""
from itertools import combinations
import numpy as np


def affine_weights(vertices, point):
    # Orthogonal projection onto affine hull in independent coordinates.
    if len(vertices)==1:return np.ones(1)
    basis=(vertices[1:]-vertices[0]).T
    tail=np.linalg.lstsq(basis,point-vertices[0],rcond=None)[0]
    return np.r_[1-tail.sum(),tail]


def evaluate(payload):
    xyz=np.asarray(payload['vertices'],float)
    values=np.asarray(payload['values'],float)
    dim=payload['dimension'];output=[]
    primitives=[[i] for i in range(len(xyz))]+payload['edges']
    if dim==3:primitives+=payload['triangles']
    cells=payload['triangles'] if dim==2 else payload['tetrahedra']
    for point in np.asarray(payload['queries'],float):
        inside=[]
        if payload['mode']=='cell':
            for cell in cells:
                coeff=affine_weights(xyz[cell],point)
                if coeff.min()>=-1e-12 and np.linalg.norm(coeff@xyz[cell]-point)<1e-11:
                    w=np.zeros(len(xyz));w[cell]=coeff;inside.append(w)
        candidates=[]
        if inside:
            candidates=[(0.,w) for w in inside]
        else:
            for primitive in primitives:
                # Every face is an active-set candidate, including vertices.
                for count in range(1,len(primitive)+1):
                    for support in combinations(primitive,count):
                        support=list(support);coeff=affine_weights(xyz[support],point)
                        if coeff.min() < -1e-12:continue
                        w=np.zeros(len(xyz));w[support]=coeff
                        candidates.append((float(np.linalg.norm(w@xyz-point)),w))
        distance,w=min(candidates,key=lambda item:item[0])
        # Distinct weights at equal minimum are intentionally outside the dataset.
        for other_distance,other_w in candidates:
            if abs(other_distance-distance)<1e-10 and not np.allclose(other_w,w,atol=1e-10,rtol=0):
                raise ValueError('Ambiguous equal-distance node weights')
        output.append({'point':(w@xyz).tolist(),'distance':distance,'weights':w.tolist(),'value':(w@values).tolist()})
    return output

if __name__=='__main__':
    import json,sys
    print(json.dumps(evaluate(json.load(open(sys.argv[1]))),indent=2))
