# 19.4.4 granular-pair-stress-repair：独立完整实际数据审计

## 结论与边界

按 caeoj-data-review 审计，结论：**通过**。范围为最终装配12正式case和公开samples01/02的全部实际输入、完整参考、评分及公开输出；没有将未加载的池条目或临时fixture计入实际覆盖。正式数据12状态、51粒子、37接触对；样例重复正式01/02，另读取6粒子/4接触对。合计14份输入HDF5、16份结果HDF5，所有数组/粒子/分量均完整读取，没有未读大数组部分。

本轮允许隐藏数据审计，与先前public-only候选审阅分开；先前报告及其读取边界未修改。数学预期只从最终 instruction.md、DATA.md 和 docs/CONTRACT.md 独立推导，不从作者实现补题意。来源JSON/README仅核身份、生产范围与绑定；未读取driver、pair实现、修复源码、reference.patch、作者generate/replay/independent/audit实现或其他隐藏题目材料。没有运行真实库构建/求解器、收费模型或正式benchmark，没有修改任务、装配回执或数据。

最终ZIP SHA=c62ed786a6a952584d2e6d403ced5683034481008b278e7a3c6a8b0ed98beef6，与本轮核验值一致。完整实际文件SHA在`runs/data-review/repair22-lammps/file-sha256.json`；解释三文档、manifest、全部输入/参考/评分/公开结果、ZIP、回执及来源JSON均有版本记录。

## 盘点、身份与消费核验

data-manifest选择12case/2sample与实际入口和回执范围一致；样例01/02的case ID与正式01/02相同，送分样例身份不消除，内部没有换成另一个同名数据。逐个检查回执记录文件的size/SHA；原始case描述由回执嵌入文本重算SHA，与manifest选择绑定相符，input/reference完整且case ID匹配。

固定装配revision为 d6ffd006f422ec9cbb1e5d337a9c294222b1c991。独立运行维护工具data verify --strict，valid=true、errors=[]，未刷新绑定或覆盖差异。这里只核本地固定装配，没有重新访问HF远端，不能把既有readback记录写成本轮远端重下载。

发布包MANIFEST的最终三文档及十份样例摘要与实际文件相符。中性SDK在本轮runs中从最终ZIP重新提取，放入新Python子进程专属PYTHONPATH，未用仓库源码替代发布SDK；实际导入路径记录于`runs/data-review/repair22-lammps/sdk-validation.json`。中性脚本没有执行pair代码。

## 逐字段对照与实际分支

|JSON路径/HDF5角色|公开定义|实际核对/覆盖|
|---|---|---|
|task、spatial_dimension、physics.model|granular-pair-stress-repair，3，instantaneous-granular-contact-v1|14入口逐份一致|
|geometries、meshes、conditions|空对象/空条件，无网格或边界力|全部入口一致，未补隐含外力|
|locations.particles / particle_ids|entities，严格递增int64，2≤N≤32，ID1..1000000|全部shape/dtype/唯一/排序/范围；每个输出原ID关联|
|locations.system / system_ids|entities，int64[0]|全部输入存在；只有实际输出使用system时才复制该轴|
|time_axes.instant / times|float64[0]，run0瞬间|全部精确值及输出复制身份|
|position|m，x/y/z，float64[1,N,3]|全部坐标/箱内球半径+0.1m余量、所有粒子对中心距≥0.05|
|diameter|m，value，[1,N,1]，0.1..1.5|每粒子检查；包含不同粒径，质量用球体积|
|material_density|mass_density，kg/m^3，value，100..10000|每粒子检查，不误当粒子质量|
|velocity|m/s，x/y/z，各−0.1..0.1|全部分量，包含静止和非零相对平动|
|angular_velocity|rad/s，x/y/z，各−0.2..0.2|全部分量，包含静止和非零转动|
|physics.parameters|仅L/kn/kt/gamma_n/gamma_t/mu/tally_mode七键的带单位常量|每键的集合、单位、有限值和DATA范围逐份核对|
|输入采样/元数据|particles/instant/point，uniform/constant/forbid；scalar或components|每字段array/quantity/unit/dtype/kind/component_shape/components均精确对照|
|force / torque|particles，N / N*m，x/y/z|全部粒子分量，所有模式必需|
|particle_virial|particles，N*m，xx/yy/zz/xy/xz/yz；每对一半W，正号|仅particle/both声明，完整逐粒子数值核对，不除体积|
|pressure_tensor|system，Pa，同六分量，sum_pairs(W)/L³|仅global/both声明，不含动能、压缩为正|

所有HDF5均按通用契约检查根层扁平dataset、有限值、完整shape/dtype、属性/链接/外部或虚拟数据/压缩约束、输入和输出精确key集合。输出保留必需IDs/时间，不导出无关输入。输入field名称与dataset key一致；system轴不能代替粒子轴或靠相同长度猜身份。

