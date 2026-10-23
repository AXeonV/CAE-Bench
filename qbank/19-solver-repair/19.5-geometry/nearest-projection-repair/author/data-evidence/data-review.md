# 独立实际数据审计：最近投影与单元插值回退

结论：**通过**。全部10正式case共40查询，以及2sample的10个重复查询，完整几何、数组、参考输出和评分绑定均已检查。公开SDK对实际材料的26项验证全部通过。审计发现的mode整数类型声明歧义已明确修订并完成最终版本有界复核，无未决项；本报告不认证尚未结束的Harbor Oracle或资源测试。

## 范围、材料和固定版本

按caeoj-data-review技能只读审计。唯一解释依据为instruction.md、DATA.md、docs/CONTRACT.md；允许的manifest、全量cases/reference/samples及装配回执均完整读取。来源检查读取source.json、pristine-baseline.json、cases.json、reference-replay.json、defect-replay.json和author/README.md。仅读公开run_case.py的serialize/adapt中性转换函数来定位payload编码；未读取或运行driver、solver、参考cpp、作者独立实现/生成器，不从其补题意。

最终ZIP SHA256实测为`b0caa6437806ba5f7c92c1a41e4fd070481b9124e19dadf12985cbcb31ee797f`。原审计ZIP为`e14c27835494d87aaf42c3e334544f0bf17bc8b6f8e2a311e0e6f0c403bef029`；类型声明修订后重新发布，case/参考/评分未变。ZIP根MANIFEST里所有与本轮已审材料对应的资产SHA均匹配，public_samples=[01,02]。完整75文件路径/SHA见`runs/data-review/repair22-precice/evidence.json`：3解释文件、manifest/回执、10case×5资产、2sample×6资产、5来源证据、README、中性适配器及ZIP。全部实际JSON、MSH、HDF5数组完整读取，没有未读大数组。

| 解释文件 | SHA256 |
|---|---|
| instruction.md | f4c6bbdd0d905b6d9d92c4c3141ff9942ec0dd1a4443e893230d7c8edbfe4fb4 |
| DATA.md | bb545ebee229ed90e0c8b68c94625620b563f5133f447d600ffe239cef1e1a13 |
| docs/CONTRACT.md | 130d4416fd533812493780c8bc6afbc0a158de6800b59bbec14a852f3cf1c063 |

selection SHA256=`686a12d73bd054662e205de0eec52e2b6b1c9cf084b6e8603e7431fe08471c35`，装配固定revision=`7147150c427dcc21434d930a1c76b58070d3334c`。独立复算每个选样描述原文SHA、case ID、complete、所有载荷size/SHA及回执绑定全部吻合。官方`data verify --strict`返回valid=true、errors=[]，准确列出sample01/02与正式01/02共享身份；未重新选样或刷新绑定。inventory枚举12入口、gaps=0，not_evaluated不是本审计结论。

## 完整数组、网格和物理声明

从最终DATA独立构造字段规范，逐项比较array、quantity、unit、kind、完整component_shape和components、location、time_axis、dtype、value_kind和sampling。D=2/3、mode=0/1、固定model、空geometries/conditions、唯一source网格引用均准确。无外部依赖或未定义边界条件。

| 对照对象 | 公开依据 | 实际检查 |
|---|---|---|
| source.msh | DATA几何与模式、CONTRACT网格 | MSH4.1 ASCII，全部节点/点/边/三角/四面体及tag连接关系逐项解析 |
| node_ids/probe_ids/probe_coordinates/times | DATA数组与输入场 | 全源节点tag严格递增int64，probe非负递增int64，Q/D完整shape、范围和float64，times=[0] |
| nodal_values | DATA输入场 | 唯一场[1,V,3]、[-1000,1000]、a/b/c三个独立无量纲分量；piecewise_linear/constant/forbid精确声明 |
| projection | DATA输出 | [1,Q,D]，全局vector，x/y(/z)，m |
| distance | DATA输出 | [1,Q,1]，scalar/value，m |
| weights | DATA输出 | [1,Q,V]，node_TAG标签按完整node_ids顺序，无遗漏或转置 |
| mapped_values | DATA输出 | [1,Q,3]，a/b/c独立分量，unit=1 |

