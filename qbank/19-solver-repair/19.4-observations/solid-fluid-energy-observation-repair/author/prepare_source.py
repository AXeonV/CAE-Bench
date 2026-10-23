"""Verify/reproduce the exact upstream new observer files; never fabricate a baseline stub."""
import argparse,hashlib,json
from pathlib import Path
TASK=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--download-upstream',action='store_true');ap.add_argument('--proxy');args=ap.parse_args();record=json.loads((TASK/'author/data-evidence/target-source-versions.json').read_text())
 for name,item in record['files'].items():
  path=TASK/'author/generated'/name
  if args.download_upstream:
   import httpx
   section='src' if name.endswith('.C') else 'include';url=f'https://raw.githubusercontent.com/idaholab/moose/{record["exact_pr_head"]}/modules/navier_stokes/{section}/postprocessors/{name}'
   with httpx.Client(proxy=args.proxy,timeout=90,follow_redirects=True) as client:r=client.get(url);r.raise_for_status();data=r.content
   if hashlib.sha256(data).hexdigest()!=item['reference']:raise ValueError('Wrong pinned source bytes')
   if path.exists() and path.read_bytes()!=data:raise ValueError('Refuse to overwrite changed reference')
   path.write_bytes(data)
  assert hashlib.sha256(path.read_bytes()).hexdigest()==item['reference'];print(name,item['reference'])
if __name__=='__main__':main()
