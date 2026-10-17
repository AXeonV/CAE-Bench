"""Generate the light case catalog and explicit fixed-revision selection recipes."""
from pathlib import Path
import argparse,hashlib,json,re


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('bundle',type=Path);p.add_argument('audit',type=Path);p.add_argument('numerical',type=Path);p.add_argument('analytic',type=Path);p.add_argument('existing',type=Path);p.add_argument('output',type=Path);p.add_argument('--revision',required=True);a=p.parse_args()
    assert re.fullmatch('[a-f0-9]{40}',a.revision)
    read=lambda p:json.loads(p.read_text(encoding='utf-8'));choice=read(a.bundle/'selection.json');old=read(a.existing);audit=read(a.audit)
    assert audit['valid'] and len(audit['cases'])==80 and len(choice['cases'])==80 and len(old['cases'])==20
    definitions={r['definition']['name']:r['definition'] for r in read(a.numerical)+read(a.analytic)};actual={r['name']:r for r in audit['cases']};rows=[]
    for number,(name,entry) in enumerate(choice['cases'].items(),21):
        path=a.bundle/'repository'/choice['repository']['path']/entry['case']['path'];desc=read(path);spec=definitions[name]
        assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['case']['sha256']
        rows.append(dict(local_id=f'{number:03}',name=name,purpose=spec['purpose'],difficulty=spec['difficulty'],**entry,
                         reference_kind='published formula' if name.startswith('x80-exact-') else 'upstream Lethe',input_identity_sha256=desc['origin']['input_identity_sha256'],
                         input_cells=actual[name]['cells'],output_quantities=actual[name]['quantities']))
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'catalog.json').write_text(json.dumps(dict(schema_version=1,case_commit=a.revision,cases=rows),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    case80=[(r['local_id'],r['case_id']) for r in rows];case20=[(f'{i:03}',entry['case_id']) for i,entry in enumerate(old['cases'].values(),1)]
    for filename,entries,sample in [('select-extra80.ps1',case80,None),('select-all100.ps1',case20+case80,old['cases']['lid-square']['case_id'])]:
        command=['data','select','--task','newtonian-incompressible-steady-2d','--revision',a.revision,'--output','work/211-'+filename.removeprefix('select-').removesuffix('.ps1')+'-selection.json']
        for number,case_id in entries:command+=['--case',number+'='+case_id]
        if sample:command+=['--sample','010='+sample]
        script='# Generated from the immutable catalog; creates a staged selection only.\nparam([string]$Python = "./.venv/Scripts/python.exe")\n$selectionArgs = @(\n'+',\n'.join("    '"+v+"'" for v in command)+'\n)\n& $Python -m caeoj_tools.cli @selectionArgs\nif ($LASTEXITCODE -ne 0) { throw "Selection failed" }\n'
        (a.output/filename).write_text(script,encoding='utf-8')
    print(json.dumps(dict(cases=80,revision=a.revision)))
