# 表面管流约束修复作者记录

来源[Cantera#1655](https://github.com/Cantera/cantera/issues/1655)的最后气相物种参与反应时质量分数和漂移。固定单占位机制，避免依赖多占位SurfPhase修复。真实原件3/9通过（惰性末物种、零吸附、零转换），完整参考9/9；同时检验气相组成、表面覆盖、压力/密度/速度，不以sumY单一指标替代物理正确性。

## 来源、参考与独立核查

真实基线为完整Cantera v3.1.0，archive SHA、精确提交及修改边界见data-evidence/source.json。两题baseline镜像均逐文件核对原始archive的全部1284个文件，见pristine-baseline.json；没有预先应用其他题补丁。

需要区分三种来源：原件；上游PR的必要子集（不等于整个PR树）；作者完整参考。PR2018原样只加入d(sumY)/dz约束，真实基线及PR2018父提交仍把表面气相质量源循环写成覆盖赋值，不能通过独立连续性核查。本题完整FlowReactor参考还将该项改为所有物种贡献累加。该改动在同一个允许源文件内，是公开守恒及排序不变性要求的必要补足，不冒称上游已经修正。upstream-subset-replay.json保留原样子集的额外实际对照。多占位的“仅Flow”分支指这个完整Flow子集，矩阵中有明确标识。

正式参考由实际修复Cantera的FlowReactor/ReactorNet及需要时SurfPhase/InterfaceKinetics运行生成，replay.py不在driver重算或纠正任何观测。独立核查independent.py由指定三反应准稳态消元和可分离管流方程的闭式积分得到，直接表面属性按位点占据及质量作用律求和，不充当参考生产者。audit_data.py覆盖全部实际输入/参考/公开输出，并检查原子/位点守恒和有区分力的非法变体。算例是作者受原issue启发的简化回归，不声称是原始工业机理或Sandia实验。

所有case的实际参考误差远低于公开判据（逐量max_tolerance_fraction见reference-replay.json）；保留跨平台数值余量，错误原件及不完整修复的差异仍被明确检出。生成器使用确定seed，温压、入口混合、位点密度、速率区、观察位置和species排序各有物理或软件意义变化，公开样例01/02同时参与计分，其身份由data-manifest保留。

## 重建、制数及判题

prepare_runtime.py --output <工作目录> --docker <docker可执行>先对共享纯基线逐文件核验，再产生context和reference-context。共享环境caeoj-cantera1872-core:offline-sdk只提供未经修复的真实v3.1.0源码/对象及SDK依赖；需要从头重建它时见双温题作者材料中的runtime构建流程，不应用其generated参考头文件。本题context构建标记对应core:base，reference-context构建标记对应reference:fixed。

参考镜像每次强制删除与可信后端相同的object、真实版本.so及driver对象/可执行后重建，避免COPY较早mtime导致无事可做。CMake编译允许源文件，其他固定上游对象直接参与真实Cantera库重链接，可信driver也重新编译；原件构建、候选构建和运行分别由共享source_repair后端负责。没有替代求解器或逐题私有verifier。

依次执行generate.py、replay.py --mode reference、原件/不完整修复对照、audit_data.py、既有data pack/upload/assemble/verify。判题配置唯一归属逐例reference/grading.json，作者模板仅制数；资源与替换声明分别归judge-config和harbor/source-repair.json。公开包用publish_dist，Harbor用prepare_harbor，实际Oracle只运行oracle agent，不调用付费考生。

最终独立设计、考生题面/考试材料、数据和后端审阅，以及固定HF回取、严格verify、最终Oracle和可信探针证据均已归档到data-evidence。有限权限/网络探针只证明实际列出的路径及条件，不外推为全容器安全认证。

## 最终验收事实（2026-10-23）

HF固定提交`3dc6f98310bbb04871ac5c51d5dcdd544fa2687a`，已用空缓存独立回取装配并严格verify通过。公开ZIP SHA256 `79ace2ad25027a9bd9c45af41846ebacb7f7665e0e5572b3d7b2ff672b6fd8bc`；题面/DATA/CONTRACT及公开样例白名单见public-materials-freeze.json。最终Harbor原始job为runs/harbor/jobs/repair22-cantera1655-oracle-final，独立verifier真实9/9，exception=null。五模式可信后端探针各通过，保留有限路径与条件边界。

独立设计报告design-review.md、考生题面与考试材料报告candidate-review.md、全部实际数据审计data-review.md、后端审阅backend-review.md均已归档。后三项为两题同批报告，本题部分按报告中的题名与路径识别；同批保存不意味着互相代替逐题证据。主整合者维护正式完成计数，本题维护材料不重复中央进度。公开冻结三文件与ZIP未因归档更改。
