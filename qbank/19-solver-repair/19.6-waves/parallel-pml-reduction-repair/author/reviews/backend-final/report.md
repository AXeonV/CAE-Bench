# SPECFEM661 独立题内后端验收

结论：**通过（后端实际执行关口通过，唯一P1已由文末有界闭包关闭）**。初审DATA的C-PML外终端Neumann声明与原生零势强制边界冲突现已更正，详见 `runs/data-review/repair22-specfem661/report.md`。本轮没有发现其他构建、MPI清理、评分或资源阻断。Oracle执行身份与最终文档包身份分别陈述。

日期2026-10-23。采用caeoj-configure-judge与caeoj-data-review技能，只写审阅目录，未prepare活动任务、未另开Oracle、未停止进程、未重跑native制数、未调用收费模型。独立脚本 [checks.py](checks.py) 与 [actualchecks.json](actualchecks.json) 记录完整v3逐case数组、probe原文/摘要、所有prepared材料SHA、构建和镜像source-tree对照。跨题共享清理审阅可复用 `runs/configure-judge/repair22-mpi-cleanup/report.md`，本轮另外证明本题真实消费身份。

## 最终v3身份与端到端结果

唯一新job `runs/harbor/jobs/repair22-specfem661-oracle-v3/parallel-pml-reduction-repair__eUViWv5`：terminal exception_info=null，verifier complete=true、completed=8/8、score=8、reward=1；2026-10-23T11:03:18Z至11:07:10Z完成验证。独立读取全部8个返回HDF5每个值和支持数组，与当前隐藏reference逐位相等，并核对逐case status=accepted、score1。本次不是引用旧v2成绩。

启动manifest里的每个task_sha256均与实际prepared文件独立核对，包含全部case/reference、source repair、selection、Dockerfile、脚本及ZIP。公开ZIP SHA256 `9cd9a7479aaa7973194bfd5099e97fbc60f40c8133cddcce8b2e7552f54c3f39`；实际prepared judge SHA256 `5595500ff6c8612f4682f4eda0cdc6521c5af94343dcba6c825bb3555141180f`，与共享审阅批准的LF副本完全相同（Windows源为5141c3a50bbae52169ea3dd1b2466fb5363cb3ebd33116df6f73b6d14deef16d）。source_repair.py SHA `714e3f76ededa181e44861f6ad5257ba8a39be83e9a4588f258a516efa212e75`；source-repair.json SHA `b2457c8edc70aaa9e2a8fd477f79d574f0b784da41f4dc937a032f4621849152`。

旧53ab包Oracle v2的8/8及旧probe前六过、第七rank残留失败均保留原身份；它们不冒充此v3结果。当前v3通过不抹去旧失败。

## 要求到实际消费者

| 公开要求 | 实际配置/消费者与证据 |
| --- | --- |
| 恰一个<=1MiB普通get_MPI.F90 | source_repair.prepare精确文件集合、拒symlink及超限；extra/symlink真实容器probe分类invalid_submission；多目录与大小界由代码同一入口检查，本轮未额外构造FIFO等非普通文件 |
| 原件先编译与健康检查 | 基线删除obj/get_MPI.spec.o、bin/xspecfem2D，真实cmake→make；baseline-report built，baseline-probe ready；禁gfortran/禁mesher探针分别infrastructure_error，不归考生0 |
| 完整替换固定源码并真实重编 | 同两artifact再次删除，源码SHA f8cdb8214e270674ddc8af880812f0f1c86a04c5c740e0ea8eb013a38f59da6e；候选built1.366秒；valid probe先把旧产物mtime置未来仍真实重编；syntax分类build_error |
| 无缓存预处理旁路 | CMake无生成/预处理副本，直接make bin/xspecfem2D；上游rules.mk `.F90`规则直接以源路径输入Fortran编译器。runtime全部916个archive src文件hash一致，production仅get_MPI不同；生产obj/exe与v3重新构建后hash一致 |
| 两个真实artifact | get_MPI.spec.o SHA `9c957fae9efcd97903a596f9f21b784d2898e60fe41471bcdab3cd0f48f40f43`；xspecfem2D SHA `c0555ce10d47baa74c4152f76296f7801ab82aec9b877588722ec31f58dba7da`；production、validprobe与v3一致；ldd含libmpi_mpifh与libmpi |
| 保持MPI及输入方法 | runner对mesher/solver均mpirun -np公开P；只序列化mesh/source/pml和读取ASCII，没有波场补算；真正分区接口头来自原生数据库，含[0,1,1]、[1,1,0]、[1,2,1,0]及正常连通/串行 |
| 点点容差/全输出 | 每例reference/grading.json direct_outputs→pointwise/per_time/per_component，SH atol2e-9 rtol2e-6、声学atol5e-6 rtol2e-6，quantity/unit准确绑定；全部Nt×Nr×1参加检查，无reference_offset，无额外平移 |
| 通过例数比例 | 8逐case accepted，reward8/8；public_cases2仍纳入总分母8。共享引擎评分/部分完成契约复用原测试；本轮两branch各阈值等号与上下侧以及NaN/轴/缺失/extra/dtype有区分力检查见数据报告 |
| 210秒求解/30秒评分/1MiB | judge-config实际prepared为210/30/1048576；runner无固定90秒截断（只author原件复现显式90）；独立真实3秒Fortran probe走相同execute超时路径；max输出资源角结果462912B |
| 编译120+120/健康预算 | source-repair.json原件120、候选120；健康min(60,120)=60；build_timeout错误分支为考生build_timeout，原件失败抛基础设施；7probe实测区分build_error与infrastructure_error，未实际耗尽120秒构建预算 |
| 总外层预算 | task.toml verifier2310s = base350+8×(210+30+5)；base容纳120+120+60及bootstrap/I/O，agent1800s、镜像构建1200s分开；实测v3 verifier232秒内完成，非最坏硬实时证明 |
| 隔离 | setpriv uid/gid1000 clear-groups no-new-privs；构建后库/可执行/固定工具root只读；/tests、logs、probe不可读；network拒绝；cgroup cpu400000/100000、memory4294967296。valid真实probe逐路径os.access确认 |
| MPI超时所有后代回收 | 实际循环Fortran三rank147/148/149及launcher144全部/proc消失，含zombie检查，同UID无关sentinel活；当前独立subreaper helper实现与共享审阅SHA一致，非容器退出后清场 |

