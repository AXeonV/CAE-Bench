# Cantera 19.3.3 独立后端配置与真实消费审阅

日期：2026-10-23。按caeoj-configure-judge技能只读检查；仅写本报告，未运行收费Benchmark、未修改实现。范围为 `two-temperature-state-repair`，不外推其他题、整个容器安全性或HF远端。初审及修复记录保留，最终验收状态见最后一节。

## 当前结论

CMake已经代替会写源码根目录的SCons构建：实际强制重编4个直接/传递依赖PlasmaPhase.h的上游翻译单元及可信driver，再链接真实Cantera共享库。头文件依赖闭包风险与world-writable权限缺陷已修复，并由最终镜像探针及独立Oracle 12/12完成有限范围验收。当前没有仍阻断本题后端通路的实现发现；使用最终job证据，不以旧v2顶替。初审下述“四项产物”等描述是历史版本，当前为7项。

## 发现与建议

### [P2] PlasmaPhase.h消费者未全部重编，类布局变化时旧factory分配尺寸失配

`public/CMakeLists.txt`仅从upstream_objects排除PlasmaPhase.os与canteraStatic.os，重编PlasmaPhase.cpp和driver。实际上游 `src/thermo/ThermoFactory.cpp:18,56`也包含PlasmaPhase.h，并通过 `new PlasmaPhase()` 实例化对象；它的旧ThermoFactory.os仍被链接。

当前参考修复若只增加覆写而不改对象布局可以工作，但允许的头文件内部实现如果引入成员缓存，旧factory编译进的sizeof(PlasmaPhase)会与新构造函数不一致，产生不正确分配。单个参考解通过不足以证明header提交的构建语义等价于从可信源码重编。

最小建议：同时排除旧ThermoFactory.os，重编真实ThermoFactory.cpp；相应声明并删除该对象产物。比新增考生类布局限制更直接。已发送实现Agent并抄送主Agent。此风险是未覆盖头文件依赖，不是已观察到当前Oracle堆损坏。

### 已知权限缺陷：修复中，等待新镜像证据

委派方报告有效未来时间戳探针发现从Windows复制的上游头文件具有world-write。共享prepare只冻结build子树；本题替换头文件位于 `/opt/cantera-source/include`，非替换头文件与可信driver源码也不在该冻结范围，因此必须由基础镜像的root所有权/权限建立只读前提。

当前 `work/repair-22/cantera-1872/offline-sdk-context/Dockerfile`已加入对 `/opt/cantera-source /opt/repair-driver /opt/repair-cmake` 的root:root与go-w处理。这是有效的静态修复方向：prepare随后仅chown build子树给UID1000，编译完成再冻结build；include/source及可信构建脚本保持只读，root verifier仍可写入声明替换头文件。须在最终镜像确认头文件本身、其父目录、非替换头文件、源码、可信driver和CMake均不能由UID1000修改，且baseline/candidate仍能构建。不能复用旧镜像通过结果关闭。

## 公开要求 → 配置/消费者

