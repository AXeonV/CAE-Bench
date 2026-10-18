"""Produce this supplement's per-case authoring report from actual native logs."""
import argparse
import datetime as dt
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import re
import time

NUMBER=r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][+-]?\d+)?'


def number(value):
    return float(value.replace('D','E').replace('d','e'))


def parse_log(solver,text):
    result={}
    if solver=='elmer':
        indices=re.findall(r'NAVIER-STOKES ITERATION\s+(\d+)',text)
        result['outer_iteration']=int(indices[-1]) if indices else None
        final=re.split(r'NAVIER-STOKES ITERATION\s+\d+',text)[-1]
        linear=re.findall(r'^\s*(\d+)\s+('+NUMBER+r')\s*$',final,re.M)
        result['last_linear_iteration']=int(linear[-1][0]) if linear else None
        result['final_linear_residual']=number(linear[-1][1]) if linear else None
        changes=re.findall(r'Relative Change\s*:\s*('+NUMBER+r')',text)
        result['absolute_nonlinear_update']=number(changes[-1]) if changes else None
        result['errors']=[line for line in text.splitlines() if 'ERROR::' in line]
    else:
        blocks=re.split(r'^Time = ([0-9.]+)\s*$',text,flags=re.M)
        result['outer_iteration']=int(float(blocks[-2])) if len(blocks)>1 else None
        final=blocks[-1]
        matches=re.findall(r'Solving for (\w+), Initial residual = ('+NUMBER+r'), Final residual = ('+NUMBER+r'), No Iterations (\d+)',final)
        result['linear_solves_last_outer']=[dict(field=f,initial_residual=number(a),final_residual=number(b),iterations=int(n)) for f,a,b,n in matches]
        continuity=re.findall(r'continuity errors : sum local = ('+NUMBER+r'), global = ('+NUMBER+r'), cumulative = ('+NUMBER+r')',text)
        result['continuity']=dict(zip(['local','global','cumulative'],map(number,continuity[-1]))) if continuity else None
        result['simple_converged']='SIMPLE solution converged' in text
        result['errors']=[line for line in text.splitlines() if 'FOAM FATAL' in line]
    return result


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


@lru_cache(maxsize=512)
def log_metrics(path,solver,size,mtime,finished):
    path=Path(path)
    with path.open('rb') as stream:
        stream.seek(max(0,size-512*1024))
        text=stream.read().decode(errors='replace')
    result=parse_log(solver,text)
    result['log_sha256']=digest(path) if finished else None
    result['log_bytes']=size
    return result


