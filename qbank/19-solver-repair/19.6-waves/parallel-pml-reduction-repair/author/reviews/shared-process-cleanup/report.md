# repair22 MPI cleanup 独立后端审阅

结论：允许集成并冻结 `judge.py` Windows 源文件 SHA256 `5141c3a50bbae52169ea3dd1b2466fb5363cb3ebd33116df6f73b6d14deef16d`。既有 prepare 的 LF 归一化后实际副本 SHA256 为 `5595500ff6c8612f4682f4eda0cdc6521c5af94343dcba6c825bb3555141180f`，新 frozen 身份应记录实际副本摘要。本次范围内未发现可复现的 P0/P1/P2 缺陷。该结论覆盖进程清理需求、实现、实际消费链与有区分力的 Linux 回归，不代表 SPEC 全数据 Oracle、MOOSE 原生任务或 Bempp 新后端 Oracle 已完成。

审阅日期：2026-10-23。独立审阅采用 `.agents/skills/caeoj-configure-judge/SKILL.md` 与 workflow；只写本审阅目录，未修改实现、未重新 prepare 活动题、未调用模型、未停止无关容器。测试使用既有镜像 `caeoj-specfem661-probes:preflight`，实际 image ID `sha256:107542dd83e647813e4a530a27f0d10e895b4ef71db9f7f010723d51c67cafba`，只新开 `--rm --network none --cpus 4 --memory 4g` 临时容器。

## 必要性与需求映射

旧实际失败证据 `work/repair-22/specfem-661/probe-evidence-v2/runtime-timeout.stderr.log` 留下 21 次 `R` 状态采样，而旧 `probe-context/backend_probe.py` 只检查一个 rank 且允许 zombie；故旧进程组 kill 的成功不能代表隔离已完成。新实现改动的是共享运行隔离，未改求解、评分指标、容差、分母、source-repair 源码白名单或构建规则。

| 要求/风险 | 当前消费者与核对结论 |
| --- | --- |
| 每例所有后代终止并回收，含 MPI setsid | `execute` 用一个独立 root Python helper 调 `supervise`；helper 在启动候选前 `PR_SET_CHILD_SUBREAPER`。先 SIGKILL 直接子进程，孤儿逐层收养，再 `waitpid(-1, WNOHANG)`；只有 ECHILD 才返回。双 fork/双 setsid、早退父进程、超时均实际验证。 |
| 不伤无关程序/避免 PID 复用误杀 | 没有全 UID、命令名或进程组扫描杀进程；只读 helper 自身 `/proc/<pid>/task/<pid>/children`。直接子进程在本 helper 显式 reap 前保留其 PID，默认 SIGCHLD 且无竞争 reaper，因此枚举至信号阶段不发生该子 PID 复用。独立同 UID sentinel 和原测试 root sentinel 均存活。 |
| SIGCHLD/线程 | 当前 helper 未安装 SIGCHLD handler、未设置 SIG_IGN/SA_NOCLDWAIT，无并发 wait 线程。独立检查确认正常入口 SIG_DFL；实际在候选 Python 线程内 fork，再两层 setsid，父进程成功早退，两个后代全部 `/proc` 消失。候选线程不会变成 helper 中的竞争 reaper。若未来改变 helper 信号或 wait/thread 模型，须重审上述 PID 前提。 |
| 有界清理/分类 | 求解返回码 0 → null，非零 → runtime_error，solver wait 超时 → timeout；三者均先完成清理。清理剩余子进程超过 5 秒写私有 infrastructure_error receipt 并抛异常，helper 非零导致 `execute` 抛 RuntimeError。`main` 不捕获为考生零分；独立 mock 证明首 case 即停止、第二 case 不创建、reward 不生成。不可安全人为制造 D 状态，5 秒失败分支采用既有受控 waitpid/clock mock，明确不是实际内核不可杀进程实验。 |
| 预算 | solver timeout 仍从 helper 内候选启动后的 `wait` 消费；helper 启动、清理和 I/O 属 verifier 开销，elapsed 包含它们。清理循环最多 5 秒另加短轮询/调度，不能宣称绝对硬实时 5 秒。`prepare.task_config` 按实际 case 数覆盖 solver+evaluation+overhead；本次 SPEC 与 Bempp overhead 都为 5 秒，另有 base 350/400 秒，需继续容纳 bootstrap/I/O/build。外层 verifier 仍是最终硬界；本改动没有普遍证明任意新任务的总预算。 |
| root/降权/环境/receipt | root helper 仅执行传入固定 JSON 命令；候选仍由 setpriv reuid/regid=1000、clear-groups、no-new-privs 启动。环境仍是固定 PATH/HOME/PYTHONDONTWRITEBYTECODE，source-repair 附固定 LD_LIBRARY_PATH；独立注入的 REVIEW_SECRET 不进入候选。`test.sh` 将 `/tests`、`/logs/verifier` 置 700；独立检查 logs 不可被 solver 读/遍历，receipt root 所有；候选不能伪造 receipt。 |
| 普通 solve.py/原生任务 | 原 per-case submission copy 与 command 未变；Linux 实测普通 solve.py 输出、直接 Python 成功/退出7、原生 C++ 编译运行通过。source-repair command/env 同时被实际 Fortran MPI timeout 消费。 |
| 真实 prepare 消费链 | `TEMPLATE_FILES` 包含 `tests/judge.py`，prepare 读取当前模板、归一 CRLF→LF 后写入独立 verifier tests，test.sh 调该文件。共享测试验证普通/source-repair staging 与私有边界；额外 disposable fixture 实际调用 publish+prepare 后比较 staged judge 与当前模板字节（按既有 LF 规则），未触碰活动任务。已有 frozen 目录不会自动升级。 |

