# point-ownership-repair 独立后端审阅

最终独立复核结论：**通过**。最终ZIP SHA256 `576823e42c10a91ca840cf6d21325340bf116ffa1582698b0f5f77bed6823a61`；新版8/8后端矩阵及formal Oracle-v3全部12例终态、源码/数据/评价绑定、资源与隔离实证已独立核对。旧120s超时和fixture误检历史保留，不计入通过依据。详见末尾“最终v3独立复核增补”。

初审结论（历史，已由末尾增补关闭）：**资料不足，完整后端验收未完成**。静态公开要求映射、独立数值边界/非法输出检查、实际原件树和九产物依赖闭包核对通过；新版300s原件基线重建、修正探针及最终ZIP真实Oracle正在由root执行，不能提前报告通过。此报告保留120s真实timeout及旧fixture误检事实，后续应以增补记录复核结果。

## 范围与版本

按caeoj-configure-judge及其workflow/current-backend执行，读取最终instruction/DATA/CONTRACT、实际12case配置、judge-config、source-repair及Harbor配置、真实消费者源码、source树和现有原始执行记录。本轮只读正式代码/数据，仅写runs。没有代实现或改动正式配置，没有运行收费模型，也没有启动额外重编以争用root的校准资源。

公开最终ZIP SHA256 `576823e42c10a91ca840cf6d21325340bf116ffa1582698b0f5f77bed6823a61`；三文件、全部实际数据和数学参考已在本agent独立全数据审计中完整核对：[数据报告](data-review.md)。本轮额外版本哈希见 [infrastructure-and-versions.json](backend-infrastructure-and-versions.json)。

## 需求→消费者→当前证据

| 公开要求 | 实际配置/消费者 | 独立证据/状态 |
|---|---|---|
| 三字段owned/cell_id/distance，所有Q均判，归属和原tag精确，distance绝对+相对1e-8 | 12个reference/grading.json的direct_outputs，quantity/unit准确绑定；共享case_grading→grading_policy→grading_metrics | 12例全部策略和完整参考已读；真实样例扰动及精确边界检查通过 |
| 每例全部通过才得1，12例等权；两sample计分case仍各一次 | judge.save_report以score==1计通过，reward=passed/total；selection.json含public_cases，path枚举12例 | 分母与公开样例标识映射明确；新完整执行待验 |
| 仅utils.h≤1048576字节普通文件 | source-repair.replacements/max_source_bytes；prepare严格文件集合、拒绝链接/超限并冻结source hash | 静态符合；v2前三cheap探针已实际拒绝extra/symlink/oversize，尚待全套结果 |
| 真正头替换、重新构建依赖闭包、不用候选缓存 | prepare先删原件9产物重编/探针，再写目标头、再删9产物候选重编，记录sources与built_artifacts SHA | 本轮实际core镜像ninja依赖核对9产物集合完全一致；新版valid重编/未来mtime陷阱实证待验 |
| 构建240s，单例20s，4CPU/8GiB | candidate compile_source.wait240、每例judge.execute.wait20；Harbor environment cpus4/memory8192 | 当前参数与消费者符合；新版cgroup实证待valid探针；runtime-timeout探针拟用3s验证同一实际C++执行路径与进程组清理，不冒称已经跑20s边界 |
| 基础设施不算候选零分 | trusted baseline失败抛RuntimeError，judge只catch ValueError作submission错误；评价worker超时/scoreNone抛RuntimeError | 缺参考/缺策略CLI均exit2；120s真实基线超时实际无reward且Harbor报RewardFileNotFoundError，不能算candidate错误 |
| build/runtime候选失败记零分 | SubmissionError build_error/build_timeout，execute runtime_error/timeout；非有限/结构错误grade invalid_output | 非法输出独立测试通过；新syntax/runtime-timeout真实探针待验 |
| verifier总预算不能截断合法路径 | merged task.toml verifier1560s，separate/no-network；base900+12*(20+30+5)=1560 | 构建300+240+baselineprobe60+12*(20+30)=1200s，余360s；静态足够，不等于真实校准通过 |
| 公共SDK和verifier相同语义、最终包可独立安装 | verifier及environment使用同SHA576823包；独立grade用新包src | root最终ZIP普通断网pip安装-v2日志已读：ordinary install成功、源码移走、pip_check无错，原件sample01=0/02=1；此为真实安装证据，不是candidate修复Oracle |

## 独立容差与非法输出实测

