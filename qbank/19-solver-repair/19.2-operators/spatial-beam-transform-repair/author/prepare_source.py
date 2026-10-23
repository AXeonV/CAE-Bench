"""Record exact upstream versions and mechanically apply upstream patch."""
import argparse,hashlib,json,pathlib,tarfile,urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[5]
WORK=ROOT/'work/repair-22/kratos-14657'
TASK=pathlib.Path(__file__).resolve().parents[1]
BASE='f4b2e970ede622ab54548c0661637f90e5ddd419'
SOURCE=WORK/('Kratos-'+BASE)
FILE='applications/StructuralMechanicsApplication/custom_elements/beam_elements/timoshenko_beam_element_3D2N.cpp'

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--proxy');args=parser.parse_args()
    WORK.mkdir(parents=True,exist_ok=True)
    archive=WORK/'baseline.tar.gz'
    if not archive.exists():
        url='https://codeload.github.com/KratosMultiphysics/Kratos/tar.gz/'+BASE
        handler=urllib.request.ProxyHandler({'https':args.proxy}) if args.proxy else urllib.request.ProxyHandler()
        with urllib.request.build_opener(handler).open(url,timeout=180) as response:archive.write_bytes(response.read())
    if digest(archive)!='86645b7c917075fe88ccb569c7f18f720f3e90d4d015d72b4b706465e78dcc90':raise ValueError('Fixed upstream archive digest mismatch')
    if not SOURCE.exists():
        with tarfile.open(archive) as tar:tar.extractall(WORK,filter='data')
    original=(SOURCE/FILE).read_text(encoding='utf-8')
    fixed=original.replace('prod(rLHS, trans(global_size_T))','prod(rLHS, global_size_T)').replace('prod(global_size_T, aux_product)','prod(trans(global_size_T), aux_product)').replace('prod(global_size_T, local_rhs)','prod(trans(global_size_T), local_rhs)')
    directory=TASK/'author/generated';directory.mkdir(exist_ok=True)
    (directory/'upstream-fixed.cpp').write_text(fixed,encoding='utf-8',newline='\n')
    upstream=WORK/'upstream-head.cpp'
    if not upstream.exists():
        url='https://raw.githubusercontent.com/KratosMultiphysics/Kratos/e7976668c8904bd29b8bb3a51ab5a0db38322422/'+FILE
        handler=urllib.request.ProxyHandler({'https':args.proxy}) if args.proxy else urllib.request.ProxyHandler()
        with urllib.request.build_opener(handler).open(url,timeout=180) as response:upstream.write_bytes(response.read())
    if upstream.read_bytes()!=(directory/'upstream-fixed.cpp').read_bytes():raise ValueError('Mechanical upstream patch does not equal pinned head source')
    supplemented=fixed.replace('if (j == 1) { // the y rotation','if (i == 1) { // the local y rotation')
    assert supplemented!=fixed
    assert supplemented.count('GetCrossArea()')==2
    supplemented=supplemented.replace('GetCrossArea()', 'r_props[CROSS_AREA]')
    (directory/'minimal-fixed.cpp').write_text(supplemented,encoding='utf-8',newline='\n')
    (directory/'timoshenko_beam_element_3D2N.cpp').write_text(supplemented,encoding='utf-8',newline='\n')
    record={'repository':'https://github.com/KratosMultiphysics/Kratos','issue':14657,'pull_request':14680,
            'baseline':BASE,'upstream_head':'e7976668c8904bd29b8bb3a51ab5a0db38322422','merge_commit':'8d03e8af0785ec33bb522826a75cad8d828eb74c',
            'archive_sha256':digest(WORK/'baseline.tar.gz'),'source_file':FILE,
            'baseline_source_sha256':digest(SOURCE/FILE),'upstream_fixed_sha256':digest(directory/'upstream-fixed.cpp'),
            'actual_head_source_sha256':digest(upstream),'mechanical_patch_matches_actual_head':True,
            'supplemented_source_sha256':digest(directory/'minimal-fixed.cpp'),
            'supplement':'Author additions: internal local y-angle sign acts as row D R, not column R D; both 3D body-force integrations read CROSS_AREA directly instead of inherited 2D thickness dispatch. Actual replay evidence recorded separately.',
            'applied_upstream_changes':'Six product expressions in RotateLHS, RotateRHS, RotateAll; test expectation changes excluded.'}
    (TASK/'author/data-evidence/source.json').write_text(json.dumps(record,indent=2)+'\n')
if __name__=='__main__':main()






