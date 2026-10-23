# Elmer 19.3.1 可信后端独立审阅

结论：通过，无未决后端问题。最终公开包正式Oracle-v2已真实12/12、completed=12、exception=null；旧冻结包v1也为12/12。只读正式实现和材料，不重跑Oracle或付费模型。

## 公开要求、配置及实际消费者

|要求|实际映射与证据|
|---|---|
|单真实Fortran源、1 MiB|source-repair.json仅接受AdvectionDiffusion.F90，目标是真实原件fem/src/modules/AdvectionDiffusion.F90。prepare校验精确文件集合、普通非symlink及≤1048576字节，冻结源摘要。原公开题面漏了大小，本轮反馈后协调方已补明，最终包见下文差分。|
|可信原件先构建及健康运行|prepare先删除预处理F90-pp.f90、实际F90.o及AdvectionDiffusion.so，再原件编译，随后以UID1000跑真实公开run_case.py/ElmerSolver/三模块健康样例；原件可数值不正确但必须真实运行成功。损坏编译器、ElmerSolver或SDK分别实际被探针识别为infrastructure_error。|
|候选强制重编真实模块|替换冻结源后再次删pp/o/so，真实Ninja输出包含预处理、编译和链接，不会用陈旧pp绕过候选。候选语法错误归build_error/零分；成功保存真实源和三产物SHA。未来mtime2100探针仍强制重建并改变so摘要，真实公开样例判1。|
|三实际全节点场|public/run_case.py仅把QUAD4/Gmsh身份转成原生Elmer节点/单元/边界，按规定SIF调用真正HeatSolve、StatCurrentSolve、AdvectionDiffusion。热/电势字段使用非默认ThermalField/ElectricField并明确实际关键词；输入密度、DT和z原值传递，没有密度补偿或作者输运求解器。native_result.py读取ASCII3原生标量节点结果，Perm第一列按网格节点定位，未将第二列solver索引再次逆置换。独立全数据审阅核对原生字段/解析及离散节点解另见runs/data-review/repair22-elmer/report.md。|
|模块确实装载|SIF Procedure使用/opt/elmer-build/fem/src/modules的绝对路径；valid探针确认模块导出真实advectiondiffusionsolver_，改变真实so后实际样例判1。本人额外ldd确认依赖真libelmersolver/mpi_stubs/matc/fhuti/arpack/BLAS/LAPACK，未用同名作者stub替代。|
|逐值阈值与等权|真实每例grading.json包含concentration、temperature、potential的quantity/unit和pointwise规则，与题面质量分数/质量浓度不同绝对容差及各自rtol一致。judge在solver前prepare_case所有输入/参考；每例全部输出通过才score1，最终passed/12，两public case不另减分母。max_output_bytes=null，没有附加未公开文件大小限制。|
|资源与预算|正式task声明4CPU/4096MiB、candidate180s、每例20s、评价30s，verifier=900+12×(20+30+5)=1560s；原件及健康各≤60s，候选180，剩余基数有裕量。真实valid探针实际2CPU/2147483648bytes，cgroup cpu.max=200000 100000、memory.max=2147483648，不能将其写成正式4CPU/4GiB快照。正式Oracle完成证明该设置下消费链成功，不另臆造cgroup采样。|
|隔离与不可写|编译/运行UID1000，clear groups/no new privileges，固定PATH/HOME和最小环境；prepare后冻结build、源与提交。valid实际不能读/tests/cases、reference、logs，不能写源/构建/真实模块及关键源码/元素定义；额外runtime-permissions.json逐一确认公开driver/native_result、两个辅助模块及SDK不可写。网络测试TCP被拒。本人核对源和构建关键祖先目录root:755。|
|普通公开离线安装|独立断网普通pip安装、SDK实际从site-packages导入、两个样例真实运行成功且原件各0分，表示故障可检出；不是安装失败。最终仅instruction/MANIFEST变化，公开SDK/源码/driver/两样例逐字节不变，可有界复用安装证据。|

## 本人额外真实验证

[source-image-check.json](source-image-check.json)：以readonly公开归档挂载并断网运行原始runtime镜像，2468源文件逐项SHA完全等于公开闭包，baseline模块摘要9758678f1cfd0d274e3dce05c3872aeb122227e07b54f4a27ed3a714efbec313；保存真实链接和关键目录uid/mode。未声称2468文件等于整仓库；它是实际配置/877目标构建所消费的保留闭包。

[threshold-check.json](threshold-check.json)：实际grade_case检查正确参考、potential在零参考值的atol=1e-10等号与内侧均通过，1.01倍阈值wrong_answer，NaN及缺potential均invalid_output/0，避免只读模板推断评分。

既有7个实际探针valid、syntax、compiler、baseline-runtime、baseline-sdk、extra、symlink全部passed，读过脚本和原始JSON而非只接受聚合通过。健康样例实际调用三模块；独立关键词消费与wrong-keyword实验留在author/data-evidence/keyword-consumption.json。可信失败和候选失败仍按共享后端分层。

## 公开版本变更有界复核

[public-version-diff.json](public-version-diff.json)保存本人对两个实际ZIP逐条SHA比较。旧9a660158718cf8b451985e8b70d684774b0b042efae20a487ab481c9035e5ba7，新79ea2a0562e2028a11685cec8cde8361b259ef09bdbcb60f180c178341116921，各40条；仅instruction新增“文件不超过1 MiB（1,048,576字节）”及MANIFEST变化，其余38条完全相同。该条文与原有实际max_source_bytes一致，未改执行配置或缩小数值问题族。大小缺口关闭；不冒称本后端审阅重新进行了盲考生全文审阅。

## 实证限制

没有本题实际无限循环或编译timeout注入，timeout后的进程组清理已审读共享执行器，不能虚称七模式包括这两项。权限与网络探针是所列范围，不是整个容器安全性证明。底层run_case失败时只保留stdout/stderr各末2000字符，完整失败输出可能缺失，本报告不从尾部臆断完整错误栈；实际成功和分类探针有完整外层日志及退出状态。几何/全节点数值正确性由独立data review负责，本后端审阅不替代其数学核验。

## 最终正式绑定核对

读取最终完成状态：`repair22-elmer-harbor-oracle-v2`，12/12、completed12、exception=null，ZIP79ea2a0562e2028a11685cec8cde8361b259ef09bdbcb60f180c178341116921。[formal-version-binding.json](formal-version-binding.json)逐项比较v1/v2冻结清单，仅两份agent.zip摘要改变；执行器、配置、参考、样例/隐藏输入与Oracle源完全相同，因此既有7探针可有界复用。

归档说明：诊断附件保留在原审阅目录，归档定位调整不改变独立结论。