[ tolerance-illegal-output.json ](backend-tolerance-illegal-output.json) 保存16个真实样例输出测试及3个可精确表示的边界测试。正确样例accepted；owned=nextafter(1,+inf)和cell_id=nextafter(31,+inf)均wrong_answer，证明无浮点宽容放过身份。distance在真实非零参考的公式阈值内侧accepted、外侧wrong_answer。直接调用同一evaluate_observation，在reference=0、atol=rtol=1e-8时，actual=nextafter(1e-8,0)、1e-8通过，nextafter(1e-8,+inf)失败；明确验证等号属于通过。

NaN、正/负Inf、缺字段、多字段、错误shape、float32替代、错误probe身份、错误times、根属性、dataset别名均invalid_output/exit1。缺参考与缺cell_distance策略均CLI exit2，记录在infrastructure-and-versions.json；不以坏参考为考生零分。所有变体仅位于runs，未修改正式参考/数据。

## 原始源码与九产物闭包：实际镜像独立核对

本轮在配置指定core:base镜像运行轻量只读程序，无网络、4CPU/8GiB，不执行构建。容器内DOLFINx456/Basix183/FFCx128个文件完整逐字节摘要分别为b53b4c1c...、ea4e5386...、2c4bac44...，与固定原始归档及此前独立cache核对记录相符；原件utils.h SHA6035e24b...。

实际ninja -t deps中目标头的消费者是6个库对象（DirichletBC、DofMap、fem/utils、VTKFile、XDMFFile、xdmf_function）加ownership_driver对象，再附libdolfinx.so.0.12.0.0与ownership_driver，共9产物。与source-repair.rebuild_files集合完全一致，全部实际存在，逐产物SHA记录在 [core-tree-closure.json](backend-core-tree-closure.json)。这证明配置使用真实完整原件且闭包没有仅重编driver；尚不能替代新版候选实际删/重编/链接证据。

## 已出现的真实失败与探针缺口

1. **保留Oracle-v2失败**：新ZIP576823的旧120s trusted baseline重建发生build_timeout，实测120.188835687s，日志列明9产物已删除。Harbor异常为RewardFileNotFoundError；CLI returncode0不代表任务通过。此次无有效candidate分数，绝不能用旧ZIP5dae的Oracle12/12为新ZIP验收背书。
2. **旧baseline-runtime误检不得计通过**：旧probes/report.json虽然将SDK破坏场景记passed，但reason实际为Trusted baseline build failed: build_timeout，根本没有走到SDK运行时检查。这是fixture假阳性，root已明确弃用该项验收。
3. **本轮独立发现并反馈探针错误字符串**：新backend_probe原严格断言期待runtime probe failed: build_error；实际compile_source(command_override)失败状态为probe_error，prepare抛runtime probe failed: probe_error。root已修正author探针；已冻结旧镜像中的失败需保留，不得改写成通过。后续只在匹配新镜像的原始日志中确认指定SDK破坏确实到达probe_error，不能接受任何基础设施异常泛化匹配。
4. 当前新v2报告已见4/8（extra/symlink/oversize/compiler），后三者及baseline-runtime、syntax、valid、runtime-timeout未齐；不同fixture镜像的结果必须各自带实际版本/原始日志，不以一份报告混淆。

## 待复核完成条件

300s配置必须实际进入最终verifier镜像；trusted baseline实际built且健康probe ready；候选PR头在240s内built并记录9产物重建/源码SHA、真实ldd库绑定；最终576823包的完整12例Oracle需complete/reward1且exception=null。valid探针需证实未来mtime仍删重编、原始树/driver/CMake及所有后续可写缓存不可改，UID1000、network denied及cgroup配额；baseline-runtime需确为probe_error，compiler确为build_error；syntax与实际C++超时/子进程组清理需完成。新原始结果齐备后独立读取并增补，当前不宣称后端通过。


## 最终v3独立复核增补

上述初审待项现已完成。这里逐一核对root提供的真实原始结果，没有代改判题/fixture或重新生产参考。

### 八项真实探针及修订链

独立读取v3全部8份stdout/stderr，将每份stdout末条JSON与matrix/report.json逐项精确比较；8/8一致且passed。完整原始日志哈希、字节数与实际结果保存在 [probes-v3-independent.json](backend-probes-v3-independent.json)。extra、symlink、1048577字节oversize均invalid_submission；compiler被破坏时为Trusted baseline build failed: build_error；破坏numpy导入的baseline-runtime确为Trusted baseline runtime probe failed: probe_error。后者只能在300s预算下实际原件编译built后到达，已排除旧“编译超时也算SDK坏”的假阳性。syntax为candidate build_error。