正式实际统计请求：global-only2例、particle-only2例、both8例。各例只声明并输出本模式要求的量；不要求缺省观测，不把未请求粒子virial等同零。

## 独立数值、力矩与非对称应力依据

在本轮先独立枚举每个无序接触对，再读取作者来源README/JSON；没有从作者independent.py借公式。按DATA算Ri=di/2、mi=rho_i*pi*di³/6，n=(xi−xj)/r、dv、vn、有效质量和包含转动项的vt；再算Fn、Ft，并检查每个实际接触Fn>0、|Ft|≤0.8muFn。无接触的对不累加，切向历史零，kt不产生初始弹簧项。

i受Fn*n+Ft，j受反向力；力矩为(−Ri*n)×Ft和(+Rj*n)×(−Ft)。对每对计算完整非对称W=(xi−xj)外积F，各粒子累加W/2，总体每对只加一次。输出只抽xx/yy/zz/xy/xz/yz，绝不做对称平均；全局压力再除L³。逐粒子W与LAMMPS stress/atom NULL pair相反号，不加动能或其他外力。

全部实际reference及公开output独立逐元素核对，全部在DATA容差内。`runs/data-review/repair22-lammps/evidence.json`保留每对ID/r/Fn/Ft/两侧力矩/完整W和独立期望输出、逐输出最大误差及容差比。非零转动/阻尼、粒径、密度和非对称W都实际进入比较，弥补之前仅公开样例静态弹簧覆盖的边界。

|正式case|N|模式|接触数|W不对称接触数|直径范围m|材料密度范围kg/m^3|
|---|---:|---|---:|---:|---|---|
|01-elastic-both-off|4|both|3|0|[1.0, 1.0]|[702.5117205566266, 1405.3278546243928]|
|02-single-both-off|2|both|1|0|[1.0, 1.0]|[1218.6768865117012, 1631.257999996357]|
|03-rotation-global-off|4|global|3|3|[1.0, 1.0]|[1013.5136173378303, 2034.9577829495115]|
|04-rotation-particle-off|4|particle|3|3|[1.0, 1.0]|[1262.8716836931007, 1915.2139288609187]|
|05-rotation-both-off|4|both|3|3|[1.0, 1.0]|[567.5296304038229, 1358.8947356061917]|
|06-polydisperse-both-off|4|both|3|3|[0.95, 1.2]|[609.4141184419863, 2047.7492711848859]|
|07-permutation-both-off|4|both|3|3|[1.0, 1.0]|[968.7197943293588, 1347.3445890871958]|
|08-cluster-both-off|7|both|6|6|[1.0, 1.0]|[643.0369589892713, 1683.4864377096253]|
|09-normal-global-off|4|global|3|0|[1.0, 1.0]|[870.0335467407249, 1889.3146863978302]|
|10-cluster-particle-off|7|particle|6|6|[1.0, 1.0]|[654.7372917792347, 2154.597482364722]|
|11-noncontact-both-off|3|both|0|0|[1.0, 1.0]|[630.5061164119282, 2140.3096033467223]|
|12-rotation-both-off|4|both|3|3|[1.0, 1.0]|[551.9577891916842, 1924.664675734495]|

第11例无接触，全部输出为零；其余按接触逐对和逐粒子核对，不使用整体平均代替局部。global-only/particle-only也独立计算全部物理量作内部依据，只比较其实际声明输出，不补额外参考字段。

|输出|全部实际参考及公开结果的最大绝对误差|最大误差/允许误差|
|---|---:|---:|
|force|1.364242e-12|4.006431e-06|
|torque|2.664535e-15|1.543475e-08|
|particle_virial|9.094947e-13|3.650194e-06|
|pressure_tensor|3.552714e-15|1.558139e-06|

## 发布SDK及合法/非法变体

新子进程共80项，零预期不符：12正式input+reference、2sample各reference/output为16次实际材料加载，其余64项是从最终DATA独立选择的变体。全部临时副本留在runs/variants，不计入真实case。

独立预期包括：L/kn/kt/gamma_n/gamma_t/mu与直径/密度/速度/角速度端点、N=2/32、最大合法ID、三种模式对应输出集合应接受；越范围、N=1/33、ID零/重复/越界、错误system/time、NaN、错误shape/dtype、缺失或额外输入/参数、错误单位/分量/采样、球越箱、重合中心、Fn为负、切向力超过0.8muFn应拒绝。三个合法模式fixture也加载其正确输出；输出缺量、多key、错轴、float32均拒绝。

固定newton pair off是题意事实，没有允许的JSON选择字段。向physics.parameters增加newton_pair=1（on）非法拒绝，增加newton_pair=0也拒绝；拒绝的是额外参数，而不是让输入重新定义固定后端组合。未拿不支持的newton-on真实库路径作为合法数据。

## 评分与实际消费

