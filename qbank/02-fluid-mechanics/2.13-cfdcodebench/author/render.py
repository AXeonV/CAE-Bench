"""Expand source definitions into self-contained candidate materials and runtime facts."""
import json,tomllib
from catalog import catalog,SECTION,ROOT,WORK,REVISION
from caeoj_tools.continuous_scoring import convert_grading, scoring_text

def dumps(value):return json.dumps(value,ensure_ascii=False,indent=2)+'\n'

def rule(index):
    return dict(metric='max_abs',time='per_time',components='per_component',limit=1e-4) if index==23 else dict(
        metric='nrmse',time='per_time',components='per_component',limit=.1,scale_floor=1e-6,weight_field='weights')

def grading(c):
    fields={n:rule(c['index']) for n in c['fields']}
    policy=dict(version=2,quantities={n:dict(unit='1',rule=r) for n,r in fields.items()})
    if not c['pressure'] and not c['offset']:
        return convert_grading(dict(version=1,checks=[dict(id='fields',evaluator='direct_outputs',reference='reference.h5',policy=policy)]))
    return convert_grading(dict(version=1,checks=[dict(id='fields',evaluator='field.normalized_outputs',reference='reference.h5',
        policy=policy,weight_field='weights',transforms={n:dict(offset=c['offset'] if n=='T' else 0,
        remove_mean=c['pressure'] and n=='p') for n in c['fields']})]))

