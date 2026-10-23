"""Close the one documentation finding without relabeling any execution."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[3];TASK=ROOT/'qbank/19-solver-repair/19.6-waves/parallel-pml-reduction-repair'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=ROOT/'runs/harbor/tasks/parallel-pml-reduction-repair/tests/agent.zip';new=ROOT/'dist/parallel-pml-reduction-repair-agent.zip'
assert sha(old)=='9cd9a7479aaa7973194bfd5099e97fbc60f40c8133cddcce8b2e7552f54c3f39'
assert sha(new)=='22aa0bcf168c9cabd7853ec8a63e2498838968fb53aa996034cb3e48108144d7'
member=TASK.relative_to(ROOT).as_posix()+'/DATA.md'
with zipfile.ZipFile(old) as a,zipfile.ZipFile(new) as b:
    assert set(a.namelist())==set(b.namelist()) and len(a.namelist())==44
    changes=[n for n in a.namelist() if a.read(n)!=b.read(n)]
    assert set(changes)=={'MANIFEST.json',member}
    text=(TASK/'DATA.md').read_text(encoding='utf-8');assert b.read(member).decode()==text.replace('\r\n','\n')
    assert 'PML外终端z=0、800施加chi=0的齐次Dirichlet截断' in text
    assert '保存的chi旧值、chi_t及chi_tt也在该外边界置零' in text
    assert '此时四壁均为chi的齐次Neumann边界' in text and '左右边界仍为齐次Neumann' in text
    manifests={label:json.loads(z.read('MANIFEST.json')) for label,z in [('old',a),('new',b)]}
    assert {k:v for k,v in manifests['old'].items() if k!='files'}=={k:v for k,v in manifests['new'].items() if k!='files'}
    assert set(manifests['old']['files'])==set(manifests['new']['files'])
    assert [k for k in manifests['old']['files'] if manifests['old']['files'][k]!=manifests['new']['files'][k]]==[member]
    for name,digest in manifests['new']['files'].items():assert hashlib.sha256(b.read(name)).hexdigest()==digest,name
    # Store both small manifests for independent examination of package receipts.
previous=json.loads((Path(__file__).parent/'actualchecks.json').read_text())['sha256'];checked=0
for name,digest in previous.items():
    path=ROOT/name
    if name.startswith(str(TASK.relative_to(ROOT)).replace('\\','/')+'/'):
        # Windows recorded strings may contain either separator.
        pass
    rel=path.relative_to(TASK) if path.is_relative_to(TASK) else None
    if rel and (rel.parts[0] in ['cases','reference','samples','public','extension','harbor'] or rel.name in ['judge-config.json','data-manifest.json','instruction.md']):
        assert sha(path)==digest,name;checked+=1
result={'finding':'P1-PML-outer-boundary','closed':True,'new_archive_sha256':sha(new),'old_oracle_archive_sha256':sha(old),'changed_members':changes,'members':44,'workspace_DATA_sha256':sha(TASK/'DATA.md'),'unchanged_workspace_assets_checked':checked,'manifests':manifests,'basis':'fixed source pml_boundary_acoustic sets potential, old potential and both time derivatives to zero; only public DATA/MANIFEST changed; no new native execution claimed'}
(Path(__file__).parent/'bounded-closure.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='manifests'},indent=2))
