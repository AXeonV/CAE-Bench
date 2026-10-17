"""Collect real OpenFOAM results, compare to immutable Lethe reference, retain evidence."""
from pathlib import Path
import argparse, csv, hashlib, json, re, shutil, tarfile
import h5py
import numpy as np


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def dump(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2)+'\n')


def metrics(a,b,atol,xy,ids):
    delta=np.abs(a-b);ratio=delta/(atol+.01*np.abs(b));i,k=np.unravel_index(ratio.argmax(),ratio.shape)
    return dict(max_abs=float(delta.max()),rms=float(np.sqrt(np.mean(delta**2))),
                max_tolerance_fraction=float(ratio.max()),outside_tolerance=int((ratio>1).sum()),
                worst=dict(probe_id=int(ids[i]),xy=xy[i].tolist(),component=int(k),
                           calculated=float(a[i,k]),reference=float(b[i,k]),abs_difference=float(delta[i,k])))


def sample(run,xy,rho,mu):
    paths=list((run/'postProcessing/samples').glob('*/observations.xy'))
    path=max(paths,key=lambda p:float(p.parent.name))
    values=np.loadtxt(path)
    assert values.shape==(len(xy),16),values.shape
    assert np.allclose(values[:,:2],xy,atol=1e-12,rtol=0)
    assert np.max(np.abs(values[:,5]))<1e-14
    grad=values[:,7:].reshape(-1,3,3)
    assert np.max(np.abs(grad[:,:,2]))<1e-12
    assert np.max(np.abs(grad[:,2,:]))<1e-12
    sym=(grad+grad.transpose(0,2,1))/2
    return dict(velocity=values[:,3:5],pressure=rho*(values[:,6:7]-values[0,6]),
                shear_rate=np.sqrt(2*np.einsum('nij,nij->n',sym,sym))[:,None],
                density=np.full((len(xy),1),rho),dynamic_viscosity=np.full((len(xy),1),mu)),path


