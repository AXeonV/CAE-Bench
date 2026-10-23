# SPECFEM2D #661 / PR660：维护入口

本题保留原来源、编号和slug；真实能力为并行接口归约参与，声学PML是受支持的回归分支。不是PML公式修复，也没有声称复现原BENCHIE流固混合爆炸。范围与来源关系见[scope](scope.md)；公开要求只由instruction、DATA和CONTRACT拥有。

固定基线fa6e905bc5cd63487cc24f68233f5992830f8b6e，PR660修复4f4cd5f6acb0a77dcab4df113bd5f8838c4ec5c8。本题只采用get_MPI.F90（真实Git blob d843513239390f2bdc18046514b6d4efb2f36235）；同PR接收器调试/声明改动不纳入。完整原始归档1760个普通文件，生产镜像逐文件核对只该目标与原始归档不同。[source.json](data-evidence/source.json)与[baseline-tree.json](data-evidence/baseline-tree.json)记录归档及源码哈希。保留GPL及上游完整源码，不以替代内核、stub或作者MPI toy冒充原求解器。

完整原始求解器已用GNU Fortran14 / OpenMPI5.0.7 / Scotch实际构建并执行；double内部计算，O2及现代Fortran参数兼容选项。默认浮点trap在MPI初始化内部触发异常，故通过正常构建选项关闭该trap，未改目标之外的源文件。公开CMake目标调用上游make，强制删除get_MPI.spec.o和xspecfem2D后重新编译；无预处理副本缓存。

## 数据与物理依据

8份参考由真实修复库生产；原件同批实际完成4例，两个隔离master例在后续接收器归约失败，两个隔离末端例真实90秒超时。实际mesher数据库的接口数逐例为[1,2,1]、[0,1,1]、[1,1,0]、[0,1,1]、[1,2,1,0]、[1,2,1]、[0]、[0]，见[input-audit](data-evidence/input-audit.json)。不是依据网格名称猜测触发条件。

[independent.py](independent.py)按独立二维Green/Duhamel核积分核对有限起点的零初态问题，并用Neumann图像源核对反射；数学出处为MIT Waves and Imaging第1章与Toronto method of descent。128/256点积分差异核查与全部8例完整时程核查通过，最大全时程L2差0.8301%。有限PML不冒充理想开域；其晚时残差相对未吸收z返回波L2为0.00045至0.00631，明确包含有限层和离散误差。完整结果见[independent-report](data-evidence/independent-report.json)。参考标答仍是固定真实离散响应，连续核查不代替该响应或放宽计分阈值。

最终模型类别使用physics.model，避免数字伪装类别。由早期数值分支元数据改为模型字符串后，已逐例证明全部原生DATA字节一致并保留原8参考，没有重新求解或重拟合；完整输入资产与参考哈希见[final-input-binding](data-evidence/final-input-binding.json)。15个独立DATA导出的合法/非法变体见[contract-probes](data-evidence/contract-probes.json)。

HF固定提交917ce12944449597f47ca95c1433edbe07134baf，49上传文件；全新cache按该提交装配52项complete，strict有效。2个公开样例与计分case同身份，公开分母2、隐藏分母6，总分母8；具体绑定由data-manifest与真实[装配回执副本](data-evidence/hf-assembly-receipt.json)拥有。

最大声明工作量已分别真实运行：6000单元、6400步、4进程、2源、8接收器，UID1000、network none、4CPU/4GiB。声学PML55.293秒；SH102.692秒，SH cgroup峰102,502,400B。见[声学资源](data-evidence/resource-corner.json)与[SH资源](data-evidence/resource-sh.json)。公开case预算210秒；去除适配器旧90秒提前截断，由实际外层统一执行预算。原件/候选编译各120秒，框架健康预算60秒，8例总verifier预算2310秒。

## 执行与当前阶段

