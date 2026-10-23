# Kratos 19.2.1 独立后端配置与真实消费审阅

日期：2026-10-23。按caeoj-configure-judge技能审阅 `spatial-beam-transform-repair`。只读实现与证据，仅写本报告，未运行收费Benchmark。物理参考、HF远端、考试材料与全部容差边界的独立审计不在本次职责；不重复这些专责审阅。

## 结论

当前本题源码修复后端可验收。允许的真实.cpp进入新对象与新梁共享库，固定driver实际加载该库及真实KratosCore并运行三API；原件/候选构建、原件运行预检、候选失败分类与全部10例判分均有实际证据。未发现需阻断验收的P1/P2实现问题。源码、非替换头文件、父目录、可信driver/CMake及Core库的权限疑问已由当前镜像的补充查询消除，不能由其他题的Windows权限故障推定本题也有该缺陷。

## 公开要求到实际消费者

| 要求 | 绑定与判断 |
|---|---|
| 只提交一个.cpp、≤1MiB | source-repair.json仅接受timoshenko_beam_element_3D2N.cpp，target指向真实StructuralMechanicsApplication源码。共享prepare比较精确文件集合、拒绝链接/超限，冻结提交并记录SHA。 |
| 真实Core与7源文件梁组件 | runtime.Dockerfile从公开闭包配置并实际构建KratosCore；public CMake将3D/2D梁、2个constitutive law、2个utilities及application variables共7个真实.cpp链接为beam_repair，链接真实libKratosCore.so。候选只能替换3D.cpp，故增量仅需强制重编其对象并重新链接梁库；不存在上一题改头文件却保留旧依赖对象的问题。 |
| 强制重建且不复用未来缓存 | rebuild_files为build目录内的真实3D.cpp.o与libbeam_repair.so；运行删除前要求普通文件且非symlink。baseline和candidate均先删除再编译，显式产物缺失/链接被视为基础设施异常。实际futuremtime探针通过。 |
| 固定driver与真实API | driver.cpp构造真实LinearTimoshenkoBeamElement3D2N、真实3D constitutive law与节点/材料/局部轴，零位移转角初始化，依次调用CalculateLocalSystem、CalculateLeftHandSide、CalculateRightHandSide；输出完整12×12矩阵及12分量外力。 |
| 中性adapter与响应输出 | run_case.py只序列化输入、解析四组真实API输出、按公开S做共轭单位缩放，再由combined后6×6块求解自由端响应；没有另算刚度/力或查参考修正。该线性求解与归一化是DATA明确规定的可信adapter职责。 |
| 库实际加载 | driver的BUILD_RPATH含/opt/kratos-build/kratos与/opt/beam-build；beam库链接Core绝对路径，共享执行器LD_LIBRARY_PATH来自build/lib。本题该LD目录不是实际梁库目录，但现有RPATH完成解析；实际ldd与真实样例判分确认加载/opt/beam-build/libbeam_repair.so及/opt/kratos-build/kratos/libKratosCore.so，不靠环境路径猜测。 |
| 输出与评分绑定 | 10个实际reference/grading.json一致，direct_outputs覆盖normalized_stiffness、normalized_generalized_force、normalized_displacement，分别绑定2矩阵、2外力及响应；pointwise/per_time/per_component。atol分别1e-4、1e-8、1e-11，rtol分别1e-9、1e-9、1e-8，与题面一致。对象名与quantity不同也正确绑定。 |
| 失败与分母 | judge预载每case实际grading，缺/坏输入参考配置为基础设施；候选语法/结构失败零分，运行/输出失败按case失败，最终passed/total等权；public_cases单列两个样例身份。非有限结果由SDK/独立grade契约检查拒绝。方法约束由另行源码审查承担，数值通过不证明无硬编码。 |
| 编译/运行预算 | 候选180秒、可信baseline构建min(60,180)=60秒、baseline_probe另60秒，逐例15秒、独立评价30秒。10例最小750秒；judge-config计算400+10×(15+30+5)=900秒，staged task.toml实际保留共享更大的1200秒，覆盖上述上界及开销。Agent1800、环境4CPU/8192MB、镜像构建1200秒；镜像构建限额不同于候选180秒。 |

## 实际版本、哈希与运行证据

读取了 `runs/authoring/repair-22/kratos-oracle/report.json` 及其build下baseline-report、baseline-probe-report、report三回执。原始总报告SHA为 `7a50346f4f4880a450fbe8f614d2b5aec7afc81f846b9ce0f08eddcc587b6b7f`，与author/data-evidence/oracle.json记录的full_run_report_sha256精确一致；原始报告complete=true、score=10、total_cases=10，各case accepted，包括两个公开样例身份。

