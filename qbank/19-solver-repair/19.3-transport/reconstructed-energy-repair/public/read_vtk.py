from pathlib import Path
import numpy as np
def read(path):
 tokens=Path(path).read_text().split();i=tokens.index('POINTS');n=int(tokens[i+1]);coords=np.array(tokens[i+3:i+3+3*n],float).reshape(n,3);i=tokens.index('POINT_DATA')+2;arrays={}
 while i<len(tokens):
  kind=tokens[i];name=tokens[i+1]
  if kind=='SCALARS':c=int(tokens[i+3]);i+=6
  elif kind=='VECTORS':c=3;i+=3
  else:raise ValueError(tokens[i:i+5])
  arrays[name]=np.array(tokens[i:i+n*c],float).reshape(n,c);i+=n*c
 return coords,arrays
