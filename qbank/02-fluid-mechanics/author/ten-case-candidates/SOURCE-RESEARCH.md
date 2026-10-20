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

## 2026-10-20续作：新增原生适配

- **Elmer FlowSolver**：固定提交`a19504ac53ec222e3355e182b08f2ff280c2203a`。读取[FlowSolve.F90](https://github.com/ElmerCSC/elmerfem/blob/a19504ac53ec222e3355e182b08f2ff280c2203a/fem/src/modules/FlowSolve.F90)、[MaterialModels.F90](https://github.com/ElmerCSC/elmerfem/blob/a19504ac53ec222e3355e182b08f2ff280c2203a/fem/src/MaterialModels.F90)和[NavierStokes.F90](https://github.com/ElmerCSC/elmerfem/blob/a19504ac53ec222e3355e182b08f2ff280c2203a/fem/src/NavierStokes.F90)。`Laplace Discretization=False`保留完整对称黏性应力；`External Pressure`是完整自然牵引，不能用固定域内静压替代。滑移采用原生法向/切向坐标。
- **Cross和Carreau族**：原生剪切不变量与`g=sqrt(2 D:D)`对应；Cross的`Viscosity Transition=lambda^m`，Carreau为lambda，Yasuda另填a。Elmer幂律只有下剪切截断，不能冒充双截断响应。非牛顿采用原生Picard迭代，没有修改零剪切物理。
- **OpenCFD powerLaw**：[v2512源码](https://api.openfoam.com/2512/powerLaw_8C_source.html)原生对运动黏度作上下截断。`k=(mu_ref/rho)*g_ref^(1-n)`，两个剪切端点对应黏度的最小/最大值作为nuMin/nuMax，与本题双端剪切截断等价；n大于/小于1均处理。周期为原生cyclic，体力为原生vectorSemiImplicitSource。周期定常工况的近零横向速度和压力会使归一化残差受舍入影响；实际停止配置保留在SIF/fvSolution中，不将停止容差称为精度认证。
- **Oldroyd-B**：原生Maxwell的sigma是`-tau_p/rho`；恢复`A=I+lambda*tau_p/mu_p`。只计算2.11.1/2.11.2闭壁分支，不加应力扩散，预应变实际传入sigma。入口构象和完整牵引出口仍未接通。原生FV场用体积加权恢复到内部节点；边界牵引用原生gradU及相邻单元应力，映射误差未评估。
- **低马赫耦合**：[固定HeatSolve.F90](https://github.com/ElmerCSC/elmerfem/blob/a19504ac53ec222e3355e182b08f2ff280c2203a/fem/src/modules/HeatSolve.F90)的`Friction Heat=True`保留黏性耗散，`Volumetric Heat Source`使用W/m3。体力为`[1-beta(T-Tref)]*a_body`，保留基底加速度。mu(T)、k(T)由原生MATC和有限元求解；没有加自编热方程。原生`Heat Flux`向内为正，输入outward_heat_flux取相反号。原生P1物性插值的离散误差未评估。
- **流率和初态映射**：按实际外边界实体平均shape和测度归一化流率，再交原生FE边界处理；连续FE对面常值Dirichlet在相交节点有离散近似，记录为局限。P1势的逐单元curl只负责制造输入；原生FV初始化取同一输入的体积平均，不以自编时间推进制造参考，不作Leray投影。

实际是否完成以执行索引为准。以上配置不能证明全部条目已算完；全部结果只作未验证候选，没有网格加密、交叉验证、判分或资源认证。

- **2.3.1–2.3.4**：固定OpenCFD v2512镜像内原生kOmegaSST、LRR和WALE。稳态LRR局部源试算达到迭代上限，记录保留，改用题面允许的SST生产者；URANS仍用LRR以保留各向同性初始R=2k/3 I，epsilon=Cmu^.75 k^1.5/l。WALE统计由规定的21个实际采样帧作等权总体协方差。LRR动量显式含完整R，p为静压；SST/WALE使用偏应力，转换为静压时减去2rho*k/3后施加题定零均值规范。原生FV均值赋给其共形子单纯形，局部P0体力先按体积映射到原生单元；这些空间近似尚未验证。源码定位为镜像`src/TurbulenceModels/turbulenceModels/RAS/{LRR,kOmegaSST}`、`LES/WALE`、`ReynoldsStress`和`linearViscousStress`。

- **2.5.3/2.5.4**：原生interFoam v2512，零表面张力，两相密度和黏度均严格正。`g=0`，实际共同加速度以原生vectorSemiImplicitSource的`rho*a`进入守恒动量；没有把一流体自由表面题混入。初始纯相单元并集由实际原生网格中心掩膜选择，公共共形子单纯形继承同一0/1指示量。原生FV均值赋子单纯形是未评估的离散近似；p_rgh因g=0即静压，再按题定全域均值规范。20项已实际算完和装配，不代表数值验证。
- **稳态RANS的后续尝试**：SST强松弛和上风生产配置后仍触及迭代上限的7项，以原生kEpsilon再做一次有界计算，改变的是题面允许的闭合选择；保留原尝试，实际闭合、系数和停止原因见逐例记录。没有用最后一个未收敛迭代冒充稳态完成。
- **SPARTA**：[官方项目](https://github.com/sparta/sparta)，镜像版本27Aug2026、固定镜像`sha256:2935438c074847a45e250dcddac72bb3b791540624a5aebe3a52b6b4ab75c2c6`。原生VSS取omega=.5、alpha=1对应硬球极限；free-molecular不启用碰撞。emit/face使用给定储槽Maxwell分布的入射半空间通量，diffuse以给定概率混合镜面/漫反射，保留壁速。compute grid/thermal/grid/pflux/grid/eflux/grid与ave/grid产生原生统计；固定种子、粒子权重、预运行和采样步数保存。当前12个盒形分支在运行，尚未完成公共四面体及壁面参考系交换量装配，不能将原生网格中心矩直接冒充题目节点或壁面输出。非盒形8项仍待适配，未改工况为盒形。
- **继续匹配的能量细节**：固定Elmer FlowSolve支持Reference Temperature理想气体且不必解温度方程，但独立体黏度和封闭质量约束仍需匹配；不能据此笼统宣布全部等温可压缩工况接通。固定DiffuseConvectiveAnisotropic源码需核对可压缩耗散的偏应力项。OpenCFD rhoPimpleFoam原生EEqn含动能和压力功，而完整黏性应力功及源项仍需逐项匹配；只加名为viscousDissipation的源不能未经等价推导就称完整总能量实现。上述源码证据保留Titan，本轮未据这些尚未完成的匹配生成参考。

- **SPARTA曲面续作**：进一步使用现成read_surf的三角形曲面、截切网格、域内/固体分类，接通原8项孔板、弯道、障碍和十字通道。Gmsh仅制造冻结几何的四面体及边界三角形；内部固壁法向反转为指向气体，位于全局盒面的壁面由原生box boundary处理。储槽发射region取实际端口边界顶点包围矩形，未把弯道/十字改成盒形。20项原生计算均已安排；最终公共输出装配仍待完成。
