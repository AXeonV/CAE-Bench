"""Copy actual public example answers and archive completed genuine replay evidence."""
import argparse,json,shutil
from pathlib import Path
TASK=Path(__file__).resolve().parents[1]
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--dataset',required=True,type=Path);a=p.parse_args();cases=sorted((a.dataset/'cases').iterdir())
 for i,case in enumerate(cases[:2],1):
  sample=a.dataset/'samples'/f'{i:02d}';shutil.copytree(case,sample/'input',dirs_exist_ok=True);shutil.copytree(a.dataset/'reference'/case.name,sample/'reference',dirs_exist_ok=True);(sample/'output').mkdir(parents=True,exist_ok=True);shutil.copyfile(sample/'reference/reference.h5',sample/'output/result.h5')
 for source,target in [('catalog.json','cases.json'),('reference-report.json','reference-replay.json'),('defect-report.json','defect-replay.json')]:
  if (a.dataset/source).exists():shutil.copyfile(a.dataset/source,TASK/'author/data-evidence'/target)
