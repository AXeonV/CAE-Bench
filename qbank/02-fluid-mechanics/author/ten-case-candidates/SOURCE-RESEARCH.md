# 现成生产者匹配记录（未完成）

以下是目前实际查到的候选实现及匹配限制，不是“这些题均已匹配”的结论。
Titan固定镜像的完整部署记录保存在独立工作目录的maintenance中。
镜像存在、模块同名或最小安装自检通过，都不能当作本题方程已经匹配。

| 实现 | 已定位的内容 | 对本批的意义及尚未解决的限制 |
|---|---|---|
| [OpenCFD OpenFOAM](https://gitlab.com/openfoam/core/openfoam)，v2512 | Titan镜像内存在`icoFoam`及`incompressible/icoFoam/cavity/cavity`原生教程；镜像ID见index.json | 适用于常密度、层流、不可压缩瞬态闭腔。压力需要从运动学压力转换为Pa并按DATA体积均值定规。尚未执行本批参考计算。速度入口/牵引出口的其他草案不能直接套用固定静压和速度零梯度的普通出口。 |
| [OpenFOAM Maxwell源码](https://api.openfoam.com/2512/Maxwell_8C_source.html)和[平面Poiseuille教程](https://doc.openfoam.com/2306/examples/verification-validation/laminar/planar-poiseuille/) | Oldroyd-B相关Maxwell实现；Titan镜像中保留`src/TurbulenceModels/turbulenceModels/laminar/Maxwell/Maxwell.C` | 为2.11.1/2.11.2提供现成实现候选。仍需核对应力/构象变量恢复、入口构象、完整牵引及初态，不能据此声称热黏弹题也匹配。 |
| [Basilisk centered Navier–Stokes](https://basilisk.fr/src/navier-stokes/centered.h)、[two-phase](https://basilisk.fr/src/two-phase.h)、[log-conform](https://basilisk.fr/src/log-conform.h) | Titan存在centered.h、log-conform.h、saint-venant.h，固定快照见index.json | 两流体、黏弹与浅水的候选。自由表面题要求气体无惯性无黏性且不求气相动量，不能用小但非零气相物性静默替换。润湿题还须匹配物理Navier滑移。 |
| [Elmer ReynoldsSolver](https://raw.githubusercontent.com/ElmerCSC/elmerfem/devel/fem/src/modules/ReynoldsSolver.F90) | 官方源码列出incompressible、isothermal ideal gas等压缩性选项；黏度模型分支为newtonian/rarefied。Titan存在ReynoldsSolver.so | 可能用于部分满膜液膜及气膜。仅凭ReynoldsSolver存在不能承诺Elrod–Adams空化、跨隙Carreau BVP或题目特定均温热液膜闭合。上游devel源码尚未和镜像构建源码逐行对齐，不能作为已固定生产者。 |
| [Clawpack/GeoClaw示例目录](https://www.clawpack.org/gallery/) | 单层/多层浅水参考实现及算例；固定镜像见index.json | 须进一步匹配线性摩擦、双层相间摩擦及公开边界。本题双层只允许完整超临界入/出流，不得套用亚临界储槽。 |
| [PICLas DSMC](https://piclas.readthedocs.io/en/stable/userguide/features-and-models/DSMC.html)与[粒子边界](https://piclas.readthedocs.io/en/stable/userguide/features-and-models/BC-particle-solver.html)，4.3.0 | VHS/碰撞设置、Maxwell漫反射/镜面混合壁等原生功能；固定镜像见index.json | 是硬球Boltzmann/无碰撞分子题候选；须把硬球参数、三维速度分布、半空间储槽及禁止碰撞的分支对应清楚，不能以BGK代替。 |

## 明确需要继续查找的闭合

- 2.7.4：题目规定带核率移位的压力线性蒸发/冷凝源；不能把常见空化模型名称相似当作等价。
- 2.8.4：题目要求局部跨隙Carreau向量BVP并积分流量，不能只传一个有效黏度给牛顿Reynolds方程。
- 2.6：公开对象是Euler体积分数和表观相通量，dense题另有指定拥挤压强及黏度；离散颗粒轨迹不是这些字段的直接参考。
- 2.7.2：要求尖锐界面法向速度跳跃、反冲牵引和完整焓跳跃，普通共速Lee体积源不能替换。
- 2.11.5：热源含构象自由能松弛项，同时温移两黏度及松弛时间；不能默认全部聚合物应力功均转化为热。

上述记录不证明没有其他现成实现；当前只是尚未完成匹配。
按用户选择继续寻找，确实匹配不到的条目暂缓，不自行扩展物理模块。
