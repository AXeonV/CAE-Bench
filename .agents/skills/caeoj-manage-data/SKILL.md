---
name: caeoj-manage-data
description: 制作和维护 CAE-Bench-OJ 的 HF 题内数据池，上传、选样、下载装配并校验输入、参考和样例。
---

# 题内数据池管理

读取本题 data-manifest.json、[存储设计](../../../qbank/design/DATA-STORAGE.md)与[操作指南](../../../qbank/maintenance/DATA-SYNC.md)，使用现有 `caeoj-maint data` 命令，不另写同步实现。HF的每个case自包含输入、reference/grading.json及其声明的参考／观测资产，本地 cases、reference、samples 是明确选样后的装配结果；作者证据归 `author/data-evidence/`。

按本次需求选择步骤：制池 `pack` → 验证 bundle → 上传 `upload` → 明确 `select` → 获取／装配 `fetch/assemble` → `verify` 与真实消费检查。纯获取无需制池或上传；新题显式分配稳定 ID 并检查唯一。

- 选样固定 case ID、描述摘要、角色和本地编号；独立测试不重复输入或来源轨迹；同一池条目可显式同时选为样例与计分测试，按存储设计作为 public_cases 报告，不放宽其他重复检查。参考完整按评价计划覆盖判断；完整提交示例单独声明，不能把稀疏参考当result.h5。参考不齐只能用于开发。
- 相同文件跳过；远端差异停止，用户授权更新后使用 `--update`。父提交冲突先重新核对，不覆盖并发修改；核验失败记录提交及未完成部分。
- 本地装配先检查差异；未知或已修改文件不静默删除，显式更新才覆盖。保留真实回执，不编辑它伪造校验通过。
- 开发不一致报告 warning；正式 benchmark 必须严格核验。HF 公开性不改变考生材料白名单，池索引、作者证据及非样例参考不进入公开包。

数据变更后检查受影响契约、样例、参考及评分消费链，报告上传提交、选择、完整性和验证范围。文件一致不等于数值正确；来源寻找及实际参考制作交 [caeoj-source-cases](../caeoj-source-cases/SKILL.md)，题意修订或模型评测交对应流程，不由本技能默认启动。

当前发行版samples输出全部为随机格式样例：用显式kind=format绑定，保留合法结构、dtype、IDs和时间轴，在公开题面注明“随机结构示例，非数值答案”；不公开sample/reference，也不提供样例数值判分命令。不能只在作者侧manifest记录角色。维护用数值角色与正式case参考继续独立验证，不能因为公开样例随机就削弱数值判题。

用户要求组装发行题库时，按[离线发行流程](../../../qbank/maintenance/RELEASE.md)冻结已装配结果：优先本地复用，使用`caeoj-maint release`绑定选样与公开闭包，分别分发考生材料和维护参考。按已确认范围纳入的未验证候选须在profile、limitations和release_notes说明缺口，不因尚未数值验收擅自删去。该步骤不替代参考资格，不自动下载HF、重算或启动模型Benchmark；无case及接口／环境未就绪项列明确排除原因。