逐份grading.json核对version/direct_outputs/reference和policy版本；所有声明quantity的unit、pointwise/per_time/per_component、atol/rtol与instruction一致。force/torque/virial为(1e−7,1e−8)，压力为(1e−9,1e−8)。四个single-tally case的policy保留另一观测quantity的模板规则，但outputs/reference/result没有该量；该规则不激活额外判据或缺省零。已通过正式消费核实这一点，不能把未用policy条目误判成缺输出。

用最终ZIP CLI grade在独立子进程逐份消费12正式reference和2公开result，14次exit0；另从语义逐项核对评分，不以自判分取代独立物理检验。详见`runs/data-review/repair22-lammps/zip-grading.json`。

## 来源、pristine与真实生产者绑定

source.json给LAMMPS官方仓库、issue4219/PR4346、固定baseline 36dd4de3bce34fea2706595f5ac419625ec68c06、reference 70cbf051fe3b546d6c28c9188816f5420a758d80及源码归档SHA。来源明确只应用允许的KOKKOS pair cpp/h，省略PR的其他邻居/Brownian/通信等改动；范围不冒充整个PR或GPU/MPI/history传输均正确。

cases.json及author/README明确工况是作者构造的回归，不冒称上游数值/实验数据；实际参考生产者记录为真实LAMMPS gran/hooke/history/kk CPU Serial run0。独立公式在本题完整公开定义之内，本轮不将临时公式核对程序当参考生产者。

source-manifest.json有5380项原文件摘要，与pristine-baseline声明未修改文件数相符，pristine记录full_source_sha_match=true。source.reference_source_sha256与oracle-build-report.sources_sha256逐项一致，后者记录成功重建、删除pair/force/lammps/main对象与库/可执行及新产物摘要。只审这些来源/构建记录，不读取源码或重建库；不能把该记录审阅写成本轮重做pristine源树校验。pristine记录使用base镜像标签，回放记录另给不可变镜像摘要；本轮没有解析标签或复验其内容。

reference-replay固定生产镜像sha256:033139463521ca0bc83b509fafc3a043f7e5eeef92aeebcf838f24079dbb35d2。逐case把output_sha256与实际reference.h5原字节SHA比较，12/12一致；再将oracle.input_assets的problem.json/input.h5与实际输入逐文件SHA核对，oracle.assets的grading/reference与实际文件相符，防止旧输入的生产记录被用于当前参考。这里hash明确匹配完整文件，未猜测为payload摘要。reference/baseline回放的runtime_id一致只记录为运行器身份一致，不把它擅自解释成输入摘要或源码证明。

reference回放12/12；baseline-replay实际仅03-global与11-noncontact通过，合计2/12，其他10例检出统计差异。该记录证明缺陷敏感性范围，不代替本轮独立数值判断。`runs/data-review/repair22-lammps/source-binding.json`保存全部当前输入/参考与producer输出摘要及source/build/manifest/回执核对。

## 未验证项与交付

本轮没有执行LAMMPS、库编译、GPU/MPI/newton-on、历史转移或时间积分，没有核验隐藏输入之外的未选池条目，没有访问上游或HF重取源码/镜像/数据，也没有重做真实资源/安全后端探针。没有从既有build耗时或回放日志宣称本轮资源达标。公开定义、实际数据结构、全参考数值、发布SDK接口和既存生产记录绑定的检查已完成；未发现输入越界、来源错绑、数值错误或影响读取的未定义分支。

证据文件：`runs/data-review/repair22-lammps/file-sha256.json`（完整逐文件SHA）、`runs/data-review/repair22-lammps/evidence.json`（所有对/数组/数值误差）、`runs/data-review/repair22-lammps/source-binding.json`（来源与当前输入/输出绑定）、`runs/data-review/repair22-lammps/data-verify.json`、`runs/data-review/repair22-lammps/sdk-validation.json`（80项）、`runs/data-review/repair22-lammps/zip-grading.json`（14次）。保持上一轮public-only候选报告不变。

## 解释材料与发布包实际版本

其余文件完整SHA见`runs/data-review/repair22-lammps/file-sha256.json`。

|文件（仓库相对）|SHA256|
|---|---|
|qbank/19-solver-repair/19.4-observations/granular-pair-stress-repair/instruction.md|47e8fce53843e29f3824abd3b25aeb24edc37e5785776168f92aa0636a1193fb|
|qbank/19-solver-repair/19.4-observations/granular-pair-stress-repair/DATA.md|b38e80d72ae2116f0050be3c69f01592197ce356bac713c9915da53675427197|
|docs/CONTRACT.md|130d4416fd533812493780c8bc6afbc0a158de6800b59bbec14a852f3cf1c063|
|dist/granular-pair-stress-repair-agent.zip|c62ed786a6a952584d2e6d403ced5683034481008b278e7a3c6a8b0ed98beef6|
