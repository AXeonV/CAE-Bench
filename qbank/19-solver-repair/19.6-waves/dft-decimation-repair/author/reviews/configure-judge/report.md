# Meep2408 / dft-decimation-repair 独立后端审阅



结论：**通过**。最终ZIP `caef0f38ac89be65ca67328eef4b4fadc5eb15cf54cf712397b3e3a82cb55706` 的真实formal Oracle全部9例终态、135产物强制重建及四源码绑定、独立安装、实际资源/隔离、精准失败分类与容差/非法输出均有对应实际证据。本轮是非作者独立configure-judge审阅，不代实现、不改正式数据、不运行收费模型。



## 版本与要求映射



已读caeoj-configure-judge及其workflow/current-backend，复用之前完整读过且版本无变的instruction/DATA/CONTRACT。实际文件SHA见 [materials.json](materials.json)。本题全部9case/2sample真实输入、参考及数学资格已由本审阅者另完成独立 [数据审计](../../../../../../../runs/data-review/repair22-meep2408/report.md)，本轮进一步核查真实后端消费链。



| 公开要求 | 当前消费者与配置 | 本轮实际证据 |

|---|---|---|

| 4逻辑字段、全部频率与Ex/Hy实虚组件；stride精确 | 各case direct_outputs，quantities normalized_finite_dft、sampling_stride、normalized_time_step、normalized_window_end | 全部9case配置读取；formal每例预检评价摘要一致，全部6输出dataset与reference逐数组误差0 |

| 复谱atol1e-9/rtol1e-8；dt1e-12/1e-12；window1e-10/1e-12 | grading_policy→grading_metrics pointwise，np.isclose按reference相对尺度 | 真样例相邻可表示阈值内/外及精确等号测试全部符合 |

| 四指定普通源码每份≤1MiB，保留真实FDTD/accumulator | source_repair.prepare严格目录集合、普通非链接文件、大小；SHA冻结后替换四src目标 | extra/symlink真实拒绝；额外独立oversize1048577字节探针拒绝且未编译；四source SHA为真实上游PR文件 |

| 真正全头依赖重编，不能沿用二进制缓存 | 清除rebuild_files再编原件、健康检查、写候选、再删同集合重编；CMake target调用真实upstream make并链真实libmeep | 实际core扫描135集合与配置完全相同；valid未来mtime陷阱仍删/重编；formal baseline/candidate各删除135并candidate记录135产物SHA |

| 候选编译300s，单例30s；基础设施错误不算考生零分 | candidate wait300、judge.execute wait30；trusted baseline失败抛RuntimeError，SubmissionError作考生失败；评价独立30s | 原件162.854s/candidate160.110s实际built，compiler失败明确build_error、SDK破坏明确probe_error；语法错误candidate build_error；实际C++循环受超时终止 |

| 4CPU/4GiB、分离无网络verifier | task cpus4/memory4096，separate/no-network | valid实测cpu.max400000/100000、memory.max4294967296、network denied、UID1000；formal同冻结task配置 |

| 每例全部过才1，9例等权，公开case仍各计一次 | judge.save_report passed/total，selection.public_cases | formal score9/total9/completed9/complete true/reward1，sample01/02各标原公开case一次 |

| 总verifier预算覆盖所有合法路径 | base1000+9*(30+30+5)=1585s；源码原件/候选各300、健康probe≤60 | 最坏300+300+60+9*(30+30)=1200s，余385s；formal完整终态无截断 |



## 正式Oracle终态、版本冻结与全部9例



独立直接读取 `runs/authoring/repair-22/repair22-meep2408-oracle-v1.json`，phase=completed、returncode0、exception_info=null；再读真实trial `runs/harbor/jobs/repair22-meep2408-oracle-v1/dft-decimation-repair__YWviCuh/result.json`，exception_info=null、verifier reward1。不是只看宿主CLI return0。



formal verifier/report.json为score9、total_cases9、completed_cases9、complete=true、reward1；全部9例accepted，公开01/02仍标sample01/02。全部实际结果HDF5逐dataset读取，key集合/dtype/shape与reference一致、所有值误差0；每例evaluation_sha256等于原预检evaluation_manifest。supervisor冻结55项任务资产SHA逐项与实际prepare目录匹配，包含两份最终caef0f38 ZIP、solution四源码、tests源码配置、9case全部输入和reference/评分，无旧版本借用。



formal原件强制重建耗时 `162.8540795939989s`，健康probe ready；候选强制重建 `160.11002411000118s < 300s`，source四SHA逐一等于冻结solution中PR四原件。原件/candidate removed列表均135，candidate built_artifacts_sha256也135且集合等于实际配置。逐例、源码与实际构建原始数据见 [formal-and-probes.json](formal-and-probes.json)。



## 真正135产物闭包与完整原件绑定



