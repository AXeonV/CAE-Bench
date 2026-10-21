# 第二章十例候选参考建设

本批在 `cases/chapter-02-ten-reference-candidates` 工作，基线是
`1740d71a86bcb9260b3b3fdde7feb6ab28ed2735`。目标为第二章除2.1.1、2.1.3
外63题各补足10例。HF仅只读核对固定提交
`d46b17a03d444646157e1e2fe4b4f00587dc5d89`；该提交没有目标题目的池。

用户要求先设计全部工况，再计算参考；本阶段不做数值验证、交叉验证、
HF上传、正式选样或模型评测。旧FOAMBench任务保持停止。
随后用户明确选择：继续寻找现成求解器，未匹配的题暂缓，不能扩展物理模块。

## 设计材料

- [CATALOG.md](CATALOG.md)：63题的逐题索引。
- [COVERAGE.md](COVERAGE.md)：逐题覆盖矩阵索引；设计分配不等于已实现。
- [ALL-CASES.md](ALL-CASES.md)：630项设计的可读列表。
- [SOURCE-RESEARCH.md](SOURCE-RESEARCH.md)：已定位实现、匹配限制和待查闭合。
- [index.json](index.json)：文档指纹、来源索引和状态。
- 各题 `author/chapter02-ten-20261020/design.json`：每例的意图、有效差异、
  全部SI参数、几何构造、初边值、源、物理时间、观测、生产者匹配风险及待办。
- [scenarios.py](scenarios.py)：物理实验草案，不是求解器，不生成答案。
- [build_designs.py](build_designs.py)：确定性生成设计清单。
- [detailed_design.py](detailed_design.py)：逐例数值实验定义，不是PDE求解器。
- [freeze_designs.py](freeze_designs.py)和[design-freeze.json](design-freeze.json)：设计完整性、逐题重复实验检查与固定文本摘要。
- [EXECUTION.md](EXECUTION.md)和[execution-summary.json](execution-summary.json)：最近一次收集的实际执行状态；不从设计文件中的执行前状态推断当前进度。

630项均已有详细数值实验定义，仍不能表述为630个实际输入包或630份参考。
根据全面覆盖要求，2.1工况已从十个闭腔实验调整为入口、牵引、周期、
滑移/对称、流量、分布源和初态的组合；先前20个闭腔配置不再作为本批十例选择。
其中2.1.2、2.1.4共6项保留完整闭腔工况。设计检查只说明数值定义、
单位、参数集合、初态/时间类型与覆盖分配完整，且没有完全相同的物理定义。
它不证明非线性求解状态、无回流、全湿、稳定性、精度或资源限制已满足。

## 计算规则

先完成全部可执行工况的设计冻结；明确暂缓条目不能混入执行队列。
不自行编写求解器或改变现成求解器的物理模块。可制作原生输入、边界条件配置、
网格与HDF5转换器；实际生产者必须有版本、固定镜像及源码定位。
文献明确给出解析关系时，可按技能规定求值；须明确区别公式生产者和原文数值求解器。

计算目录与旧FOAMBench目录隔离。只将脚本、设计、轻量索引和摘要留Git；
原生网格、完整场、日志、执行记录及输入参考载荷保存在Titan。
成功执行与输出存在不等于数值准确。结果必须标记 `unvalidated_candidate`，
不得在没有相应证据时报告稳态收敛、精度通过或适用于正式测试。

已接通的生产入口：

