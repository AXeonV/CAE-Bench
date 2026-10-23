# ASPECT6818 全量实际数据独立审计

结论：**数据与参考资格通过**。最终可信后端端到端资格另见 `runs/configure-judge/repair22-aspect6818/report.md`，本结论不将早期启动失败 Oracle 计作通过。审阅日期 2026-10-23；按 caeoj-data-review 与 caeoj-configure-judge 技能，先阅读 instruction.md、DATA.md、docs/CONTRACT.md，之后才读维护实现。只在指定审阅目录写证据，没有改题、池、中央源码、没有重跑大型编译/24个ASPECT/30个Elmer或付费模型。

冻结公开包 SHA256 `9acb735ced6dcc52c86ffb187a5c7b3ae34e784713ba5b963f6d412e3e6b63ee`，40成员；HF revision `eebdf355f381244b685814da1309e7d42296488f`。脚本 `audit.py`、`variants.py`、`identity.py` 为审阅者独立写成，未调用作者 audit/read_elmer 实现；结果分别为 full-audit.json、variants.json、identity.json。

## 全量覆盖与公开语义

读取12个cases、2个samples全部JSON、全部输入数组及全部参考/公开输出，逐项检查数据类型、完整shape、有限数、严格递增非负IDs、整个时轴、复制支持、HDF5根dataset、无属性/外部/虚拟引用及允许过滤器。输入均恰有probe_ids、probe_coordinates、times；输出均恰有probe_ids、times、velocity、pressure。没有未读数组、未读帧或抽样代替全量。

|公开约定|实际核验|
|---|---|
|三种physics.model与精确族参数/单位/范围|12case+2sample全量check，并独立检查通用参数、维度、全时轴与各时刻边界距离；参数/值域/shape全录于full-audit.json|
|全时域固定Eulerian探针、距边界下限|逐点逐帧独立计算侧壁/斜壁欧氏距离，圆环用径向距离；所有点满足1e-4最小几何长度下限，非网格坐标|
|boxes等步长，圆环[0]|全部数组与arange(dt)精确相等；包括t=0已求解帧|
|velocity[T,N,D]与pressure[T,N,1]|全部参考及公开输出逐数组核对；样例output/reference完全一致|
|每例全部分量、点、帧；两项同时通过|逐case检查grading.json的pointwise/per_time/per_component、unit、atol/rtol与题面完全一致|
|六位有效数字原生PointValues|全部24个native point_values.txt读取，并逐数值与对应H5精确相等；全时轴和Cartesian坐标逐行核验；没有作者额外插值|

12个正式case包含二维/三维平行、正负/静态/pivot坡率，静态圆环正反转及三种非均匀wedge。全部12个原件与修复件原生结果都已读取，不仅复用了作者汇总。原生PointValues源码副本 point_values.cc 显示直接 `VectorTools::point_value(mapping,dof_handler,solution,evaluation_points_cartesian[p])`，默认流精度输出；helper_functions.cc 显示当前mapping面JxW积分top压力，按面积均值移零。这与公开DATA定义一致。

## 独立数学与独立求解器复核

平行域独立代入匀速解 `u=(Vx,Vy,t(rx Vx+ry Vy)), p=0`，二维删除y项；该解满足不可压、零应变及当前上下法向条件。全部7个平行case速度最大误差6.62e-15 m/s，压力最大3.91e-8 Pa。圆环独立代入刚体转动 `u=ω(-y,x), p=0`：两case速度误差4.27319e-6、2.90725e-7 m/s，压力均<7e-10 Pa，均满足公开阈值。细化圆环native文本逐值比较速度变化≤6.17e-11、压力≤9.20e-10，说明主要差来自公开原生文本量化。

三非均匀case×5frames×2网格共30个Elmer运行的 flow.result 全文、mesh.nodes、mesh.elements、mesh.boundary、flow.ep 实际读取，原生17digit标量按节点序核验，flow.ep用于独立交叉校验。全三角形元素determinant同号且非零，总面积逐网格独立核对width×height，全部solver日志实际到达ELMER SOLVER FINISHED。ModelDescription.F90原生SaveResult源码实际读取并留存，确认写出Values(Perm(i))按节点i顺序，不能把这些值再按方程序重排。每个探针在实际网格唯一节点命中<1e-10，没有自编空间插值。

