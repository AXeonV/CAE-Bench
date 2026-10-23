# ASPECT 6818 作者记录

固定来源为 [issue 6818](https://github.com/geodynamics/aspect/issues/6818)，实际合并修复为 [PR 6829](https://github.com/geodynamics/aspect/pull/6829)。6818不是PR。原始缺陷树为合并提交的第一父提交 `021e8ef55cae159a101e234ff9622e5de0364068`；依赖镜像中预装的较新ASPECT只用于参数预检，没有作为基线或参考生产者。

完整原始源码在官方依赖环境中真实构建。参考只替换 `source/simulator/core.cc`，从上游修复保留AMG所需的当前几何约束及变形后约束／稀疏刷新；新缓存集合接口用原有接口的局部集合运算实现，避免要求另交头文件。参考不覆盖GMG，上游也未解决该路径。`generated/core.cc` 是实际参考替换件，不进入公开包。真实原件与参考的源码、二进制及依赖身份见 `data-evidence/source.json`。

## 采样、参考和独立资格

正式输入使用CONTRACT的固定Cartesian points，真实ASPECT原生PointValues后处理器按要求的全部时刻取值。没有移动entities、自编插值或输出修正。`replay.py` 生成参考；正式原生输出与求解日志保留在忽略的工作目录。原件实际4/12通过、参考12/12通过；静态退化例的通过是必要回归。该数字是逐例SDK评分结果，不等于最终Harbor或隔离验收。

平行平面族的材料速度 `(U,V,t(kU+lV))` 空间恒定，零应变、零散度且与当前平面相切，压力规范给出零压。圆环的刚体转动同样零应变，采用实际细化检查曲面离散误差。两族在所有实际采样点和时刻逐分量核对，见formal-replay及formal-convergence记录。

非均匀底壁驱动族未用解析匀速替代。独立检查使用真实Elmer原始 `FlowSolve.F90`、NavierStokes模块及原生二次三角形有限元，在每个时刻独立构造当前静态域。Gmsh将每个固定探针嵌入为网格顶点，读取Elmer原生节点结果，不进行插值。三例、各五帧、两级网格共30次求解；较细一级与ASPECT的最大速度差低于5e-5 m/s、压力差低于7e-4 Pa，速度误差约按四倍下降。ASPECT本身细化差异另列，不把跨实现相合当严格误差界。

Elmer的压力零空间保留了较大的任意常数，需读取17位ASCII `flow.result`，不能使用8位ElmerPost压力。按原生拓扑节点和二次边积分移除当前顶边的压力均值，匹配公开规范。读取器依固定Elmer源码的节点顺序解析，并逐节点对照原生ElmerPost速度；这是压力规范转换，不是修正流场。偏置大小及两个细化级别的差异保留在独立报告中供审阅。

## 离线环境与资源

依赖为固定官方ASPECT镜像；从原始完整archive重编源代码，Release、unity/PCH、上游参数 `ASPECT_ADDITIONAL_CXX_FLAGS=-g0`、WorldBuilder关闭。公开源码闭包包含完整main source/include及影响unity排列的unit_tests，保留原始CMake、许可和必要配置目录；在新目录实际configure通过。环境内 `/opt/aspect` 保留原始完整树，开发不需要联网获取源码。

真实替换编译需强制重建unity45对象及真实ASPECT程序，单次已测177秒；可信预算900秒，不能把小型驱动编译时间代替实际求解器。8GiB环境考虑PCH和unity编译峰值，运行采用单线程及OpenMPI官方 `ess_singleton_isolated=1` 单进程设置。Python3.14.9 standalone与真实SDK依赖已离线安装并经无网络、UID65534的原生求解检验。镜像只含原始基线，不含作者参考替换件或作者参考二进制。

`generate.py`声明输入；`replay.py`由真实库制参考；`formal_convergence.py`核验ASPECT细化；`prepare_elmer.py`、`read_elmer.py`、`summarize_independent.py`执行独立交叉核验。判据唯一消费入口为每例reference/grading.json，模板只用于制数。使用既有data pack/upload/assemble/verify、publish_dist、prepare_harbor与共享source-repair后端。后续正式HF提交、严格回取、公开包及Oracle身份单独记录，不以本记录提前宣称就绪。

## 最终生产验证（2026-10-23）

HF固定提交 `eebdf355f381244b685814da1309e7d42296488f`，从全新缓存按该提交回取装配全部58文件，complete=true，严格verify有效。当前公开ZIP SHA256为 `9acb735ced6dcc52c86ffb187a5c7b3ae34e784713ba5b963f6d412e3e6b63ee`，40成员。三族以physics.model字符串选择；逐例模型迁移前后原生PRM字节、采样及参考完全相同的证据单独保留。

生产镜像为offline-v4，完整摘要及私有后端冻结见runtime-v4-freeze.json。旧offline-v3继承官方bash入口，曾导致Oracle-v1在环境启动时退出126；该失败完整保留。v4清空入口并明确工作目录，未改变源码、构建缓存、SDK或二进制；对v4重新核验全部8236原始archive文件一致。source.json分列旧v3与新v4，不把早期镜像身份冒称最终环境。

实际Oracle-v2为12/12，completed=true、exception_info=null，完整trial、编译日志及绑定索引见data-evidence/oracle-v2。可信后端以UID1000删除受影响unity45对象及真实程序后分别重编原件和参考，实际57.66／54.80秒；原始177秒原型记录属于不同负载下的历史测量，预算仍按公开900秒执行。

另外实际运行公开尺寸上限组合：非均匀wedge、refinement6、9帧、128固定内点，在4CPU8GiB、UID1000下28.65秒完成真实参考求解与完整HDF5写出，cgroup memory.peak296771584字节。该结果是此明确参数组合的运行证据，不外推为所有连续参数组合的严格耗时上界。

八项真实可信后端探针全通过，见backend-probes.json及忽略工作目录中的逐模式原始日志。至多两个独立4CPU8GiB容器并行，valid模式实际内存峰值3255836672字节；它核验未来mtime下仍强制重建、两个样例真实SDK评分、净环境SDK导入、428个保护／实际动态依赖及其父路径在UID1000下不可写、三个隐藏目录不可读和无外网。候选语法错误、额外文件、符号链接、编译器故障、基线健康探针故障及受保护include被分别正确分类；注入实际C++约束函数的死循环触发共享3秒运行超时，真实native进程被清理且无zombie，无关同UID进程存活。有限路径与模式的探针不冒充整个容器的形式安全证明。

独立设计、盲考生考试材料、全量数据／数学与后端审阅各自按冻结身份归档；其中数据审阅独立读完全部24个ASPECT PointValues和30个Elmer原始17位结果，独立积分压力规范，没有用作者摘要代替全数组。维护者统一记录最终完成计数和Git提交，本题不重复中央进度。

整题已按固定最终版本验收完成。[独立数据终审](reviews/data-final/report.md)及[后端终审](reviews/backend-final/report.md)覆盖全部原生/独立参考、变体、源码、当前Oracle和八探针；[最终冻结](data-evidence/final-freeze.json)绑定当前公开材料、真实源码及数据。未新增收费模型Benchmark。
