"""Pin supplementary independent solver sources and preserve licenses/hashes."""
import hashlib,json,urllib.request
from catalog import WORK

REVISION='5b171f11fd7a3e810ee7a74a4d9f2dff01d65a6e'

def main():
    out=WORK/'sources';out.mkdir(exist_ok=True);rows=[]
    for name in ('exact_solvers/euler.py','exact_solvers/burgers.py','LICENSE-CODE','LICENSE-TEXT.md','README.md'):
        url=f'https://raw.githubusercontent.com/clawpack/riemann_book/{REVISION}/{name}'
        path=out/('clawpack-'+name.replace('/','-'))
        if not path.exists():path.write_bytes(urllib.request.urlopen(url,timeout=60).read())
        rows.append(dict(url=url,file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    (out/'clawpack-manifest.json').write_text(json.dumps(dict(repository='clawpack/riemann_book',revision=REVISION,files=rows),indent=2))
    for slug,url in [('ngsolve-navierstokes','https://docu.ngsolve.org/latest/i-tutorials/unit-3.2-navierstokes/navierstokes.html'),
                     ('ngsolve-poisson','https://docu.ngsolve.org/latest/i-tutorials/unit-1.1-poisson/poisson.html'),
                     ('dedalus-tau','https://dedalus-project.readthedocs.io/en/latest/pages/tau_method.html'),
                     ('guermond-heat','https://people.it.tamu.edu/~guermond/M602_FALL_2024/vol1.pdf')]:
        path=out/(slug+('.pdf' if url.endswith('.pdf') else '.html'))
        try:
            if not path.exists():
                request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 CAE-Bench-OJ reference audit'})
                path.write_bytes(urllib.request.urlopen(request,timeout=60).read())
            rows.append(dict(url=url,file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),note='retrieval snapshot, not an immutable upstream revision'))
        except Exception as exc:
            rows.append(dict(url=url,status='retrieval_failed',error=str(exc)))
    (out/'validation-sources.json').write_text(json.dumps(rows,indent=2))

if __name__=='__main__':main()
