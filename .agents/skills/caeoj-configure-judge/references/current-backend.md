# 当前仓库的定位线索

本页记录当前实现的定位线索；架构与装配详见[运行说明](../../../../qbank/maintenance/RUNTIME.md)，评分语义见[GRADING.md](../../../../docs/GRADING.md)。每次执行先检查实际版本及读取者；框架更新后同步本页，不让旧字段表覆盖新实现。不要让考生阅读本页补足题意。

| 当前位置 | 当前职责与需要核查的事实 |
|---|---|
| src/caeoj_tools/grading_policy.py 的 task_policy；src/caeoj/grading_policy.py 的 resolve_policy | grading v1 精确覆盖逻辑字段；v2 根据每例 outputs.quantity 与 unit 绑定实际逻辑字段，可按显式声明读取 physics.parameters 标量偏置。题库统一显式提供 grading.json；judge-config 不定义 atol/rtol，缺评分策略时停止运行 |
| src/caeoj/grading.schema.json、grading_metrics.py、grading.py | 策略结构、逐值／误差指标、时间与分量聚合、权重、reference_offset 和实际比较；以实现及 docs/GRADING.md 为维护参考，题面需完整公开实际规则 |
| qbank/<chapter>/<section>/<task>/judge-config.json | timeout_seconds 为逐例时限；max_output_bytes 显式 null 无独立字节限额，省略仍保留旧128MiB缺省。verifier_budget 由组装器按真实案例数计算总预算。瞬态热传导本地 author/check.py 使用 memory_mb 检查 RSS，须与本题 Harbor 内存配置一致；资源是否生效应核对各实际执行器 |
| src/utils/harbor/tests/judge.py | 冻结提交、逐例独立运行、逐例墙钟、输出与结构检查、评分调用和汇总；当前最终 reward 为通过例数/总例数，不凭额外 points_per_case 字段认定权重已生效 |
| src/utils/harbor/task.toml、prepare_harbor.py 的 task_config | 合并资源覆盖并计算动态总预算；模板显式 Linux、0 GPU、separate verifier；no-network 仅配置于 verifier 阶段。CPU／内存未声明的题不凭空加配额；Dockerfile指定linux/amd64。实际安装的Harbor须支持阶段网络策略，不将模型解析视为容器执行证据 |
| qbank/<chapter>/<section>/<task>/harbor/task.toml、harbor/requirements.txt | 当前题目的资源／依赖覆盖，实际生效值是与模板合并结果；CPU／内存与逐例超时不在同一消费层 |
| src/utils/publish_dist.py 维护入口、src/caeoj_tools/assembly.py | 根据可信绑定装配核心、所需物理扩展及运行描述，生成公开安装材料；会导出 grading.json 及机器策略的可读表示，不意味着考生必须额外阅读它们来理解规则；维护资料不打包 |
| src/utils/prepare_harbor.py 的 prepare | 通过 caeoj_tools.task_paths.task_directory 按唯一 slug 定位 qbank/<chapter>/<section>/<task> 布局，要求真实 cases、reference 与有效公开 ZIP，校验策略及包内容一致性；不能假设支持 examples 布局或无数据题目 |
| src/caeoj_tools/dependencies.py 的 lock_dependencies | 按当前安装环境遍历传递依赖、markers及extras，检查版本／Python约束并精确锁定；缺包或冲突阻止发布。依赖锁是当前构建环境证据，不自动证明另一平台可安装；packaging仅属maint可选依赖 |
| src/caeoj/runtime.py、qbank/extensions/caeoj_bundle、qbank/extensions/caeoj_ext | 已安装 provider 提供受控描述，扩展按物理能力组织；核对实际 runtime／assembly API，不从输入动态导入任意路径 |
| src/caeoj/cli.py、src/caeoj_tools/cli.py | 公共命令 validate-input／validate-output／grade／info 与 --version；grade 的坏输入／参考／配置归基础设施错误，退出 2，不计零分。维护 make-cases／smoke 是独立入口 |
| tests/test_grading_policy.py、test_runtime_assembly.py、test_harbor.py、test_publish.py、test_plasma_contract.py | 找现有边界、隔离、错误分类、配置覆盖与过期包行为的验证方式；不能只沿用测试数而不检查本次变更 |
| 各题author/check.py等维护入口 | 配置可能另有本地运行消费者，删键前搜索全部读取者；本地检查同样读取显式 grading.json；瞬态题的 memory_mb 与 Harbor 配额须保持一致，相关回归在 test_heat.py、test_transient.py |

当前时间预算至少分为 agent 生成时间、构建时间、逐例 solver 时间与总 verifier 时间。总 verifier 还包含数据装载／检查、拷贝、判分和报告，不等于某一个 case 的时间。未来框架若并行执行，按实际调度计算，不能机械套用串行总和。

题目目录可定位不表示数据就绪；按实际样例、cases 和 reference 检查 prepare 的前置要求。临时 fixture 只验证工具，不替代正式数据。题目状态见维护说明，不在本页重复维护章号或题数。

各题的配置覆盖与数据就绪情况详见 [评测配置维护说明](../../../../qbank/maintenance/EVALUATION.md)。字段表仍以实际消费者为准；新增后端需要重新核对，不将本次模板文件名视为永久协议。
