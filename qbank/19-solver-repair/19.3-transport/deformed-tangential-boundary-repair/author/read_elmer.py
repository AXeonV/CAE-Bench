"""Read native ElmerPost nodal results at mesh-embedded probes, no interpolation."""
from pathlib import Path
import json,math,sys
w=Path(sys.argv[1]); lines=(w/'mesh/flow.ep').read_text().splitlines();n=int(lines[0].split()[0])
coords=[[float(v) for v in l.split()] for l in lines[2:2+n]]
start=next(i for i,l in enumerate(lines) if l.startswith('#time'))+1
values=[[float(v) for v in l.split()] for l in lines[start:start+n]]
# Native ASCII result retains full precision, unlike the 8-digit ElmerPost field.
# Its explicit permutation maps node identity to stored scalar DOFs.
res=(w/'mesh/flow.result').read_text().splitlines();perm=None;fields={}
for label in ['velocity 1','velocity 2','pressure']:
 at=next(i for i,l in enumerate(res) if l.strip()==label)+1
 if 'use previous' not in res[at]:
  nn=int(res[at].split()[1]);table=[list(map(int,l.split())) for l in res[at+1:at+1+nn]]
  perm={node:idx for node,idx in table};at+=1+nn
 else:at+=1
 raw=[float(l) for l in res[at:at+n]]
 # Elmer ModelDescription::SaveResult writes Var%Values(Perm(i)) in node i
 # order, not in equation order (fixed source lines4029..4035).
 if sorted(perm)!=list(range(1,n+1)):raise ValueError('Expected fully active nodal scalar field')
 fields[label]=raw
for j in range(n):
 if max(abs(values[j][k]-fields['velocity '+str(k+1)][j]) for k in (0,1))>2e-7:raise ValueError('Native result permutation disagrees with native ElmerPost velocity')
 values[j]=[fields['velocity 1'][j],fields['velocity 2'][j],0.,fields['pressure'][j]]
lookup={tuple(round(v,6) for v in p):i for i,p in enumerate(coords)}
total=length=0.
for s in (l.split() for l in lines if l.startswith('Constraint3 ')):
 if int(s[1]) in (202,203):
  a,b=(int(t) for t in s[2:4]);pa,pb=coords[a],coords[b];ds=math.dist(pa,pb)
  if int(s[1])==203:
   mid=int(s[4]);total+=ds*(values[a][3]+values[b][3]+4*values[mid][3])/6
  else:total+=ds*(values[a][3]+values[b][3])/2
  length+=ds
mean=total/length
probes=json.loads((w/'probes.json').read_text());sample=[]
for p in probes:
 i=min(range(n),key=lambda j:math.dist(coords[j],p+[0.]))
 if math.dist(coords[i],p+[0.])>1e-8:raise ValueError('Embedded probe identity not recovered from native mesh')
 sample.append({'point':p,'velocity':values[i][:2],'pressure':values[i][3]-mean})
report={'nodes':n,'surface_pressure_mean_removed':mean,'samples':sample}
(w/'native-probe-values.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