从实际mesh.boundary的tag3二次边单元和mesh.nodes坐标辨认当前top；审阅者用三点Gauss积分二次压力形函数，先减去固定压力基准再积分，以减轻高达2.117651224e9 Pa任意偏置的消去误差。独立积分与作者归一化最大差<3e-6 Pa；此差远小于2e-3 Pa公开绝对容差。每个top节点按当前解析斜线核验（ASCII网格坐标精度下1e-9 m）。case.sif逐文件保留Stokes、真实黏度、抛物线底驱动与其他壁法向零条件，未用作者summary替代实际raw。

|case|Elmer h02速度/压力最大差|Elmer h01速度/压力最大差|ASPECT进一步细化速度/压力变化|
|---|---|---|---|
|09-wedge-negative|1.98812e-4 / 2.50382e-3|4.95754e-5 / 6.56856e-4|1.1e-6 / 1.06e-3|
|10-wedge-positive|1.32220e-4 / 1.39588e-3|3.30305e-5 / 5.31008e-4|2e-6 / 7e-4|
|11-wedge-static|1.98174e-4 / 2.51984e-3|4.97690e-5 / 6.89347e-4|1e-6 / 1.06e-3|

Elmer加密后误差显著下降，三case的h01速度和压力均满足公开atol（无需利用rtol）；ASPECT进一步细化变化也在公开atol内。该证据是本批采样观测的数值合格，非所有允许参数连续范围的严格误差上界证明。

## 输入、输出及评分变体

从DATA独立选32个输入变体，覆盖通用参数端点和nextafter越界、未知model、旧family、多余/缺少三维参数、wedge3D、圆环时间错误、非整数步数、refinement类型/上下界、错误时轴、域外/过近探针、合法单探针、错误输出定义等；全部与公开预期一致。这里修改内存problem后显式调用题内checker，基础结构仍由全量原始load_problem完成，未宣称内存变体覆盖完整CLI解析。

7种实际H5非法输出（缺字段、多字段、float32、NaN、错误ID、错误时间、扁平pressure）全部由真实grade返回invalid_output/0。12case各速度/压力在最大幅值位置按公开阈值0.999/1.001扰动，共48次真实grade，全部预期通过/失败。另用明确标记的临时合成零参考与二进制精确atol=.125/rtol=0核验等号及nextafter两侧3次，确认<=等号语义；临时fixture不混入正式数值资格。

## 来源、生产者和模型迁移身份

原始源码压缩包 d8dbcd698c55c10957bf3971300ef99649e7cd426798efb1e7d083f0ff742a87 内8236原文件与生产source树逐SHA全部一致，无差异。baseline core ede312bb… 与压缩包内原件字节相同，baseline binary bb0deae0…；reference core eeb67502…、binary bdc6993c…；Elmer实际FlowSolve源646bf011…与保留原件一致。公开源码闭包fb58b7d5…独立核验，最终ZIP40成员独立核验。

修复仅涉及core.cc现有约束路径：区分未动/变形切向边界、对后者当前mapping法向重建约束、网格变形后更新约束及必要稀疏结构。相较原上游修复以旧API返回集合做交集适配；没有另写Stokes入口/解析答案/采样修正。GMG没有进入资格结论。

对12case独立导入迁移前后adapter，固定同一输出目录生成PRM并逐字节相等，全部采样input.h5与迁移原件SHA相等，正式reference.h5与原native参考SHA相等。三model更名没有改变求解、采样或参考数据。

公开包在独立target以常规pip构建安装，-I进程仅显式加入已安装目录，caeoj与题内extension均由安装目录导入，包内2样例真实grade=1。证据在configure-judge对应目录installation.json。最终后端环境、编译和Oracle需要按其自身新镜像/新trial封审，数据结论不替代它们。