输入HDF5恰含5项：node_ids、probe_ids、probe_coordinates、times、nodal_values；输出恰含6项：4场、probe_ids、times。不要求复制未被输出位置引用的node_ids。完整dtype/shape/有限值、输出轴复制及HDF5扁平结构通过；无属性/子组/软外链/别名/外存储/虚拟dataset或非许可过滤器。

所有源节点数、原语数量、坐标与查询范围、不同节点间距和边长均合DATA。D=2全部z=0且无四面体。每个三角的3条边、每个四面体的6条边及4个面均显式存在；同一无序节点集无重复。逐三角/四面体、逐顶点检查边向量矩阵奇异值比≥0.01。另对同维原语各对，用独立线性规划检查相对内部不相交；本轮全部通过。节点不重合、原语非退化，未用隐含边面补齐资料。

源节点文件顺序与字段轴确有区别，例如case01的文件节点顺序[24,7,41]，node_ids=[7,24,41]；数学核查用tag关联坐标和场，不按读取顺序或tag数值猜几何。所有case与sample均如此独立关联后验证。

## 模式和几何变体实际覆盖

| case | D / mode | 边/三角/四面体数 | 查询数 | 主要实际分支 |
|---|---|---|---:|---|
| 01-triangle-fallback-public | 2/cell | 3/1/0 | 5 | 三角内部及外部边/顶点回退 |
| 02-spatial-cell-public | 3/cell | 6/4/1 | 5 | 四面体内部及面/边回退 |
| 03-isolated-near-vertex | 2/nearest | 1/0/0 | 4 | 独立节点胜过较远边 |
| 04-spatial-edge-only | 3/nearest | 2/0/0 | 4 | 3D降维边集合 |
| 05-closer-independent-edge | 3/nearest | 4/1/0 | 4 | 独立边胜过较远面 |
| 06-far-face-near-node | 3/nearest | 3/1/0 | 3 | 独立节点胜过较远面 |
| 07-cell-without-triangles | 2/cell | 2/0/0 | 4 | 无2D闭单元，全部nearest |
| 08-cell-without-tetrahedra | 3/cell | 6/2/0 | 4 | 无3D闭单元，投影到导出面/边 |
| 09-vertices-only | 3/cell | 0/0/0 | 3 | 仅节点回退 |
| 10-nearest-ignores-volume | 3/nearest | 6/4/1 | 4 | nearest忽略四面体内部 |

正式40查询中3个使用闭单元内插，37个使用nearest。权重正支持节点数1/2/3/4分别出现16/12/11/1次。case03、06各有1个不连接边面的独立节点，case09有3个；没有把点单元数量当作顶点候选的唯一来源。两个sample分别重复正式01/02的5查询。

## 独立几何及四输出数值

未读取preCICE或作者参考算法。按公开几何集合选候选：nearest总含全部节点及导出边，D=3另含导出三角，忽略D=2三角内部与D=3四面体内部；cell先检闭三角/四面体包含，否则同nearest。

对每个候选闭单纯形独立枚举非空顶点子集，在其仿射包做最小二乘正交投影，保留非负重心坐标，再比较欧氏距离，得到闭边/面端点约束下的最近点。未使用无限延拓的负权重。cell以完整闭单元重心坐标检查包含，多个包含单元须映射到同一完整节点权重。所有竞争原语若完整节点权重不同，其距离与最小值的最小实际间隔为0.022374841615668384 m，超过1e-6保证；共享顶点/边的零权重表达按同一完整权重处理。

完整权重、加权位置、欧氏距离、三场Σw_i value_i均逐查询检查，不只查sum=1或常数保持。全部权重非负且和为1，内部cell距离按定义为0。

| 输出 | 正式40查询最大绝对误差 | atol / rtol |
|---|---:|---|
| weights | 2.2204460493e-16 | 1e-9 / 1e-8 |
| projection | 1.3322676296e-15 m | 1e-8 m / 1e-8 |
| distance | 1.1443916996e-16 m | 1e-8 m / 1e-8 |
| mapped_values（三独立场） | 8.8817841970e-16 | 1e-8 / 1e-8 |

