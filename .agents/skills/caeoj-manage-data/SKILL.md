---
name: caeoj-manage-data
description: 制作和维护 CAE-Bench-OJ 的 HF 题内数据池，上传、选样、下载装配并校验输入、参考和样例。
---

# 题内数据池管理

读取本题 data-manifest.json、[存储设计](../../../qbank/design/DATA-STORAGE.md)与[操作指南](../../../qbank/maintenance/DATA-SYNC.md)，使用现有 `caeoj-maint data` 命令，不另写同步实现。HF的每个case自包含输入、reference/grading.json及其声明的参考／观测资产，本地 cases、reference、samples 是明确选样后的装配结果；作者证据归 `author/data-evidence/`。

按本次需求选择步骤：制池 `pack` → 验证 bundle → 上传 `upload` → 元数据分页 `list` → 明确 `select` → 获取／装配 `fetch/assemble` → `verify` 与真实消费检查。分页和后续选样使用首轮返回的固定 revision；纯获取无需制池或上传，新题显式分配稳定 ID 并检查唯一。开发取用在独立工作区选样，不自动改动正式清单。

- 选样固定 case ID、描述摘要、角色和本地编号；独立测试不重复输入或来源轨迹；同一池条目可显式同时选为样例与计分测试，按存储设计作为 public_cases 报告，不放宽其他重复检查。参考完整按评价计划覆盖判断；完整提交示例单独声明，不能把稀疏参考当result.h5。参考不齐只能用于开发。
- HF 来源证书使用 source_repository、source_sha256、sample_index 绑定内容轨迹，source_file 和固定 source_revision 用于定位；不把 SHA256 填进 source_md5，也不把版本或文件名变化当作独立轨迹。实际核验范围单列。
- 相同文件跳过；远端差异停止，用户授权更新后使用 `--update`。父提交冲突先重新核对，不覆盖并发修改；核验失败记录提交及未完成部分。
- 本地装配先检查差异；未知或已修改文件不静默删除，显式更新才覆盖。保留真实回执，不编辑它伪造校验通过。
- 开发不一致报告 warning；正式 benchmark 必须严格核验。HF 公开性不改变考生材料白名单，池索引、作者证据及非样例参考不进入公开包。

并行迁移收束时先停止写入并固定各源分支提交，按 verified 检查点和真实消费回执筛选，不能把已发布池根计数或 prepared 状态直接认作完成。沿用共享分区归并逻辑，服务端复制不可变资产，最终原子发布根索引；冲突停止，不覆盖。合并后核对全部描述绑定和唯一来源覆盖，元数据核对不另称为新数值消费。恢复时按当前剩余来源和分族实测重新估算时限，另计未包含在批次 elapsed 内的 verified 提交等待、启动及最终归并；与最新账本联合校验，不能挤小可信时限凑预算。所有分支及最终归并的实际 commit 请求共用仓库级节流，429 冷却与未知提交结果核查纳入作业限时和预算。

数据变更后检查受影响契约、样例、参考及评分消费链，报告上传提交、选择、完整性和验证范围。文件一致不等于数值正确；来源寻找及实际参考制作交 [caeoj-source-cases](../caeoj-source-cases/SKILL.md)，题意修订或模型评测交对应流程，不由本技能默认启动。

大池使用 `pack --shard-mib <1..512>`，随后沿用相同 upload/select/fetch/assemble/verify。上传验证全批与默认选择，先暂存不可变 TAR/locator，最后原子发布变动哈希分区及根索引；重复批次保留原绑定，不覆盖其他批次。选样只取 JSON，装配取所在完整 TAR，缓存复用；不宣称 HTTP range。根索引格式及分区归属只在存储设计维护。已有直接目录池不能隐式升级，需显式迁移验收。非 editable 安装使用 `--root <作者工作区>`，避免把安装路径当题库根。
