"""Read-only fast-profile access for RC5 (environment-patched), RC6 and RC7."""
import argparse, hashlib, json, pathlib, subprocess, sys
EXCLUDED = ['transition-gas','incompressible-navier-stokes-2d','compressible-navier-stokes-2d','compressible-navier-stokes-3d','thermal-rans-3d','viscoelastic-steady','rans-steady-3d','reaction-diffusion-2d']
def profile(root):
    root=pathlib.Path(root).resolve(); p=root/'catalog.json'; catalog=json.loads(p.read_text(encoding='utf-8-sig'))
    release=catalog['release_id']
    if release not in ('caeoj-qbank-20261024-rc5','caeoj-qbank-20261024-rc6','caeoj-qbank-20261029-rc7'):raise ValueError('Unsupported release identity')
    tasks=catalog['tasks'];names=[t['task'] for t in tasks]
    if len(names)!=len(set(names)):raise ValueError('Duplicate task identity')
    if len(tasks)!=(74 if release.endswith('rc7') else 82):raise ValueError('Unexpected base task count')
    selected=[t for t in tasks if t['task'] not in EXCLUDED]
    if len(selected)!=74:raise ValueError('Fast profile must contain exactly 74 tasks')
    return root,{'profile':'fast-v1','base_release':release,'catalog_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'tasks':[{'task':t['task'],'path':t['path'],'public_archive':t['public_archive'],'case_count':len(t['cases'])} for t in selected],'excluded_tasks':EXCLUDED,'task_count':74,'case_count':sum(len(t['cases']) for t in selected),'scoring':'mean case score per task; equal mean over these 74 tasks; label fast-v1; never compare as full-82 score','rc5_environment_patch_required':release.endswith('rc5')}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=pathlib.Path,required=True);s=p.add_subparsers(dest='command',required=True);s.add_parser('list');s.add_parser('manifest');e=s.add_parser('extract');e.add_argument('task');e.add_argument('target',type=pathlib.Path);a=p.parse_args();root,d=profile(a.root)
    if a.command=='extract':
        if a.task not in {t['task'] for t in d['tasks']}:raise ValueError('Task excluded from fast-v1')
        subprocess.run([sys.executable,str(root/'release.py'),'--root',str(root),'extract',a.task,str(a.target)],check=True)
    elif a.command=='list':print('\n'.join(t['task'] for t in d['tasks']))
    else:print(json.dumps(d,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
