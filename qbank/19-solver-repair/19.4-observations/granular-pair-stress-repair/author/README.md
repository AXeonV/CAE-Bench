# LAMMPS 来源与验收

固定基线、参考提交和源码摘要见 `data-evidence/source.json`；来源为 LAMMPS issue4219/PR4346。真实生产者是原始 `gran/hooke/history/kk` CPU Serial 路径，参考只应用上游两个同名 cpp/h 文件，不采用其它 PR 变更。归档保留原许可证、完整 src、cmake、内置 lib/kokkos 和相关文档；`source-manifest.json` 对每个原文件记录 SHA256。

`generate.py` 制作独立的合成颗粒接触工况，不冒称为上游实验。`replay.py` 在固定 image 中低权限、无网络运行真实 LAMMPS，使用严格装配的 SDK 写结果。`independent.py` 全枚举接触对，以弹簧和阻尼定律、力臂及成对外积核查全部输出；只用于作者审计。`audit_data.py` 核对所有实际输入、参考及公开输出、力平衡和跨统计量一致性。

源码范围是成对作用力与维里累加，以及全局/逐粒子同时请求时的分派与归约。必须同时保留两项能力。零初始历史的 `run 0` 避免要求本题之外的接触记忆演化；低于摩擦界限的输入不触发另一个滑移行为。

最终范围只支持 `newton pair off`。最初探索 `on` 在计算并输出瞬间后，仍由真实 `Verlet::cleanup -> FixNeighHistory::post_run -> FixNeighHistoryKokkos::pre_exchange` 抛错退出；它没有完成合法 run0。该辅助模块限制未由 pair 文件修复，不吞掉错误码取部分输出。原始失败 stderr 和三个原源码文件归档在 data-evidence/newton-on-unsupported-stderr.log 与 upstream-*.cpp；范围卡末记录调整。这不影响两项统计缺陷在 off 路径真实复现。

构建删除真实编译依赖闭包的三个对象（pair cpp、force.cpp、lammps.cpp）以及 main 对象、liblammps.so.0 和 lmp。真实 compiler .o.d 确认三 TU 传递包含可替换头文件；允许合法头文件实现调整时工厂与类布局同步，不以 mtime 判断是否重建。完整原库构建及二文件参考重建日志已归档。

当前完成的重放、数据审计、HF、Oracle及独立审阅分别以 data-evidence 内实际报告为准；不能将可行性运行或本说明当作其余步骤通过证明。

## 实际运行结果（独立审阅另行验收）

十二组真实参考均通过独立逐对公式和评分；原件仅2/12通过，10例检出应力错误，力和力矩控制仍保持。公式覆盖全部参考输出；data-audit.json另核对力平衡、两种统计量的总和、公开完整输出和非法声明，包括禁止引入newton on参数。

官方HF上传固定commit `d6ffd006f422ec9cbb1e5d337a9c294222b1c991`，新空缓存回取complete:true，strict verify valid:true。公开ZIP SHA256 `c62ed786a6a952584d2e6d403ced5683034481008b278e7a3c6a8b0ed98beef6`，仅公开samples01/02的10份输入/参考/输出资产，详见public-materials-freeze.json。

Harbor job `runs/harbor/jobs/repair22-lammps4219-oracle-final` 的独立verifier为12/12，exception=null，baseline真正重编并通过实际样例运行probe，候选完整依赖闭包重编。六模式后端探针覆盖valid未来mtime/产物哈希与ldd绑定/低UID权限和网络、语法错误、额外文件、缺编译器、缺运行时入口、实际候选C++死循环超时及子进程终止。超时v1正确判timeout但即时/proc断言未过，原件历史保留；最终最多2秒观察的重放首个状态为Z。不能用有限路径探针外推全容器安全，也不能从未记录的v1状态断言根因。

最终独立设计、考生题面与考试材料、全数据来源和数值审计、可信后端审阅均通过，分别归档于design-review.md、candidate-review.md、data-review.md、backend-review.md。考生与全数据审阅的诊断资产保留原runs维护路径；归档报告仅改诊断路径，不改结论。作者自审和Oracle不代替这些独立审阅。主协调者维护正式提交与完成计数。

公开限制补明：现行公开包已明确此前后端一直执行的每文件1 MiB上限；当前/原包摘要及逐项差分见[source-size-clarification.json](data-evidence/source-size-clarification.json)。独立[有界变更复核](../../../../design/reviews/repair-source-size-clarifications.md)通过，源码、SDK、输入、参考、评分和驱动载荷均未变。上述Oracle、安装和考生/数据审阅记录保留各自历史冻结包身份；本轮未把它们改称运行新包，也未无故重复相同数值计算。当前公开版本由新包摘要与该有界复核单独绑定。