## 独立实际检查

所有命令从仓库根执行，完整输出与脚本留在本目录；运行时的摘要冻结见 `materials-sha256.json`。

- `.venv/Scripts/python.exe -m unittest discover -s tests -p test_harbor.py -q`：30 项通过，111.223 秒，`shared-tests.log`。包括真正的预检/装配/评分 worker fixture，而非只解析配置。
- 既有 Linux 镜像只读挂仓库运行 `python /audit/tests/test_harbor_process_cleanup.py -v`：5 项通过，13.958 秒，`process-tests.log`。覆盖 Python normal/runtime_error、C++、ordinary solve.py、double fork/setsid timeout/normal early parent exit、不可回收 mock；所有记录 PID 必须完全不存在，不能仅是 Z。
- 同镜像运行本目录 `reviewer_checks.py`：3 项通过，3.258 秒，`reviewer-checks.log`。增加线程 fork/双 setsid、同 UID sentinel、实际降权/环境/私有 receipt、helper 非零分类、main 首 case 失败后拒绝继续且无 reward。
- 同镜像只读覆盖 `/tests/judge.py` 和 `/opt/backend_probe.py`，运行 `python /opt/backend_probe.py runtime-timeout`：退出 0，`real-fortran-timeout.log`。真实构建被注入无限循环的 Fortran，baseline probe ready；记录 launcher 131/143、rank 146/147/148；返回后记录 launcher/rank 均从 `/proc` 消失（无 zombie），无关同 UID sentinel 存活。此为 reviewer 新运行，作者原始 cleanup-v3 证据保留未覆盖。
- `.venv/Scripts/python.exe runs/configure-judge/repair22-mpi-cleanup/assembly_check.py`：独立临时 fixture 的当前模板→prepare staged 副本字节比较通过，`assembly-check.log`。

真实 MPI probe 观察器按命令筛选只用于记录证据，没有参与清理；rank 自己写 PID 的三份文件加 launcher 观察记录交叉验证。容器结束才由 Docker 清场不构成此项成功：断言在 execute 返回后、容器仍运行时完成。

## 集成条件与证据复用边界

1. 以以上 SHA 为冻结对象。每个新 prepared verifier 的实际 judge 按 LF 规则核对摘要，并保留新的任务/镜像/包/数据/Oracle 身份；不能仅替换共享源文件后声称旧 frozen 目录已使用它。若实现、线程/信号模型、权限或调用链再改，重做相应检查。
2. 本次共享清理审阅和便宜回归可供 SPEC/MOOSE/Bempp 共同复用；每题实际 runner、构建与完整 case 的原生 Oracle/预算/资源证据仍各自完成。SPEC 全数据及新 frozen 原生 Oracle 不在本次执行范围。
3. Bempp 最终 3b2 包旧 frozen judge 的 clean Oracle-v3，只有在公开包、全部输入/参考、评分闭包、候选源码、构建产物与参数相同的项上，才可复用其数值正确性/参考一致性结论。旧结果保留原 judge 身份；它不证明新 helper 入口、进程回收、耗时预算或新镜像端到端运行。跨后端可作有界数值证据，不能改旧 manifest/SHA 冒充新跑。全 12 参考的独立数学合格属于另一项已给定证据，本审阅未重新核算。
4. 可将清理语义（成功/失败分类与额外 verifier 开销）收束到维护文档 EVALUATION 的运行说明；它属于共享机制，不应放入单题公开 DATA 或通用数据 CONTRACT。当前代码/证据已经明确，未发现需要阻止集成的文档歧义。

本报告不把结构检查等同于数值、资源或正式发布合格，也不要求额外付费模型运行。