def read_json(path):
    for attempt in range(3):
        try:return json.loads(path.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            if attempt==2:raise
            time.sleep(.02)


def scheduler_running(state,work):
    if not Path('/proc').exists():return None
    proc=Path(f"/proc/{state.get('pid')}/cmdline")
    return proc.exists() and str(work).encode() in proc.read_bytes().split(b'\0')


def locate_run(work,solvers,name,code,n,solver,binding):
    folder=work/'native'/name/code/f'{solver}-n{n}'
    receipt=None
    if binding and binding.get('reused_native_run'):
        receipt=solvers/'local/runs'/solver/binding['reused_native_run']/'record.json'
    elif binding:
        command=binding['command']
        folder=Path(command[command.index('--workdir')+1])
    execution=folder/'execution.log'
    if receipt is None and execution.exists():
        match=re.search(r'run record: (.+)',execution.read_text())
        if match:receipt=Path(match[1].strip())/'record.json'
    record=read_json(receipt) if receipt and receipt.exists() else {}
    if record:folder=Path(record['workdir'])
    return folder,record


def run_metrics(work,solvers,name,code,n,solver,binding):
    folder,record=locate_run(work,solvers,name,code,n,solver,binding)
    state='finished' if record.get('exit_code')==0 else 'failed' if 'exit_code' in record else 'running' if record else 'unbound'
    item=dict(solver=solver,state=state,run_id=record.get('id'),image_id=record.get('image_id'),
              workdir=str(folder.relative_to(work)) if folder.is_relative_to(work) else str(folder),
              actual_budget=record.get('resources'),wall_seconds=record.get('seconds'),
              exit_code=record.get('exit_code'),timed_out=record.get('timed_out'),
              reused=bool(binding and binding.get('reused_native_run')),
              native_inputs_sha256=record.get('inputs_sha256'))
    config=folder/'flow.sif' if solver=='elmer' else folder/'system/controlDict'
    item['iteration_limits']={}
    if config.exists():
        text=config.read_text()
        patterns={'outer':r'Nonlinear System Max Iterations\s*=\s*(\d+)',
                  'linear':r'Linear System Max Iterations\s*=\s*(\d+)'} if solver=='elmer' else {'outer':r'\bendTime\s+(\d+)\s*;'}
        for key,pattern in patterns.items():
            match=re.search(pattern,text)
            if match:item['iteration_limits'][key]=int(match[1])
    log=folder/'flow.log'
    if log.exists():
        stat=log.stat();item.update(log_metrics(str(log),solver,stat.st_size,stat.st_mtime_ns,'exit_code' in record))
    return item


def collect(work,solvers,scheduler):
    state=read_json(scheduler);batch_log=scheduler.parent/state['stdout_log']
    batch_bytes=batch_log.read_bytes();completed={}
    for line in batch_bytes.decode(errors='replace').splitlines():
        try:
            row=json.loads(line)
            if 'case' in row and 'passed' in row:completed[row['case']]=row
        except ValueError:pass
    rows=[]
    for problem in sorted((work/'generated/cases').glob('*/problem.json')):
        name=problem.parent.name;path=work/'evidence'/(name+'.json')
        record=read_json(path) if path.exists() else {}
        current=record.get('code_id')==state['code_id']
        attempts=record.get('attempts',[]) if current else []
        levels={a['n']:a for a in attempts}
        for directory in (work/'native'/name/state['code_id']).glob('*-n*'):
            match=re.fullmatch(r'(elmer|openfoam)-n(\d+)',directory.name)
            if match:levels.setdefault(int(match[2]),dict(n=int(match[2])))
        entry=dict(case=name,status='passed' if completed.get(name,{}).get('passed') else 'failed' if name in completed else 'incomplete',
                   input_sha256={p.name:digest(p) for p in sorted(problem.parent.iterdir()) if p.is_file()},attempts=[])
        units={s['array']:s['unit'] for s in read_json(problem)['outputs'].values()}
        for n,a in sorted(levels.items()):
            bindings={x['run']['solver']:x['run'] for x in a.get('runs',[])}
            result={key:a[key] for key in ['n','cross_score','max_budget_ratio','producer_analytic_budget_ratio','error','stage'] if key in a}
            result['errors']={key:dict(value,unit=units[key]) for key,value in a.get('errors',{}).items()}
            result['solvers']=[run_metrics(work,solvers,name,state['code_id'],n,sid,bindings.get(sid)) for sid in ['elmer','openfoam']]
            entry['attempts'].append(result)
        rows.append(entry)
    publication=Path(__file__).parent/'data-evidence/supplement/publication.json'
    return dict(captured_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),code_id=state['code_id'],
                requested_budget=state['author_budget'],workers=state['workers'],
                completed=len(completed),passed=sum(r['passed'] for r in completed.values()),failed=sum(not r['passed'] for r in completed.values()),
                target=len(rows),batch_log_sha256=hashlib.sha256(batch_bytes).hexdigest(),
                scheduler_running=scheduler_running(state,work),
                publication=read_json(publication) if publication.exists() else None,cases=rows)


def fmt(value):
    return '—' if value is None else str(value) if isinstance(value,int) else f'{value:.4g}' if isinstance(value,float) else str(value).replace('|','/').replace('\n',' ')


def residual_text(run):
    if run['solver']=='elmer':return fmt(run.get('final_linear_residual'))
    solves=run.get('linear_solves_last_outer',[]);seen={};parts=[]
    for s in solves:
        field=s['field'];seen[field]=seen.get(field,0)+1
        label=field+f"[{seen[field]}]" if sum(x['field']==field for x in solves)>1 else field
        parts.append(f"{label}={fmt(s['final_residual'])}")
    return '; '.join(parts) or '—'