- [native_closed_cavity.py](native_closed_cavity.py)：未修改的OpenCFD icoFoam，6个瞬态闭腔。
- [polytropic_reference.py](polytropic_reference.py)：文献静水平衡公式、固定势与质量归一化，20项。
- [native_euler_transient.py](native_euler_transient.py)：未修改的rhoCentralFoam，18个无外源Euler瞬态；2个加速度源工况仍待原生源项匹配。
- [native_gas_film.py](native_gas_film.py)：未修改的Elmer ReynoldsSolver，可压缩等温气膜10项。
- [native_elmer_incompressible.py](native_elmer_incompressible.py)：原生Elmer FlowSolver的完整牵引、滑移、体力、Cross/Carreau/Carreau–Yasuda及流率适配。
- [native_maxwell.py](native_maxwell.py)：原生OpenCFD Maxwell的闭壁Oldroyd-B候选，保留预应变；节点场由原生FV场恢复。
- [native_lowmach.py](native_lowmach.py)：原生Elmer FlowSolver/HeatSolver耦合，保留基底加速度、Boussinesq修正、黏性耗散及温度物性。
- [native_immiscible.py](native_immiscible.py)：原生interFoam两惯性黏性相、零表面张力及相同体加速度，20项候选已实际装配。
- [native_sparta.py](native_sparta.py)：原生SPARTA的硬球/无碰撞工况，已接通盒形及矩形切孔/弯道/十字通道的原生曲面配置；原生统计经[sample_sparta_references.py](sample_sparta_references.py)及[sparta_reference.py](sparta_reference.py)装配四面体公共包。壁面事件观测补丁只读记录既有碰撞，不改变动力学；其源码、二进制和检查点摘要留在生产记录。
- [native_turbulence.py](native_turbulence.py)：原生SST/k–ε稳态RANS、LRR URANS、WALE尺度解析离散统计；局部体力按实际P0输入装配。
- [native_power_periodic.py](native_power_periodic.py)：原生OpenCFD幂律双端截断、周期源项及P1势旋涡初态的配置和转换。

这些入口是输入/输出适配器及原生配置，结果均为未验证候选参考。其余条目仍须匹配和装配。
不能把“找到了候选模块但适配未完成”说成“没有现成求解器”；具体闭合缺口与普通待执行工作在实际执行索引中分开记录。

在保留题面、DATA、grading-template和本目录的快照根目录中生成并冻结设计：

```powershell
python qbank/02-fluid-mechanics/author/ten-case-candidates/build_designs.py
python qbank/02-fluid-mechanics/author/ten-case-candidates/freeze_designs.py
```

生产脚本统一接受`--root <独立计算目录> --snapshot <冻结快照根目录>`，在Titan现有caeoj Python环境执行。
闭腔入口额外要求`--execute`；Euler与气膜可用`--limit`限制任务数。执行前检查主机、父级cgroup和已有任务的实际资源。
已有status.json的条目不会自动重启；失败后的修复须先核实容器结束状态、保留旧配置/日志，再只重做必要步骤。
新增队列通过[titan_resources.py](titan_resources.py)串行预约资源，最多40个一核任务，主机和52 GiB父级cgroup保留至少8 GiB实际内存余量。可回收缓存按Docker working-set口径扣除，不能将内层限额直接当实际用量。
队列只执行预先列出的有限工况；[finish_elmer_flow.py](finish_elmer_flow.py)是一次性后处理，不是持续Agent循环。
运行[execution_report.py](execution_report.py)收集真实载荷状态与摘要；它只检查文件存在与摘要一致性，不做数值验证。

[finalize_queues.py](finalize_queues.py)只等待显式给定控制器的PID/starttime身份，最多24小时后生成一次存储索引；不续算、不验证。
[finish_sparta_trial.py](finish_sparta_trial.py)仅在原试算自然结束且日志匹配已知averaging语法错误后保留旧目录、重做这一项；其他错误停止。

持久脚本调度、半小时短摘要巡检和有界维护见[AUTOMATION.md](AUTOMATION.md)。
[native_isothermal.py](native_isothermal.py)使用原生温度约束及精确状态关系；[native_compressible_thermal.py](native_compressible_thermal.py)使用原生完整总能量方程，幂律物性只注册已有原生类型组合。两者只运行明确匹配的子集。

[native_thermal_rans.py](native_thermal_rans.py)配置原生Elmer标准k–epsilon、FlowSolver和HeatSolver，覆盖2.4.1的10个稳态工况。原生无滑移壁处理、Pr_t=0.85及有效黏度Friction Heat闭合明确留在生产记录；输出扣除2rho k/3后施加静压规范。当前为实际启动的未验证生产队列，不是已确认精度的参考。

