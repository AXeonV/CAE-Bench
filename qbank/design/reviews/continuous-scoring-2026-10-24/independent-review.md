# 独立审阅：统一线性连续评分

日期：2026-10-24（Asia/Hong_Kong）。审阅者为独立代码／设计审阅 agent；已知实现与作者迁移方案，**不属于新上下文考生审阅**。只读源代码、配置、公开材料，唯一新增文件是本目录审阅脚本和证据。未运行模型、求解器或下载来源数据。

## 范围与当前结论

本轮审查用户已确认的规则：80 道数值题按每个物理量、分量、输出时刻的空间加权 NRMSE 取最大值 E；E≤0.05 得 1，E≥0.10 得 0，中间 (0.10−E)/0.05；题目 reward 为全部正式 case 得分的平均值。第 0 章 2 道接口题保持旧规则。

**核心实现与准备区的正式评分配置本轮未发现未解决阻断项。** 已独立实际运行 24 项检查，全部通过，详见 `independent-checks.json` 与可重放脚本 `independent_checks.py`。另以未调用作者转换 helper 的独立代码核对全部 82 题：630 个数值 case 的评分配置逐字段等于独立转换预期，17 个第 0 章 case 配置与 RC4 原件字节相同，见 `independent-mapping.json` 与 `independent_mapping.py`。最终题面与 RC 工件仍由后续集成核对记录证明；本报告不外推为参考答案准确或阈值完成科学校准。

## 需求映射

| 用户／公开要求 | 当前消费者与独立证据 |
|---|---|
| 5% 满分、10% 零分、中间线性 | `src/caeoj/case_grading.py` 的 `PreparedCase.evaluate`；独立 0、4、5、7.5、10、11% 测试 |
| 每时刻、每分量计算，再取所有输出最大 NRMSE | `prepare_case` 仅允许 per_time/per_component NRMSE 条件，拒绝旧 metric、合并计算、不同 limit 和不受支持评价器；聚合实际 groups 的最大值；分量与时刻反例已运行 |
| 空间加权 RMS 与分母尺度下限 | `src/caeoj/grading_metrics.py` 同一组权重用于误差和参考 RMS；非均匀 3:1 权重及零参考 floor 已独立测试 |
| reference_offset 只改变分母参考尺度 | 引擎计算误差仍为 submitted−reference，参考 RMS 使用 reference−offset；101 参考、100 offset 的反例通过 |
| 格式错误得 0 | 完整数值比较前 `check_result`；缺输出、NaN、错误 dtype 和 IDs 均为 invalid_output／0 分 |
| 保留已有固定归一化 | `qbank/extensions/caeoj_ext/normalized_fields.py` 在公开固定 offset／去均值后比较；合法有限提交变换后溢出的独立反例为 wrong_answer／0 分，而非基础设施错误 |
| 全部正式 case 分数平均 | `src/utils/harbor/tests/judge.py` 的 `save_report` 使用 `math.fsum`，passed_cases 仅诊断；部分完成和最终报告中 0.5 分均保留 |
| 坏配置不计考生 0 分 | 配置端点次序、非 NRMSE、错误聚合和 limit 在 prepare 阶段拒绝；原 grade_case 错误分类保持 |

## 设计注意与限制

1. 将旧绝对容差作为新 scale_floor 是**显式的政策迁移，不是数值等价变换**：零参考附近旧 atol 的 5% 才满分，10% 已零分；例如 EVP 旧 max_abs=1e-4 作 floor 后，零参考 RMSE 达 1e-5 即零分。最终题面必须公开实际 floor，维护材料须保留未经重新校准的限制。
2. 输入参考 offset 不是允许对提交任意平移。只有原先明确采用去均值的固定题，才保留相同的去均值操作；不能隐式推广到其他压力输出。
3. max 聚合避免平均掩盖差分量，但会随输出量和时刻增加变严格。这是用户确认的政策；不据此声称原 82 题成绩可与新 RC 直接比较。
4. 等采样权重是缺少已有空间权重时的明确选择；不等价于非均匀网格上的物理体积积分。
5. 独立检查为合成契约／数值反例，不能证明正式参考准确、求解器资源可达或全部题覆盖承诺。

