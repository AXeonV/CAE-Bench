import argparse,os
import numpy as np
from caeoj.sdk import load_problem,write_result
p=argparse.ArgumentParser();p.add_argument('--input');p.add_argument('--output');a=p.parse_args()
assert os.getuid()==1000
assert not os.access('/tests/reference',os.R_OK)
assert not os.access('/private-materials/reference',os.R_OK)
problem=load_problem(a.input);u=problem.arrays['initial_state'][0,:,0]
s=problem.arrays['times']*problem.manifest['physics']['parameters']['velocity']['value']*len(u)
k=np.floor(s).astype(np.int64);f=s-k
value=np.asarray([(1-c)*np.roll(u,int(i))+c*np.roll(u,int(i)+1) for i,c in zip(k,f)])[...,None]
write_result(a.output,problem,{'state':value})
