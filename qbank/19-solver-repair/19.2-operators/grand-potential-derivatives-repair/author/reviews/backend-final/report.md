# MOOSE #30236 题内后端独立终审

结论：**通过（记录明确的证据复用边界）**。2026-10-23；未发现需修订的P0/P1/P2。全数据数值资格见 `runs/data-review/repair22-moose30236/report.md`，本报告说明配置→消费者→实际执行与最终身份。

## 最终冻结与正式执行

唯一正式 Oracle 为 `repair22-moose30236-harbor-oracle-v1`。实际读取job/trial/verifier及全部case报告、H5、构建stdout/stderr、健康记录；对 `frozen-run.json` 中全部prepared文件重新计算SHA并相等，对归档manifest所有条目重新计算字节数与SHA并相等。prepared的judge实际为LF文件 **5595500ff6c8612f4682f4eda0cdc6521c5af94343dcba6c825bb3555141180f**；没有把源文件CRLF SHA当作实际冻结SHA。全部12真实H5逐数组等于现行reference，并通过当前评分入口；formal score12、total12、completed12、complete=true、reward1，trial无exception，进程returncode0。没有重新prepare或覆盖活动目录。

共享subreaper审阅复用 `runs/configure-judge/repair22-mpi-cleanup/report.md` 及其冻结材料；本题prepared的实际LF SHA完全匹配该独立审阅允许集成的版本。这里不重写或重新声称已执行其Linux/MPI实验。

| 公开要求 | 配置/消费者与实际证据 |
|---|---|
| 恰两个普通文件，每个≤1MiB | source-repair.json两项替换、max_source_bytes1048576；source_repair.prepare检查集合/普通文件/链接/大小；extra/symlink/oversize真实探针均invalid_submission |
| 真实材料编译，不改框架/驱动 | 固定基线源码closure25,078文件逐项核验；target C/h摘要分列原件、原样PR和作者补充；公开观察器源码读取属性和DOF，不补导数；CMake包装真实make -j2 METHOD=opt ENABLE_LIBTORCH=false |
| 候选必须实质重建 | 每次先删除unity.lo、真实.libs/unity.o、真实phase_field共享库、应用四个普通产物，再构建；四产物SHA、真实新库、ldd实际native路径和nm目标方法均有raw；future mtime设为2100年仍真实重编 |
| 构建/基础设施错误分开 | 真实语法错误build_error；缺编译器、原件runtime健康缺失、原件SDK缺失均infrastructure_error；baseline-runtime在真实原件重编后注入，非把强制删除的应用误当坏环境 |
| 单例全20输出通过才得1 | 全12 case唯一reference/grading.json，direct_outputs完整校验后按quantity/unit绑定；数据审阅75变体含全部20输出容差两侧、非法输出和阈值等号 |
| 等权12例含公开样例 | formal12/12，strict verify公开case01/02清晰标识，不减分母；原件/PR/作者数值身份分别2/3/12 |
| 4CPU/4GiB | Harbor merged task.toml cpus4/memory_mb4096；固定valid探针实采cpu.max=400000 100000、memory.max4294967296；正式退休容器未另行实采，明确有界复用 |
| 构建300秒/输入30秒 | source-repair baseline/candidate均300；judge timeout30/evaluation30；正式baseline151.0991秒、candidate151.9716秒、health6.64秒，全部case完成 |
| 总预算不截断 | prepared verifier1680=900+12×(30+30+5)，base900足以容纳两次300构建+最多60健康及剩余开销；agent1800；环境镜像build1200另计；formal真实端到端约677秒 |
| 隔离/线程/网络 | solver由setpriv UID/GID1000、clear-groups、no-new-privs；tests/logs私有，候选构建后源/库/app/framework/依赖/适配器归root只读；网络none与一次连接拒绝实采；新judge后代回收使用已独立审阅subreaper |

