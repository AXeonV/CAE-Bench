# preCICE 19.5.2 可信后端独立审阅

结论：通过，无未决阻断。审阅最终ZIP `08223e23aeb1ab6cd9c01b53fd60fbb53dc4d4eacc29f04a6ba88d7d7e895a5c`，43条；正式真实Harbor Oracle-v2完成10/10、completed=10、exception=null。未调用付费考生。本轮只在此审阅目录写报告和证据，未改正式代码、数据或配置。

## 公开要求到实际消费者

|公开要求|配置/代码与实际证据|
|---|---|
|只提交Index.cpp，≤1 MiB|harbor/source-repair.json唯一替换真实基线src/query/Index.cpp，max_source_bytes=1048576；source_repair.prepare核对目录精确集合、普通文件/非symlink/字节数，冻结源SHA。发现题面原未说明大小，协调方已在最终instruction补明，配置未放宽。|
|保持真实库与API，driver不代替选择|审读public/driver.cpp，实际构造mesh::Mesh、调用Index两入口，n=max(1,边数,面数)，仅把返回polation权重映射至完整轴、重建位置和三个场；distance直接来自polation，无作者最近点算法嵌入。public/run_case.py只作协议/身份转换、进程调用及HDF5序列化。|
|可信强制重建|CMake排除原Index对象，其余真实上游对象参与链接。配置四项为Index.cpp.o、版本化libprecice.so.2.5.0、driver.cpp.o和projection-driver。prepare先删四项原件真实编译、再健康探针，替换候选后再次删四项编译；两轮实际日志与最终源/产物SHA记录相符。有效探针先把四项mtime设至2100年仍删除重建。只允许cpp，无本题头文件依赖闭包问题。|
|实际加载新实现|valid探针实际运行公开case并判1，ldd解析libprecice.so.2至/opt/precice-repair-build/lib；源与四产物SHA重新计算相符。正式Oracle10例也均通过。|
|四输出逐值阈值与case等权|全部正式reference/grading.json按quantity/unit绑定projection/distance/weights/mapped_values；pointwise、per_time、per_component，rtol=1e-8，weights atol=1e-9，其余1e-8，符合公开定义。judge先prepare_case全部参考，逐例grade，passed/10，public两例仍在同一正式分母。没有judge-config第二容差入口。|
|30s/例，编译180s，4CPU/8GiB|judge.execute以30s等待并finally killpg；源码编译candidate180s，原件和baseline_probe各min(60,180)。task.toml cpus=4/memory_mb=8192，valid真实容器cgroup cpu.max=400000 100000、memory.max=8589934592。此为真实同配置探针证据，不冒称正式Oracle保存了cgroup快照。|
|总预算|10例总verifier1350s=700+10×(30执行+30评价+5开销)，700基数覆盖原件60+健康60+候选180及预检等；agent1800s，环境build1200s分开。当前正式10例完成未超预算。max_output_bytes显式null，不额外引入未公开输出字节上限；逻辑shape由协议校验。|
|离线环境/普通公开安装|runtime Dockerfile提供固定numpy/h5py/gmsh/jsonschema/typing-extensions及本地setuptools/wheel wheelhouse，PIP_NO_INDEX=1。已有最终SDK相同版本普通断网pip install .、移走SDK源码、两样例实际run均exit0、pip check无缺依赖；原件样例grade0是预期真实缺陷，不是安装失败。最终只改instruction，逐条验证41个其他包条目不变，故有界复用安装证据。|
|低权限、不可读隐藏/不可改可信路径|编译/运行均setpriv UID1000、clear groups、no new privileges，清理env；准备后build/源/提交root冻结。valid实际UID1000不能读/tests、/logs/verifier和/probe，不能写提交、驱动、构建规则、关键头文件/父目录、替换源、四产物和全部真实原件objects；网络连接失败。本人另核对关键祖先目录root:755。|

## 实际证据及独立补查

- [source-image-check.json](source-image-check.json)：本人以断网只读挂载正式源码归档，对core镜像全部962文件逐项计算SHA，精确等于归档；树摘要`e42412ef3433e46af5a31e26e14de092d455d00bae1c5e3f390b1be9be4547a4`。131个实际上游objects存在，原源码及构建关键祖先目录为root:755，没有以作者自编库替换真实源码。
- `runs/authoring/repair-22/precice-backend-probes/report.json`：7模式均真实exit0。valid真实重建+输出判1；syntax归build_error；extra/symlink归invalid_submission；移除真实g++后原件强制编译归infrastructure_error；破坏真实NumPy模块后baseline运行健康失败归infrastructure_error，不给考生零分。native C++无限循环实际触发3s执行timeout，子进程结束为Z，非仍运行进程；原始探针代码与日志均已读。
- [threshold-check.json](threshold-check.json)：本人以实际grade_case核对正确参考、距离阈值等号、阈值内通过；阈值外wrong_answer；NaN和缺distance均invalid_output/0。没有只凭模板或结构推断数值策略。
- `runs/authoring/repair-22/repair22-precice-oracle-v2.json`：读取完成记录及原始消费代码，最终ZIP绑定10/10、无异常。v1同代码数据已10/10；[formal-version-binding.json](formal-version-binding.json)逐项核对v1/v2冻结清单，只有environment/tests agent.zip变化，其余代码、配置、case、参考、Oracle源都相同。7探针因此可以有界复用，没有不必要重复编译。
- 最终ZIP逐条核对MANIFEST中的42个SHA，43条无author、隐藏cases或修复Index.cpp。公开归档保持原件/许可证。独立数学全数据审计另见`runs/data-review/repair22-precice/report.md`，本后端审阅未重复冒称完成全部几何独立参考审计。

## 共用.inl文件名扩展

审读src/caeoj_tools/source_repair.py差异只在完整锚定的plain filename正则增加inl，与cpp/h等沿用同一规则；不允许目录、双后缀或任意脚本。实际执行器未变。已有29项test_harbor unittest exit0，证据`runs/authoring/repair-22/inl-harbor-regression.json`；该语法能力不等于SU2头文件的实际编译依赖已认证，SU2仍需自己的全依赖强制重建证据。

## 限制

有限权限探针、ldd和单次断网连接不是整个容器安全性证明。未实际注入编译超时；其进程组清理仅审读实现，原件缺编译器/候选语法错及真实求解无限循环已实测。未认证MPI、性能、高阶几何、通信或GPU等公开范围外能力；未新增模型成绩。原考生旧ZIP无原件时的版本边界见[有界公开变更复核](bounded-public-change-review.md)，不篡改旧考生报告或假称重新从零独立审阅。

归档说明：诊断附件保留在原审阅目录，上述路径仅作归档定位，不改变审阅结论。
