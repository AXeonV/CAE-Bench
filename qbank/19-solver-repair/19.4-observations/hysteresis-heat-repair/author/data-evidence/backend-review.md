# 19.4.3 hysteresis-heat-repair 独立后端审阅

日期：2026-10-23。按caeoj-configure-judge技能，只读审查本题公开接口、配置、运行环境、共享执行器及实际Oracle/probe证据；只写本报告，未运行收费模型。本次不代替物理参考、题目设计、考生材料或HF远端审计。

## 结论

当前后端可验收，无阻断P1/P2发现。真实旧PyBaMM在独立Python3.11/NumPy1.26.4 venv中构建和执行，SDK在root Python3.11/NumPy2.4.6中消费协议；实际导入源码/缓存及低权限只读证据覆盖这两个环境边界。driver读取真实thermal子模型现有观测，没有在转换或输出中补数学热源。正式Harbor Oracle实际14/14、reward1、exception=null，最终六项探针全部通过；前两次探针自身错误不被算成候选或正式runtime错误。

## 要求到真实消费者

| 公开要求 | 实际实现与判断 |
|---|---|
| 仅base_thermal.py、普通文件≤1MiB | source-repair.json精确绑定真实thermal/base_thermal.py；共享prepare检查文件集合、普通文件/链接/大小，冻结提交并记录SHA。开发目录与依赖改动不随提交进入独立verifier。 |
| 可信语法构建及实际缓存 | CMake固定调用/opt/solver-venv/bin/python -m py_compile，目标为build/source内真实base_thermal.py；ALL custom target每次执行，未依靠mtime判断是否无事可做。配置明确删除同路径__pycache__/base_thermal.cpython-311.pyc，删除前要求普通文件且非symlink；路径在build_directory内。 |
| 真实旧求解器环境 | 镜像Python3.11，solver venv独立安装editable固定源码，NumPy1.x；root SDK单独装NumPy2.x/h5py/jsonschema/gmsh。运行adapter显式调用venv解释器；CMake、driver和实际导入探针使用同一解释器，不受root NumPy2影响。 |
| 原件故障基础设施、候选错误零分 | baseline删除缓存并真实构建，再执行维护端baseline_probe；probe同时检查root NumPy2/gmsh导出符号及venv真实driver零源状态。构建/probe失败RuntimeError，不被judge候选ValueError分支捕获。候选语法失败SubmissionError→build_error，运行错误/超时按case未通过。 |
| 真实thermal调用 | driver按相数/开关构造真实BatteryModelOptions、LithiumIonParameters与BaseThermal，将给定J/eta/U/Ueq/entropy及零输运场广播到真实域，调用_get_standard_coupled_variables；再由ParameterValues、真实Mesh/Discretisation求值现有Total heating观测。 |
| driver不补热源 | driver只构造题面给定变量、设置几何/面积/并联数/体积参数、读取thermal返回的电极端点/单位面积/全电池/体积平均观测。源码没有计算J(U−Ueq)、补偿遗漏滞回项、裁剪或参考查表。run_case只序列化、调用venv并写结果；不用参数输入或输出后处理代替库内修复。 |
| 全部输出分别评分 | 14个实际grading.json一致，direct_outputs完整绑定5输出到3个quantity：volumetric_heat_power覆盖两极及volume_heat，area_heat_power、heat_power各一项；pointwise/per_time/per_component。atol分别1e-6/1e-8/1e-9，rtol均1e-8，和题面一致。 |
| 资源及总预算 | 候选build60秒、baseline build60秒、baseline probe60秒、14×(执行30+评价30)=840秒，共1020秒最低；judge-config base180+14×65=1090秒，实际staged task.toml采用更大的共享1200秒。Agent1800秒、环境4CPU/8192MB；镜像构建1200秒与候选编译限额分别消费。 |

## 正式Oracle与版本冻结

本轮实际读取 `runs/authoring/repair-22/repair22-hysteresis-oracle-v1.json` 冻结清单，逐文件计算当前staged task全部列出资产的SHA，未发现不一致。当前共享source_repair.py、judge.py及题内source-repair.json与staged副本一致（仅归一化CRLF）。被冻结agent.zip的driver.py、CMakeLists.txt、run_case.py与当前public内容一致，因此没有用较新公开驱动解释旧Oracle。