| 要求 | 实际绑定与静态判断 |
|---|---|
| 仅提交PlasmaPhase.h | source-repair.json恰声明一个basename，target为真实include路径；共享prepare拒绝额外文件、链接和>1048576字节文件，冻结提交并哈希。 |
| 真实头文件进入新对象 | CMake使用真实PlasmaPhase.cpp、真实include；删除其CMake .o可强制重编，即使头文件/旧产物未来mtime。factory依赖风险见上。 |
| 真实新共享库与驱动 | CMake目标cantera_repair输出lib/libcantera_shared.so.3.1.0，SOVERSION3；driver链接该目标。配置删除真实版本文件及driver真实.o/bin，避开CMake创建的.so/.so.3链接。共享运行环境LD_LIBRARY_PATH来自build_directory/lib；实际ldd和执行待探针。 |
| rebuild_files约束 | 四项均在build_directory之下；配置校验拒绝越界，运行删除前要求普通文件且非symlink。静态不能证明镜像内当时文件类型与目标路径一致，需实际构建日志/探针。 |
| TD/TP实际调用与状态独立 | driver每行newThermo，先组分与Te，再TD或TP，改Te2；mode1重设同一压力。通过ThermoPhase&调用真实API，输出pressure/electronPressure/density/concentration；没有在adapter计算修正答案。 |
| 方法约束 | 只接收头文件且可信driver/其余源码不可修改由装配与权限实现；禁止参考读取/硬编码及保留既有接口须另做源码方法审查，数值grader不自动证明。 |
| 数值容差与四输出 | 12个实际reference/grading.json均direct_outputs，四quantity规则完整；pressure/electron_pressure atol1e-7，density1e-12，molar_concentration1e-14，rtol均1e-10，逐时逐分量pointwise。concentrations输出对象与molar_concentration quantity区分正确；author模板非运行时入口。未独立审计参考物理数值。 |
| 全case等权 | 共享judge预载全部case的实际grading；各例score==1计通过，reward=passed/total。缺参考/坏配置先于提交执行失败；非有限/缺输出由SDK及独立grade结构校验拒绝。 |
| 失败分类 | baseline删除产物后真实构建，最多60秒，失败RuntimeError为基础设施；候选最多900秒，失败SubmissionError转build_error/build_timeout零分。数值执行失败/超时记零分；输入/参考/判分故障抛基础设施。当前没有baseline_probe，可信动态运行时损坏尚未实际注入验证；不能仅以编译成功宣称所有运行时故障分类覆盖。 |
| 时间预算 | 候选900秒、基线min(60,900)=60秒；单例30秒、判分30秒；12例装配最小1680秒。judge-config base1900+12×(30+30+5)=2680秒，实际staged task.toml消费2680。agent2400、environment构建1500，后者是镜像构建上限，不是候选编译上限。当前上界静态覆盖；最终真实执行与资源cgroup待证。 |

## 证据状态与下一步

Oracle v1原始exception保留为RewardFileNotFoundError（未产生reward文件）；委派方归因为UID1000 baseline SCons需写源根，属基础设施故障，不记候选错误。本次读取异常仅证明外层未产reward，不据其单独推断更深原因。v2委派方报告12/12，但发生在权限修复前，暂不作为最终镜像验收。

已读author/backend_probe.py，当前设计覆盖valid未来产物时间戳、真实公开样例判分、源/产物SHA、ldd、UID1000指定路径权限、额外文件、语法和可信编译器缺失分类。脚本存在不等于结果已通过。最终需接收：新镜像有效探针、非替换头文件/父目录只读证据、真实加载新共享库路径与产物hash、baseline/compiler故障分类、重建范围修复及匹配版本Oracle报告。公开包独立普通安装、候选编译超时及运行超时/进程清理等未由上述脚本覆盖，保持明确边界；不机械要求全部重复低风险旧框架测试。

## 增量静态复核

头文件消费者闭包问题实现已修：当前CMake排除并重编ThermoFactory.cpp，同时还纳入经上游间接include闭包识别的ElectronCollisionPlasmaRate.cpp、ReactionRateFactory.cpp；rebuild_files同步增加三个真实CMake对象，现共7项（4个库对象、真实版本库、driver对象和执行文件）。原P2的最小修复方向成立，等待该版本实际构建和运行，不以旧版Oracle关闭。

本轮另读取Oracle v1的原始baseline-report和baseline-stderr：真实baseline build_error、exit2，stderr明确SCons写cantera.conf发生Permission denied，并有外层RewardFileNotFoundError。由此可以直接将失败定位为候选替换前的可信baseline构建基础设施失败，无需只依赖委派归因；保留此失败历史。

## 最终镜像与真实消费验收

### 版本和证据核对

本轮读取了最终 `runs/harbor/jobs/repair22-cantera1872-oracle-final/two-temperature-state-repair__CSArLUJ/` 的result.json、verifier/report.json、baseline/candidate构建report及baseline stdout；最终归档oracle.json的全部cases与原始报告逐项一致。原始result明确agent=oracle、verifier_environment_mode=separate、reward=1.0、exception_info=null，完成12/12，不是旧v2结果。

当前共享source_repair.py、judge.py及题内source-repair.json，与 `runs/harbor/tasks/two-temperature-state-repair/tests/` 的装配副本逐字一致（只归一化CRLF）；public CMake与offline-sdk镜像构建上下文CMake一致。最终Oracle日志实际编译4个上游.cpp、driver.cpp，再链接库与执行文件，支持实际消费已修CMake，而非仅看到文件存在。

