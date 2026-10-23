# LAMMPS granular-pair-stress-repair 独立后端审阅

日期：2026-10-23。按caeoj-configure-judge技能，只读检查配置、真实构建/调用及证据，未修改实现或运行收费模型；只写本报告。物理参考与完整数据审计、方法审查、HF及考试材料另有专责，本次不替代。

## 结论

当前最终后端可验收，无阻断P1/P2发现。允许cpp+h实际进入3个依赖翻译单元及新LAMMPS库；真实lmp完整执行run 0并以退出状态决定是否接收输出。最终独立Harbor Oracle 12/12、reward1、exception=null，冻结资产及六项最终探针匹配当前版本。早期timeout探针立即/proc断言失败的原因未记录，不能从最终重放通过倒推其确切原因。

## 公开要求到真实消费者

| 要求 | 绑定与判断 |
|---|---|
| 仅cpp+h | source-repair.json精确接受pair_gran_hooke_history_kokkos.cpp/.h，target为真实src/KOKKOS；共享prepare检查普通文件、链接、额外文件、每文件≤1048576字节并冻结/SHA绑定。 |
| 原始完整构建 | runtime使用公开归档内src、原生cmake及bundled Kokkos配置真实LAMMPS，BUILD_MPI=OFF、SHARED=ON、GRANULAR/KOKKOS=ON、Serial=ON、OpenMP=OFF、C++17，不用私有逐题替代pair实现。 |
| header依赖闭包 | pristine-baseline记录真实*.o.d中包含该header的3个TU为pair cpp、force.cpp、lammps.cpp；全部对象加入rebuild_files。main.cpp.o另强制重编，真实liblammps.so.0与lmp另删重链接。避免只重编pair却保留header消费者旧代码。 |
| 删除真实产物 | 六项rebuild_files全部位于/opt/lammps-build；共享配置校验拒绝越界，运行删除前要求普通文件非symlink。声明真实.so.0而非.so链接；实际baseline/candidate执行并报告全部六项删除重建成功。 |
| 固定实际运行模式 | adapter显式使用-k on、-sf kk、-pk kokkos neigh half newton off；输入脚本也newton off。非周期sphere、无积分fix、run 0、零新建历史，与公开固定范围一致；不外推GPU/MPI/OpenMP或newton on。 |
| 完整solver退出 | subprocess.run同步等待完整lmp结束，非零退出先转发stdout/stderr并抛异常，随后才读dump/global及write_result。没有忽略cleanup异常、只因dump存在就接受部分输出或截取成功段。 |
| 输出转换 | 力/力矩直接读dump，按实际粒子ID重排；particle_virial仅对compute stress/atom做DATA明确规定的负号转换，不除粒子体积；压力直接读compute pressure NULL pair。未按解析公式重算力/应力或补倍数修正。 |
| 模式与评分 | global输出force/torque/pressure，particle输出force/torque/virial，both包含全部；write_result与独立grade检查实际outputs契约。12个grading配置的direct_outputs规则匹配：力/力矩/virial atol1e-7、压力1e-9，rtol均1e-8，逐点逐分量；模板多quantity策略不意味着未声明输出被虚构成必需量。 |
| 基线/候选分类 | baseline先强制构建，再以UID1000通过公开adapter实际运行公开样例，仅检查能执行/协议写回，不要求缺陷原件数值满分。原件构建/probe失败RuntimeError基础设施；候选语法失败build_error，额外文件invalid_submission；运行超时按case未通过。 |
| 资源/总预算 | 候选300秒、baseline构建60秒、baseline probe60秒、12×(执行60+评价20)=960秒，最低1380秒；实际judge-config自动预算700+12×85=1720秒，staged task.toml正为1720。环境4CPU/8192MB、Agent2400、镜像构建1500秒分开消费。 |

## 原始源码、实际构建与加载

已读prepare_runtime.py与pristine-baseline.json。公开archive SHA绑定source.json，source-manifest列5380个原始文件，实际镜像逐文件SHA核对通过；未将只检查两个允许文件称为完整基线校验。真实编译器依赖扫描给出3个header消费者，和配置删除项一致。此检查覆盖归档列出的原始文件与实际构建依赖，不是全部镜像资产或所有可能未来include改动的通用证明。

原始最终baseline stdout明确编译force.cpp、lammps.cpp、pair_gran_hooke_history_kokkos.cpp、main.cpp并链接liblammps.so/lmp；baseline构建38.05秒、真实公开adapter预检1.10秒、候选构建38.96秒，均低于实际60/60/300秒预算。库和可执行文件不是仅检查存在或缓存无事可做。