原始job `runs/harbor/jobs/repair22-hysteresis-oracle-v1/hysteresis-heat-repair__6gfMxS5/` 的result.json明确oracle agent、separate verifier、reward=1.0、exception_info=null；verifier/report.json complete=true、14/14，各例实际accepted。author/data-evidence/oracle.json摘要的14项通过及两个公开样例身份与原始报告相符。

原始build回执显示baseline构建约0.071秒、真实baseline probe1.760秒、候选语法构建0.069秒成功；verifier阶段实际约65.66秒，低于1200秒。本次参考解实际通过不能外推任意候选的最坏资源校准。

允许提交、staged Oracle、当前author/generated及valid实际导入源码SHA一致，均为 `316ba29de5564d39d286b28e4810818a59bd955737f7759fce5ff1c9b51cc53f`。Oracle pyc SHA为 `23901c071baa9b28ffbbf976ea23857abcf41c3126c1466445af4fcc5df524ce`；valid探针另一次构建为 `60914ae2450052550786960747f4b053848e46843bd9e4c842ce8cd1b188df44`，各自与同次构建报告绑定。默认py_compile缓存包含源文件时间信息，因此跨次pyc SHA不同不是源码漂移证据，不要求它们跨运行相同。

prepare_runtime.py校验固定base/fixed归档SHA，并复用成熟verify_tree核验实际解包及context/source全树，防止正确归档配上未核验旧缓存；Oracle只复制真实fixed thermal文件，没有连带采用整棵上游PR。runtime-dependencies.json记录实际SDK NumPy2.4.6、solver NumPy1.26.4及Python3.11.17、镜像ID；最终实际探针同样观察到这两个NumPy版本，而非仅依赖声明。

## 最终六项探针

已读取 `runs/authoring/repair-22/hysteresis-backend-probes-v2/report.json`，和author/data-evidence/backend-probes.json JSON内容完全一致；六项returncode均0、passed=true。复读当前author/backend_probe.py核对实际断言：

- valid给旧pyc设置2100年mtime，真实prepare先删除再编译，旧/新pyc SHA不同；真实judge.execute运行公开样例并经grade_case断言满分，不是只mock退出码。
- 低权限探针使用/opt/solver-venv/bin/python及HOME=/home/solver，实际UID1000、cache_tag=cpython-311；__file__精确为配置target，__cached__精确为rebuild_files。导入后源/pyc SHA与同次可信build报告一致。
- solver实际NumPy1.26.4与root SDK实际NumPy2.4.6均被检查；venv根、pyvenv.cfg、解释器、NumPy初始化文件、editable .pth、driver/CMake及其目录、public adapter、提交与源/pyc均对UID1000不可写。/tests/cases/reference、logs/verifier与/probe不可读写。shared prepare最终冻结整个build子树，覆盖真实源码及缓存。
- syntax→build_error，extra与symlink→invalid_submission；移走真实root Python3.11 NumPy初始化文件，baseline runtime probe失败→infrastructure_error，未记候选错误。
- 候选thermal import加入实际无限循环，并写PID marker；5秒探针预算返回timeout，PID已退出或为僵尸。结合共享执行器killpg逻辑，支持此次真实候选导入超时清理；没有泛称任意恶意后台进程都已覆盖。
- valid记录cpu.max=400000/100000、memory.max=8589934592，对应4CPU/8GiB；docker参数明确network none，单次外部socket失败。它们证明此次具体配置与尝试，不是全容器安全性认证。

## 历史错误与未验证范围

委派方指出此前两个探针错误为：独立探针未使用judge的HOME=/home/solver，以及baseline-runtime测试误指root NumPy3.14目录。当前脚本均已改为真实执行环境，并在最终v2结果实际通过；正式driver/runtime、冻结task配置未因此更改。原始正式Oracle本身成功且与当前冻结资产一致，没有理由为修正探针自身路径而重复收费或正式运行；历史失败日志应保留，不冒称它们是考生或正式求解器故障。

本次是证据复核，没有重跑容器或付费模型；权限为指定路径os.access查询，未逐项实际写入，不证明整个文件系统安全。未实际探测候选语法构建超时、超限文件、所有非法结果/容差等号边界或超时后后续case恢复。无共享框架改动，成熟执行器已有行为不机械重复全套；这些未覆盖项不被包装为通过。本报告不认证完整声明参数域的物理参考精度、HF远端或所有依赖来源，也不以14/14替代独立考试材料与方法约束审查。