def main():
    rows=[];models={}
    for c in catalog():
        i=c['index'];path=SECTION/c['task'];path.mkdir(exist_ok=True)
        config_path=path/'judge-config.json'
        config=json.loads(config_path.read_text(encoding='utf-8')) if config_path.exists() else dict(timeout_seconds=1800,max_output_bytes=None,stage='provisional',verifier_budget=dict(base_seconds=300,per_case_overhead_seconds=60))
        limits=tomllib.loads((path/'harbor/task.toml').read_text(encoding='utf-8')) if (path/'harbor/task.toml').exists() else {}
        cpus=limits.get('environment',{}).get('cpus',1);memory_mb=limits.get('environment',{}).get('memory_mb',4096)
        resource_text=(f"每 case 求解墙钟上限 {config['timeout_seconds']} 秒，内存上限 {memory_mb} MiB，CPU 配额 {cpus} 核；所有进程和线程共用配额。允许进程、线程及编译辅助程序，入口遵守提交接口。" if config.get('stage')=='calibrated' else f"设计上限为每 case 求解墙钟 {config['timeout_seconds']} 秒、内存 {memory_mb} MiB；实际 CPU 配额待资源校准。")
        resource_note=('已在限定资源的容器中实测现成求解器或解析表示；这不保证任意数值方法都能在限额内完成。' if config.get('stage')=='calibrated' else '此资源设置在实际参考与执行校准完成前不代表正式评测发布；该状态不改变数学要求和评分式。')
        title=f"2.13.{i} {c['title']}";fields='、'.join(c['fields']);pressure=c['pressure']
        models[f'cfdcodebench-c{i:02}-v1']={k:c[k] for k in ('index','task','fields','dimension','domain','time')}
        normalization=('压力 p 的候选与参考分别减去全部观测点上的加权均值后评分；允许常数基准差，不拟合比例或相位。' if pressure else '')
        normalization+=f"温度 T 的候选与参考均减去公开固定背景{c['offset']}后计算尺度及误差。" if c['offset'] else ''
        score=scoring_text(grading(c)['checks'][0]['policy'], normalization=normalization)
        instruction=f'''# {title}

求解 DATA 所定义的固定连续问题，在输入给出的观测位置及终止时刻提交 {fields}。
语言、软件、内部网格和数值方法自由；必须保留给定 PDE、系数、初边值及选解条件。
本题属于 CFDCodeBench 兼容专题；输入输出采用本题库协议。

公开要求由本文、[DATA](DATA.md) 和 [CONTRACT](../../../../docs/CONTRACT.md) 完整定义。
从输入目录读取 problem.json 及其 data_file 指向的 HDF5，向指定输出路径写 result.h5。
输出位置是观测点，不是必须采用的计算网格。不得按数组行号猜测坐标、IDs 或请求时刻。

## 提交与运行

入口为 `solve.py`，每例独立启动：

```sh
python solve.py --input /path/to/problem.json --output /path/to/result.h5
```

路径以参数为准；输入中的相对路径相对于 `problem.json` 所在目录解析。成功时以0退出，并将完整结果写到 `--output`。日志不作为答案；运行依赖须提前准备，逐例运行无需网络。入口可调用自行编译的其他语言程序。

## 评分

{score}

## 执行资源

{resource_text}
{resource_note}

## 公开格式样例

`samples/01/` 仅展示输入与输出结构。其 `output/result.h5` 是随机生成的格式示例，不是本题数值解，也不保证满足物理约束。可用它核对数组、IDs和时间轴的读写，不能将其作为正确答案、误差参考或本地数值判分依据。正式case使用独立的隐藏参考判分。
'''
        times='稳态或谱观测标记0，不是迭代时间' if c['time']==0 else f"唯一物理终止时刻 {c['time']!r}；不是内部步长"
        location=('observations 为 entities，恰有一个模态身份；没有伪坐标，s 是该模态族最右实增长率。' if i==23 else
                  'observations 为 points；coordinates 引用 float64[N,D] 的显式坐标。所有二维观测严格位于域内；一维允许端点。圆环坐标为 (r*cos(theta),r*sin(theta))，径向球对称问题的单坐标为 r。')
        weight_note=('本题只有一个实体观测，评分采用单点等权；输入中的 weights 不影响分值，无需在输出中复制。' if i==23 else '权重为严格正且有限的公开积分/观测权重，只决定公开评分的空间加权；无需提交。')
        dat=f'''# {title}：数据与连续定义

遵循 [CONTRACT](../../../../docs/CONTRACT.md)。task="{c['task']}"，physics.model="cfdcodebench-c{i:02}-v1"，spatial_dimension={c['dimension']}。
协议坐标和时刻遵守 CONTRACT，分别以 m、s 表示。下面连续方程使用归一化坐标 x*=x/(1 m)、时间 t*=t/(1 s)，省略星号；两者数值恰与协议值相同，不另换算。所有输出场及公开权重为题定无量纲量，单位字符串为 "1"；温度读数的标度如本页特别说明。
physics.parameters={{}}；模型及其固定参数由本页完整定义，不读取外部默认配置。

## 连续问题

{c['equation']}

计算域与时间范围：

{c['domain_text']}

边界：

{c['boundary']}

初态：

{c['initial'] if i!=24 else '无物理初态。按下述正基态条件选择非线性边值解。'}

补充及优先定义：

{c['note']}

{normalization}

## 实际输入

problem.json 的 data_file 指向包内 input.h5。meshes、geometries 为空字典，conditions 为空列表：上述条件为本模型固定定义。
不得加入未声明的条件、参数或场。{location}
location 对象名为 observations，其 ids 引用非负、唯一、有序身份 int64[N]；行顺序只由该轴决定。IDs 均须实际读取；points 位置还必须读取 coordinates，entities 没有坐标。
允许 N 在1到65536之间；圆管特征值任务固定 N=1。
time_axes.output 引用 float64[1]：{times}。所有数组 key 从 manifest 引用读取，不依赖文件中的默认命名。

唯一 fields 对象 weights：quantity="observation_weight"，scalar，float64，[1,N,1]，components=["value"]，component_shape=[1]，unit="1"，location="observations"，time_axis="output"。
{weight_note}
一维/矩形权重可为一致点观测权或正控制体权；圆环权包含径向 Jacobian，球对称径向权包含壳体积。
输入不含必须使用的计算网格；可以在任意内部离散上求解后重建。

## 输出与采样语义

{''.join(f'- `{n}`：quantity="{n}"，默认 array="{n}"。'+chr(10) for n in c['fields'])}

每个 outputs 对象均为 scalar、float64、component_shape=[1]、components=["value"]、unit="1"，location="observations"，time_axis="output"，数组 shape=[1,N,1]。
value_kind="point"；{'这是实体身份上的谱标量，不作空间点采样或空间积分。' if i==23 else '输出是连续解在给定坐标的点值，不是任意计算单元的平均值。'}
只导出 outputs 引用的数值数组以及原样复制的 IDs 和输出时间轴；不导出输入权重、坐标、初态或其他未要求场。
需要所有字段及全部点；未要求的速度、压力、通量或特征向量不作为额外必交物。
'''
        # EVP generic entity observations permit point only? contract-specific
        # vocabulary is checked by the core before any numerical comparison.
        if i==23:dat=dat.replace('value_kind="integral"','value_kind="integral"')
        (path/'instruction.md').write_text('\n'.join(line.rstrip() for line in instruction.splitlines())+'\n',encoding='utf-8')
        (path/'DATA.md').write_text('\n'.join(line.rstrip() for line in dat.splitlines())+'\n',encoding='utf-8')
        if not config_path.exists():config_path.write_text(dumps(config),encoding='utf-8')
        (path/'author').mkdir(exist_ok=True)
        plan=grading(c)
        (path/'author/grading-template.json').write_text(dumps(plan),encoding='utf-8')
        rows.append(f"| 2.13.{i} | [{c['title']}]({c['task']}/instruction.md) · [DATA]({c['task']}/DATA.md) | `{c['source_id']}` |")
    (ROOT/'qbank/extensions/caeoj_ext/cfdcodebench/models.json').write_text(dumps(models),encoding='utf-8')
    runtime_path=ROOT/'qbank/extensions/caeoj_bundle/runtime.json';runtime=json.loads(runtime_path.read_text(encoding='utf-8'))
    runtime['extensions']['compat.cfdcodebench']=dict(version=1,requires=[],
        selectors=[{'physics.model':name} for name in models],check='caeoj_ext.cfdcodebench:check',
        files=['caeoj_ext/__init__.py','caeoj_ext/cfdcodebench/__init__.py','caeoj_ext/cfdcodebench/models.json','caeoj_ext/normalized_fields.py'],
        evaluators={'field.normalized_outputs':'caeoj_ext.normalized_fields:prepare'})
    for c in catalog():runtime['tasks'][c['task']]=['compat.cfdcodebench']
    runtime_path.write_text(dumps(runtime),encoding='utf-8')
    (SECTION/'README.md').write_text('# 2.13 CFDCodeBench 兼容题集\n\n保留24个来源题身份，语言和数值方法自由。general problem 仍为题库核心。\n\n题面与 DATA 以修订后的连续定义为准；原身份不表示与原排行榜成绩直接可比。参考、逐字段判分和本地验证状态见 [维护记录](author/README.md)，当前数据与发布定位以维护记录中的固定提交索引为准。\n\n| 编号 | 题目 | 来源身份 |\n|---|---|---|\n'+'\n'.join(rows)+'\n',encoding='utf-8')
    (WORK/'catalog.json').write_text(dumps(catalog()),encoding='utf-8')
    print(f'Rendered {len(models)} tasks')

if __name__=='__main__':main()
