# Case 判题后续修复与验证

2026-10-17，基于 PR20 的 `bb897f3` 修复三项实际消费问题。当前规则由[存储设计](../DATA-STORAGE.md)、[数据操作](../../maintenance/DATA-SYNC.md)及[评测维护说明](../../maintenance/EVALUATION.md)拥有；本页只记录原因、证据及验证边界。

## 修复

1. **Harbor 漏复制嵌套资产。** 原来仅遍历 case 顶层文件。现在从已校验清单收集 problem.json、data_file、全部 mesh／geometry 文件，按原相对路径复制；不递归带入未引用文件。复制后的暂存输入与参考重新加载及预检，通过后才替换旧任务。回归将 HDF5、网格和几何移入 assets/nested，验证字节保留、可判分且私有笔记不进入 verifier。
2. **测试依赖本地题库。** 统一使用 tests/task_fixtures.py，在系统临时目录离线生成输入、参考、样例及源码项目；不读取或复制 task 根层的现有载荷、清单或回执，也不把数据写入 qbank。发布、Harbor、协议和数值测试均改用这些 fixture。HF 完整性测试自己建立本地池并通过真实 assemble 生成回执。顺带修复普通 Windows 入口的 UTF-8 读取，包括固体作者规划 JSON。
3. **送分样例被严格检查拒绝。** 跨测试／样例角色显式选择同一 case ID 与描述绑定时允许计分，报告 public_cases；Harbor 将身份保存至私有 selection.json，成绩报告保留对应关系并在执行行标记 public_sample。分数、测试总数和通过率分母均不删减。指纹保存全部先前条目，仍拒绝角色内部重复和不同池条目的输入／来源轨迹重叠，不能借公开样例掩盖其他重复。

## 验证证据

- 发布、Harbor、池工具定向组合：53 passed、16 subtests passed。包括嵌套引用闭包、暂存后判分、送分样例实际参与分数及报告、双角色内部重复，以及同轨迹不同输入仍拒绝。
- 独立审阅在无本地载荷／回执的临时代码副本运行 Harbor、data_pool、offset 共 51 项测试，全部通过。审阅发现的 offset 遗留路径和 Windows 默认编码问题已修复。早期人工副本漏复制材料的诊断不作为整库验收证据；该诊断进程及其遗留临时 fixture 已清理。
- 两道真实 HF 导热题按固定提交 c1bc9417f2f4fceb8d654a2833a90f22a8e3b7f4 下载至临时项目，通过全套严格核验、公开发布和 Harbor 准备。稳态仍为 32 个 case，其中 1 个公开送分样例；瞬态仍为 24 个 case，其中 2 个公开送分样例。没有删除或改写数值数据，也没有改变既有选样。
- HF README 同步规则的提交为 [d46b17a03d444646157e1e2fe4b4f00587dc5d89](https://huggingface.co/datasets/jimzhouzzy2006/CAE-Bench-OJ/commit/d46b17a03d444646157e1e2fe4b4f00587dc5d89)，只修改 README.md。
- 修改的技能及相关文档链接按当前规则同步，技能格式校验通过。

最终全库以普通 Windows Python（未启用 -X utf8）及 HF_HUB_OFFLINE=1 运行：437 passed、5 skipped、1,323 subtests passed。运行前后，源码题库均无 cases/reference/samples 载荷或装配回执；所有会话 fixture 正常自动清理。真实 HF 验证的缓存、临时项目和旧审阅残留已清理。5 项跳过仍是 Windows 生命周期或链接能力限制。

## 边界

本次验证消费链和错误分类，不重做物理参考精度或最大规模资源校准。未运行实际 Linux Harbor 容器和收费 Agent benchmark。公开送分样例的成绩不能解释为独立未见输入上的泛化证据。
