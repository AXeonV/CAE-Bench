# Meep #2338 独立可信后端审阅

结论：**通过，限于本报告列明的实际证据范围**。按 caeoj-configure-judge 及 caeoj-author-repair-question/references/backend.md 对最终公开要求、配置、共享消费者、冻结材料、正式 Oracle 与真实七探针进行独立审阅。没有修改实现、重编求解器、重跑长FDTD或调用收费模型。本次新增容器只读已有源码并运行 ldd。

冻结 ZIP `acac8a89d2b02b4aa1a753fcdd2354b836c2af0af1cb21748973ed41564e0027`，HF `7abc5ec8686026548ae4abdfeb4530a33ccd8332`。脚本 independent_backend.py、实际输出 actual-evidence.json、材料 materials-sha256.json 与两个独立 image JSON 位于本目录。数据与数学认证见 `runs/data-review/repair22-meep2338/report.md`。

## 公开要求到消费者

| 要求 | 配置与真实消费者 | 实际证据 |
|---|---|---|
| 仅一个普通 step_db.cpp、≤1048576字节 | harbor/source-repair.json replacements/max_source_bytes；共享 source_repair.prepare | 精确目录集、普通文件、symlink与大小检查在冻结前；额外文件和软链真实探针拒绝 |
| 原件健康、候选真实重编一个目标TU | baseline_timeout_seconds=300、build_timeout_seconds=300；remove_build_artifacts、compile_source | 原件/候选分别删除7产物；两份真实stdout都有 step_db.lo 编译、libmeep.la 链接、driver.o编译和exe链接 |
| 真实原件故障不得计候选错误 | 原件compile/probe先于替换；RuntimeError与SubmissionError分层 | 缺g++及SDK健康故障真实探针均 infrastructure_error；候选语法错为build_error |
| 四输出逐值严格比较、每例全部满足 | 8份 reference/grading.json direct_outputs，四quantity各自绑定unit=1与pointwise/per_time/per_component | 独立8阈值两侧、8 nextafter邻界、结构/数值错误与坏参考检查；score分别1/0/null，未使用作者模板作运行时容差 |
| 每例1800秒、评分30秒 | judge-config.json；judge.execute/评分worker subprocess | 正式报告limits一致；1800逐例调用、独立评分预算与超时基础设施分类可追踪 |
| 4CPU/4GiB、无外网 | 最终task.toml、独立verifier环境；setpriv UID1000 | 真实探针 cgroup cpu.max=400000 100000、memory.max=4294967296、网络访问denied；配置no-network |
| 总预算覆盖所有阶段 | prepare_harbor task_config及修复后端最低预算检查 | 实际准备 task.toml verifier=15680秒；1000+8×(1800+30+5)，最低含300+300+60+8×1830=15300秒 |

源文件白名单只允许真实 step_db.cpp；头文件不允许修改，因此本题强制重建的是该实现TU及其真实库与驱动，而非声称重建任意头文件依赖闭包。两种.o、.lo、.la、版本so、driver.o及exe七项均显式列明，不将CMake build无动作当编译验证。候选编译后build树转root归属/只读，源文件和固定驱动本身不向运行UID开放写权限。

## 独立源码与执行闭包

独立 tar 哈希检查全部700原始文件，真实head仅step_db.cpp和上游Python测试不同；producer只应用真实step_db.cpp。再启动两个无网络、UID1000只读容器逐文件校验base与production：base700原件零差异，production仅step_db.cpp变化，其SHA为 `019e50fd8f5bebc9cf65efd2d1573eb10d1780b334527ff1ff56fbef9e864887`，两者均733文件，另33项均Autotools生成材料。两镜像真实driver与CMake文件SHA也分别记录并匹配题内固定文件；ldd实际指向 `/opt/meep-repair-build/upstream/src/.libs/libmeep.so.30`。

独立比较探针context与最终正式prepared tests：source_repair.py、judge.py、source-repair.json、judge-config.json、selection.json及agent.zip一致；probe提交逐字节等于真实修复文件。共享当前judge.py在Windows工作树采用CRLF，prepare_harbor按实现转LF；文本完全相同，prepared和probe实际字节相同，已分别保存SHA，不掩盖换行差异。

逐项重新计算 formal-oracle/runner-state.json 记录的全部正式prepared文件SHA，全部匹配，确保探针和Oracle消费的代码、数据、参考及ZIP是本轮固定材料。没有把随机目录下旧探针当作最终证据。正式build/report.json记录源码SHA和七产物SHA，原件和候选stdout实际显示上述完整TU/库/驱动构建链。

