# 当前仓库的定位线索

本页依据 2026-10-15 仓库实现编写，是维护方线索，不是固定接口规范。每次执行先检查实际版本及读取者；框架更新后同步本页，不让旧字段表覆盖新实现。不要让考生阅读本页补足题意。

| 当前位置 | 当前职责与需要核查的事实 |
|---|---|
| src/caeoj/grading_policy.py 的 task_policy | 若有 grading.json，按 outputs 的逻辑字段名绑定；与 judge-config 中旧 atol/rtol 并存时报错。没有 grading.json 可从旧容差派生策略，缺少显式配置也可能走默认值，不能把缺省视为符合题面 |
| src/caeoj/grading.schema.json、grading_metrics.py、grading.py | 策略结构、逐值／误差指标、时间与分量聚合、权重、reference_offset 和实际比较；以实现及 docs/GRADING.md 为维护参考，题面需完整公开实际规则 |
| tasks/<task>/judge-config.json | 当前 Harbor 组装器及运行 verifier 要读取此文件；逐例 timeout_seconds、输出文件上限等的实际消费点要逐项确认。memory_mb、points_per_case 等即使出现在旧文件也不能假定执行器实际读取 |
| src/utils/harbor/tests/judge.py | 冻结提交、逐例独立运行、逐例墙钟、输出与结构检查、评分调用和汇总；当前最终 reward 为通过例数/总例数，不凭额外 points_per_case 字段认定权重已生效 |
| src/utils/harbor/task.toml、prepare_harbor.py 的 task_config | Harbor 共享模板与受限覆盖白名单。单题 harbor/task.toml 可省略并继承模板，不能由此推断模板资源满足题面 |
| tasks/<task>/harbor/task.toml、harbor/requirements.txt | 当前题目的资源／依赖覆盖，实际生效值是与模板合并结果；CPU／内存与逐例超时不在同一消费层 |
| src/utils/publish_dist.py | 打包公开策略和必要工具；会导出 grading.json 及机器策略的可读表示，不意味着考生必须额外阅读它们来理解规则；维护资料不打包 |
| src/utils/prepare_harbor.py 的 prepare | 当前只接受 tasks/<name> 布局，要求真实 cases、reference 与有效公开 ZIP，校验策略及包内容一致性；不能假设已支持 qbank/examples 或无数据题目 |
| tests/test_grading_policy.py、test_harbor.py、test_publish.py | 找现有边界、隔离、错误分类、配置覆盖与过期包行为的验证方式；不能只沿用测试数而不检查本次变更 |

当前时间预算至少分为 agent 生成时间、构建时间、逐例 solver 时间与总 verifier 时间。总 verifier 还包含数据装载／检查、拷贝、判分和报告，不等于某一个 case 的时间。未来框架若并行执行，按实际调度计算，不能机械套用串行总和。

qbank 第二章目前只有完整题面与 DATA，没有正式数据；不是运行现有 prepare_harbor.py 的直接输入。可以在临时目录用 fixture 验证适配，但不能将目录迁入 tasks、伪造真实样例或绕过发布校验来声称正式可运行。
