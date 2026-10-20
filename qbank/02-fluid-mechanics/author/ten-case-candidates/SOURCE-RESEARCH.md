# 现成生产者匹配记录

以下是目前实际查到的候选实现及匹配限制，不是“这些题均已匹配”的结论。
Titan固定镜像的完整部署记录保存在独立工作目录的maintenance中。实际状态另见[EXECUTION.md](EXECUTION.md)。
镜像存在、模块同名或最小安装自检通过，都不能当作本题方程已经匹配。

| 实现 | 已定位的内容 | 对本批的意义及尚未解决的限制 |
|---|---|---|
| [OpenCFD OpenFOAM](https://gitlab.com/openfoam/core/openfoam)，v2512 | Titan镜像内存在`icoFoam`及`incompressible/icoFoam/cavity/cavity`原生教程；镜像ID见index.json | 常密度、层流、不可压缩瞬态闭腔已接通，实际状态见执行索引。压力从运动学压力转换为Pa并按DATA体积均值定规。速度入口/牵引出口的其他设计不能直接套用固定静压和速度零梯度的普通出口。 |
| [OpenFOAM Maxwell源码](https://api.openfoam.com/2512/Maxwell_8C_source.html)和[平面Poiseuille教程](https://doc.openfoam.com/2306/examples/verification-validation/laminar/planar-poiseuille/) | Oldroyd-B相关Maxwell实现；Titan镜像中保留`src/TurbulenceModels/turbulenceModels/laminar/Maxwell/Maxwell.C` | 为2.11.1/2.11.2提供现成实现候选。仍需核对应力/构象变量恢复、入口构象、完整牵引及初态，不能据此声称热黏弹题也匹配。 |
| [Basilisk centered Navier–Stokes](https://basilisk.fr/src/navier-stokes/centered.h)、[two-phase](https://basilisk.fr/src/two-phase.h)、[log-conform](https://basilisk.fr/src/log-conform.h) | Titan存在centered.h、log-conform.h、saint-venant.h，固定快照见index.json | 两流体、黏弹与浅水的候选。自由表面题要求气体无惯性无黏性且不求气相动量，不能用小但非零气相物性静默替换。润湿题还须匹配物理Navier滑移。 |
| [Elmer ReynoldsSolver固定源码](https://github.com/ElmerCSC/elmerfem/blob/a19504ac53ec222e3355e182b08f2ff280c2203a/fem/src/modules/ReynoldsSolver.F90) | 原生气膜分支已匹配到镜像构建提交。另有incompressible选项，黏度分支为newtonian/rarefied | 气膜实际生产说明见下文。不能由此推及Elrod–Adams空化、跨隙Carreau BVP或题目特定均温热液膜闭合。 |
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

## 本轮实际接通的生产者

- **icoFoam，OpenCFD v2512固定镜像**：实际执行2.1.2/2.1.4的6项闭腔。原生源代码、版本横幅、配置、完整日志与输出保留在Titan。前表中其他OpenFOAM模块仍是候选，不能由这6项推及其余题。
- **文献公式**：[Chandrashekar、Zenk，arXiv:1511.08739v2](https://arxiv.org/abs/1511.08739)，§2.1.2和§3.1。按其多方静水平衡关系求值2.2.5/2.2.7的20项，取多方指数为gamma、K由本题Tref/rhos确定；标量常数按质量库存归一化。三维是同一静水平衡关系的几何延伸，并非声称论文公开了这20个工况。实际输入体力为连续P1势的逐单元负梯度，参考对相同分片势按8点Gauss/Duffy积分取单元平均。保存PDF摘要、生产脚本和归一化常数；没有积分误差认证。
- **rhoCentralFoam，OpenCFD v2512固定镜像**：使用镜像内原生`forwardStep`教程的无黏理想气体模型配置及Kurganov通量。`mu=0, Pr=1`，无黏性和热导；γ=1.4、R=287。用于无外源的18个封闭滑移Euler瞬态，另外2个加速度源工况尚未接通。初密度/温度按实际原生单元取8点张量Gauss输入平均；压力由实际输入状态关系确定。输出按同一单元ID顺序转换，不把单元场冒充节点点值。
- **Elmer ReynoldsSolver，release-26.2.1**：固定源码提交`a19504ac53ec222e3355e182b08f2ff280c2203a`，镜像ID见index。已下载该固定提交的原始源码并保留摘要。`isothermal ideal gas`分支的密度因子为绝对p；质量矩阵系数为−h、压力扩散系数为−p h³/(12μ)，`Surface Velocity=U0+U1`、`Normal Velocity=∂t h`；整体1/(R Tref)相消，匹配本题气膜质量方程。使用原生MATC输入函数在节点求值，随后由原生P1形函数重建；没有新增求解器模块。输出压力/密度为真实节点近似，通量采用面积加权恢复梯度，载荷为P1场面积积分；恢复梯度和8位原生VTU输出均无精度认证。

完整输入/参考包实际存在与数值正确分开记录，本轮没有网格加密、独立比对或判分验证。