## 材料

- `.agents/skills/caeoj-configure-judge/SKILL.md` 及 workflow、current-backend。
- `.agents/skills/caeoj-design-review/SKILL.md`、`qbank/PHILOSOPHY.md`。
- 核心评分、schema、公开策略渲染、CLI、Harbor 汇总、固定归一化 extension 与对应测试。
- `independent-checks.json`（24 项通过，实际执行命令：`.venv/Scripts/python.exe runs/continuous-scoring/independent_checks.py`）。
- `independent-mapping.json`（82 题／647 case 配置，实际执行命令：`.venv/Scripts/python.exe runs/continuous-scoring/independent_mapping.py`；包含所审核心实现 SHA256）。基线 Git HEAD 为 `d9dde6a980c3f78ec7ee9db0037e5e048bd604a8`，当前为集成中的未提交改动。

## 最终代码与生产入口复核

在 core 与 author policy 实现冻结后，重新执行上述两个独立脚本，24 项数值／契约／汇总检查仍全部通过。全量独立映射新增逐题读取 `author_case_grading`，验证 **80 个当前 author 模板均为完整 outer plan**、scoring 精确为 0.05／0.10，与准备区 **630 个正式数值 case** 的每个 check 的 evaluator、reference、policy、transform、weight 及 scoring 完全一致（check ID 仅作诊断标签，不影响映射）。全部通过，24 个重复 `author/case-grading-template.json` 均已移除。记录逐题模板 SHA256 和 16 个核心／生产入口 SHA256，便于集成方在产物冻结时确认未变。

逐路径检查：

- `src/caeoj_tools/grading_policy.py`：完整 outer 由 `parse_config` 读取，不剥离 scoring；`write_case_grading` 写全对象；`materialize_references(case_config=...)` 写同一完整对象。旧 inner policy 只在显式 legacy 分支包为二元计划，不根据题名猜评分。
- 两个 thermal `author/generate.py`：均调用 `author_case_grading`，再以 `case_config=` 写入正式 reference，不经过会丢失 outer scoring 的 `author_policy`／`direct_config`。
- `src/utils/PDEBench/pipeline.py`：在正式 case 的 reference 已存在时以完整 author plan 写 `grading.json`，随机 public sample 仍无评分材料。
- CFDCodeBench `author/render.py` 的 `grading(c)`：从公开固定目录规则显式迁移为完整连续 plan，同时保留旧固定压力／温度 transforms；`build_local.py` 使用同一函数生成正式配置；renderer 只写唯一模板。
- `qbank/maintenance/authoring/verify_install.py`：安装校验只改完整 plan 的 reference 文件名，其余 scoring/policy 保持；该脚本是合成读写链验证，不是参考精度认证。
- 20261020 `ten-case-candidates/build_designs.py` 原先直接读当前 outer 模板，而 `detailed_design.py:630` 需要 inner `grading['quantities']`。此问题已修复并关闭：该设计提案入口现通过 `author_policy(task_dir)` 明确提取唯一 check 的 policy，供观测清单生成，不重写冻结设计及评分快照，也不把提取结果误写成正式 case plan。最终映射记录增加该文件 SHA256，共 16 个源文件。

另读取而未重复执行实现方日志：`core-tests.log` 最终 91 passed／154 subtests；`endpoint-tests.log` 30 passed／28 subtests；`compatibility-tests.log` 23 passed／17 subtests；`helper-tests.log` 4 passed／3 subtests。最早 `authoring-tests.log` 中 11 个旧 contract hash 断言失败有独立的 `pdebench-historical-tests.log`（1 passed／11 subtests）和 `pdebench-tests-fixed.log`（23 passed／24 subtests）后续记录，不能把旧失败日志伪称全绿。

