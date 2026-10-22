# Chrono #846 修复题实施记录

## 授权、分支与目标

用户要求在新分支规划并实现推荐的真实求解器修复题，使用 Luna 完成完整 Benchmark，持续推进并用 scheduled task 接续长跑。

- 分支：`codex/chrono-846-repair-benchmark`，起点 `3fea4ce`。
- 既有 issue 搜集材料保持原样，不混入本次提交。
- 目标：19.1.1 `constrained-assembly-repair`；章级规划见[第十九章规划](../chapter-19-solver-repair.md)。
- Benchmark：`gpt-6-luna`、medium、独立尝试 1、并发 1、自动重试 0。未因失败成绩增加模型调用；基础设施错误单独分类。
- scheduled task：`chrono-846-luna-benchmark`，本会话每 20 分钟接续，完成后暂停。

## 实施状态

| 阶段 | 状态 | 证据及下一步 |
|---|---|---|
| 分支及持续调度 | 已建立 | 分支与 app scheduled task 已实际创建 |
| 章/节/题规划 | 已完成 | 独立设计审阅及修订复核见 runs/design-review/chrono-846-final/report.md |
| 源码基线与构建 | 已完成 | 两个固定源码归档、实际核心/驱动构建，公开源码闭包及 SHA 白名单 |
| 题面与 DATA | 已完成 | statements 及 exam-materials 独立考生审阅均未发现未决问题 |
| 判题适配 | 已完成并实际验证 | 原件和候选均强制重建；UID1000运行；构建后冻结库；最终9个容器探针全部通过 |
| 数据与独立 reference | 已验证 | 固定上游修复内核实际生成20例参考，全部通过精确约束微分核对；原缺陷版7/20 |
| 实际数据审计 | 已完成 | 20例及2个公开样例全部字段/输出/评分绑定审计，5类非法变体拒绝；独立后端复核再次核对40个清单/评分文件 |
| 独立 verifier | 已完成 | 最终后端 Oracle 20/20；先前缺Gmsh系统库失败保留，未算考生错误 |
| HF 任务分支 | 已完成远端核验 | cases/chrono-846-repair；固定提交重取90个文件，严格核验有效；详见本题author/data-evidence/hf-upload.json |
| Luna Benchmark | 已完成 | 固定提交740aaa0；唯一medium trial：5/20（25%），公开1/2、隐藏4/18；全部20例执行完成，基础设施异常0 |

## 已确认的工程事实

原通用后端将 `/app/submission/solve.py` 复制到逐例隔离目录运行。本次在维护/Harbor 层新增显式源码修复通道：只接收限定源文件，可信 verifier 从固定基线重新编译，并通过不可修改的驱动调用真实 Chrono API。通用物理协议保持原职责。

本机 Docker 需使用安装目录下的 docker.exe。构建后曾发生 Docker Desktop WSL 引擎失败，使用 Desktop 专用 restart 恢复，未执行 WSL shutdown。共享 Viewer 已核对健康接口、jobs 根目录及实际 HTML 页面，地址 http://127.0.0.1:8080。

## 审阅与验收证据

- 设计：runs/design-review/chrono-846-plan/report.md 指出新章归属规则缺口，已在总体目录登记修复章例外；final/report.md 复核实际题面落实。
- 考生：runs/candidate-review/chrono-846-statements/report.md 和 chrono-846-exam/report.md；后者中性解析全部两例样例及公开 ZIP 清单、README、MANIFEST。
- 评测适配：runs/configure-judge/chrono-846-backend/final-review.md。三项P2（源码大小未声明、可信构建故障归因、README仍示范solve.py）均关闭；对实际证据的范围和未覆盖的对抗边界保持明确。
- 容器探针：runs/benchmarks/chrono-846-repair/backend-probes-final/report.json，9/9；包括保留缓存但移除编译器的基础设施故障，以及未来object时间戳强制重建。
- 数据：runs/data-review/chrono-846/report.json；author/data-evidence 保存实际来源、工况、数值差异和生产者。
- 通用后端回归：tests/test_harbor.py 全部29项通过；新容器另实际走通普通 solve.py 的 freeze/execute/grade，但不称为所有普通 Harbor 任务的完整端到端证明。
- 最终原件强制重建后的独立verifier再次20/20：原件编译约1.47秒，候选编译约1.62秒，最大逐例求解约0.53秒；题面资源保持原要求。
- 上述审阅与精简验证证据已归档到本题author/data-evidence。题面收尾仅删除一个末尾LF，独立考生已确认其余公开内容不变及原审阅对当前哈希继续适用。

数值参考的加速度误差最高约为其逐分量评分容差的3.24%，反力约1.66%；位置/速度回归为双精度舍入量级。它们支持本批20例的验收，不作为整个声明参数范围的数学误差上界。

## Luna 实测结果

唯一一次独立求解为 `chrono846-luna-medium`，Codex 0.163.0 / `openai/gpt-6-luna` / medium，禁用搜索，重试0。运行于2026-10-22 17:15:32–17:21:50 UTC（香港2026-10-23 01:15:32–01:21:50），约6分19秒，包含环境准备及验证。

- 总分5/20（25%）；公开1/2，隐藏4/18。20例均有终态，不存在未执行例。
- 15个加速度case全部 `runtime_error`、退出1；2个位置及3个速度case通过。Luna改为调用 `StateSolveA()`，原件与候选均强制编译成功。考生公开样例诊断出现 `Invalid dimensions`；verifier外层仅保存子进程退出1，未保留嵌套驱动stderr，因此不推断更精确的内部抛出位置。
- 相同冻结环境的参考补丁20/20；上述运行失败归考生提交，未追加模型调用、未按隐藏反馈修补答案。
- 输入514332 tokens，其中缓存470784；输出2438 tokens。适配器报告费用估计USD0.01028164，不作为账单；一次尝试不能估计模型稳定通过率。
- 机器摘要、实际编译摘要和原始产物SHA见本题 `author/data-evidence/benchmark.json`；冻结计划见 `benchmark-plan.json`；考生改动见 `luna-submission.diff`。完整逐例报告保留在 `runs/benchmarks/chrono-846-repair/report.md`，原始trial、日志和候选源码位于 `runs/harbor/jobs/chrono846-luna-medium`。

共享 [Viewer](http://127.0.0.1:8080) 保留供回看。Windows上停止前先用 `Get-NetTCPConnection -LocalPort 8080 -State Listen` 查询PID，并用 `Get-CimInstance Win32_Process -Filter "ProcessId=<PID>"` 核对命令仍为本仓库 `runs/harbor/monitor/start_viewer.py`，确认后执行 `Stop-Process -Id <PID>`。交付时PID49104，健康接口正常且jobs目录匹配；POSIX viewer辅助脚本不支持本机，不能用作Windows停止入口。本次不停止共享服务。长跑scheduled task在交付完成后暂停。

## 续作入口

先读 `runs/benchmarks/chrono-846-repair/status.json`，核对当前分支及活动构建/试跑。每轮完成一个可审查的阶段并更新此表；构建脚本和模型控制器写持久日志、PID、命令及退出状态。数据、源码缓存与运行产物留忽略目录，制作及校验工具进入题目 author。不得把计划、结构检查或上游测试报告称作实际数值验证。
