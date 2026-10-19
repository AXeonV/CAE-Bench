# case→example 引用与公开身份验收（2026-10-19）

本次只补齐工具，不启动[七题试验](../../pdebench-seven-task-trial.md)。操作与格式见 [PDEBench README](../../../../src/utils/PDEBench/README.md)，共享装配核验见[评测维护说明](../../../maintenance/EVALUATION.md)。未修改题面、DATA、参考数值规则或执行限额；未调用模型、求解器、HF Jobs，未上传数据或推送 Git。

## 实现与身份

selection schema_version=2 的 entries 只登记唯一来源轨迹，examples 按 task/sample ID 引用已有 case ID，不接受额外来源或帧配置。每题 20 条 case 加 2 个引用式 example，仍是 20 条计分轨迹，其中 2 条公开、18 条未公开。

example 从已制作且核验摘要的 case 复制全部声明输入、评分资产和完整 reference.h5，后者同时作为 output/result.h5；继承 case 全部时间帧，最多 9 帧，不重新打开来源。独立 role=sample 的已有入口保留，仍最多 5 帧，不允许以重复来源条目绕过显式引用。

工作区冻结选择摘要、公开身份及完整 case/sample ID 集合。题内作者绑定保存输入、参考和示例摘要，发布与 Harbor 装配共用校验器，并将相同 case/sample/case_id 写入 tests/selection.json。判题器沿用既有 public_cases 和逐例 public_sample，公开 case 留在分母。作者绑定与隐藏材料不进入公开 ZIP，不混用 HF 清单。

## 验收证据

- 20 条独立合成轨迹、每条 9 帧、2 个引用式 example：全部输入、参考、示例及时间轴逐字节一致；生成和恢复不重新读取来源。公开 ZIP 只有选定样例，无隐藏 case、作者绑定或回执。
- 实际装配 20 条 case，并运行生成的 judge.py 的预检、评价 worker 与汇总；20/20 正例通过，分母 20、公开 2，两个对应逐例标记正确。该测试替换了考生执行、冻结及权限操作，向评分链提供已知 fixture 输出；不是容器隔离验收或模型成绩。现有容器隔离证据见[上次验收](../pdebench-direct-20261019/REPORT.md)。
- 修改输入时间、参考、公开输出或绑定身份，删除必要绑定，以及注入额外样例，均在 verify、发布、装配阶段拒绝。样例 rename 后、receipt 写入前中断可凭事务恢复，不重新读取来源。
- 使用已有 DaRUS 缓存重新制作平流来源 255674 的轨迹 2、3、4、5，帧 0/1/7/61/200；case 001、003 引用为 example 01、02。4/4 正例得 1、错误数值控制得 0，实际公开 ZIP 与 Harbor 装配保留 4 个 case、2 个公开身份。响应体预算 0，实际请求 0、接收 0 字节。机器摘要见 [cached-summary.json](cached-summary.json)。此小样本只验证工具消费，不代表七题全量来源或连续 PDE 精度已验收。
- 最终相关测试 58 项通过：PDEBench 23、发布 9、Harbor 26。独立只读 subagent 复核并另跑 5 项引用测试通过；其发现的删除绑定后身份丢失、额外样例可能泄漏两项问题已通过冻结授权及完整集合核验修复。

原始日志与缓存试验产物保存在忽略目录 runs/pdebench-public-examples/；运行材料不进入通用指南或公开包。下一阶段按用户指定来源制作七题 140 条时，仍须冻结真实选择并逐题完成来源与装配验收，不能将本次 fixture 检查解释为该批数据已经就绪。
