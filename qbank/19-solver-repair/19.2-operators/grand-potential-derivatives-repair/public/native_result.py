"""Read actual PETSc ASCII-MATLAB residual/matrix and actual MOOSE CSV identities."""
import csv,re
import numpy as np

def residual_and_jacobian(text):
    vector=re.search(r'Vec_\w+\s*=\s*\[(.*?)\];',text,re.S)
    if vector is None:raise ValueError('Missing native PETSc residual vector')
    residual=np.fromstring(vector.group(1),sep=' ')
    marker='Hand-coded Jacobian ----------'
    if marker not in text:raise ValueError('Missing actual assembled analytic Jacobian')
    section=text.split(marker,1)[1].split('Finite difference Jacobian ----------',1)[0]
    size=re.search(r'% Size = (\d+) (\d+)',section);body=re.search(r'zzz = \[(.*?)\];',section,re.S)
    if size is None or body is None:raise ValueError('Invalid native PETSc matrix')
    n,m=map(int,size.groups());matrix=np.zeros((n,m));seen=set()
    for row in body.group(1).splitlines():
        if not row.strip():continue
        i,j,v=row.split();i=int(i)-1;j=int(j)-1
        if not 0<=i<n or not 0<=j<m or (i,j) in seen:raise ValueError('Invalid matrix row identity')
        matrix[i,j]=float(v);seen.add((i,j))
    if residual.shape!=(n,) or n!=m or not np.isfinite(residual).all() or not np.isfinite(matrix).all():raise ValueError('Invalid native FE dimensions/values')
    return residual,matrix

def csv_rows(path):
    with path.open(newline='') as stream:return list(csv.DictReader(stream))

def dof_groups(path,n,length,names):
    rows=sorted(csv_rows(path),key=lambda r:float(r['x']))
    if len(rows)!=2*n:raise ValueError('Unexpected native node count')
    groups=[];all_dofs=set()
    for i in range(n):
        pair=rows[2*i:2*i+2];expected=[3*i*length,(3*i+1)*length]
        if not np.allclose([float(r['x']) for r in pair],expected,atol=1e-12*length,rtol=1e-12):raise ValueError('Unexpected native segment coordinates')
        result={}
        for logical,actual in names.items():
            ids=[]
            for row in pair:
                value=float(row['dof_'+actual])
                if value!=int(value) or value<0 or int(value) in all_dofs:raise ValueError('Invalid actual DOF identity')
                ids.append(int(value));all_dofs.add(int(value))
            result[logical]=ids
        groups.append(result)
    return groups
