"""Read the real Elmer ASCII3 scalar-node result format, preserving mesh order."""
import re
from pathlib import Path
import numpy as np

def read_result(path):
 lines=Path(path).read_text().splitlines()
 if lines[0].strip()!='ASCII 3':raise ValueError('Expected native Elmer ASCII 3')
 sizes={};i=1;nnode=None
 while i<len(lines) and not lines[i].startswith('Time:'):
  row=lines[i];m=re.match(r'(.+?)\s*:\s+(\d+)\s+(\d+)\s+(\d+)\s*:',row)
  if m:
   name,n,perms,dof=m.groups()
   if int(dof)!=1:raise ValueError('Scalar node variables required')
   sizes[name.strip()]=(int(n),int(perms))
  if 'Number Of Nodes:' in row:nnode=int(row.split(':')[-1])
  i+=1
 if not nnode or not sizes:raise ValueError('Missing result header')
 result={};frames=0;previous=None
 while i<len(lines):
  row=lines[i].strip()
  if row.startswith('Time:'):frames+=1;previous=None;i+=1;continue
  if row not in sizes:raise ValueError('Unknown result variable: '+row)
  name=row;n,perms=sizes[name];i+=1;row=lines[i].strip();i+=1
  if row=='Perm: use previous':
   if previous is None:raise ValueError('No previous permutation')
   order=previous
  else:
   m=re.fullmatch(r'Perm:\s+(\d+)\s+(\d+)',row)
   if not m:raise ValueError('Unsupported permutation representation')
   full,active=map(int,m.groups());pairs=np.array([[int(x) for x in line.split()] for line in lines[i:i+active]],dtype='int64');i+=active
   if full!=nnode or active!=nnode or n!=nnode or perms!=nnode:raise ValueError('All nodes must be active')
   if not np.array_equal(np.sort(pairs[:,0]),np.arange(1,nnode+1)) or not np.array_equal(np.sort(pairs[:,1]),np.arange(1,nnode+1)):raise ValueError('Invalid permutation')
   order=pairs[:,0]-1;previous=order
  values=np.array([float(x.replace('D','E')) for x in lines[i:i+n]]);i+=n
  if len(values)!=nnode or not np.all(np.isfinite(values)):raise ValueError('Invalid scalar field')
  field=np.empty(nnode);field[order]=values;result[name]=field
 if set(result)!=set(sizes):raise ValueError('Incomplete final fields')
 return result,frames