七个v3 probe各在独立容器执行，全部passed：valid、syntax、extra、symlink、compiler、baseline-runtime、runtime-timeout。独立读取 `work/repair-22/specfem-661/probe-evidence-v3/*stdout.json` 与脚本断言，不只看聚合passed。运行器运行失败/超时分类共享代码及独立共享审阅已覆盖；本题真实timeout执行补证。无法安全构造内核D态清理失败，继承共享审阅受控mock的边界，不宣称做了真实不可杀实验。

## 最大声明工作量与公开包

独立全读两份resource-corner/resource-sh真实problem/mesh/HDF5/输出，不只看作者scope字符串：6000单元、6400采样、P4、Ns2、Nr8，float64全有限，实际最大输出462912B。作者保留docker调用为UID1000、network none、4CPU/4GiB；实测声学PML55.293秒、SH102.692秒；cgroup均4CPU/4GiB，SH峰102502400B。不是形式上的JSON数值，也不是对任意机器210秒的性能保证。本轮未重新运行这两项native角例。

ZIP独立枚举44成员，无author/cases/private tests、无非samples reference。既有最终9cd普通离线安装记录逐步检查了pip install、移走src、site-packages导入、题目录下两样例真实CLI运行/grade1与pip check；本轮只读复核该命令及文件身份，没有重复高成本安装执行。SDK、扩展、数据、grader均在ZIP闭包；隐藏材料由separate verifier独立注入。公开包安装和结构正确不能消除PML物理定义冲突。

## 未决与闭包要求

1. P1边界定义修订前不可宣告整题通过。DATA应明确固定库PML上下外终端chi强制为零，不能照抄源码陈旧Neumann注释。连续Green/open-z核查不识别这个细小有限层残余的外端边界。
2. 修文档会改变ZIP；此报告完整Oracle只认证9cd/v3/559550身份。可有界复用数据、native/reference、source/artifacts及数值结果，但必须逐成员差异证明后明确新身份，不能改写或重命名旧Oracle。是否重跑新Oracle由根协调者依最终任务验收要求决定。
3. 本题后端大改的独立subagent审阅需求由已完成共享清理独立审阅覆盖；本轮题内审阅未再派子agent。未执行模型benchmark，未声称正式发布已完成。

## 22aa文档修订的有界闭包

上列第1项已关闭。独立新检查 `runs/data-review/repair22-specfem661/bounded_closure.py` 确认最终包SHA256 `22aa0bcf168c9cabd7853ec8a63e2498838968fb53aa996034cb3e48108144d7`，相对原v3消费的9cd包44成员集合不变、仅DATA+MANIFEST改变；MANIFEST仅DATA哈希变化且全部条目重新校验。新DATA准确写PML上下外终端齐次Dirichlet及保存势/导数置零，无PML/左右Neumann定义保留；与实际原生源和固定production构建一致。工作区64项相关runtime/config/input/reference/sample资产SHA不变。

由此可有界复用既有native/source/artifact/参考/数值/资源证据，不需要再生产8参考。v3唯一正式执行8/8仍标记**旧9cd文档包、559550后端**；没有伪造22aa新Oracle。本轮通过是最终22aa文档与已独立验证同一运行闭包的有界一致性验收，不是新执行记录。候选与设计针对更正的独立文本复核由根另行完成；不在此宣告整个多题项目或正式发布完成。
