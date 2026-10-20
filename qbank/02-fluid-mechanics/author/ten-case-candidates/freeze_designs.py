"""Check design completeness and freeze fingerprints; no numerical validation."""
import hashlib
import json
from pathlib import Path
from detailed_design import required_parameters

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]

def sha(p):return hashlib.sha256(p.read_text(encoding='utf8').encode()).hexdigest()

def main():
    index=json.loads((HERE/'index.json').read_text(encoding='utf8'))
    ids=set();errors=[];counts={}
    for row in index['questions']:
        path=ROOT/row['path'];r=json.loads(path.read_text(encoding='utf8'))
        assert sha(path)==row['sha256'],row['path']
        task=ROOT/r['question_path'];data=(task/'DATA.md').read_text(encoding='utf8')
        expected=dict(required_parameters(data))
        counts[r['question']]=len(r['proposed_cases'])
        experiments={}
        for e in r['proposed_cases']:
            key=e['design_id'];assert key not in ids;ids.add(key)
            s=e['detailed_spec'];assert set(s['parameters'])==set(expected),key
            if r['question'].startswith('2.3.'):
                assert 'heat_source' not in s['sources'],(key,'isothermal DATA forbids heat sources')
            physical_keys=('geometry','parameters','materials','analysis','initial','domain_conditions','sources','boundaries','thermal_partition','time_interval_s','output_times_s','initial_phase_geometry','native_closed_cavity_prescription')
            physical={k:s[k] for k in physical_keys if k in s}
            physical['special_field_definitions']={k:v for k,v in s['definitions'].items() if k in ('Phi_nodes','carrier_C')}
            signature=hashlib.sha256(json.dumps(physical,sort_keys=True).encode()).hexdigest()
            assert signature not in experiments,(key,experiments.get(signature),'identical physical design')
            experiments[signature]=key
            assert all(v['unit']==expected[k] for k,v in s['parameters'].items()),key
            assert s['geometry']['dimension']==e['spatial_dimension'],key
            assert s['boundaries'] and s['output_times_s'] and s['observation_requests'],key
            if r['analysis_kind']=='steady':assert not s['initial'] and s['output_times_s']==[0.],key
            else:assert s['initial'] and s['time_interval_s'][1]>0,key
            for k in ('minimum_temperature','maximum_temperature'):
                if k in s['parameters']:assert s['parameters'][k]['value']>0,key
        assert not any(not x['assigned_design_ids'] for x in r['coverage_matrix']),r['question']
    assert len(counts)==63 and len(ids)==630 and set(counts.values())=={10}
    result={'stage':'detailed_design_20261020','design_complete':True,'input_packages_complete':False,
        'scope':{'questions':63,'detailed_experiments':630},'checks':'design inventory, units, parameter keys, initial-state presence, time mode, coverage assignment and text fingerprints only; no PDE/numerical validation',
        'limitations':['Coverage assignment is intent, not proof of achieved regime or output accuracy.','Input assembly must resolve the exact DATA operators and all entity selections. Stop on incompatible definition; never silently approximate a closure.','A producer match and actual execution are still required.'],
        'index_sha256':sha(HERE/'index.json'),'designs':{r['path']:r['sha256'] for r in index['questions']}}
    (HERE/'design-freeze.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps({'detailed_experiments':len(ids),'questions':len(counts),'design_freeze':sha(HERE/'design-freeze.json'),'numerical_validation':False}))

if __name__=='__main__':main()