valid的ldd实际解析 `/opt/lammps-build/liblammps.so.0`；其源/六产物SHA与可信构建报告逐项相同，全部产物SHA也与最终Oracle相同。两个当前generated源码SHA分别为cpp `f840bc1e580497b3b253c918d304ece05217c912e6e02f33db4f6e1fedf77232`、h `e0e9a59df31ad445c3e761484ff5f5c9ee3bac6769a8d59da0499e4c37fe9680`，和Oracle/valid一致；新库SHA为 `bd3d3e7afbe3672fc41236dec63caae0730f7ab5cf4aea8cb25884a8182ba232`，lmp为 `864f0a1cb32c4be50489378acb496a882df28afb9229b71a8809b9c3d5bd2f46`。

author保留的fixed stdout明确KOKKOS启用、half/newton off/size/history、half/bin/newtoff/size/kk/device，和构建Serial参数及真实调用路径一致。日志中的“无时间积分fix”警告符合run 0目标，不当作错误吞掉；也不从通用“1 OpenMP thread”文本推断启用了OpenMP执行后端，后端选项由真实构建配置与运行命令限定。

## 最终冻结与正式Oracle

重新计算 `runs/authoring/repair-22/repair22-lammps4219-oracle-final.json` 65项staged文件SHA，全部一致。最终agent.zip SHA为 `c62ed786a6a952584d2e6d403ced5683034481008b278e7a3c6a8b0ed98beef6`；当前instruction、DATA、run_case.py与冻结ZIP内容相同；共享source_repair.py、judge.py及本题配置和staged副本一致（仅归一化CRLF）。未用较新adapter解释旧结果。

正式job `runs/harbor/jobs/repair22-lammps4219-oracle-final/granular-pair-stress-repair__pz5GVQ5/` 原始result明确oracle、separate verifier、reward1、exception=null；verifier报告complete、12/12，归档oracle.json全部cases与原始逐项完全一致。verifier实际约156.65秒，低于1720秒；成功参考解时间不外推任意候选最坏资源校准。

## 六项探针、权限与失败历史

各 `work/repair-22/lammps-4219/probe-{valid,syntax,extra,baseline-compiler,baseline-runtime,runtime-timeout}.json` 原始结果与backend-probes.json逐项一致，当前author/backend_probe.py已复读。

- valid将六项产物mtime设到2100年，再真实prepare、judge.execute及grade_case样例满分；不是mock编译退出码。实际源/产物hash与真实加载链共同支持候选绑定。
- syntax→build_error，extra→invalid_submission；移走g++导致真实baseline构建失败→基础设施；将维护端baseline实际solver入口设为missing导致probe_error→基础设施，未记候选零分。
- runtime-timeout在真实候选pair的compute入口插入PID marker与C++无限循环，实际lmp进入该实现后3秒超时，judge返回timeout。最终脚本最多20次、间隔0.1秒有界观察PID状态，实际termination_states为["Z"]，支持此次底层执行已终止为僵尸；共享judge的killpg未改变。
- v1 raw stderr只证明timeout分类之后的立即/proc“已消失或Z”断言失败，未记录当时具体状态。不能将其解释成已证实的race、仍活着的泄漏、清理失效或任何确切原因；最终重放通过也不覆盖或删除这条历史。
- valid为UID1000，source/src/KOKKOS、非替换pair.h、原生CMake、两候选源、全部对象/库/执行文件均不可写，隐藏/tests、logs/verifier、/probe不可读写。runtime将整棵source/build设root/go-w，prepare仅在构建时交build给UID1000再冻结；源与header不在可写build树，root verifier可以完成替换。
- valid实际cpu.max=400000/100000、memory.max=8589934592，支持该次4CPU/8GiB资源；一次外部socket失败。权限是os.access查询，网络是有限尝试，不宣称完整容器安全性。

## 未验证范围

本次没有重跑容器/Oracle或收费Benchmark。未注入候选编译超时、symlink/超限文件、任意恶意进程脱离组、超时后后续case恢复或全部数值阈值/非法输出边界；不把共享成熟实现能力等同于本题全部场景已实测。原始源码逐SHA、ldd与成功样例并不单独认证所有动态加载或所有声明参数域物理精度。完整数据审计尚由对应审阅收束，后端通过不替代它；考生/方法/HF审阅不在本报告认证范围。未发现这些有限边界引出的实际阻断故障。