**最终代码审阅结论：当前发行范围内的核心判分与当前生产入口，本轮未发现未解决的阻断项。** 最终公开 floor／权重表另由新上下文考生审阅；最终 RC 包内源码、所有数据池绑定与独立安装链由集成方最后核对。本结论不声称本报告已独立解包和安装最终 RC。

## 原来源身份恢复脚本窄审

审阅 `runs/continuous-scoring/restore_provenance.py`，SHA256 为 `5ea1d90793034e1149b176a80308a15ef8bcd95223baf84bd08ff966778f071c`；已实际 AST 解析通过，未自行运行该会装配正式数据的脚本。

**方案与静态实现未发现阻断项。** 原 pack 在未携带历史证书文件时会丢失 PDE case 的 `origin.certificate_identity`，这属于来源元数据丢失，不应假冒新证书补齐。恢复脚本从 RC4 原回执取已经绑定的 descriptor：先验证旧 selection canonical SHA256 与回执一致，再逐个验证旧 descriptor 原始字节 SHA256 与旧 selection case binding 一致，并校验 case ID。对于新池，再核对其 index 绑定的 descriptor SHA256；旧／新 input 文件集合、逐文件 size/hash 必须相同，并要求**除 reference/grading.json 外所有 descriptor 文件元数据完全相同**，包含参考数组、观测和样例资产。这比只比较 case ID 更充分，拒绝用旧来源身份覆盖发生内容变更的输入／参考。

脚本只将原 origin 字典原样放回新 descriptor，不更改旧 certificate contract/tool/source 字段，不创建 certificate，也不声称旧证书认证新评分；更新 descriptor 及 index 的真实摘要后，经原 `pool.select` 重新生成选择绑定，再调用 `validate_bundle`、真实 `assemble` 与 `verify(strict=True)`。stage 和已有 current 数据回执均由 assembly 生成，没有手工编辑回执。每题记录原 receipt SHA256、恢复的 case 列表与 `new_certificate_created:false`，新描述符明确尚未上传 HF。原证书身份因此只表示**未变输入／参考的历史来源**，新连续评分修改由本轮独立迁移证据负责。

调用方仍须等实际脚本完成，检查 80 题最终来源保存记录、执行成功状态与最终 RC 内绑定；静态审阅不替代实际装配或最终归档验证。

## 资源消费与并行装配工作流窄审

读取真实 `large-preflight.json` 与测量脚本：它从当前 frozen public ZIP 解压，普通本地 pip 安装至新 target，在 `python -I` 子进程中断言导入的 caeoj 来自该安装路径，用真实 prepared 三维可压流 case `001` 的正式参考走 `grade_case`，记录得分 1、57.391 秒及 evaluation SHA。该计时包括 grade_case 调用，不包含整个容器、所有 case 或全部前置消费；不能据此称异机或全题资源校准。

独立实际调用当前 `prepare_harbor.task_config`，使用该题真实主配置和私有 TOML、正式例数 6：`evaluation_timeout_seconds=120`、求解时限仍 1800，得到 `verifier.timeout_sec=300+6*(1800+120+60)=12180`。主目录与 publish-stage 的 judge-config/TOML 字节相同；`build.py` 会从 publish-stage 复制这两份私有资源文件至最终 release source。Harbor judge 的实际 worker subprocess 使用 `timeout=budget`（budget 来自 evaluation_timeout_seconds），求解 supervisor 则消费原 timeout_seconds，两个限额未混淆。证据为实际通过的 `independent-resource.json` 与轻量可重放 `independent_resource.py`，没有重新加载大型 case。此变更是依据代表例为评价器增加余量；不认证 solver 资源、全例或异机可达性。