## 正式Oracle

独立读取 trial-result.json：exception_info=null；verifier-report 为 complete=true、8/8 accepted、reward=1。原件真实重编 **8.74799秒**，候选 **9.72800秒**，原件实际健康探针 **1.07962秒**。全部8份真实运行HDF5另外由本次独立脚本打开，7数组的dtype/shape/值逐位等于本例正式reference。未仅引用作者 output-bindings.json 的断言。

评分消费者在执行候选之前prepare全部实际参考/config；独立损坏reference试验返回evaluation_error且score=null，框架在preflight/worker路径将其作为基础设施错误。四quantity数值策略与公开atol/rtol一致，构造错误底面符号、分量反序或通量比例均失败；非法输出由完整CONTRACT先行拒绝。

## 七个真实探针的原始证据复核

逐一读取 runs/authoring/repair-22/meep2338-backend-probes 的原始 stdout JSON，与作者汇总每一个原始键交叉核对，并检查脚本实际注入和共享消费者。

| 模式 | 实际故障/动作 | 结果与范围 |
|---|---|---|
| valid | 给七产物设未来mtime=4102444800，再真实原件/候选强制重建 | actual TU/库/driver重编，来源与七产物SHA绑定；真实样例判1；prepared ZIP SHA精确匹配最终ZIP |
| syntax | 候选替换为非法C++ | 原件健康之后候选g++报告语法错，build_error；候选失败 |
| extra | 额外extra.cpp | invalid_submission，未混入编译 |
| symlink | 提交指向私有修复的软链 | invalid_submission，未混入编译 |
| compiler | 完整缓存存在时移走/usr/bin/g++ | 删除缓存后原件实际重编报告g++不存在，infrastructure_error |
| baseline-runtime | 移走真实numpy初始化文件 | 先成功原件重编，原件健康探针真实导入h5py/numpy失败（缺__version__），infrastructure_error；未把SDK故障归为候选数值错误 |
| runtime-timeout | 在真实fields_chunk::step_db注入无限循环并写native PID | 编译成功，真实native逐例超时；记录主PID1071，kill后状态Z；仅支持该被测native主进程终止结论 |

valid还实际以UID1000检查/tests、/logs/verifier、/probe不可读，以及submission、固定源与头、构建规则、驱动、七产物、/opt父路径与site-packages等列举路径不可写；真实网络连接denied，cgroup为4CPU/4GiB。报告保留全部路径及结果，不把有限路径权限检查或ldd提升为整容器安全性证明。

compile_source和judge.execute都以独立session运行并在finally kill进程组。本轮真实七探针未单独触发“候选编译超时”或穷尽子孙进程逃逸；不声称已做。实际runtime-timeout仅核验主PID1071及Z状态，不将其写成所有任意进程树已不存在。超大文件没有新增真实容器探针，静态明确size判断仍在冻结前。上述边界不构成本轮固定单TU路径的未决冲突。

## 公开包、物理职责与资源

ZIP显式公开材料检查没有author、generated、hidden cases泄露；两个公开sample属于声明的公开材料。driver构造真实Meep域、PML、source与DFT，adapter只序列化并写回native输出。没有根据解析结果、样例reference或模式符号替代场更新。真实修复文件未进入考生ZIP；许可证及完整原始源码保留。

既有 public-install.json 给出精确最终ZIP的实际普通离线 `pip install .`，随后移动SDK源码目录，从site-packages导入，pip check通过，并真实运行两例原始库：负m样例0、正m样例1，符合原件缺陷。此次复核命令、完整日志、归档SHA和公开包成员；没有再运行两例长FDTD，故此段属于匹配固定材料的既有实际安装证据复核。

最大允许域R3/Z2/rPML2/zPML2/res40的既有原生无trace记录包含真实86400步、200×320名义格、UID1000、cpu.max/memory.max、native stdout和峰内存。独立读取其原始JSON并确认exit0，原生 **1082.973秒<1800秒**、总1085.875秒，memory.peak=31,453,184字节；未拿作者含trace路径或旧841秒路径代替此corner证据。该实测支持当前预算，不宣称对任意机器及负载保证固定耗时。

本次没有重新发布、提交Git或跑付费模型Benchmark。实际数据绑定、正式Oracle、真实探针、独立数学检查和资源记录分别成立；未发现需要修订的配置消费、错误分层或公开承诺冲突。
