"""Stage exact stock OpenFOAM transport coefficients; boundary matching remains open.

This only writes native material dictionaries, never solves or creates references.
"""
import argparse
import hashlib
import json
from pathlib import Path
from native_closed_cavity import save

IMAGE='sha256:d6e27c56bb5f598bc93597fdf671d6e9d06534b1851885f1b093e3cc627ea67e'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);a=ap.parse_args()
    freeze=json.loads((a.snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates/design-freeze.json').read_text());records=[]
    for p in a.snapshot.glob('qbank/02-fluid-mechanics/*/generalized-newtonian-incompressible-*/author/chapter02-ten-20261020/design.json'):
        assert hashlib.sha256(p.read_bytes()).hexdigest()==freeze['designs'][p.relative_to(a.snapshot).as_posix()]
        for e in json.loads(p.read_text())['proposed_cases']:
            s=e['detailed_spec'];v=s['materials']['viscosity']
            if v['kind']!='power_law' or not any(e['design_id'].endswith(suffix) for suffix in ('01-power_law_channel','06-power_law_traction')):continue
            q={k:v['value'] for k,v in v['parameters'].items()};rho=s['materials']['density']['parameters']['density']['value']
            mu=q['reference_viscosity'];g=q['reference_shear_rate'];n=q['power_index'];lo=q['minimum_shear_rate'];hi=q['maximum_shear_rate']
            assert 0<lo<=g<=hi and rho>0 and n>0
            k=mu/rho*g**(1-n);ends=[mu/rho*(x/g)**(n-1) for x in (lo,hi)]
            text='transportModel powerLaw;\npowerLawCoeffs\n{\n'+f' k [0 2 -1 0 0 0 0] {k:.17g};\n n [0 0 0 0 0 0 0] {n:.17g};\n nuMin [0 2 -1 0 0 0 0] {min(ends):.17g};\n nuMax [0 2 -1 0 0 0 0] {max(ends):.17g};\n'+'}\n'
            out=a.root/'maintenance/power-law-transport-stage'/e['design_id'];out.mkdir(parents=True,exist_ok=True);(out/'transportProperties.fragment').write_text(text)
            record={'case_id':e['design_id'],'stage':'constitutive_mapping_only_boundary_unmatched','image':IMAGE,'native_source':'src/transportModels/incompressible/viscosityModels/powerLaw/powerLaw.C:54-75','source_evidence':str(a.root/'maintenance/openfoam-powerLaw.C'),'identity':'k=(mu_ref/rho)*g_ref^(1-n); nuMin/min and nuMax/max of endpoint viscosities. Stock max(nuMin,min(nuMax,k*(g*1s)^(n-1))) equals the frozen two-sided clipped power law, including shear thickening.','k':k,'nuMin':min(ends),'nuMax':max(ends),'n':n,'remaining':'Match native full sigma*n traction and symmetric viscous operator before solve; pressure/zeroGradient is not assumed equivalent.','solver_started':False,'reference_produced':False,'numerical_validation':False}
            save(out/'mapping.json',record);records.append(record)
    assert len(records)==8,len(records)
    save(a.root/'maintenance/power-law-transport-stage/summary.json',{'cases':records,'ready_for_solve':False,'ordinary_pending_not_held':True})
    print(json.dumps({'native_material_dictionaries':len(records),'ready_for_solve':False,'reference_produced':False}))

if __name__=='__main__':main()