`generate.py`只生成输入；`native_produce.py`运行真实mesher/solver并保存原始日志；`finalize_data.py`只绑定已存在的真实参考和判题配置。`prepare_runtime.py`复用已完成的固定MPI构建，安装现有通用runtime_materials装配的SDK；`baseline_health.py`是维护侧的400步串行非零传播健康检查，不进入公开模型或评分数据。固定来源完整构建日志和原始算例日志留本任务忽略工作区，不抄进操作指南。

初版完整并行健康检查在并发私有probe中超过60秒，该失败日志保留为[health-v1-timeout](data-evidence/health-v1-timeout.stderr.log)；不是候选失败。原v1正式Oracle本身健康14.329秒并8/8、reward1、exception null，所有返回数组逐位等于reference，见[Oracle v1](data-evidence/oracle-v1.json)。健康改为同一真实solver的短串行波传播运行，正式时程不缩短。

最终闭包SDK为317d0db7083b994e53ed63ecd59c8b6f2bc66a00ab5bff722a0cd19935b9b871。v2 Oracle绑定旧公开ZIP 53ab80e1e927c46b20bc2c12cb161e1b48cac988ec20b8cbb4e6ba25febecaeb，实际8/8、reward1、exception null，全部数组逐位等于reference，见[Oracle v2](data-evidence/oracle-v2.json)。

考生审阅后只改DATA输出支持量误要求及instruction相对命令工作目录；当时公开ZIP为9cd9a7479aaa7973194bfd5099e97fbc60f40c8133cddcce8b2e7552f54c3f39、44文件。[全成员比较](data-evidence/public-doc-only-diff.json)证明仅两份文档及对应MANIFEST哈希变化，源码、SDK、数据、样例、配置无变化。最终包普通离线安装并移走SDK源码后，按新说明进入题目录，两例真实CLI均score1且pip check通过，见[安装证据](data-evidence/public-install.json)。

旧七模式探针实际前六项通过，第七项真实Fortran超时发现MPI rank逃逸进程组而残留，旧失败日志保留于本任务工作区，不能记为7/7。共享judge改为每例独立Linux subreaper supervisor，仅终止和回收自身后代；[新清理证据](data-evidence/process-cleanup-v3.json)记录原3秒Fortran超时后launcher及三个rank全部消失、同UID无关sentinel存活。真实Linux测试覆盖普通solve.py、direct Python与C++、setsid/双fork及父提前退出，共享Harbor30项测试也通过。

最终公开ZIP为22aa0bcf168c9cabd7853ec8a63e2498838968fb53aa996034cb3e48108144d7。独立全量审计发现旧DATA误写PML外终端为Neumann；真实原生执行体在PML上下外终端把chi、旧chi及一二阶时间量置零，现已公开明确为齐次Dirichlet截断。无PML四壁及PML左右Neumann保持。独立逐成员比较证明相对9cd仅DATA与MANIFEST变化，64项运行/输入/参考资产不变；不得用微小晚时残差冒充对旧边界误写的认证。最终设计和盲考生有界审阅均关闭公开说明缺口，见reviews/design-final和reviews/candidate-final。

正式Oracle-v3使用9cd文档身份及新版559550共享judge，真实8/8、exception null，全部返回数组逐位等于参考；最终22aa仅文档修订，数值/源码/运行证据经独立逐成员证明有界复用，没有伪称22aa运行过新Oracle。原始8份结果、两次构建和真实健康/逐例报告见[data-evidence/oracle-v3](data-evidence/oracle-v3/binding.json)。新7模式探针全部通过，含真实Fortran三rank超时后的完全回收；旧rank残留失败保持原身份。

最终22aa另在断网容器普通pip安装、移走src、离开源码后按公开命令实际运行两个样例，均grade1，pip check有效，见[最终安装](data-evidence/public-install-22aa.json)。独立全数据和后端终审均通过，涵盖全部8例/2样例、全时程独立Green核查、实际MPI数据库与源树/重编产物、真实8例返回结果及7探针，见reviews/data-final和reviews/backend-final。最终冻结见[data-evidence/final-freeze.json](data-evidence/final-freeze.json)。整题验收完成。旧v2prepared与失败证据保留，未运行新增收费模型Benchmark。