修订链清晰保留：最旧report把baseline build_timeout误记baseline-runtime通过；v2冻结fixture已实际到达probe_error却因严格断言仍写build_error而AssertionError；独立反馈后v3只接受准确probe_error并实际通过。v2失败stderr及旧report仍在原目录，不以更新后的fixture重解释旧日志。

valid探针先把9产物mtime设未来，后端仍明确删除全部9产物并真正重建，candidate built耗时 `86.74153513800047s < 240s`，source utils.h SHA为上游PR完整头 `44cee2d91b2400ce193c6a93879884cdf6aaec06c343b3c36718590b6fb7b4eb`。九产物removed集合、built_artifacts_sha256集合与配置和本轮实际ninja闭包均相同。ldd确认ownership_driver实际加载 `/opt/dolfinx-repair-build/lib/libdolfinx.so.0.12`，driver二进制摘要变化，没有沿用旧驱动。

valid的真实solver UID1000下，/tests、/logs/verifier、/probe不可读写；submission、原源码树及头/其他mesh头、driver/CMake目录与文件、全部九构建产物及旧原件对象缓存均不可写，network=denied。cgroup cpu.max=`400000 100000`、memory.max=`8589934592`，即4CPU/8GiB，健康baseline probe ready。无限循环插入真正C++入口的runtime-timeout在同一judge.execute的3s探针限额触发timeout，实际原生主C++进程pid144终态Z，证明该主进程已终止，不是仅模拟Python睡眠；共享执行器源码执行killpg，但本轮未逐个实测所有MPI辅助进程。3s是探针加速限额；正式消费者配置仍为20s。

### 最终formal Oracle-v3终态与所有12例

独立读取 `runs/authoring/repair-22/repair22-dolfinx-oracle-v3.json`：phase=completed、returncode0、trials1、exception_info=null。再直接读取 `runs/harbor/jobs/repair22-dolfinx-oracle-v3/point-ownership-repair__6UZQeip/result.json`：exception_info=null，verifier reward1。formal verifier/report.json为score12/total_cases12/completed_cases12/complete=true/reward1；逐例01..12均accepted/score1，公开case01/02分别保留public_sample01/02，未变分母。

formal的真实baseline在300s配置下built，耗时 `99.69161644999986s`；健康probe ready耗时 `1.588349814999674s`；候选PR头built耗时 `71.7777625350027s < 240s`。baseline与candidate都记录删除全部9产物，candidate记录source SHA44cee...及九产物构建SHA。新300s预算并没有修改公开240s候选限额。

对全部12例，逐份读取实际verifier result.h5，与该冻结任务reference.h5的所有dataset比对：key集合、dtype/shape与全部数组值逐项一致；每例evaluation_sha256与预检evaluation_manifest一致。再核supervisor冻结的76项任务资产SHA与当前实际准备目录逐份比对，全部匹配，包含两个agent.zip、source-repair配置、solution PR头、全部输入和全部case评分/参考。由此确认完整运行绑定最终ZIP576823与baseline300配置，不是把旧ZIP Oracle搬用到新版。

formal真实容器snapshot的Docker内存8589934592、NanoCpus4000000000及内部cgroup快照4CPU/8GiB也独立核读；snapshot_exit_code0。该独立formal快照与valid探针限额相符，不只依赖TOML声明。网络隔离的实际可连接性由同后端valid探针验证，formal配置为separate/no-network。

完整独立终态、全部case输出摘要/逐数组误差、预检评价绑定、76冻结资产检查、baseline/candidate状态、formal cgroup及最终原始报告SHA见 [formal-v3-independent.json](backend-formal-v3-independent.json)。最终版断网普通pip安装证据亦为576823，见前述public-install-v2日志；全部数据/参考独立数学资格见另行数据报告。

### 最终边界

本轮原先的后端待项全部关闭，最终配置/数据/公开包/真实执行及资源对本题合法范围相符。历史120.1888s原件超时仍属真实基础设施失败记录；候选被接受的证据仅来自新v3完整终态。结论只针对固定单进程线性三角形/四面体API范围与当前冻结资产，不外推到MPI或其他未声明功能，也不是所有未来修复提交的性能保证。

归档说明：原始独立报告保留于runs/configure-judge/repair22-dolfinx/report.md；本副本只调整同目录证据链接，审阅结论及原版本身份保留。