def markdown(report):
    b=report['requested_budget']
    lines=['# 2.1.3 算例出题报告','',
           f"当前快照：完成 {report['completed']}/{report['target']}，通过 {report['passed']}，未通过 {report['failed']}；未完成项不计为失败。",'',
           '## 参考生产预算与计量','',
           f"当前每次原生求解申请 {b['cpus']} CPU、{b['memory']} 内存、{b['timeout']} 秒，{report['workers']} 路制作。具体离散和迭代上限见[作者配置](README.md#求解器配置)。本报告耗时来自共享环境中的参考生产，不代表考生资源可行性验证。",'',
           '耗时统一取原生工具回执的 `seconds`，不混用适配器外围计时；复用项记录历史运行的实际配额和耗时。迭代上限来自各次原生配置，OpenFOAM 的稳态伪时间每次增加 1，因此 endTime 对应 SIMPLE 外迭代上限。每个网格级别分别列出两套求解器；“—”表示未记录或不适用，不代表零。运行中条目显示最后观测值，正常退出也不单独代表算例通过。', '',
           '线性残差保留求解器原生口径，不能跨软件直接比较。Elmer 的非线性绝对更新量单列，不冒充方程残差；OpenFOAM 的 SIMPLE 外迭代编号、最后一轮各次线性求解残差及连续性指标分别保存。误差比为绝对差除以判分允许误差，超过 1 表示不通过；制作参考另有精度余量要求。', '',
           '机器可读明细与日志摘要绑定见 [production-report.json](data-evidence/supplement/production-report.json)，可逐例查看完整输出误差、OpenFOAM 线性求解初始／最终残差、线性迭代数和运行身份。快照时间与批次代码摘要也保存在该文件。','',
           '## 逐例记录','']
    if report.get('publication'):
        publication=report['publication']
        lines[2:2]=[f"已发布范围仍以[发布记录](data-evidence/supplement/publication.json)为准：{publication['validated_preview_cases']} 例，固定提交 `{publication['uploaded_commit']}`。以下是当前制作批次的数值记录，通过数量不等于已发布数量。",'']
    labels={'passed':'通过','failed':'未通过','incomplete':'计算／验证未完成'}
    if report.get('scheduler_running') is False and report['completed']<report['target']:
        lines[2:2]=['计算进程已退出，当前报告仍有未完成算例。','']
    for case in report['cases']:
        lines.extend([f"### {case['case']}：{labels[case['status']]}",'',
                      '| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |',
                      '|---:|---|---|---|---:|---:|---|---:|---:|'])
        if not case['attempts']:lines.append('| — | — | — | — | — | — | — | — | — |')
        for a in case['attempts']:
            for r in a['solvers']:
                budget=r['actual_budget'];budget_text=f"{budget.get('cpus','—')}/{budget.get('memory','—')}/{budget.get('timeout','—')}" if budget else '—'
                solver=r['solver']+('（复用）' if r['reused'] else '')
                limits=r['iteration_limits'];limit_text=f"{fmt(limits.get('outer'))}/{fmt(limits.get('linear'))}"
                lines.append(f"| {a['n']} | {solver} | {budget_text} | {limit_text} | {fmt(r['wall_seconds'])} | {fmt(r.get('outer_iteration'))} | {residual_text(r)} | {fmt(r.get('absolute_nonlinear_update'))} | {fmt(r['exit_code'])} |")
            if a.get('error'):lines.extend(['',f"n={a['n']}：{fmt(a['error'])}",''])
        errors=[a for a in case['attempts'] if a.get('errors')]
        if errors:
            lines.extend(['','| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |','|---:|---|---:|---|---:|'])
            for a in errors:
                for key,error in a['errors'].items():
                    lines.append(f"| {a['n']} | {key} | {fmt(error['max_abs'])} | {error['unit']} | {fmt(error['max_budget_ratio'])} |")
        lines.append('')
    return '\n'.join(lines)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work',type=Path,required=True);p.add_argument('--solvers',type=Path,required=True)
    p.add_argument('--scheduler',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--json-output',type=Path,required=True);p.add_argument('--watch',type=int,default=0)
    args=p.parse_args()
    args.work=args.work.resolve();args.solvers=args.solvers.resolve();args.scheduler=args.scheduler.resolve()
    if args.watch<0:p.error('--watch must not be negative')
    previous=None
    while True:
        state=read_json(args.scheduler);log=args.scheduler.parent/state['stdout_log']
        active=scheduler_running(state,args.work)
        marker=(log.stat().st_size,state['code_id'],active)
        if marker!=previous:
            result=collect(args.work,args.solvers,args.scheduler)
            for path in [args.output,args.json_output]:path.parent.mkdir(parents=True,exist_ok=True)
            for path,text in [(args.json_output,json.dumps(result,indent=2,allow_nan=False)+'\n'),(args.output,markdown(result))]:
                temporary=path.with_name(path.name+f'.tmp-{os.getpid()}')
                temporary.write_text(text,encoding='utf-8');temporary.replace(path)
            print(f"Report: {result['completed']}/{result['target']}, passed {result['passed']}, failed {result['failed']}",flush=True)
            previous=marker
        if not args.watch or result['completed']==result['target'] or active is False:break
        time.sleep(args.watch)


if __name__=='__main__':main()
