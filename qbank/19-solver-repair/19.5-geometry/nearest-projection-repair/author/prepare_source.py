"""Verify genuine source archive and prepare the smallest permitted reference edit."""
import argparse,hashlib,json,shutil,tarfile,importlib.util
from pathlib import Path
import httpx
TASK=Path(__file__).resolve().parents[1]
BASE='c2a06a65631e15a6622f5ecffae194f82ba0bae3'
ARCHIVE_SHA='fb98709cb22cde539735dc079a7979d296f603d15f249ed0f16ba778e632b81b'
URL='https://codeload.github.com/precice/precice/tar.gz/'+BASE

def prepare(work,proxy=None):
    work.mkdir(parents=True,exist_ok=True);archive=work/'source.tar.gz'
    if not archive.exists():
        with httpx.Client(proxy=proxy,follow_redirects=True,timeout=120) as client:
            response=client.get(URL);response.raise_for_status();archive.write_bytes(response.content)
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=ARCHIVE_SHA:raise ValueError('Source archive digest mismatch')
    unpack=work/'verified-source'
    if not unpack.exists():
        unpack.mkdir()
        with tarfile.open(archive) as source:source.extractall(unpack,filter='data')
    root=unpack/('precice-'+BASE)
    helper=TASK.parents[1]/'19.4-observations/diffusion-element-heat-repair/author/prepare_runtime.py'
    spec=importlib.util.spec_from_file_location('repair_archive_checks',helper)
    checks=importlib.util.module_from_spec(spec);spec.loader.exec_module(checks)
    manifest_sha=checks.verify_tree(archive,root)
    evidence=TASK/'author/data-evidence/source.json'
    evidence.write_text(json.dumps({'repository':'https://github.com/precice/precice','issue':'https://github.com/precice/precice/issues/1304','pull':'https://github.com/precice/precice/pull/1351','baseline':BASE,'upstream_head':'5f9b85d0bb1e48905f526b417abe038c36fe980e','merge':'dd16669a5bd306d59721ff8a23c11a2568b58076','archive_url':URL,'archive_sha256':ARCHIVE_SHA,'tree_manifest_sha256':manifest_sha,'reference_kind':'minimal cpp implementation of edge-vs-vertex repair plus author complete face-vs-edge comparison; no header signature changes'},indent=2)+'\n',encoding='utf-8')
    original=(root/'src/query/Index.cpp').read_text(encoding='utf-8')
    edge="""  // Pick the smallest candidate by distance
  auto min = std::min_element(candidates.begin(), candidates.end());
  if (min != candidates.end()) {
    return *min;
  }
  // Could not find edge projection element, fall back to vertex projection
  return findVertexProjection(location);"""
    triangle="""  // Pick the smallest candidate by distance
  auto min = std::min_element(candidates.begin(), candidates.end());
  if (min != candidates.end()) {
    return *min;
  }

  // Could not triangle find projection element, fall back to edge projection
  return findEdgeProjection(location, n);"""
    def replacement(lower):return """  auto closest = LOWER;
  auto min = std::min_element(candidates.begin(), candidates.end());
  if (min != candidates.end() && min->polation.distance() <= closest.polation.distance()) {
    return *min;
  }
  return closest;""".replace('LOWER',lower)
    if original.count(edge)!=1 or original.count(triangle)!=1:raise ValueError('Pinned source anchors changed')
    fixed=original.replace(edge,replacement('findVertexProjection(location)')).replace(triangle,replacement('findEdgeProjection(location, n)'))
    out=TASK/'author/generated';out.mkdir(exist_ok=True);(out/'Index.cpp').write_bytes(fixed.encode('utf-8'))
    (TASK/'public').mkdir(exist_ok=True);shutil.copyfile(archive,TASK/'public/precice-source.tar.gz')
    return root

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--work',required=True,type=Path);parser.add_argument('--proxy');args=parser.parse_args();print(prepare(args.work,args.proxy))
