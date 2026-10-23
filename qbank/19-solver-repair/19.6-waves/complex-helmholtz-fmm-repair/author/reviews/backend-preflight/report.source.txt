# Bempp20 独立后端配置预审

结论：**公开要求、实际配置和后端消费映射通过本次预审；最终 ZIP 的完整 formal Oracle-v3 验收尚未完成。** 没有发现需要更改正式配置或执行器的 P0/P1 问题。旧版真实探针 7/7、原生参考 12/12 与最终包的有界数据/SDK 验证具有清楚的版本边界，不能合并声称最终包已完成全量原生 Oracle。

本次按 `caeoj-configure-judge` 及 workflow/current-backend 读取 instruction、DATA、CONTRACT、实际 12 case 配置、public/extension/harbor、共享 source_repair、judge 和 prepare_harbor 消费者。仅写本报告目录；没有 prepare、重启/中止 Oracle、重算高成本参考、改动正式材料或调用付费模型。独立便宜检查入口为 [checks.py](checks.py) 与 [inspect_runtime.py](inspect_runtime.py)。

## 公开要求→实际消费者→证据

| 公开要求 | 实际配置与消费者 | 独立核对结果 |
|---|---|---|
| 恰有 exafmm.py/fmm_assembler.py/helpers.py，普通文件，各≤1048576字节 | source-repair.json 三替换项及 max_source_bytes；source_repair.prepare 精确集合、is_file/is_symlink/字节大小检查 | extra/symlink 实际 invalid_submission；syntax 实际 candidate build_error。超限普通文件边界本轮仅静态核对，不冒充已有 oversize 探针 |
| 真实完整原库，仅替换三 PY；真实快速接口，Numba近场、P1强形式 | public driver 固定调用 ExafmmInterface、dense_interaction_evaluator、Bempp strong_form、FMM potential；p10/ncrit16/dense_evaluation=False、regular6/singular8 | 驱动没有解析答案/结果纠正；三 PY 和三 pyc 位于 /opt/upstream；独立数据审计已核对 base/reference 各371源文件，reference 仅三文件允许变化 |
| 原件基线及健康检查先于候选执行 | prepare 先删原件三 pyc→baseline build→baseline_probe→写三候选→再删三 pyc→candidate build | compiler 破坏原 Python 为 Trusted baseline build failed: build_error；破坏原 driver 确到 Trusted baseline runtime probe failed: probe_error，均属 RuntimeError 基础设施错误 |
| 强制实际重编，不信任未来 mtime | rebuild_files 三 pyc；CMake repair_sources 调 py_compile CHECKED_HASH；prepare 两阶段删除三文件并记录 rebuilt SHA | valid 实际将原 pyc 时间置2100年后仍重建；三候选源码 SHA 与真实 import 的 __file__、__cached__ 及三 pyc SHA 逐项吻合，且都不同于原件 pyc。候选编译耗时0.2683秒 |
| 运行时源码、原生 ExaFMM及依赖固定 | prepare 最后递归将整个 buildroot root-owned并移除 solver写权限；venv 在 buildroot外 root-owned；每例 PYTHONDONTWRITEBYTECODE=1 | valid 的 UID1000 无权改 /opt/upstream、三PY/pyc、driver/CMake、submission；本轮另检查 base venv 全8726条目，无 solver 模式写权限，真实 ExaFMM .so 为 root:root 0755 |
| 点四输出、曲面五输出，实虚/xyz逐项容差1e-6+1e-5*abs(ref)，每例全通过才得1 | 每例 reference/grading.json direct_outputs，pointwise/per_time/per_component；judge预检全部计划；grade调用公共同入口 | 本轮实际 preflight 全12case，逐一核对所有 output→quantity→unit→array→component绑定及精确容差，见 actual-case-plans.json；独立数据审计364次0.99/1.01阈值扰动与非法输出验证通过 |
| 缺输出/非法/非有限不能通过 | judge 区分 missing_output/invalid_output_file，独立 grade worker 再作完整契约与数值检查 | 结构/非法输出及 final ZIP 14参考、28真实磁盘变体由独立数据报告证明；评分配置坏或参考缺失在候选之前预检 |
| 逐例600秒、评分30秒 | judge.execute process.wait(600)，grade worker subprocess.run(timeout=30)；max_output_bytes=null | 候选运行失败/超时记0；grade超时或score=null抛基础设施错误，不能作零分；null无额外未公开文件限额，仍完整契约校验 |
| 源码编译60秒；原件/环境故障不计候选零分 | source-repair build_timeout=60，baseline_timeout=60；健康probe使用min(60,build_timeout)=60 | compile_source独立进程组，超时killpg；候选build_error/build_timeout封装SubmissionError；原件build/probe RuntimeError不被judge的ValueError捕获 |
| 真正 Python 导入挂起能被终止 | runtime-timeout在候选exafmm.py追加循环，真实run_case→真实driver导入此模块 | 实际经同一judge.execute的5秒加速限额返回timeout；实际Python pid61已不存在或Z，非只在mock里sleep；不声称实测600秒边界 |
| 4CPU、4GiB、无外网；独立verifier私有资料 | merge environment cpus4/memory4096，verifier separate/no-network；test.sh chmod700 /tests /logs/verifier；solver UID1000/no-new-privs | 旧valid实测 cpu.max=400000 100000，memory.max=4294967296，外连denied；/tests、cases、reference、logs、probe不可读写。公开ZIP无author/hidden cases/harbor/tests |
| 可写磁盘工作目录、至少8GiB，例后回收 | judge每例 TemporaryDirectory，cwd该目录、chown1000且0700；driver将Numba/OpenCL缓存独立临时目录；真实ExaFMM相对缓存落当前工作目录 | 12原生参考实际使用磁盘scratch；之前小tmpfs失败保留。本轮只读base容器/tmp可用约903GB，仅说明当前Docker磁盘条件，最终formal逐例磁盘与完整运行仍待v3结果核对 |
| 12例等权，两个公开样例仍在分母内 | judge paths实际12，save_report passed/total；selection public_cases仅加public_sample，不减分母 | 分母静态确认12；最终complete/reward/逐例标识待读取v3真实报告 |
| 总预算覆盖所有合法逐例执行 | task_config合并verifier=8020秒：400+12*(600+30+5)；repair显式minimum=60+60+60+12*(600+30)=7740秒 | 额外余量280秒；agent1800秒、environment build1200秒另列，均非逐例执行预算。静态预算足够，不等于最终formal已校准 |

