"""Independent geometry checks only; actual DOLFINx produces formal references."""
from itertools import combinations
import numpy as np

def weights(vertices,point):
    if len(vertices)==1:return np.ones(1)
    tail=np.linalg.lstsq((vertices[1:]-vertices[0]).T,point-vertices[0],rcond=None)[0]
    return np.r_[1-tail.sum(),tail]

def closed_distance(vertices,point):
    candidates=[]
    for count in range(1,len(vertices)+1):
        for indices in combinations(range(len(vertices)),count):
            face=vertices[list(indices)];w=weights(face,point)
            if w.min()>=-1e-12:candidates.append(np.linalg.norm(w@face-point))
    return float(min(candidates))

def evaluate(payload):
    xyz=np.asarray(payload['vertices']);cells=payload['cells'];labels=payload['cell_ids']
    output=[];audit=[]
    for point in np.asarray(payload['queries']):
        containing=[];candidates=[];distances=[]
        for i,cell in enumerate(cells):
            vertices=xyz[cell];w=weights(vertices,point)
            distance=closed_distance(vertices,point);distances.append(distance)
            if w.min()>=-1e-12 and np.linalg.norm(w@vertices-point)<1e-11:containing.append(i)
            if np.all(point>=vertices.min(axis=0)-payload['padding']) and np.all(point<=vertices.max(axis=0)+payload['padding']):candidates.append(i)
        assert len(containing)<=1,'Query has ambiguous containment'
        if not containing:assert min(distances)>=1e-5,'Query is too close to a closed cell'
        selected=containing[0] if containing else None
        if not containing and payload['mode']!=0 and candidates:
            ordered=sorted(candidates,key=lambda i:distances[i]);selected=ordered[0]
            if len(ordered)>1:assert distances[ordered[1]]-distances[ordered[0]]>=1e-6,'Ambiguous closest cell'
        output.append({'owned':int(selected is not None),'cell_id':-1 if selected is None else labels[selected],
                       'distance':-1. if selected is None else (0. if containing else distances[selected])})
        audit.append({'containing_cells':[labels[i] for i in containing],'bbox_candidates':[labels[i] for i in candidates],
                      'all_cell_distances':distances})
    return output,audit