def collect(source,runs,catalog,output):
    output.mkdir(parents=True,exist_ok=True)
    rows=[];atols=dict(velocity=.001,pressure=.1,shear_rate=.01,density=.0001,dynamic_viscosity=.000001)
    configs=tarfile.open(output/'actual-configurations.tar.gz','w:gz')
    with (output/'pointwise-differences.csv').open('w',newline='') as f:
        csvout=csv.writer(f);csvout.writerow(['alias','name','quantity','probe_id','x','y','component','openfoam','lethe','signed_difference','tolerance_fraction'])
        for c in json.loads(catalog.read_text()):
            if c['name']=='lid-square':continue
            name=c['name'];inp=source/'cases'/name;ref=source/'reference'/name
            assert {p.name:sha(p) for p in inp.iterdir() if p.is_file()}==c['input_files']
            assert {p.name:sha(p) for p in ref.iterdir() if p.is_file()}==c['reference_files']
            j=json.loads((inp/'problem.json').read_text());mat=next(iter(j['materials'].values()))
            rho=mat['density']['parameters']['density']['value'];mu=mat['viscosity']['parameters']['dynamic_viscosity']['value']
            with h5py.File(inp/'input.h5') as h:arr={k:h[k][:] for k in h}
            xy=arr['probe_xy'];ids=arr['probe_ids']
            with h5py.File(ref/'reference.h5') as h:reference={q:h[q][0] for q in atols}
            result={};execution={};record=dict(alias=c['local_id'],name=name,case_id=c['case_id'],hf_commit=c['hf_commit'],input_hashes=c['input_files'],reference_hashes=c['reference_files'])
            levels=sorted(int(p.name[1:]) for p in (runs/name).glob('n*') if (p/'execution.json').exists())
            assert len(levels)>=2,(name,levels)
            for n in levels:
                run=runs/name/f'n{n}';dest=output/'runs'/name/f'n{n}';dest.mkdir(parents=True,exist_ok=True)
                execution[n]=json.loads((run/'execution.json').read_text())
                assert execution[n]['solver']['returncode']==0
                result[n],path=sample(run,xy,rho,mu)
                shutil.copyfile(path,dest/'observations.xy')
                for file in ('execution.json','translation.json','checkMesh.log','blockMesh.log'):
                    shutil.copyfile(run/file,dest/file)
                if (run/'mapFields.log').exists():shutil.copyfile(run/'mapFields.log',dest/'mapFields.log')
                log=(run/'solver.log').read_text();(dest/'convergence-tail.log').write_text('\n'.join(log.splitlines()[-42:])+'\n')
                assert 'Mesh OK.' in (run/'checkMesh.log').read_text()
                initial={key:[float(x) for x in re.findall(r'Solving for '+key+r', Initial residual = ([^,]+)',log)][-1] for key in ('Ux','Uy','p')}
                continuity=re.findall(r'continuity errors : sum local = ([^,]+), global = ([^,]+), cumulative = ([^\n]+)',log)[-1]
                execution[n].update(final_initial_residual=initial,continuity=dict(zip(('sum_local','global','cumulative'),map(float,continuity))),sample_sha256=sha(path))
                for folder in ('0','system','constant'):
                    for p in (run/folder).glob('*'):
                        if p.is_file():configs.add(p,arcname=str(Path(name)/f'n{n}'/folder/p.name))
                with h5py.File(dest/'result.h5','w') as h:
                    h['clock']=arr['clock'];h['probe_ids']=ids
                    for q,a in result[n].items():h[q]=a[None].astype(np.float64)
                execution[n]['result_sha256']=sha(dest/'result.h5')
            record['levels']=execution;record['comparison']={}
            for n in levels:
                record['comparison'][str(n)]={q:metrics(result[n][q],reference[q],atols[q],xy,ids) for q in atols}
            record['mesh_comparison']={f'{a}-{b}':{q:metrics(result[a][q],result[b][q],atols[q],xy,ids) for q in ('velocity','pressure','shear_rate')} for a,b in zip(levels,levels[1:])}
            last=levels[-1];mesh=record['mesh_comparison'][f'{levels[-2]}-{last}']
            record['cross_agreement']=all(x['outside_tolerance']==0 for x in record['comparison'][str(last)].values())
            record['mesh_stable']=all(x['max_tolerance_fraction']<.25 for x in mesh.values())
            record['all_runs_converged']=all(x['converged'] for x in execution.values())
            record['accepted']=record['cross_agreement'] and record['mesh_stable'] and record['all_runs_converged']
            for q,a in result[last].items():
                b=reference[q]
                for i in range(len(xy)):
                    for k in range(a.shape[1]):csvout.writerow([c['local_id'],name,q,int(ids[i]),*xy[i],k,a[i,k],b[i,k],a[i,k]-b[i,k],abs(a[i,k]-b[i,k])/(atols[q]+.01*abs(b[i,k]))])
            rows.append(record)
            print(name,'accepted',record['accepted'],'cross',max(v['max_tolerance_fraction'] for v in record['comparison'][str(last)].values()),'mesh',max(v['max_tolerance_fraction'] for v in mesh.values()),flush=True)
    configs.close();dump(output/'comparison.json',rows)
    assert len(rows)==19
    return rows


def grade(source,output):
    from caeoj.sdk import load_problem,load_result
    from caeoj.case_grading import grade_case
    rows=json.loads((output/'comparison.json').read_text());records=[]
    for row in rows:
        name=row['name'];inp=source/'cases'/name;ref=source/'reference'/name
        n=max(map(int,row['levels']));result=output/'runs'/name/f'n{n}'/'result.h5'
        load_result(load_problem(inp/'problem.json'),result)
        graded=grade_case(inp/'problem.json',result,ref/'grading.json')
        records.append(dict(name=name,case_id=row['case_id'],level=n,contract_valid=True,grading=graded))
        print(name,graded['status'],graded['score'],flush=True)
    dump(output/'production-grading.json',records)