## 版本与旧证据的有界复用

旧ZIP为 `241b6bad4d344139e034dd798638a0cb62d0a364ae28c9b999a41a7bb9e18e27`，来自 `bempp-oracle-v1-prepared/tests/agent.zip`。最终ZIP为 `3b2f5344125bf5679bd026bef828bbe97a44c9a132cca97a5975a25ed8d319bf`。本轮读取双方全部41个member并逐字节SHA比较，**无新增/删除，36份完全相同、5份变化**，完整清单和文本diff见 [zip-comparison.json](zip-comparison.json)。

实际语义变化只有 extension 两行固定 `data_file == input.h5` 校验与 instruction 安装后切换到题目录说明；instruction同时由LF改为CRLF。其余三份变化为 MANIFEST 的内容SHA/assembly、pyproject bundle版本、runtime bundle ID，均随上述材料更新。DATA、CONTRACT、全部通用SDK/评分代码、driver、run_case、CMake、两份来源档案、全部公开样例输入/参考/策略字节完全相同。

因此旧探针可复用来证明：相同后端source_repair/同语义judge、原件健康、三PY/三pyc强制重建与导入、相同真实驱动和原生FMM路径、该样例数值判分、相同UID/只读边界/网络与cgroup参数。这是**旧版本实际执行加未变代码的有界推论**，不是最终ZIP重跑。新data_file拒绝分支不能用旧包证明；最终bundle绑定身份、最终包普通安装、最终formal的完整12例与资源/预算须单独取证。

探针构建上下文 agent.zip 独立SHA也确为旧241b6bad，fixture原文件/上下文文件SHA一致；7项原始stdout全部有passed=true、各原始执行returncode0。原始日志逐SHA及实际结果保存在 [probes-independent.json](probes-independent.json)，没有改旧身份或原始日志。仅compiler/baseline-runtime两项的捕获条件较宽，但本轮进一步读取其准确error文本，确认分别真实到达baseline build_error与runtime probe_error，而非把任意RuntimeError误判为指定故障。

