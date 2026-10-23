"""Verify unmodified DOLFINx and dependency archives and the genuine PR header."""
import argparse,hashlib,importlib.util,json,shutil,tarfile
from pathlib import Path
import httpx

TASK=Path(__file__).resolve().parents[1]
BASE='2d6d22a8c2cc9d3488f8910238e9740c6247f83b'
HEAD='56977f3dd3e9a0418306f4c6a1d591693dc66457'
SOURCES=[
 ('dolfinx',BASE,'13a7287d9066e807a2e1578977f0c637a746409448eee0debf5ee10332ec2f91'),
 ('basix','0005e60fe56c8ff6e7436dc6c7ddba677e408b43','f87c146f085ec1a0e4457d59e040a9fa7c717551012f7f3eeffa860dddc641a3'),
 ('ffcx','76744fe1e6de4aad30f8d3db3dd5f57562472924','acdfcd1e5829a3dd85a6af781185cea4fcef5021d9a048987ebfb802d8adf097')]
HEADER_SHA='44cee2d91b2400ce193c6a93879884cdf6aaec06c343b3c36718590b6fb7b4eb'
HEADER_BLOB='b14ab337c22c5ba4d4516ab59913a91753e718eb'
LINKS={'dolfinx':{'cpp/test/vcpkg.json':'../vcpkg.json','python/COPYING':'../COPYING',
 'python/COPYING.LESSER':'../COPYING.LESSER','python/vcpkg.json':'../cpp/vcpkg.json'},
 'basix':{'python/LICENSE':'../LICENSE','vcpkg.json':'cpp/vcpkg.json'},'ffcx':{}}

def prepare(work,proxy=None):
    work.mkdir(parents=True,exist_ok=True)
    helper=TASK.parents[1]/'19.4-observations/diffusion-element-heat-repair/author/prepare_runtime.py'
    spec=importlib.util.spec_from_file_location('repair_archive_checks',helper)
    checks=importlib.util.module_from_spec(spec);spec.loader.exec_module(checks)
    public=TASK/'public';public.mkdir(exist_ok=True)
    evidence=[]
    with httpx.Client(proxy=proxy,follow_redirects=True,timeout=120) as client:
        for repository,commit,digest in SOURCES:
            url=f'https://codeload.github.com/FEniCS/{repository}/tar.gz/{commit}'
            archive=work/(repository+'.tar.gz')
            if not archive.exists():
                response=client.get(url);response.raise_for_status();archive.write_bytes(response.content)
            if hashlib.sha256(archive.read_bytes()).hexdigest()!=digest:
                raise ValueError('Source archive mismatch: '+repository)
            unpack=work/('verified-'+repository)
            if not unpack.exists():
                unpack.mkdir()
                with tarfile.open(archive) as source:source.extractall(unpack,filter='data')
            tree=unpack/(repository+'-'+commit)
            # Windows tarfile materializes these reviewed internal links. On
            # POSIX normalize them to the identical bytes for the cache audit;
            # the distributed original archives retain all upstream links.
            for relative,link in LINKS[repository].items():
                path=tree/relative
                if path.is_symlink():
                    if path.readlink().as_posix()!=link or not path.resolve().is_relative_to(tree.resolve()):
                        raise ValueError('Changed cache link: '+relative)
                    data=path.read_bytes();path.unlink();path.write_bytes(data)
            tree_digest=checks.verify_tree(archive,tree,LINKS[repository])
            shutil.copyfile(archive,public/(repository+'-source.tar.gz'))
            evidence.append({'repository':'https://github.com/FEniCS/'+repository,'commit':commit,
              'archive_url':url,'archive_sha256':digest,'tree_manifest_sha256':tree_digest,
              'reviewed_links':LINKS[repository],
              'cache_link_representation':'Materialized identical target bytes; distributed original archive preserves links'})
        header=work/'fixed-utils.h'
        url=f'https://raw.githubusercontent.com/FEniCS/dolfinx/{HEAD}/cpp/dolfinx/geometry/utils.h'
        if not header.exists():
            response=client.get(url);response.raise_for_status();header.write_bytes(response.content)
        data=header.read_bytes()
        if hashlib.sha256(data).hexdigest()!=HEADER_SHA or hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()!=HEADER_BLOB:
            raise ValueError('Upstream reference header mismatch')
    generated=TASK/'author/generated';generated.mkdir(exist_ok=True)
    shutil.copyfile(header,generated/'utils.h')
    out=TASK/'author/data-evidence';out.mkdir(exist_ok=True)
    (out/'source.json').write_text(json.dumps({'issue':'https://github.com/FEniCS/dolfinx/issues/4450',
      'pull':'https://github.com/FEniCS/dolfinx/pull/4453','baseline':BASE,'upstream_head':HEAD,
      'merge':'700e97727b23060bd7a0a871a9478d5972c75853','sources':evidence,
      'reference_header_sha256':HEADER_SHA,'reference_header_git_blob':HEADER_BLOB,
      'reference_kind':'Exact upstream geometry/utils.h; no Python/fem wrapper changes used by the C++ driver'},indent=2)+'\n',encoding='utf-8')
    return work/'verified-dolfinx'/('dolfinx-'+BASE)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--work',type=Path,required=True);parser.add_argument('--proxy')
    args=parser.parse_args();print(prepare(args.work,args.proxy))
