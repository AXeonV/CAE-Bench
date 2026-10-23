# 双温状态修复作者材料

来源为[Cantera issue1872](https://github.com/Cantera/cantera/issues/1872)。固定真实源码为v3.1.0，精确提交、archive SHA和改动边界见data-evidence/source.json。上游PR2101含较广热力学重构，本题仅回移双温状态方程和直接TD/TP设置路径；参考generated/PlasmaPhase.h只覆写总压和设置总压时的密度关系。不存在其他题补丁。

## 复现与独立依据

public/driver.cpp通过ThermoFactory创建真实Cantera相，用ThermoPhase虚接口设置T/D/P/Te并获取观测；不在驱动重算或纠正答案。public/plasma.yaml定义三物种及常数热容，热容不参与本题输出。generate.py制作12族、每族12状态；原始issue族保留300 K、rho0.6415和O2/E各半，仅改变最终Te。其余为作者改编回归，非声称来自上游实验。

replay.py在固定原件与修复库上运行同一驱动，参考确由Cantera输出写入HDF5。独立核对按混合理想气体的逐物种分压与质量求和；audit_data.py重新从全部实际输入计算，用不同表达路径核对全部参考和公开样例，另核查非法mode、温度、密度和组分被拒绝。固定密度的Te变化、固定总压重设、零电子、等温、冷热电子及微量电子均有实质覆盖。本题不评价化学势、平衡、热容和电子分布求解。

## 构建和可信判题

prepare_runtime.py --output work/repair-22/cantera-1872-rebuild --sdk-wheels <已核验SDK构建工具wheel目录> 准备构建context与reference-context；对context执行docker build，标记caeoj-cantera1872-core:offline-sdk，再构建reference-context。runtime.Dockerfile完整说明实际依赖与真实上游全量对象的生产步骤。SDK缓存只提供协议依赖，不是物理参考。public源码包保持原始完整许可证。

最终增量目标重新编译PlasmaPhase.h的全部直接/传递上游依赖闭包：PlasmaPhase.cpp、ThermoFactory.cpp、ElectronCollisionPlasmaRate.cpp、ReactionRateFactory.cpp，以及可信driver；其余固定上游对象重链接同一真实Cantera库。CMake object、真实版本共享库和driver对象/可执行均强制删除重建，避免头文件布局和未来mtime缓存问题。具体配置只归harbor/source-repair.json。源码、非替换头文件、构建材料与驱动源由root持有且无组/其他写权限，构建后产物由共享后端冻结。

初次Oracle失败来自SCons写源码根cantera.conf而被低权限拒绝，属基础设施；后续转为真正CMake目标后实测通过。不能以此前失败或未完成权限探针的旧成绩替代最终验收。最终Oracle及probes记录放data-evidence，原始日志位于独立runs/harbor/jobs/repair22-cantera1872-*和work缓存。

## 数据与审阅

data-manifest.json是本题选样唯一归属；固定HF回下载及strictverify证据放data-evidence/hf-fixed-assembly.json和strict-verification.json。使用既有CLI pack/upload/assemble/verify，不手改装配回执。公开样例01/02同时是计分case，身份由selection保留。

独立设计范围审阅、考生题面/考试材料审阅、独立后端审阅的最终记录须归档后才宣称全部交付完成。实际付费考生Benchmark不在本轮授权验收内，Oracle只验证真实构建、执行和判分，不构成模型成绩。

最终验收：独立范围设计、三文件及实际公开考试材料审阅均通过，最终后端独立审阅已关闭头文件依赖闭包和非替换头文件权限缺口。最终只读镜像Oracle12/12、4种后端实际probe通过；此前SCons和未完成权限修复的旧镜像结果不替代本次证据。HF固定提交为ffd36ebc2f604ccb6b37889f8a27275bee803376，官方远端assemble complete与严格valid已核实；12例中公开2、隐藏10。全部细节及有限探针边界见对应data-evidence文件。

公开限制补明：现行公开包已明确此前后端一直执行的每文件1 MiB上限；当前/原包摘要及逐项差分见[source-size-clarification.json](data-evidence/source-size-clarification.json)。独立[有界变更复核](../../../../design/reviews/repair-source-size-clarifications.md)通过，源码、SDK、输入、参考、评分和驱动载荷均未变。上述Oracle、安装和考生/数据审阅记录保留各自历史冻结包身份；本轮未把它们改称运行新包，也未无故重复相同数值计算。当前公开版本由新包摘要与该有界复核单独绑定。