def report(output):
    rows=json.loads((output/'comparison.json').read_text())
    grades=json.loads((output/'production-grading.json').read_text())
    final=[r['comparison'][str(max(map(int,r['levels'])))] for r in rows]
    maxabs={q:max(r[q]['max_abs'] for r in final) for q in ('velocity','pressure','shear_rate')}
    cross=max((m['max_tolerance_fraction'],r['alias'],q) for r,mq in zip(rows,final) for q,m in mq.items())
    meshmax=max(m['max_tolerance_fraction'] for r in rows for m in r['mesh_comparison']['24-32'].values())
    points=sum(len(json.loads((output/'runs'/r['name']/'n32/translation.json').read_text())['probes']) for r in rows)
    lines=['# 19 例独立交叉验证结论','',
           f"实际执行 OpenFOAM Foundation incompressibleFluid：19 例 × 16/24/32 三档网格，共 57 次最终计算。{sum(r['all_runs_converged'] for r in rows)}/19 例全部网格收敛，57 个网格均通过 checkMesh。{sum(r['accepted'] for r in rows)}/19 例通过本次交叉验证判据，现有实际 grade_case 消费链 {sum(g['grading']['score']==1 for g in grades)}/19 得 1。",'',
           f'全部 {points} 个观测点、{points*6} 个请求标量分量均比较；最细网格的跨求解器最大绝对差分别为：速度 {maxabs["velocity"]:.9g} m/s、压力 {maxabs["pressure"]:.9g} Pa、剪切率 {maxabs["shear_rate"]:.9g} 1/s。全批最大题面容差占比为 {cross[0]:.6f}，位于 {cross[1]} 的 {cross[2]}。','',
           f'最终两档 24→32 网格的最大差异为题面容差的 {meshmax:.6f} 倍。经验验收要求：全部实际分量跨求解器差异不超过题面容差，最后两档网格差异小于对应容差的 25%，且全部最终计算收敛。完整的 16→24、24→32 差异及每档与原参考的差异均保存，未丢弃较粗档结果。','',
           '| 编号 | 算例 | 最大速度差 m/s | 最大压力差 Pa | 最大剪切率差 1/s | 跨程序最大容差占比 | 24→32 最大容差占比 | 结论 |',
           '|---|---|---:|---:|---:|---:|---:|---|']
    for r,m in zip(rows,final):
        ratio=max(v['max_tolerance_fraction'] for v in m.values());mesh=max(v['max_tolerance_fraction'] for v in r['mesh_comparison']['24-32'].values())
        lines.append(f'| {r["alias"]} | {r["name"]} | {m["velocity"]["max_abs"]:.6g} | {m["pressure"]["max_abs"]:.6g} | {m["shear_rate"]["max_abs"]:.6g} | {ratio:.5f} | {mesh:.5f} | '+('通过' if r['accepted'] else '需进一步核验')+' |')
    lines += ['', '本次保持冻结的几何、孔洞、材料、移动壁面斜坡、滑移、体加速度和观测位置不变。压力按照输入的 pin=0 Pa 实施点基准，未根据 Lethe 结果作偏移拟合；原 reference.h5、grading.json、正式 cases/samples 均未修改。HF 固定提交仍为 `fbe115effe8131bd575c0cde1c9ca87a9d87fd3a`，HF main 未写入。','',
              '验证支持这些原参考在当前全部请求观测和题面容差内的数值一致性；它不把原参考替换为 OpenFOAM 解，也不证明连续全场无误。网格变化阈值是经验控制，不是严格后验误差界；边界插值、点采样及梯度重建仍有离散误差。两套程序共享同一连续物理模型，本次没有新的实验真值。密度、黏度是材料常量回读，单列为接口／单位核对，不视作独立流场证据。','',
              '标准方腔 010 不在本次范围，原 Ghia 中线速度比较保持原记录；本次 19 例覆盖也不代表 pressure_outlet、traction、periodic、高 Re 或全题所有合法输入已验证。计算使用 titan 的可用资源，未重新认证考生资源限制，未运行 LLM 或 Agent benchmark。','',
              '详细来源、物理转换及复现见 README.md；实际配置归档位置与摘要见 configuration-archive.json，完整逐点差异见 pointwise-differences.csv，逐档采样、收敛记录与完整 HDF5 在 runs/，原始维护档案位置及 SHA-256 见 raw-results.json。']
    (output/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    dump(output/'summary.json',dict(cases=19,runs=57,probes=points,scalar_components=points*6,accepted=sum(r['accepted'] for r in rows),graded_pass=sum(g['grading']['score']==1 for g in grades),max_abs=maxabs,max_tolerance_fraction=cross[0],max_final_mesh_tolerance_fraction=meshmax))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);p.add_argument('--runs',type=Path);p.add_argument('--catalog',type=Path);p.add_argument('--grade',action='store_true');p.add_argument('--report',action='store_true');a=p.parse_args()
    if a.runs:collect(a.source,a.runs,a.catalog,a.output)
    if a.grade:grade(a.source,a.output)
    if a.report:report(a.output)
