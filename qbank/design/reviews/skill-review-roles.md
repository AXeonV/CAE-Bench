# 出题与三类审阅技能整理

日期：2026-10-16。基线 `a96176e`。本轮仅修改维护技能及工作流，不修改题面、DATA、数值数据、运行实现或评分配置；不启动全仓审阅或 benchmark。

## 现行入口

| 入口 | 职责 |
|---|---|
| [caeoj-author-question](../../../.agents/skills/caeoj-author-question/SKILL.md) | 单题、节或章出题，补齐上级规划，协调专业技能 |
| [caeoj-design-review](../../../.agents/skills/caeoj-design-review/SKILL.md) | 独立检查 general problem、能力划分、来源独立性与建模评价一致性 |
| [caeoj-candidate-review](../../../.agents/skills/caeoj-candidate-review/SKILL.md) | 仅用公开材料推演实现任务，区分题面与考试材料模式 |
| [caeoj-data-review](../../../.agents/skills/caeoj-data-review/SKILL.md) | 对照全部实际输入及公开输出与三文件契约 |
| [caeoj-design-data](../../../.agents/skills/caeoj-design-data/SKILL.md) | 自包含 DATA 设计，按需扩展协议与工具 |
| [caeoj-configure-judge](../../../.agents/skills/caeoj-configure-judge/SKILL.md) | 配置兑现与实际加载／执行验证 |
| [caeoj-run-benchmark](../../../.agents/skills/caeoj-run-benchmark/SKILL.md) | 冻结评测、运行、监控与完整结果汇总 |

原 author-section、review-statements、audit-data 分别迁移到 author-question、candidate-review、data-review，旧目录不保留；历史报告中的名称和原命令仍作为历史证据，唯一失效的技能链接更新到现行入口。

出题流程在能力清单形成后调用独立设计审阅；题面与 DATA 完成后调用独立考生审阅，最后核对题面对设计的落实。两类审阅不共用上下文；规划和设计报告不能补足考生题意。数据审阅保留数据对照所需的文档检查，不重复拥有完整考生审阅流程。

专业技能向当前协调方反馈上游缺陷，不递归启动整套出题。按文件版本、模式、覆盖和跨题依赖复用结论，变更后只复核受影响部分。设计、考生、实际数据和配置执行状态分别记录。

## 静态与辅助脚本验证

- 七项技能均通过 skill-creator 的 quick_validate；现行技能／README／设计入口的相对文件链接检查通过。
- 技能目录、frontmatter 与 UI 调用名称一致，现行文档无旧名称调用；历史记录保留旧名称。
- 迁移后的 check_statements.py 与 inventory.py 与基线逐字节一致。
- 新路径运行第 0 章静态检查：1 题通过；盘点 smoke-test：11 个输入、0 文件缺口，报告明确 audit_verdict=not_evaluated。只证明脚本在迁移路径可用，不构成正式数据审计。
- git diff --check 通过。未运行数值求解或全量运行时回归，本轮没有运行实现变化。

独立行为验证的原始材料、SHA256 与报告保存于本地忽略目录 `runs/skill-review-roles/`；其结果与限制见下文。

## 独立行为验证

设计审阅使用新上下文独立审阅者，完整覆盖临时规划 A–E，仅读取指定技能、规划及哲学。A（固定轨迹查询）、C（仅按软件来源重复立题）、E（自主闭合却强制专有量与固定闭合结果）被识别为需修订；B（有实质几何／参数／条件变化的窄范围流动题）与 D（明确用途的第 0 章接口测试）未被误拒绝。规划缺少题面未被当作缺陷。材料散列前后未变，未读取实际题库、实现或旧报告。

考生审阅使用两个彼此独立的新上下文，只接收临时接口题三文件及通用方法。statements 模式未发现明确阻断缺陷，允许未提供样例；exam-materials 模式因缺真实公开输入报告整体资料不足，未自动降级。两者都指出临时材料“精确比较数值”的表示语义可进一步说明，一份列为可选精炼，另一份列为待核实，汇总保留分歧。三文件前后 SHA256 一致；未生成样例、编写求解器或用规划补足题意。

设计场景结束后，为最终技能补充了整章／整库分组需安排跨组重复与边界核查的要求。版本补记记录审阅时与最终技能散列及唯一差异；A–E 结果不变，但本轮没有执行跨组或全库行为验证。行为验证仅证明这些有限场景下的表现，不保证无缺陷或整个题库已审阅。
