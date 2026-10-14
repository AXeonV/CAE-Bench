# CAE-Bench-OJ 公开算例来源参考清单

整理日期：2026-10-14。

用途：供自动发现、提取和改编工程算例的 Agent 参考。范围包括传统基准、软件验证手册、可运行示例、实验数据集和 Agent Benchmark，不限于 CFD 或数学 PDE。

本清单包含 45 个候选来源，排除正在另行处理的 **PDEBench** 和 **PDEAgent-Bench**。

本文件整理自已有检索结果，并非逐例验收报告。列入清单只表示可能提供有用算例，不代表其中所有输入、参考答案、许可证和下载入口均已逐项核验。部分商业软件模型需要许可证运行，部分基准文档需要购买。“可用材料”描述来源提供的内容，不表示可以直接作为 OJ 标答。

## 1. 结构力学、振动、接触与土木工程

| 编号 | 来源 | 可能提取的题目 | 可用材料 |
|---:|---|---|---|
| 1 | [NAFEMS Benchmarks](https://www.nafems.org/publications/resource_center/p18/) | 梁、板、壳、热应力、自由振动；其他系列涵盖非线性问题 | 独立问题规范、参考目标值；部分文档付费 |
| 2 | [Abaqus Verification / Benchmarks / Example Problems](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEVERRefMap/simaver-c-ov.htm) | 弹塑性、超弹性、接触、屈曲、动力学、热耦合 | 问题说明、比较结果；输入文件随软件提供，可用 fetch 提取 |
| 3 | [Ansys Workbench Verification Manual](https://ansyshelp.ansys.com/public/Views/Secured/corp/v261/en/pdf/Ansys_Workbench_Verification_Manual.pdf) | 静力、模态、屈曲、瞬态结构、热分析 | 验证案例、参考来源与结果；模型获取条件逐例确认 |
| 4 | [SOFiSTiK Verification Benchmarks](https://docs.sofistik.com/2026/en/verification/index.html) | 梁板结构、振动、稳定性、预应力及结构设计计算 | PDF 说明和 ZIP 输入文件，适合超出 PDE 场求解的工程题 |
| 5 | [Code_Aster 验证案例](https://code-aster.org/doc/v14/index.html) | 非线性材料、接触、断裂、动力学、热机械 | 验证文档；相应输入文件位于 astest 测试库；此链接为 v14 文档 |
| 6 | [CalculiX Test Examples](https://www.dhondt.de/) | 弹性、塑性、接触、模态、热应力 | 可下载输入文件、测试示例和手册 |
| 7 | [FEBio Verification Problems](https://febio.org/site/uploads/maas_jbme_2012.pdf) | 超弹性、软组织、双相介质、接触 | 解析解和跨软件比较案例；模型文件需继续逐项定位 |
| 8 | [OpenSees Verification & Validation](https://opensees.berkeley.edu/wiki/index.php/VerificationAndValidation) | 框架、结构动力响应、材料模型、岩土问题 | Tcl 示例及与手算、文献或其他软件的比较 |

## 2. 通用多物理场软件与算例库

| 编号 | 来源 | 可能提取的题目 | 可用材料 |
|---:|---|---|---|
| 9 | [COMSOL Application Gallery](https://www.comsol.com/models) | 结构、热、电磁、声学、流体、化学、MEMS | 大量模型和建模说明；另有[验证与验证模型集合](https://www.comsol.com/blogs/now-available-collection-of-comsol-verification-and-validation-models) |
| 10 | [Elmer FEM](https://github.com/ElmerCSC/elmerfem) | 结构、热、电磁、声学、流动及耦合 | 教程、fem/tests 与示例输入；参考性质逐例审查 |
| 11 | [MOOSE Physics Modules](https://mooseframework.inl.gov/modules/index.html) | 固体、接触、相场、孔隙流、热传导、化学耦合 | 模块示例、输入文件与测试；应区分回归测试和精度验证 |
| 12 | [MFEM Examples & Miniapps](https://mfem.org/examples/) | 多材料弹性、非线性弹性、模态、电磁、Darcy 等 | 源码、网格；部分算例有精确解和误差计算 |
| 13 | [deal.II Tutorials](https://dealii.org/current/doxygen/deal.II/Tutorial.html) | 弹性、接触、塑性、热、流动与多场问题 | 完整程序、数学说明和结果讨论 |
| 14 | [Coupled Theories FEniCSx Codes](https://github.com/SolidMechanicsCoupledTheories/FEniCSx_codes) | 有限变形、粘弹性、热弹性、凝胶、电弹性 | 耦合模型的开放实现，适合作为新题与参考程序起点 |

## 3. 流动、自由表面与流固／热流耦合

| 编号 | 来源 | 可能提取的题目 | 可用材料 |
|---:|---|---|---|
| 15 | [DFG / FEATFLOW Benchmarks](https://wwwold.mathematik.tu-dortmund.de/~featflow/en/benchmarks/cfdbenchmarking.html) | 圆柱绕流、上升气泡等 | 明确设置、观测量和数值比较；部分有网格／时间步研究 |
| 16 | [NASA Turbulence Modeling Resource](https://www.nasa.gov/nasa-turbulence-modeling-resource/) | 平板、翼型、凸包分离流及湍流模型验证 | 网格、模型定义、数值结果、实验或 DNS／LES 数据 |
| 17 | [SU2 TestCases](https://github.com/su2code/TestCases) | 翼型、喷管、可压缩流、传热及多物理场 | 网格、配置和测试案例；参考用途需逐例确认 |
| 18 | [OpenFOAM Tutorials](https://doc.cfd.direct/openfoam/user-guide-v13/tutorials) | 多相流、传热、可压缩流、燃烧等 | 可运行算例与设置，适合提取问题；教程结果未必是独立标答 |
| 19 | [SPHERIC Validation Tests](https://www.spheric-sph.org/validation-tests) | 溃坝、冲击、自由表面及流固作用 | 题目规范、实验设置与测量数据 |
| 20 | [preCICE Tutorials](https://precice.org/tutorials) | 弹性挡板、共轭传热、换热器等 | 多求解器耦合输入文件与运行说明，适合耦合任务 |

## 4. 电磁、光学、声学

| 编号 | 来源 | 可能提取的题目 | 可用材料 |
|---:|---|---|---|
| 21 | [COMPUMAG TEAM Problems](https://www.compumag.org/wp/team/) | 涡流、非线性磁场、电磁力、电机、感应加热 | 标准问题规范，部分提供实验、解析参考与输入数据 |
| 22 | [NIST µMAG Standard Problems](https://www.ctcms.nist.gov/mumag/toc.html) | 磁化动力学、磁滞、平衡磁结构 | 标准参数、问题说明及多个提交结果 |
| 23 | [Meep Tutorials](https://meep.readthedocs.io/en/latest/Python_Tutorials/Basics/) | 波导传输、环形谐振器、散射及光学器件 | 可运行脚本；可提取透射谱、反射谱、谐振频率等任务 |
| 24 | [Bempp Tutorials](https://bempp.com/documentation/) | 声散射、声辐射、边界元问题 | 代码、几何及建模说明；参考解依据逐例检查 |

## 5. 电池、燃烧、流程与建筑能源

| 编号 | 来源 | 可能提取的题目 | 可用材料 |
|---:|---|---|---|
| 25 | [PyBaMM Examples](https://docs.pybamm.org/en/v25.4.0/source/examples/index.html) | 电池充放电、粒子扩散、热响应、退化 | 模型、参数集、实验程序；部分有 COMSOL 或实验比较；此链接为 v25.4.0 文档 |
| 26 | [Cantera Examples](https://cantera.org/stable/examples/index.html) | 点火延迟、层流火焰速度、反应器网络、热力循环 | 脚本、反应机理与输出；部分包含收敛分析 |
| 27 | [IDAES Examples](https://github.com/IDAES/examples) | 换热器、反应器、流程网络、动力系统、优化 | 可运行流程模型与教程，适合系统级工程计算题 |
| 28 | [EnergyPlus / BESTEST](https://energyplus.readthedocs.io/en/v24.2.0/tips_and_tricks/tips_and_tricks.html) | 建筑热响应、围护结构、HVAC、能耗 | 标准测试说明、验证报告及[软件测试模型](https://github.com/NatLabRockies/EnergyPlus)；文档链接为 v24.2.0 |

## 6. 多体动力学、颗粒、材料与岩土

| 编号 | 来源 | 可能提取的题目 | 可用材料 |
|---:|---|---|---|
| 29 | [Project Chrono](https://github.com/projectchrono/chrono) | 机构、关节、接触、车辆、柔性体 | 模型、演示与验证测试；旧 chrono-validation 已迁入主库 |
| 30 | [MercuryDPM](https://www.mercurydpm.org/documentation) | 颗粒碰撞、堆积、料仓与接触模型 | 教程、程序和测试，适合离散元任务 |
| 31 | [LAMMPS Examples](https://docs.lammps.org/Examples.html) | 弹性常数、压痕、断裂、摩擦、热导率、颗粒 | 输入脚本、初始数据和示例日志；统计量与确定性轨迹要分别设计判分 |
| 32 | [OpenGeoSys Benchmarks](https://www.opengeosys.org/6.5.9/models/processes/) | 固结、渗流、热水力耦合、岩石变形、裂纹 | 多类问题说明、模型与测试资源；此链接为 6.5.9 |
| 33 | [GEOS Advanced Examples](https://geosx-geosx.readthedocs-hosted.com/en/latest/docs/sphinx/advancedExamples/Index.html) | 地质力学、多孔介质流动、裂隙与储层问题 | 模型输入、教程及基准示例 |

## 7. 科学机器学习 Benchmark 与参考数据集

| 编号 | 来源 | 可能提取的题目 | 可用材料 |
|---:|---|---|---|
| 34 | [PINNacle](https://github.com/i207M/PINNacle) | 热、波、复杂几何流动、反应扩散等 | 方程、条件、参考场及参考求解器说明 |
| 35 | [CFDBench](https://github.com/luo-yining/CFDBench) | 方腔、管流、溃坝、圆柱绕流 | 变化物性、边界和几何的数据；Fluent／ICEM 生成材料 |
| 36 | [FlowBench](https://huggingface.co/datasets/BGLab/FlowBench) | 复杂障碍物上的流动与热耦合 | 几何、条件和参考场，适合几何变化题 |
| 37 | [AirfRANS](https://github.com/Extrality/airfrans_lib) | 不同翼型、攻角和 Re 的 RANS | 非结构网格、流场及翼型表面信息 |
| 38 | [LagrangeBench](https://github.com/tumaer/lagrangebench) | 涡流、方腔、反向 Poiseuille、溃坝 | SPH 粒子轨迹与生成方法 |
| 39 | [PDEArena](https://github.com/pdearena/pdearena) | NS、浅水、Maxwell | 时空轨迹、生成资源与评测代码 |
| 40 | [The Well](https://polymathic-ai.org/the_well/datasets_overview/) | 声散射、流体、反应系统、磁流体等 | 多来源仿真数据与元数据，需逐个子集审查 |

## 8. Agent 相关工作中的算例

| 编号 | 来源 | 可能提取的题目 | 可用材料 |
|---:|---|---|---|
| 41 | [CodePDE](https://github.com/LithiumDA/CodePDE) | 对流、Burgers、反应扩散、可压缩流、Darcy | 问题描述、开发／测试输入与数值基线 |
| 42 | [FEABench（Google）](https://github.com/google/feabench) | 热学、结构特征频率及多物理场 | Gold 完整题目与目标值；Large 提供 COMSOL 教程索引；勿与 Microsoft 的软件工程 FEA-Bench 混淆 |
| 43 | [CFDLLMBench：CFDCodeBench / FoamBench](https://github.com/NLR-Theseus/cfdllmbench) | 输运、激波、对流、涡卷起及 OpenFOAM 工程流动 | 题面、参考程序或算例文件 |
| 44 | [HWE-bench](https://github.com/svd-ai-lab/hwe-bench) | 流体、电池、燃烧等工程任务 | 题面、oracle 与 KPI 材料；运行就绪程度需逐例确认 |
| 45 | [SimBench](https://github.com/uwsbel/SimBench) | 多体、车辆、机器人、有限元数字孪生 | 基于 Chrono 的任务与模型生成素材 |

## 9. 后续逐例筛选建议

优先扩展 CFD 之外题库时，可先检查 NAFEMS、SOFiSTiK、CalculiX、Code_Aster、TEAM、OpenGeoSys、Chrono、PyBaMM、Cantera 和 IDAES。

可考虑的输出不限于完整场，还包括位移／应力、固有频率、屈曲载荷、电磁力、机构轨迹、电池电压、点火延迟和换热性能。

为每个具体候选记录：

- 问题定义是否完整，几何、材料、条件、单位和输出是否明确。
- 原始输入、网格、数据和模型文件能否实际获取。
- 哪些参数或场可以变化，以及变化后是否仍有对应参考结果。
- 参考量来自解析解、收敛数值解、跨软件比较、实验测量还是回归输出。
- 代码与数据各自的复用条件、来源版本和稳定下载入口。
- 下载与计算规模，能否先选少量代表性 case 建立工作流。
- 转化为 general problem 时新增了哪些定义，哪些范围仍缺少依据。

参考数据公开可获取，不等于已经具备我们判分阈值所需的精度保证。不同来源的同一经典算例也应去重并保留关联。此清单是候选发现入口，不是正式题目或验收标准。
