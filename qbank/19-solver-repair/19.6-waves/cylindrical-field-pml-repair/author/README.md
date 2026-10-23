# Meep #2338：作者维护入口

来源NanoComp/meep#2338及PR2382。完整固定原件700文件、baseline85e107771808a4b89e4b4514007512f48c1c121b、head2828d4d92cac52c5666ca18351b6d64f4feefb09。公开任务位于instruction/DATA；范围/数学论证和实际阶段日志位于runs/authoring/repair-22/meep-2338-*，原始历史研究保持原样。

完整原始runtime及单真实上游修复production镜像均已实际构建，700个原始文件SHA一致，另有33个Autotools生成文件。8例真实reference均通过，8例原件仅正m的02/07通过；完整trace独立DTFT误差最大1.1325e-14。官方HF固定提交7abc5ec8686026548ae4abdfeb4530a33ccd8332已新缓存取回，52装配项、changed0、strict有效；最终公开ZIP为acac8a89d2b02b4aa1a753fcdd2354b836c2af0af1cb21748973ed41564e0027。普通离线pip安装、移动SDK源码后site-packages导入与2例真实运行均通过。设计、资源有界复核及新鲜盲考生两模式已通过；正式Oracle真实8/8、reward1、exceptionnull，8份实际H5全数组与reference逐位一致，原件重编8.748秒、候选9.728秒、健康1.080秒；最终全数据与后端独立审阅均通过，本题验收完成；原始报告与实际独立证据见[数据审阅](reviews/data/report.md)及[后端审阅](reviews/configure-judge/report.md)。

真实C++ FDTD原型已复现R2/Z1/res30负m端盖谱通量原件2.2303300588、修复2.1071566794（差5.845%）。修复正负m三通量完全匹配，内部6复分量满足Er/Ez/Hphi偶、Ephi/Hr/Hz奇；3条64800步实际trace独立有限DTFT误差最大1.14e-14。该内部场原件/修复实际相同，不能声称它本身检出PML缺陷；加入它为了保留角模式旋向。

实际轴心源实例系数A*res^2/2、位置r=1/(2res)，可推导等效连续圆偏振电偶极源q=pi*A*Jhat/(4res)，P0=pi^3*fc^2*A^2*tau^2/(12res^2)，角密度1+cos^2(theta)。真实窄带R3/Z2/res30→40的绝对总量相对连续源误差2.861%→2.006%，端盖分配差0.003700→0.003106。它是渐近物理归一化支持，不是精确离散reference；未声称收敛阶数。正式标答取完整真实上游修复库原生结果，独立数学FT及连续物理用于认证。

初次COPY修复文件因mtime较旧造成make无动作，此cached-unrebuilt镜像保留为失败史，不当修复证据；真实参考强删.lo/.o/.la/so后重新编译。某些单点坐标在res20扩大为两点，相关失败日志保留；正式限定res30/40，经32个真实PML/几何初始化组合确认6个分量均N=1。不得在adapter中重算或纠正场与通量。

prepare_source.py验证完整两存档及准确差分step_db.cpp和Python上游测试，只将真实step_db.cpp作为私有修复文件；prepare_runtime.py构建完整原始源码，配置固定7产物（真实step_db两种.o/.lo、.la、版本so、driver.o和exe）强制重建。所有其他头文件/源固定。source archive只原件进入public；author/generated不得公开。generate.py生成真实MSH4.1三条观测母线及8个独立机制例；MSH不是内部FDTD网格。independent.py只数学DTFT和解析连续源核对，不是作者电磁求解器。

公开说明、实际接口、数据及配置更改后，重做相应真实消费链及独立审阅；只有固定HF取回strict、正式Oracle和全部独立报告完成才能更新完成状态。本轮不调用收费模型Benchmark。

独立真空点电流retarded Green近场六复分量核对见 `runs/authoring/repair-22/meep-2338-nearfield-analytic.json`：含1/r、1/r²、1/r³项，从源q推导，±m最大相对复误差1.437%，不拟合原生值。所有正式reference将独立认证完整trace DTFT及连续场/总量的量级；连续支持不替代严格离散标答。

资源：完整声明范围保留，包括res40大域与独立r/zPML。当前公开单例执行预算1800秒，编译各300、评价30，外层8例预算15680秒。真实最大cornerR3/Z2/rp2/zp2/res40、200×320名义格、86400步，在生产镜像无作者trace路径实际完成：原生1082.973秒、总1085.875秒、exit0，实际4CPU/4GiB/UID1000、峰内存31,453,184字节，结果见data-evidence/resource-corner.json；1800单例预算取得实际支持，独立有界设计复核及最终正式全数据／后端审阅均已通过。旧阶段R3Z2/PML1/res40无trace841.187秒完整保留；当前177.422秒reference含全时域get_field×6/CSV工作量，二者不混称正式无trace路径。

实际后端七模式均通过，见[data-evidence/backend-probes.json](data-evidence/backend-probes.json)：正确替换、语法错、额外文件、软链、编译器故障、原件SDK健康故障、真实C++无限循环超时。正确路径实际原件重编8.374秒、候选10.167秒、健康探针1.266秒；全部7产物强制移除并重建，实际动态链接libmeep。超时原生主PID1071杀后Z，仅断言该被测进程。独立审阅原报告原始字节和链接可读归档位于[reviews](reviews/design/report.md)。

环境重建见prepare_source.py、prepare_runtime.py及runtime.Dockerfile；dependencies.Dockerfile保留实际Meep依赖镜像的源代码无关构建配方。SDK依赖镜像与离线wheelhouse按共享修复题流程准备，实际image ID列于[data-evidence/runtime-images.json](data-evidence/runtime-images.json)。

正式Oracle完整原件/候选编译、健康检查及终态证据见[data-evidence/formal-oracle/output-bindings.json](data-evidence/formal-oracle/output-bindings.json)；全部8例真实输出逐数据集逐位比对通过。独立全数据与后端验收均已通过，原始证据及其结论适用范围分别保留；没有将连续物理误差用作严格离散评分容差。
