# Meep #2408：作者维护入口

本题修复真实 Meep 电非线性计算中的自动 DFT 抽样步长。来源为 [issue2408](https://github.com/NanoComp/meep/issues/2408)、[PR2413](https://github.com/NanoComp/meep/pull/2413)。固定 baseline `ccb3c372dc34ca75ce01f99c2b50e0e89ad0a203`、参考 head `50118dbc8e54ac022e9e17400f43cc56e5bac560`。公开说明位于 [instruction](../instruction.md) 与 [DATA](../DATA.md)；能力界限由公开材料定义。

当前实际结果：真实 Meep 9/9 reference、4/9 baseline；正式 Harbor Oracle-v1 9/9、exception null；公共 ZIP `caef0f38ac89be65ca67328eef4b4fadc5eb15cf54cf712397b3e3a82cb55706`。普通离线 pip 安装、移走 SDK 源目录后导入已安装包、两公开样例原件运行及判错、pip check 均通过。运行时包含的701个上游存档原始文件逐个 SHA 核对无差异；另有33个必要的Autotools生成文件（运行时目录734文件），701不是运行时目录全部文件数。固定HF提交 `f0b30c3f3abe16bba73136747d23aa458e9a91f2` 官方装配计46资产项changed0（9case×4、2sample×5），fresh缓存为9 descriptor+36唯一asset=45文件、strict有效；7个真实后端模式全通过，实际4CPU/4GiB，正式原件162.854秒、候选160.110秒均删135产物后重编。独立考生两个模式、最终设计有界复核及全数据审计已通过；全数据112个变体中31合法、81拒绝。独立可信后端报告亦已通过，全部设计、考生、数据与后端验收证据已就绪。中央完成状态与Git收束由root维护。

## 真实源码与构建

`prepare_source.py --work work/repair-22/meep-2408` 核验两个完整存档、701文件及上游精确四文件差分，公开原件，参考四文件保存在私有 generated。`prepare_runtime.py` 创建完整真实原件离线镜像。`runtime.Dockerfile` 使用原始 Autotools 构建完整 Meep C++；`public/CMakeLists.txt` 链接实际 `libmeep.so.30`。由于 `meep.hpp` 可修改，判题配置强制删除并重新生成135个原件/候选构建产物，覆盖所有头文件消费者。Fortran 编译器用于原项目配置的符号包装探测，计算驱动为真实 C++ FDTD。

原型曾遇旧版 `get_dft_array` 单点后处理崩溃/插值差异，正式驱动改用真实 `dft_chunk.dft`，不在适配器中重算频谱。`use_centered_grid=true` 使用真实库分量特定空间平均；H 时间标签相对 E 为半步。坐标使用 DATA 指定的一次有理除法，避免浮点表达顺序令单点闭包扩成两点。

## 数据与参考

`generate.py` 生成9个有效差异算例和2个公开样例。`replay.py` 在实际原件/完整上游参考镜像中运行同一驱动；每例保留输入、原生输出、完整 E/H 时间记录和精确命令/文件 SHA。`independent.py` 仅独立执行有限窗口 DTFT 求和，无作者 Maxwell 求解器。229800个实际时间步、442频率请求均逐复分量认证，最大误差约1.18e-13。`audit_data.py` 覆盖19个输入声明变体、5个输出评分变体；错 H 半步相位和错步长均判零。

额外真实物理核对见 `data-evidence/physics-check.json`：弱二次/三次非线性幅度比接近4/8，线性双测点传播相位与一维 Yee 色散关系一致。它们支持源/相位/非线性行为，不代替原生参考和逐时间步 DTFT。完整非线性区域及不同实际 chunk 分割均进入正式数据。

`data-evidence/` 保存源、原件/参考重放、独立 DTFT、数据变体、实际安装及源树核验。大体积原始 trace 位于 `work/repair-22/meep-2408/dataset/replay/`。首次正式 Oracle 状态位于 `runs/authoring/repair-22/repair22-meep2408-oracle-v1.json`。本轮不调用收费模型 Benchmark。

## 更新流程

源码/接口变更先重做原型和相应物理核验，再生成全部实际数据、官方 pack/upload/fixed-commit assemble/strict、重新冻结 ZIP、prepare 与真实 Oracle。独立审阅通过才更新正式完成状态。不要将作者日志、修复文件或 reference 放入公开包；不要把基线的错误样例输出称为参考。

独立最终报告：`runs/design-review/repair22-meep2408/revision-report.md`、`runs/candidate-review/repair22-meep2408-statements/report.md`、`runs/candidate-review/repair22-meep2408-exam/report.md`、`runs/data-review/repair22-meep2408/report.md`、`runs/configure-judge/repair22-meep2408/report.md`。原设计报告的NEEDSREVISION保留，最终增补关闭F1/F2/F3；不将增补称为新盲考生报告。

最终后端审阅已归档至 [author/reviews/configure-judge/report.md](reviews/configure-judge/report.md)，附4份实际检查证据JSON及材料版本表；`report.source.md`保留原报告字节，`archive.json`记录源/归档SHA及外部报告相对链接改写。原运行报告不修改。