本轮同时核对旧v1启动清单的全部72个文件与保存快照，**72/72一致，0缺失/差异**。当前 source_repair.py、source-repair.json、judge-config.json与其完全一致；judge.py仅工作区CRLF/装配LF不同，规范LF文本一致。该快照恢复身份不代表中途Windows共享目录锁事故没有发生，也不能证明运行中的v1没有受影响；旧v1最终结果必须按其真实终态与异常记录解释。

## 原生来源、数值和最终SDK的已存在证据

本轮重新读取 `dataset-v2/reference-report.json` 全12条原生执行：returncode均0、score均1，点例约15.58–37.64秒，曲面约84.67–126.55秒，均低于600秒；全部以4CPU/4GiB/no-network且真实不可变reference image运行。图像ID、driver SHA、输出SHA、逐例耗时摘录为 [reference-run-summary.json](reference-run-summary.json)。这些是原生参考运行，区别于最终SDK/verifier的端到端Oracle。

独立全量数值与契约审计见 [数据审阅报告](../../data-review/repair22-bempp20/report.md)：全部6点直接Green/梯度独立计算，全部6曲面原始dense弱形式加独立P1质量逆及独立外势积分；全部12参考与原生stdout一致。点FMM最大容差占用0.410544，曲面边界最大0.035600，外势最大0.023342；没有把结构预检等同数值正确。

最终ZIP内SDK由数据审阅者用-I隔离子进程真实绑定后重新完整校验/评分全部14输入参考与28磁盘变体，原固定文件名漏检已关闭；包内41份材料全部SHA核对。它证明新SDK/extension绑定的适配与合法固定数据保持不变，不能替代普通离线pip安装或原生Oracle。协调者的 `bempp-offline-v2.stdout.log` 已出现 `12 [(1, 0), (0, 0)]`，仅此简略stdout不足以独立说明全部安装条件，本预审不据此宣布普通离线安装验收完成，最终closure应读其完整脚本/结构记录。

本轮只读base检查 [runtime-readonly-inspection.json](runtime-readonly-inspection.json) 记录不可变image ID、三份原pyc头flags=3（checked-hash），真实原生 `.so` SHA `9732e560b1cb42155b7a310af6156a7d1526b1e5379acd8791ead1550c165689`，venv全部8726条目的solver模式写权限均否。容器带--read-only，故另外按原owner/group/mode计算权限，未只用os.access推断原文件模式。此检查没有运行数值求解。

## 最终formal未决项与已保留失败

预审时 `bempp-final-oracle-pipeline.json` 为 `waiting-for-owned-v1-to-finish-before-touching-prepared-directory`。其脚本等待旧v1状态出现returncode，再顺序唯一prepare最终包并启动Oracle-v3；本轮未触碰该流程。

`repair22-bempp20-oracle-v2.json` 保留phase=needs_review、returncode1、trials0、task_sha256={}。这是活动时prepare/Windows文件锁关联的启动失败，不是候选数值成绩，也不能算完整Oracle。旧v1仍按旧241b6bad身份记录；不能将其结果改写为最终3b2f5344的运行结果。

最终closure须独立读取：最终v3运行冻结清单中environment/tests ZIP均为3b2f5344；全部实际数据/参考/策略、三候选文件与本报告对应；trial exception_info=null；baseline60内built、健康probe60内ready、candidate60内built且记录三pyc重建与源SHA；formal verifier/report.json为complete=true、completed_cases=total_cases=12、score12/reward1，所有实际输出数值逐例accepted，公开样例标识及分母正确；实际资源/隔离条件和磁盘scratch不回退小tmpfs；最终包普通离线安装与源码移走的完整证据。若有超时、运行异常或部分完成则如实保留并定位，不能因进程returncode0或有参考输出便宣布完成。

配置加载、材料版本、有界旧探针与独立数值证据已经闭环到本预审范围；**最终ZIP完整formal执行与发布资格仍待上述v3证据，当前不宣布整题完成。**