所有完整参考及sample输出均通过。全部12份grading.json的4quantity、单位、逐时刻逐分量pointwise、容差与instruction一致，reference.h5存在且完整；2sample output/result.h5与参考全数组一致。没有把参考自判分当成独立最近点认证。

## 来源生产者与输入/参考绑定

source.json固定preCICE issue1304/PR1351、基线`c2a06a65631e15a6622f5ecffae194f82ba0bae3`、上游head、merge、归档与树摘要。pristine-baseline.json记录962文件、all_files_match=true，其树摘要与source相同。此为既有源码完整性证据；本轮未重新读归档或镜像源码树。

最新README已将最初过时的“制作中/HF未完成”说明改为真实进度，并明确上游边/顶点修复和作者额外面/边完整比较的贡献边界，不把原样上游合并当成完整正确性证明。cases.json的D、mode、节点/查询数与全部实际资料一致；工况为作者依机制新增回归，未冒称原始耦合应用实验。

reference-replay.json生产者声明为实际固定preCICE query::Index，参考镜像80303206...；10份output_sha256与当前reference.h5逐字节一致，记录10/10通过。defect-replay.json记录实际原件镜像783e6987...，3/10通过；本轮没有读其装配范围外缺陷输出文件，不对该output_sha另作字节认证。

两记录明确input_payload_sha256为给真实C++driver的精确UTF-8 JSON；每个row另有problem.json、input.h5、source.msh三项raw input_assets摘要。从实际网格tag到排序节点轴、按单元tag排序的连接关系、查询及节点三场独立重建中性serialize payload，全部20个payload摘要和60个raw资产摘要吻合。10参考H5输出摘要也全部匹配。生产者与独立几何核查分别陈述，没有用生成器或生产实现作为数学预期。

## 最终ZIP SDK与独立声明变体

仅提取已固定ZIP的src/caeoj、caeoj_bundle、caeoj_task_ext运行包，每次新子进程将ZIP src置于优先PYTHONPATH，避开本地模块缓存；不提取/运行题目solver或driver。正式SDK对12实际输入、12完整参考及2sample输出共26次validate-input/output均通过，见`runs/data-review/repair22-precice/check_sdk.py`、`runs/data-review/repair22-precice/sdk-evidence.json`。最终重发后逐字节核对19个SDK运行文件与原测试运行包完全一致，故有界复用这些检查，未无理由重复求解或测试。

5个独立合法变体均接受：probe编号含0、三个节点场全零、场值−1000边界、不导出任何点单元但保留全部源节点、网格与查询同时放大2倍。18个非法变体均拒绝：mode=2或浮点1.0、node_ids反序/不属于网格、负probe ID、查询或场值越界、缺三角必需边、重复无序边、退化三角、重合节点、2D非零z、错误sampling、把三个非空间场声明为vector、weights标签反序、缺weights输出、多余node_ids输出、times非0。

发现与关闭：原DATA只写mode.value为“0或1”，未明写整数，独立variant=1.0被SDK以E_PROJECTION拒绝。为避免从实现反推有限标量参数的类型，审阅反馈后DATA现已明确“JSON整数，不使用浮点1.0/0.0或布尔”。该补明与既有SDK一致，未更改case/参考/评分/校验器。最终复核确认除DATA、其ZIP与MANIFEST摘要、README进度说明外，全部已审资产均未变；旧/新摘要及19文件SDK同一性证据见`runs/data-review/repair22-precice/final-version-review.json`。此项已关闭，无未决合法域分歧。

## 验证边界与复现

数学审计脚本为`runs/data-review/repair22-precice/inspect_all.py`，完整逐查询支持、间隔和误差见`runs/data-review/repair22-precice/evidence.json`。审阅者只在本审计目录写证据和副本；声明修订由协调方完成，未改正式数据、评分或真实实现。未重跑固定库、源码构建、离线镜像SDK安装、后端probe或Harbor Oracle；最新README已记录普通断网安装及SDK消费通过，本轮未亲自复验，不能因既有来源重放记录认证整个最终消费链。未做MPI/GPU、高阶几何、性能或资源实测，公开范围之外的问题没有被引入审计要求。

归档说明：诊断附件保留在原审阅目录，上述路径仅作归档定位，不改变审阅结论。