工作流静态核对：`pack.py` 每个结果必须先通过真实 `pool.assemble`、`pool.verify(strict=True)`、case/sample 身份比较及所有 non-grading 原资产 size/SHA 验证，然后才写成功 state；`--task` 将 state 和条目隔离到 task slug。`parallel_tail.py` 只分配首 15 题之外的 67 个独立任务，逐子进程检查退出码，最多 3 路，没有用模板填充成功状态。`merge.py` 收集首 15 条真实全局状态和另 67 条单任务完整状态，不运行假 judge，也不制作参考。后续来源恢复会再次通过真实装配／strict；最终 release build 另做消费核对。已建议给 merge 添加 result task、task entry 身份和实际例数的显式防错断言，避免仅依靠文件名隔离作为绑定证据；本报告不把尚未完成的最终合并说成通过。

`watch-prefix.ps1` 只针对已指定的本次串行 pack PID：先取 CreationDate 和命令行，要求命令包含当前 pack 路径且排除 `--task`；在首 15 题末题的 strict success 写入后，再比 creation ticks 和命令行一致才 Stop-Process。它不停止 Viewer、WSL 或无关容器／进程；PID 复用时拒绝操作。`merge.py` 还要求首 15 题全部存在，不能仅因末题标记补造其他题成功。静态未发现结果伪造；现场执行是否完成、停止是否真的发生和最终任务绑定，须以最终 checkpoint、merge 和验证记录确认。

本次窄审发生在最后大型任务仍装配时；**最终 RC 尚未 build**，本节不是最终发布工件验收。

## 最终元数据恢复与合并调整复核

再次静态审阅恢复脚本，当前 SHA256 `c24bf1515fd09e118d977654b1f359b56996fa6cc86f244113390b1db903b219`；合并脚本 SHA256 `e538d390da8b031d38fa33704f44f128502c97e521539d0ee4a37a81d66246fa`，两者实际 AST 解析通过，未运行大型数据检查。

恢复步骤去掉原脚本的第二次 `validate_bundle`，保留 pack 阶段已有的完整 bundle 验证。该调整**未发现绑定缺口**：恢复仍逐个校验旧 selection 与 descriptor 摘要、新 descriptor 与 index 摘要，且除 `reference/grading.json` 外所有 descriptor 文件元数据严格相等；唯一写入是原 origin 和对应 index/selection 摘要，并新增 repository 文件路径清单不变断言。随后仍经真实 `pool.select` 重新绑定、真实 `assemble` 生成回执、`verify(strict=True)` 检查装配资产与新 grading；current 已有回执时另执行真实更新装配和 strict。恢复脚本不改数组和 grading，因此无需为这个来源字典补回动作反复做同一原 bundle 的全池数值预检。

核对实际 data_pool 消费者后，**精确的检查链为 select→plan（描述符、角色、身份与文件映射），assemble→fetch（payload size/SHA、真实输入／参考及 grading 预检），strict→prepare_case（实际装配文件与新评分预检）**；select 自身不调用 fetch，不将它算成第三次数值预检。原早期脚本额外执行过恢复后 validate_bundle 的记录与后续仅继承 pack 验证的记录应保留区别；调用方以 validation_basis 表明，不追改旧历史成绩或证书身份。

merge 防错建议已落实并关闭：先 deepcopy 保存原 plan，验证每个 result.task；尾题 entry 的 task、task_path、source_root 与原计划／目标 staging 对应；逐题旧新 manifest task_id 相等、实际 formal/sample 数量匹配结果、每个选样名字映射到完全相同的 case_id。严格成功状态不能从另一题借用，旧 plan 不会因原地更新 source_root 失去基线。未发现通过重命名状态文件或模板填充伪造成功的代码。

结论仍限于静态实现与已有消费函数核对；后续 80 题恢复是否实际全部完成、最终合并与 RC 是否正确，由主任务的真实运行、来源保存账本与最终包校验闭环。