[native_thermal_urans.py](native_thermal_urans.py)复用原生Elmer KE/Flow/Heat配置，执行2.4.2前9个常值公开k/长度尺度初态的瞬态工况；全部请求帧独立恢复静压，实际输入补齐两项P0湍流初态。第10例由[native_thermal_urans_nonuniform.py](native_thermal_urans_nonuniform.py)和[native_initial_ke.py](native_initial_ke.py)单独装配：保留实际P0初值，经体积集块映射到原生P1节点；[InitialKE.F90](InitialKE.F90)只读入节点初值，不实现演化或物理模块。映射与近壁误差尚未验证。

[native_isothermal_rans.py](native_isothermal_rans.py)针对2.3.5使用原生rhoSimpleFoam、全Reynolds应力LRR及固定温度约束。公共包保持本题parameters协议；内部复用2.1状态关系/网格配置视图，不将其作为公共题目。源项为rho*a，绝对静压不扣除k或重新归零，参考仍未验证。

[finish_elmer_node_order.py](finish_elmer_node_order.py)只对已确认原生退出码0、因旧节点顺序断言而失败的一例重做转换；归档旧公共载荷，保留原生场，通过坐标双射恢复节点身份，记录转换摘要，不重新求解或声称数值验证。

[native_thermal_statistics.py](native_thermal_statistics.py)使用原生Elmer三维非定常Navier–Stokes/HeatSolver生成2.4.3的21个实际离散样本，先取单元平均再计算六项统计输出。不使用RANS方差或合成扰动；无显式SGS模型，DNS空间/时间分辨率及统计充分性未经核实，不能称为已验证尺度解析参考。原生瞬时样本与统计转换记录单独保留。

[retry_thermal_statistics_linear.py](retry_thermal_statistics_linear.py)只执行已归档的四项原生BiCGStabL线性迭代失败的一次UMFPACK修复。先核实容器已停止及明确错误，保留旧场和日志；物理、网格、1000步时间网格、样本时刻及收敛阈值不变，不自动无限重试。

[native_pyclaw_closed_flat.py](native_pyclaw_closed_flat.py)与[pyclaw_closed_flat_runtime.py](pyclaw_closed_flat_runtime.py)只装配2.9.2首例平床、零摩擦、反射壁工况。原生PyClaw Classic二维HLLE负责全部演化；实际公共P1水深通过三角形/矩形精确裁剪积分映射到原生有限体积均值，节点点值使用连续双线性重建，水体积使用原生面积积分。非平床、摩擦、储槽、孔洞、干湿条件不由该入口替代；精度未验证。

[native_pyclaw_bathymetry.py](native_pyclaw_bathymetry.py)与[pyclaw_bathymetry_runtime.py](pyclaw_bathymetry_runtime.py)扩展至另外五例封闭、全湿、零摩擦的地形工况。原生二维bathymetry f-wave处理底坡项；P1地形和水深均作精确单元积分映射，干容差只记录为原生数值配置，不能据此声称干湿题已适配。

### 浅水储槽的有限适配

`native_pyclaw_reservoir.py`仅处理 2.9.2 第07例：实际公开边界实体保存储槽水深的线性时间表，原生 PyClaw 的外部幽灵单元读取该表；内部单元由原生三波 f-wave Riemann 核的正负波传播更新。其他边界保持水墙，零摩擦。配置脚本见 `pyclaw_reservoir_runtime.py`。该入口不覆盖摩擦、孔洞或干湿界面；不作数值正确性声明。逐次源文件摘要、配置、原始场和执行状态保存在计算目录的维护证据中。

### 稳态浅水的有限原生队列