当前author/generated/PlasmaPhase.h实际SHA为 `92dce971460d46ce4b52daf3b2db4e9eb8396c936d9481b544a5d877c25e269a`，与最终Oracle、valid探针源码哈希相同。最终Oracle的7项产物SHA与valid探针的7项也全部相同，覆盖4个库对象、真实版本.so、driver对象和执行文件。

归档backend-probes.json的4项逐项匹配 `work/repair-22/cantera-1872/probe-{valid,syntax,extra,baseline-compiler}-final.json` 原始结果，四项均通过；同时复读author/backend_probe.py核对断言实际含义。本审阅未重新运行容器，不把这些证据扩写为任意未来重打镜像的认证。

### 关闭的发现

**头文件依赖闭包P2关闭。** header-dependency-closure.json列出4个上游TU；独立rg确认PlasmaPhase.cpp、ThermoFactory.cpp直接包含PlasmaPhase.h，ElectronCollisionPlasmaRate.h包含该头并被ElectronCollisionPlasmaRate.cpp、ReactionRateFactory.cpp使用，完整src/include搜索未发现其他消费者。当前CMake显式重编这4个真实源码并排除它们的旧.os，配置明确删除相应4个.o，driver另重编。实际最终baseline stdout逐项显示这5次编译及新库/driver链接，关闭旧factory sizeof/头文件布局风险。

**既有权限缺陷关闭其本题可信路径范围。** 镜像对整个 `/opt/cantera-source /opt/repair-driver /opt/repair-cmake` 设置root所有权与go-w；prepare仅在构建期间将build子树交UID1000并最终冻结。valid在UID1000查询的os.access结果覆盖替换头、非替换ThermoPhase.h、真实PlasmaPhase.cpp、源码根/src/include、driver目录/源码、CMake目录/文件、最终库/bin：均可读不可写；submission不可写，/tests、/logs/verifier、/probe不可读写。该结果与递归权限实现一致，说明之前world-write状态没有进入这次有效探针。不将os.access查询冒称为对每个文件实际发起写入系统调用，也不外推整个文件系统安全性。

### 重建、绑定、分类与资源

valid脚本在prepare前给全部7项声明产物设置2100年mtime；prepare实际删除后重建成功，候选报告为built约21.29秒，真实公开样例由judge.execute调用固定adapter/driver并经grade_case断言满分。脚本比较提交SHA及全部实际产物SHA与可信构建报告；ldd确认driver解析到 `/opt/cantera-source/build/lib/libcantera_shared.so.3`。结合真实输出判分与最终Oracle相同产物哈希，足以支持本题header→新对象→新共享库→可信driver的实际绑定；ldd单独不会被视为完整动态加载证明。

syntax实际分类build_error、额外文件分类invalid_submission；移走缓存构建原先使用的g++后，baseline重新构建失败并走RuntimeError基础设施分支。此分类覆盖可信编译器损坏，不声称覆盖所有潜在运行时基础设施故障。v1失败继续保留为基线SCons写源码根导致的基础设施历史，未记考生错误。

valid记录cpu.max=`400000 100000`与memory.max=`8589934592`，匹配4CPU/8GiB；一个外部socket尝试失败。最终Oracle baseline构建约13.79秒、候选构建约29.23秒，低于实际60/900秒限额，verifier总阶段约93.17秒，低于2680秒。只证明此次实际执行及配置预算覆盖，不以参考解耗时替代所有候选最坏资源校准。

### 验收结论与范围

本题当前最终版本的配置/真实构建执行链可验收：初审闭包问题、权限问题均有修复与匹配版本证据；最终独立Oracle全12例通过，无exception。没有需继续阻断此后端验收的P1/P2发现。

有限探针未覆盖候选编译超时、超限文件、运行超时及后续case恢复；没有对整个容器进行安全审计，也没有独立重做全部物理参考/容差边界审计、方法审查或HF远端检查。公共包独立普通安装与最终考试材料的独立审阅可由对应专责证据交付，不从Oracle通过推断。上述未覆盖范围不被包装为通过结果，亦不为了形式机械追加无新风险的同批测试。
