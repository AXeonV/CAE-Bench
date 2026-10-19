---
name: caeoj-manage-data
description: 制作和维护 CAE-Bench-OJ 的 HF 题内数据池，上传、选样、下载装配并校验输入、参考和样例。
---

# 题内数据池管理

读取本题 data-manifest.json、data-lock.json、[存储设计](../../../qbank/design/DATA-STORAGE.md)与[操作指南](../../../qbank/maintenance/DATA-SYNC.md)。使用 `caeoj data list/fetch/verify` 从本地、SSH/SCP或固定HF提交获取已发布数据；制池、上传和选样继续使用 `caeoj-maint data`，不另写同步实现。每个case自包含输入、reference/grading.json及其声明的参考／观测资产，本地 cases、reference、samples 是明确选样后的装配结果；作者证据归 `author/data-evidence/`。

按本次需求选择步骤：制池 `pack` → 验证 bundle → 上传 `upload` → 明确 `select` → `caeoj data lock` 固定所选元数据 → 审核清单与锁 → `caeoj data fetch` 获取并装配 → `verify --strict` 与真实消费检查。纯获取无需制池或上传；新题显式分配稳定 ID 并检查唯一。未登记、未锁定及不完整数据应明确报告，不当作已发布；不把main或本机路径写作可复现版本。保留仍被Git引用的已发布载荷。

- 选样固定 case ID、描述摘要、角色和本地编号；独立测试不重复输入或来源轨迹；同一池条目可显式同时选为样例与计分测试，按存储设计作为 public_cases 报告，不放宽其他重复检查。参考完整按评价计划覆盖判断；完整提交示例单独声明，不能把稀疏参考当result.h5。参考不齐只能用于开发。
- 相同文件跳过；远端差异停止，用户授权更新后使用 `--update`。父提交冲突先重新核对，不覆盖并发修改；核验失败记录提交及未完成部分。
- 本地装配先检查差异；未知或已修改文件不静默删除，显式更新才覆盖。保留真实回执，不编辑它伪造校验通过。
- 开发不一致报告 warning；正式 benchmark 必须严格核验。HF 公开性不改变考生材料白名单，池索引、作者证据及非样例参考不进入公开包。

数据变更后检查受影响契约、样例、参考及评分消费链，报告上传提交、选择、完整性和验证范围。文件一致不等于数值正确；来源寻找及实际参考制作交 [caeoj-source-cases](../caeoj-source-cases/SKILL.md)，题意修订或模型评测交对应流程，不由本技能默认启动。

需要验证存储来源时，按[传输测试指南](../../../docs/DATA-TRANSPORT-TESTING.md)在独立目标和缓存中测试；可用 `src/utils/data_transport_lab.py` 准备本机只读 SSH 服务，分别验证本地目录、SFTP与旧SCP。HF访问申请或身份失败应保留失败证据，不将复用已有文件报告为远端下载通过。