`native_pyclaw_steady.py`只处理矩形、无孔洞、零摩擦的稳态浅水五例；收缩与扩张的多边形域不在该入口范围。`pyclaw_steady_runtime.py`使用原生 PyClaw f-wave，在两端设置储槽外部幽灵状态，侧面为水墙。初始水深和流速只作私有迭代种子，公开稳态输入不含初始条件。最多推进1000个一秒窗口，连续五个窗口的逐守恒分量归一化变化率小于1e-8才生成候选参考，否则保留迭代上限状态与原始输出。该收敛停止条件不构成离散误差或数值正确性验证。

### 干湿浅水的原生实现与输入表示

`native_pyclaw_wetdry.py`使用镜像中已编译的 Clawpack 5.9 `sw_aug_2D`，对应官方 `rpn2_sw_aug.f90`、`rpt2_sw_aug.f90`。该原生实现包含干区跳过、干湿界面和地形处理；不使用仅适用于湿区的 HLLE/普通 f-wave 核，不添加人工水深。有限队列只含矩形、无孔洞、零摩擦、全水墙的五例；复合几何继续待适配。采用一阶原生推进，输出在真实内部节点进行连续守恒变量重建，正水深时速度为动量/水深，零水深时速度为零。计算完成不表示干湿前沿或空间误差已经验证。

`shallow_reservoir_fields.py`把储槽常量速度明确写成同边界位置的 P0 平均字段，边界水深字段同样使用平均值语义。原有输入归档，已算参考文件摘要保持不变；这是表示修复，不是重新计算或物理变更。后续储槽生产者复用该转换。

干湿储槽第07例由 `native_pyclaw_wetdry_reservoir.py` 复用同一原生干湿生产与输出装配流程，`pyclaw_wetdry_reservoir_runtime.py` 只把公开时间表映射到外部幽灵状态，内部水深和动量由原生 Riemann 波传播推进。初始干区保留零水深，其他边界保持水墙。该入口只处理已冻结的矩形、零摩擦工况，不覆盖复合几何或摩擦闭合。

### 无黏可压缩时变体力

`native_euler_gravity.py`处理两例时变体加速度工况，复用已有初态、网格和输出装配。原生 `rhoPimpleFoam` 在零黏度和零导热下推进动量及总能量形式；原生 `SemiImplicitSource` 的 `exprField` 分别计算 `rho*a` 和 `rho*(U dot a)`，加速度严格按实际公开输入样本作分段线性插值。没有新增或编译物理模块，不能把这个无黏等价配置直接用于要求完整黏性应力做功的工况。原生源文件及摘要、配置和实际日志保存在计算目录的维护证据中。

热统计线性故障复用 `retry_thermal_statistics_linear.execute` 的有限执行器。每次仅消费维护目录中已保存的退出与归档证据；存在修复后工况目录就拒绝重复执行。自然对流新增故障的单例入口为 `retry_thermal_statistics_natural_convection.py`，仅将已结束任务的线性方法改为原生 UMFPACK，保留原始计算记录。

`codesaturne_mesh_adapter.py`为首个冻结热压缩工况制作同坐标、同连接和同实体身份的公开MSH4.1与原生MSH2.2网格，并实际执行Code_Saturne预处理器。热边界物理组分别保留热墙、冷墙和绝热墙。该步骤仅完成网格适配，不生产参考解；热物性XML、原生应力做功与体积黏度定义的源码摘要及后续边界/稳态映射待办保存在计算目录维护记录中。

`codesaturne_boundary_setup.py`在原生配置API中建立三组无滑移壁和温度/绝热分区，温度边界由原生 `cfxtcl` 转换成相应能量边界，不直接用 `cv*T` 替代温度条件。数据准备通过 `code_saturne run --initialize` 执行；该步骤没有调用 `--execute`。闭域质量库存、稳态收敛停止及输出装配完成前，不把这一配置计作参考解。

原始热统计队列结束后新发现的混合逆向对流线性故障，由 `retry_thermal_statistics_remaining_linear.py` 消费单独归档的有限清单，继续复用同一个修复执行器；不重复已经采用UMFPACK的工况。