本轮另外在配置base_image的真实runtime中轻量只读扫描upstream/src所有普通.o/.lo/.la，附真实libmeep.so.30.0.0、driver对象与driver，共135；与source-repair.rebuild_files集合精确相同，全部实际存在且不是链接，并读取实际.deps/*.Plo里的meep.hpp依赖记录。不是只相信作者给出的135计数。详细路径/每产物摘要见 [actual-closure.json](actual-closure.json)。



公开CMake真实meep_upstream target调用原upstream/src Makefile，driver依赖此target、直接链接该build目录的真实shared lib；135是保守全清理覆盖，比仅删一个调用driver更强。valid把135mtime设未来后仍逐项删除再构建，真实ldd确认加载 `/opt/meep-repair-build/upstream/src/.libs/libmeep.so.30`。



完整源绑定复用本审阅者本轮之前亲查同版本的 [runtime-source-bindings.json](../../../../../../../runs/data-review/repair22-meep2408/runtime-source-bindings.json)：baseline701上游原始文件逐SHA全同，reference-producer仅4个真实上游文件替换，其余697全同；runtime目录另有33个正常Autotools生成物，不混称总数仅701。固定原始archive与head archive都已实际读全树核过，四候选即真实PR替换而非作者新写求解器。



## 七项原始探针与精确基础设施分类



全部7mode的stdout/stderr已实际读取，每份stdout末条JSON逐字段等于汇总报告（汇总另含宿主command/elapsed）。valid、syntax、extra、symlink、compiler、baseline-runtime、runtime-timeout全部passed。原始日志摘要与详细结果在formal-and-probes.json，未只复述“7/7”。



特别防止旧Dolly误归因：本题fixture源对RuntimeError仍只泛化匹配Trusted baseline，因此本轮**额外独立严格断言实际reason**：compiler恰为 `Trusted baseline build failed: build_error`；破坏numpy导入的baseline-runtime恰为 `Trusted baseline runtime probe failed: probe_error`。后者只有真正原件built后运行健康probe才能到达，不能用build_timeout充数。实际证据满足精准分类；未来fixture如改动，应继续保存/核对reason而不是泛化RuntimeError。



valid候选实际编译 `59.96559848099787s`，健康probe ready，135产物删除/构建SHA与四source SHA完整。实际UID1000下submission、原源树/其余头、可信driver/CMake及目录、全部构建产物、已安装SDK目录/模块均不可写；/tests、/logs/verifier、/probe不可读；外连1.1.1.1失败，cgroup4CPU/4GiB实测符合。此实际cgroup来自valid探针，formal使用同冻结配置，不冒称另采集了已退出formal容器的cgroup。



runtime-timeout是真正C++ dft_chunk::update_dft插入无限循环，judge.execute探针3s触发timeout，原生主C++进程PID5683随后为Z，证明该主进程已终止；共享执行器源码执行killpg，本轮未逐个实测所有MPI辅助进程。探针3s用于快速证明同执行器超时路径，正式每例仍30s。



另由本审阅者在同private verifier镜像独立运行廉价oversize探针：四文件齐全，其中dft.cpp1048577字节，prepare在编译前抛invalid_submission，exit0为探针成功而非候选成功，见 [infra-and-oversize.json](infra-and-oversize.json)。没有为了补探针重新做重编或改变实现。



## 容差、非法输出与基础设施错误



独立18个真实sample01 HDF5变体：correct通过；复谱/dt/window各用“最大可表示且满足公开式的值”和其nextafter邻值作为阈值内/外，对应通过/失败；stride=nextafter(1,+inf)失败，证明不宽容身份元数据。NaN、Inf、缺输出、多数组、float32、少复组件、错ID、错times、根属性、dataset别名全部invalid_output。另对三种容差各做reference0处nextafter下侧/精确等号/上侧9个metric测试，等号通过、上侧失败，避免把浮点加法舍入误称边界错误。详情 [tolerance-and-illegal.json](tolerance-and-illegal.json)。



缺reference与缺sampling_stride策略的两坏基础设施配置在实际CLI均exit2，未计候选零分，见infra-and-oversize.json。source syntax实际是SubmissionError build_error，运行循环实际timeout；shared judge对可信baseline失败不catch为submission_error，评价worker有独立30s限时并将异常/scoreNone归infra，符合公开契约。



## 普通断网安装与结论边界



已完整读实际author/data-evidence/public-install.json的命令及结果，archive SHA恰为最终caef0f38。在无网络4CPU/4GiB原件runtime容器中普通pip install .成功；把src移出、在/tmp导入site-packages，pip check无破损依赖。两公开样例真实baseline运行均exit0而grade退出码1、score0、wrong_answer，符合应检出原件缺陷，不能把原件样例错误当SDK安装失败。



本轮结合真实producer、独立DTFT和已有数据/设计/考生审阅，确认本题公开要求→配置→实际执行已闭环。没有重跑完整Oracle或构建参考，也不以Oracle替代数值资格。结论仅覆盖当前冻结单进程1D电chi2/chi3问题族与所声明观察，不外推MPIhelpers、磁非线性、多能级或未来任意提交性能。

