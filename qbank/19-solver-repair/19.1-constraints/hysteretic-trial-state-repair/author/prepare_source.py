"""Fetch pinned upstream source and verify the complete two-file upstream patch."""
import argparse,hashlib,json,tarfile,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
TASK=Path(__file__).resolve().parents[1]
WORK=ROOT/'work/repair-22/opensees-1817'
BASE='915a5d0eb862010868ee88706e4381e478724c9e'
HEAD='e9a890ef7e8be7873faf1fc91554e7dbc3b8a647'
SOURCE=WORK/('OpenSees-'+BASE)
NAMES=('HystereticMaterial','HystereticSMMaterial')
ARCHIVE_SHA='32cc8c481196d35441852caefdeba5cf97df42e63aa2a5258f349c7b788bfb14'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def patch(data):
    token=b'if (fabs(dStrain) < DBL_EPSILON)'
    assert data.count(token)==1
    start=data.index(token);i=data.index(b'return 0;',start)
    return data[:i]+b'return this->revertToLastCommit();'+data[i+9:]
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--proxy');args=parser.parse_args()
    WORK.mkdir(parents=True,exist_ok=True)
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({'https':args.proxy}) if args.proxy else urllib.request.ProxyHandler())
    def fetch(url,path):
        if not path.exists():
            with opener.open(url,timeout=180) as response:path.write_bytes(response.read())
    archive=WORK/'baseline.tar.gz';fetch('https://codeload.github.com/OpenSees/OpenSees/tar.gz/'+BASE,archive)
    if sha(archive)!=ARCHIVE_SHA:raise ValueError('Pinned upstream archive digest mismatch')
    if not SOURCE.exists():
        with tarfile.open(archive) as tar:tar.extractall(WORK,filter='data')
    generated=TASK/'author/generated';generated.mkdir(exist_ok=True)
    records=[]
    for name in NAMES:
        rel='SRC/material/uniaxial/'+name+'.cpp';original=SOURCE/rel;upstream=WORK/(name+'-upstream.cpp')
        fetch('https://raw.githubusercontent.com/OpenSees/OpenSees/'+HEAD+'/'+rel,upstream)
        fixed=patch(original.read_bytes())
        if fixed!=upstream.read_bytes():raise ValueError('Mechanical patch differs from pinned head: '+name)
        (generated/(name+'.cpp')).write_bytes(fixed)
        records.append({'file':rel,'baseline_sha256':sha(original),'fixed_sha256':sha(upstream),'mechanical_patch_matches_head':True})
    record={'repository':'https://github.com/OpenSees/OpenSees','issue':1817,'pull_request':1818,'baseline':BASE,'head':HEAD,'merge':'3c546b43be9b837db34083296310a60b3eb8280d','archive_sha256':ARCHIVE_SHA,'files':records,'applied_patch':'Complete upstream PR: the near-committed-strain return in both material classes restores the complete committed state; no author supplements.','original_reproducer':'Full issue bridge Tcl cached separately. Formal task adapts the root material API mechanism; no full bridge/gravity/eigen replay claim.'}
    (TASK/'author/data-evidence/source.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
if __name__=='__main__':main()