构建阶段仍由固定native make执行，--parallel4为CMake包装调用参数，真实子make-j2见公开CMake；不将其误称4条编译线程。未知实现合法候选的最坏资源不能由单个参考耗时普遍证明，本次只确认公开限制真实消费、参考有充分预算及错误分类。

## 源码与raw核验

`evidence_review.py` 实际读取最终ZIP、原始归档与closure manifest：25,078文件全覆盖，对固定原始归档逐字节相等；native原件镜像内又全25,078 SHA相等，结果 `native-image-closure.json`。未把作者摘要视为证明。原件真实可执行文件存在；`reference-image.json`、`upstream-image.json`、`probe-image.json` 保留镜像实际目标C/h、观察器、库、应用摘要及ldd，PR与作者补充身份明确。参考镜像RepairDofMap.C在src/postprocessors，最终镜像在src/vectorpostprocessors，两者字节SHA相同，属于观察器源码布局差异，raw实际DOF与20输出均核对。

36份raw的case.i均与本次公开适配器从当前输入生成的精确字节一致；全部材料CSV及原生首残量/hand-coded Jacobian重新提取，并用真实DOF位置读取，未猜14N的变量编号。独立80位数学计算不依赖该适配器，给出另一条全输出数值验证链。

## 固定八探针的身份边界

八探针实际在 **f2994588faffcc22d2d5c0d50170dc181c3acbd08dfbf40597fc87bd6a1a785b** 内运行。审阅者重新读取该镜像：其 `/tests/judge.py` 是旧 **64dbd215ebdde01aa66bd11d22f681724416287fe65d6e3dd32580326f5df3a7**，故八探针**不是新judge正式Harbor job**。它们直接import并调用source_repair.prepare；镜像内此后端SHA **714e3f76ededa181e44861f6ad5257ba8a39be83e9a4588f258a516efa212e75** 与正式prepared/当前LF完全相同，镜像内ZIP亦为最终04563。审阅读取probe源码，确认future-mtime、故障注入时机、权限实查、ldd/nm及资源实采，与8份raw相符；没有重新运行8次大build。valid128.725秒，真实新库前后SHA不同，样例02得1。

这条证据支持同一源码构建后端、最终公开包、权限/资源探针和错误分类；新judge完整入口及逐case执行由新正式Oracle与共享subreaper审阅支持，两种证据不混称。一次网络连接失败和有限路径os.access检查不外推为容器全安全证明。

## 最终公开包普通安装

ZIP04563已在固定镜像真实Docker build以普通 `python -m pip install --no-cache-dir /app -r ...` 安装，已实际读取 `moose-30236-verifier-build-v1.job.log` 中构建wheel和Successfully installed记录，未采用editable或源码目录直接import。审阅者又在该最终ZIP固定镜像的新临时容器，禁网/4CPU/4GiB，挂载只读公开验证脚本，从/tmp、低UID清空环境实际重跑两样例8条CLI（validate-input、native run_case、validate-output、grade），结果 `public-cli-rerun.json`。caeoj和caeoj_bundle均从 `/opt/task-python/lib64/python3.11/site-packages` 导入，NumPy2.4.6/h5py3.16.0；命令返回0/0/0/1两次，数值0分是缺陷原件应有结果，不能叫修复参考成绩。

## 未验证项

不重做一次性MOOSE框架构建、12例原生重放、收费考生或新benchmark；不重采已退出正式容器cgroup；不宣称原始两步回归的形貌/Exodiff gold正确。未制造不可杀内核D状态；共享helper的清理失败分支保持原独立mock证据边界。固定HF fresh-cache来自已读生产回执，本次另做本地严格verify而未再次联网fetch。后端探针未直接调用新judge，已明确旧身份。上述边界内，实际完整Oracle/独立数学/源码与raw链条足以支持本题最终后端和数据通过。

原始检查脚本、全部JSON和运行材料SHA列在 `materials-sha256.json` 与 `evidence-checks.json`；实际脚本输出 `evidence-review.log`。本次不改任何公开文件或中央状态。
