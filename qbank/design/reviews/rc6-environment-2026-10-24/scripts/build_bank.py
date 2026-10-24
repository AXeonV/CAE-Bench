"""Rebuild RC6 from the local frozen RC5 payload, adding omitted environment files."""
import hashlib,json,os,shutil,time
from pathlib import Path
from caeoj_tools.release import build
ROOT=Path('D:/Code/CAE-Bench-OJ');WORK=ROOT/'runs/releases/rc6-authoring'
PREVIOUS=ROOT/'runs/releases/caeoj-qbank-20261024-rc5';TARGET=ROOT/'runs/releases/caeoj-qbank-20261024-rc6'
stage=WORK/'stage';source=ROOT/'runs/continuous-scoring/stage'
def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert not TARGET.exists() and not stage.exists()
shutil.copytree(source,stage,copy_function=os.link)
old=json.loads((PREVIOUS/'catalog.json').read_text(encoding='utf-8'))
plan=json.loads((ROOT/'runs/continuous-scoring/plan.json').read_text(encoding='utf-8'))
plan['release_id']=TARGET.name
plan['release_notes']=[
    'RC6修复RC5遗漏题内harbor/requirements.txt的发行问题；补入现有环境配置，提供统一科学计算运行环境和使用步骤。',
    '82题、647个正式case、96个随机格式样例沿用RC5。题面、DATA、正式输入、参考、评分规则、资源及公开包保持字节一致；新增的是环境依赖与发行使用材料。',
    '全新考生环境与独立断网判题环境的依赖及工具验证另见environment/README.md与environment/validation.json。',
    '不更正受影响的历史成绩、不重新调用模型、不重新生产参考。RC5原标签及附件保留追溯。',
    '本版仍为内部试运行RC，未宣称全体参考精度或异机资源资格已经完成。']
restored=[]
for entry in plan['tasks']:
    original=next(t for t in old['tasks'] if t['task']==entry['task'])
    entry['source_root']=str(stage);entry['public_archive']=str(PREVIOUS/original['public_archive'])
    entry['public_archive_sha256']=sha(Path(entry['public_archive']))
    req=ROOT/entry['task_path']/'harbor/requirements.txt'
    if req.exists():
        destination=stage/entry['task_path']/'harbor/requirements.txt';destination.parent.mkdir(exist_ok=True)
        assert not destination.exists();shutil.copyfile(req,destination)
        restored.append({'task':entry['task'],'sha256':sha(req)})
assert len(restored)==71
(WORK/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
(WORK/'restored-requirements.json').write_text(json.dumps(restored,ensure_ascii=False,indent=2),encoding='utf-8')
catalog=build(WORK/'plan.json',TARGET)
comparison=[]
for task in catalog['tasks']:
    prior=next(t for t in old['tasks'] if t['task']==task['task'])
    assert task['cases']==prior['cases'] and task['samples']==prior['samples']
    changed=[n for n in task['files'] if task['files'][n]!=prior['files'].get(n)]
    assert changed in ([],['harbor/requirements.txt'])
    assert all(task['files'][n]==h for n,h in prior['files'].items())
    assert sha(TARGET/task['public_archive'])==sha(PREVIOUS/prior['public_archive'])
    comparison.append({'task':task['task'],'only_new_files':changed,'all_rc5_files_unchanged':True,
                       'public_archive_unchanged':True,'case_count':len(task['cases']),'sample_count':len(task['samples'])})
(WORK/'rc5-rc6-comparison.json').write_text(json.dumps({'status':'passed','tasks':comparison,'no_score_correction':True},ensure_ascii=False,indent=2),encoding='utf-8')
print('RC6 bank built; 82 public packages and all original task files unchanged; 71 environment files restored',flush=True)
