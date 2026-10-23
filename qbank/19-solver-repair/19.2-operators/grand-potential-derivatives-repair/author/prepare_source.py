"""Reproduce the explicit mixed-derivative supplement from exact pinned PR files."""
import argparse
import hashlib
import json
from pathlib import Path

TASK=Path(__file__).resolve().parents[1]


def once(text,before,after):
    if text.count(before)!=1:raise ValueError('Unexpected fixed upstream source anchor')
    return text.replace(before,after)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--download-upstream',action='store_true');parser.add_argument('--proxy');args=parser.parse_args()
    identity=json.loads((TASK/'author/data-evidence/target-source-versions.json').read_text())
    for name,hashes in identity['files'].items():
        upstream=TASK/'author/upstream'/name
        if args.download_upstream:
            import httpx
            section='src' if name.endswith('.C') else 'include'
            url=f'https://raw.githubusercontent.com/idaholab/moose/{identity["exact_pr_head"]}/modules/phase_field/{section}/materials/{name}'
            with httpx.Client(proxy=args.proxy,timeout=90,follow_redirects=True) as client:
                response=client.get(url);response.raise_for_status();data=response.content
            if hashlib.sha256(data).hexdigest()!=hashes['upstream']:raise ValueError('Wrong pinned upstream bytes')
            upstream.write_bytes(data)
        data=upstream.read_bytes()
        if hashlib.sha256(data).hexdigest()!=hashes['upstream']:raise ValueError('Changed upstream source')
        text=data.decode()
        if name.endswith('.h'):
            text=once(text,'  std::vector<MaterialProperty<Real> *> _dhs_c_min;\n','  std::vector<MaterialProperty<Real> *> _dhs_c_min;\n  std::vector<MaterialProperty<Real> *> _d2hs_c_mindphideta;\n')
        else:
            text=once(text,'    _dhs_c_min(_neta),\n','    _dhs_c_min(_neta),\n    _d2hs_c_mindphideta(_neta),\n')
            text=once(text,'    _dhs_c_min[i] = &declarePropertyDerivative<Real>("hs_c_min", _eta_name[i]);\n','    _dhs_c_min[i] = &declarePropertyDerivative<Real>("hs_c_min", _eta_name[i]);\n    _d2hs_c_mindphideta[i] =\n        &declarePropertyDerivative<Real>("hs_c_min", _phi_name, _eta_name[i]);\n')
            text=once(text,'        (*_dhs_c_min[i])[_qp] = _hs[_qp] * (*_dcs_eq[i])[_qp];\n','        (*_dhs_c_min[i])[_qp] = _hs[_qp] * (*_dcs_eq[i])[_qp];\n        (*_d2hs_c_mindphideta[i])[_qp] = _dhs[_qp] * (*_dcs_eq[i])[_qp];\n')
        data=text.encode()
        if hashlib.sha256(data).hexdigest()!=hashes['author-complete']:raise ValueError('Reproduced reference differs from frozen actual Oracle sources')
        target=TASK/'author/generated'/name
        if target.exists() and target.read_bytes()!=data:raise ValueError('Refuse to overwrite changed author reference')
        if not target.exists():target.write_bytes(data)
        print(name,hashes['author-complete'])


if __name__=='__main__':main()