实际可信baseline构建19.25秒、原件真实driver预检0.035秒、候选重建10.55秒，均成功且在各自预算内。baseline_probe实际为UID1000通过setpriv调用beam_driver读取固定probe-input，非空转py_compile或只检查文件存在。该预检不比较缺陷基线数值，不会把应考缺陷错当成基础设施。

当前允许源码与Oracle/probe记录的SHA均为 `2cac9687926d55d52d6331dc33060a49b2e3f3afdffe84ed304813ed95f0b2ee`；Oracle与valid的真实对象SHA均为 `ab46133f2c311848f30d8938c0246da799eaffad086e5eb4e38f2a8a862890d2`，梁库SHA均为 `d6143ffabcaa829cab908ed1d9b1c5d606bd00b5347b006e3054d204fbe83f42`。valid确认旧库SHA与新库不同，低权限真实运行公开样例02并经相同grade_case得1分。

runtime-images.json记录driver可执行SHA `3356fde3933564e6cd45a0beaaea67b1c7a6cc696efd9a2a9d096ecc457b8d78`、Core库SHA `6594a3098dd591cb5766c837084470192f9d5bf3719ee83df4d9ceeb0173bed2`，在baseline/upstream/author_supplemented三镜像一致；driver源码SHA `a4b8febebc3f4c55dbad9a75618ed6d8e3c751cc8ef5c9edcd60b8c4afc90e44`与当前public/driver.cpp实际SHA一致。因此候选变化绑定梁实现，而非改driver或Core。driver未列入每次强制重建，这是.cpp替换题的固定可信产物设计，不是header ABI问题。

当前共享source_repair.py、judge.py及本题source-repair.json与staged Harbor tests副本逐字一致（只归一化CRLF）。现有原始Oracle材料是固定verifier中的真实共享judge消费证据；不额外声称存在本次未提供的Harbor job result或调度生命周期证明。

source-closure.json记录915个真实Ninja依赖、公开包2337个文件，missing/different_bytes均为空，runtime_image_id与runtime-images基线ID一致。已读audit_source_closure.py：从Core/beam两构建的ninja deps收集实际源码路径，并对归档常规文件逐字节比较；这支持公开闭包与实际构建源码一致，未把2337文件存在本身当成编译依赖验证。本次不另作上游来源独立性认证或物理审查。

## 六种探针与权限补证

六个 `runs/authoring/repair-22/kratos-probe-{valid,syntax,compiler,baseline-runtime,extra,symlink}.json` 原始结果与backend-probes.json各项逐项一致，已复读author/backend_probe.py核对断言：

- valid先将对象/库mtime设置2100年，再真实prepare和加载新库、真实样例判分；不是仅mock构建退出码。
- syntax → build_error，extra/symlink → invalid_submission。
- 移走clang++，即使旧产物完整，baseline真实强制构建仍失败 → infrastructure_error；移走实际baseline driver入口 → baseline runtime probe失败 → infrastructure_error。这两类不记候选零分。
- UID1000不可读/tests/cases、/tests/reference、logs/verifier，不能写允许源码、梁库或driver；记录cgroup cpu.max=400000/100000、memory.max=8589934592，匹配4CPU/8GiB；一次外部socket失败。

初读runtime.Dockerfile未见统一go-w且原探针未覆盖非替换材料，因此向实现Agent索取当前镜像证据，没有直接认定缺陷。补充 `runs/authoring/repair-22/kratos-runtime-permissions.json` 表明源码根、beam父目录、非替换3D.h/2D.cpp、beam-driver目录及driver.cpp/CMake/run_case.py、Core和zlib目录/库均不可写。实现Agent说明查询由当前固定verifier的UID/GID1000、clear-groups执行；原始头/目录为664/775但组root，不赋予UID1000写权，故不需要以放宽构建权限修复并不存在的故障。

补充JSON已重新实际查询并完善：记录固定verifier镜像ID `sha256:eb655262bed114158d9c474ccb9d723574d958a76db291a8d4e19eec106d1dd1`，与runtime-images.json的verifier_image_id相同；实际UID/GID均1000、groups为空，完整docker/setpriv参数及“fresh verifier before source backend prepare”阶段自包含。原始JSON与author/data-evidence/runtime-permissions.json逐字一致。它证明prepare前非构建子树的只读前提，valid则证明prepare后允许源码/库/driver被冻结；这两个阶段没有混用。不再保留证据metadata完善待办。

## 有限边界

权限结果是os.access查询，未逐文件发起写入系统调用；网络仅单目标尝试，ldd与一次样例不证明任意动态加载情境或全容器安全。探针未实际覆盖候选编译超时、候选运行超时/后续case恢复、超限文件及非法数值的所有边界；公共后端本轮未改，不机械重复其所有旧通路测试。真实Oracle与样例判分支持当前配置消费链，不替代允许参数域的全部物理正确性证明、方法约束审查或独立公共包安装证明。最终考试材料/HF可按对应专责记录验收，本报告不越权认证。
