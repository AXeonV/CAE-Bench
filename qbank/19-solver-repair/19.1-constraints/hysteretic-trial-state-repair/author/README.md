# 作者维护记录：双材料试探状态恢复

来源为 [OpenSees issue 1817](https://github.com/OpenSees/OpenSees/issues/1817) 与 [PR1818](https://github.com/OpenSees/OpenSees/pull/1818)。完整固定版本、归档摘要和逐文件基线/修复SHA见 data-evidence/source.json。本题完整采用该PR的两个cpp改动，不含作者逻辑补足；机械替换逐字等于固定head的真实下载原件。原始桥梁Tcl保存在 data-evidence/original-issue-bridge.tcl。本题直接改编其材料状态根因，没有运行或认证完整桥梁、重力或特征值分析。

公开能力以 instruction.md、DATA.md、CONTRACT 为准。仅允许替换两个真实材料cpp，损伤/包络退化关闭；单向已提交历史与任意方向未提交试探分开。源码包保留COPYRIGHT和各文件原声明。真实闭包49文件约450KB、压缩79.5KB，19个上游cpp；function/data sections仅剔除未调用的解释器factory。driver提供上游嵌入程序所需的StandardStream日志全局，未定义替代材料、假OPS函数或stub。真实两材料的全部虚表依赖均链接；source-closure-audit.json核实Ninja实际48个源码/头文件恰等公共闭包（另保留COPYRIGHT），镜像全部源码字节与公开包一致。

## 参考与数据

10个正式文件、每文件4个相互独立材料程序，共40条；两个文件显式同时作为公开样例。作者新增/改编身份与逐条参数见 cases.json。包括Hysteretic 2/3点、SM 2..7点和不同两侧点数、非对称正负骨架、零/非零已提交态、屈后多段与弹性态、多次跨零试探、float64阈值和正常非触发回归。actual-coverage.json逐程序记录实际差而非只看输入delta，以及全部计分非零应变与折点的间隔。

参考生产者为真实上游修复材料。independent.py独立按输入分段骨架计算应力/斜率、按API梯形步进计算已提交功密度，并核对near-return快照、显式rollback和reset恒等；它不复制试探卸载/捏拢算法，也不把跨折点连续积分冒作API离散功。未提交probe响应不计分。10个正式文件全部输出均通过该独立核对，见 reference-replay.json；缺陷基线2/10通过，8类文件检出状态污染，另两个正常非触发文件通过，见 defect-replay.json。两份replay记录顶层hash_semantics明确driver_input_sha256为序列化input.txt payload摘要，不是原始HDF5；result_sha256为对应模式输出的reference.h5/result.h5摘要，不是raw output.txt。40条正式程序之外的4条原型与96条参数边界原型保留单独报告，不能替代正式数据验收。另有exact-threshold-regression.json记录两材料正负方向共4条实际float64差恰等EPS的正常非触发控制：真实修复材料全部输出符合独立参考；它们是作者额外边界核查，不冒称正式池条目。

## 已执行消费链

公开ZIP在断网基线容器中独立安装，离开解包目录后调用公开run_case.py并写HDF5，两公开样例均正确观察到缺陷，见 public-install.json。安装实际公开SDK后，10输入与参考消费/评分、20非法声明拒绝均通过，见 data-audit.json。

固定verifier六模式均以Docker参数--cpus 2、--memory 2g运行；valid实际cgroup采样cpu.max=200000 100000、memory.max=2147483648，对应2CPU/2GiB。其他错误模式仅记录启动参数，没有逐一采样cgroup。它们与正式Harbor任务的4CPU/4GiB配置分开，见probe-resources.json。固定verifier实际六模式见 backend-probes.json，逐模式镜像ID见 probe-images.json，原始JSON/stdout/stderr在 runs/authoring/repair-22/opensees-probe-*。valid设置未来mtime后仍删除对象和可执行文件并重新编译、改写可执行SHA，两材料真实符号仍存在，实际公开样例通过；syntax属于candidate build_error，缺编译器与可信probe输入属于基础设施错误，额外文件和符号链接属于invalid_submission。初版baseline-runtime探针删除了本来列为rebuild artifact的可执行文件，先正确报基础设施缺件；最终探针改缺probe输入以检验运行阶段，初次诊断日志单独保留，未把探针断言不符算作考生错误。runtime-permissions.json以固定镜像及完整命令记录UID/GID1000、groups=[]，61个源码、父目录、驱动、CMake、编译器与可执行目标均不可写。valid probe另核对prepare后的冻结权限和隐藏路径不可读；有限路径/单网络连接检查不外推全容器审计。

正式Harbor仅运行Oracle，没有付费模型。v1为最初ZIP，10/10、无exception；独立候选发现公开示例将HDF5输出误写result.json，已修result.h5并重发ZIP。v2绑定.h5命令修订版，10/10、无exception；随后仅修公开CONTRACT链接和补明既有4CPU/4GiB资源。最终候选有界复核已通过，v3完整生命周期已完成：单次Oracle、10/10、reward=1、无exception，绑定最终ZIP ac438c25f7416d325897acb6b763642fc27e518af2e205035d30e53bd9bc16c9 和既有4CPU/4GiB配置。正式v3未额外采集容器inspect/cgroup快照；4CPU/4GiB依据冻结task.toml和该正式任务生命周期，不将2CPU/2GiB探针采样当作正式容器采样。主证据harbor-oracle.json/harbor-oracle-report.json/harbor-job-result.json及harbor-构建报告均来自v3；v1/v2状态另存，原jobs不覆盖。作者侧真实重放、六模式固定verifier与正式Harbor生命周期证据分别保留。

HF官方upload提交为05a921e30ad641028ec7f07b1cfb403f5995d8c0，51文件；重复官方检查uploaded_files=0。固定commit新缓存独立装配完整且strict verify通过，回执为hf-fixed-assembly.json和hf-strict-verification.json；本地离线装配/strict亦通过。独立设计通过见design-review-excerpt.md；独立考生statements与全部公开exam最终通过，原文candidate-review.md。独立全数据审阅通过，原文data-review.md。独立最终后端审阅通过，原文backend-review.md；设计、最终考生/全部公开exam、全数据与后端独立审阅均已闭合。上述独立审阅各自保留实际范围，不以作者自检替代。

## 重建入口

依次运行 author/prepare_source.py（需要时用--proxy）、pack_source.py、generate.py。build_runtime.py以--work指定空目录、--offline-wheels指定setuptools/wheel离线wheel目录，复用记录的GCC14.2/SDK依赖基础镜像；依赖COPY及go-w规范化在runtime.Dockerfile中。build_reference.py以--work指定空目录，reference镜像仅在基线运行镜像内替换author/generated两cpp并真实重编译，不能把修复源码放进基线公开包。运行replay.py --mode reference/defect --image相应固定镜像，随后按项目数据池流程pack/upload/fixed assemble/strict verify，再publish_dist和prepare_harbor。

独立公开SDK安装后运行audit_data.py；audit_source.py核对固定基线镜像闭包；verify_public.py运行断网安装及公开.h5命令。正式Oracle入口使用 runs/authoring/repair-22/run_oracle.py，任务名hysteretic-trial-state-repair，必须用新job名且运行中保持prepared task冻结。author/generated、public源码tar、数据池装配、SDK缓存和执行日志属于忽略产物；维护源码、固定选择和作者证据入库，不提交本地H5。

公开限制补明：现行公开包已明确此前后端一直执行的每文件1 MiB上限；当前/原包摘要及逐项差分见[source-size-clarification.json](data-evidence/source-size-clarification.json)。独立[有界变更复核](../../../../design/reviews/repair-source-size-clarifications.md)通过，源码、SDK、输入、参考、评分和驱动载荷均未变。上述Oracle、安装和考生/数据审阅记录保留各自历史冻结包身份；本轮未把它们改称运行新包，也未无故重复相同数值计算。当前公开版本由新包摘要与该有界复核单独绑定。
