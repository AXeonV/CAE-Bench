# 2.1.3 补充算例维护

`supplement.py` 定义 100 个候选工况并生成契约输入；`native.py` 生成原生求解器配置、运行及转换结果。二者不自行离散或求解动量／连续性方程。

## 工况与来源

本批工况由作者按题目范围配置，采用静水平衡、平行剪切流、周期驱动流、三维壁面驱动腔及直通流五类。障碍物布局是本批定义的几何，不声称复现某篇文献的数值数据。参考生产者是 Elmer 的原生 `FlowSolve/FlowSolver`，独立验证者是 OpenFOAM 的原生 `simpleFoam`；不是借用其名称包装自编求解器。

| 候选编号 | 数量 | 主要考查差异 |
|---|---:|---|
| 001–018 | 18 | 体加速度与静压、自然边界／封闭域、线性／仿射加速度、压力基准 |
| 019–038 | 20 | 单／双运动壁、三分量剪切、周期边界／剪切牵引、压力与剪切／载荷输出 |
| 039–058 | 20 | 体加速度驱动、滑移／对称／无滑移侧壁、运动壁叠加、四种障碍物布局 |
| 059–082 | 24 | 三维单／双壁驱动、非均匀壁速、长宽比与雷诺数、障碍物／挡板 |
| 083–100 | 18 | 速度／总流率入口、压力／牵引出口、流率归一化、流入流出符号与密度换算 |

材料及尺度系列用于比较黏性主导与惯性影响、动力／运动黏度、静压及载荷尺度；坐标旋转、单元类型与输出位置变化覆盖接口。坐标变化本身不算新增物理家族。实际目录由 `catalog` 导出，验证状态以逐例计算记录为准，候选数量不代表全部验证通过或覆盖题面任意组合。

## 求解器依据

- **Elmer 26.2.1**：[固定源码](https://github.com/ElmerCSC/elmerfem/tree/a19504ac53ec222e3355e182b08f2ff280c2203a)、[FlowSolve](https://github.com/ElmerCSC/elmerfem/blob/a19504ac53ec222e3355e182b08f2ff280c2203a/fem/src/modules/FlowSolve.F90)、[模型手册](https://www.nic.funet.fi/pub/sci/physics/elmer/doc/ElmerModelsManual.pdf)。使用完整 Navier–Stokes 模型、稳定化有限元与原生非线性迭代。Fortran 回调只读取给定边界／源项表。
- **OpenFOAM OpenCFD 2512**：[发行说明](https://www.openfoam.com/news/main-news/openfoam-v2512)、[simpleFoam 官方说明](https://doc.openfoam.com/2306/tools/processing/solvers/rtm/incompressible/simpleFoam/)。采用稳态不可压缩层流 SIMPLE；原生运动学压力转换为 Pa。具体镜像摘要固定在脚本中，实际执行记录保存输入与输出摘要。

两者共享几何定义与格式转换代码，离散及迭代实现不同。对可用的经典平衡／平行流另做解析一致性检查；这些公式只用于附加验证，不替代原生求解器生产参考。三维腔流及障碍物没有借用未经实际取得的文献曲线。

## 复现

在已经配置求解器工具集的机器上运行；`--solvers` 指向包含 `solver.py` 的工具集目录，输出放在忽略目录。

```sh
python <task>/author/supplement.py catalog --output runs/2-1-3/catalog.json
python <task>/author/supplement.py inputs --output runs/2-1-3/inputs
python <task>/author/supplement.py run --output <solver-workspace> --solvers <solver-images> --workers 20 --native-timeout 3600 --native-cpus 2 --native-memory 4g
python <task>/author/test_native.py
```

`--only 4 5` 可重算指定候选编号，`--workers` 控制同时计算的算例数。`--native-*` 是每次原生求解的作者侧预算，与考生资源限制分开；并发数须适合宿主机的实际 CPU 和内存余量。两个求解器及调度进程的 BLAS／OpenMP 均保持单线程，可在启动前设置 `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1`。原生计算目录必须可由求解器容器挂载。输入完全相同、镜像一致且通过当前收敛与压力约束检查的原生记录才可复用。

## 验证与适用边界

生成目录包含 `cases/`、`reference/`，计算证据在工作目录 `evidence/`。参考由 Elmer 生成，OpenFOAM 生成完整独立输出并交实际逐 case 判分器；另检查错误速度输出会失分。只将通过独立比对及精度预留检查的候选计为通过；失败记录不得混作就绪数据。`audit.py` 对全部输入检查接口、原生 Gmsh Jacobian、体积、封闭边界与覆盖计数，结果结构与数值资格分别记录。

原生计算网格可比契约输入细，输出按声明重建并恢复压力基准。自然牵引向 OpenFOAM 的压力／零法向速度梯度转换仅用于相容的平衡／平行流工况，不是任意牵引的通用适配器。对于保守体加速度，OpenFOAM 使用 `p/ρ=q+Φ`、`∇Φ=a` 的等价变量变换，原生求解 q 与速度，转换时恢复静压；原生配置保存 Φ 的定义。Elmer 仍求完整体力与压力，不使用该变换。非均匀腔壁速度按实际输入的 P1 场读取，不以另一光滑函数替换。

封闭域的数值压力固定点选择实际流体内部节点，避开周期与壁面约束交点；除更新量外还核查原生压力固定值。OpenFOAM 的边界法向逐面按原生几何计算，障碍物集合不假定共用一个法向；边界迹恢复按实际平面定位，不把边界编号当坐标轴。有限体积均压直接使用有效流体单元值，避免孔洞插值掩码污染。配置与转换异常保存调用栈，不因加密网格盲目重试。`test_native.py` 覆盖全部 100 个候选的原生配置、压力固定点、旋转梯度及全部障碍物候选的字段转换，实际数值资格仍由双求解器计算确定。

两套数值方法吻合并不证明连续真解精确；共享几何／转换错误仍需接口审计排查。障碍物附近的采样不能跨越固体插值。正式资源可行性与本批参考资格应分别审核，不能只凭原生程序成功退出就宣布题库就绪。

制池及隔离装配复用[现有数据管理流程](../../../../maintenance/DATA-SYNC.md)，通过 HF 原生 PR 引用发布。固定提交与核验状态见[发布记录](data-evidence/supplement/publication.json)；[暂存选样](data-evidence/supplement/selection.json)仅用于本批验证，不修改正式测试或样例选择。

之后从暂存选样读取 case ID，按发布记录的固定提交生成新的运行选择：

```sh
python -m caeoj_tools.cli data select --task newtonian-incompressible-steady-3d --manifest <task>/author/data-evidence/supplement/selection.json --revision <HF固定提交> --case '001=<case-id>' --output runs/2-1-3-selection.json
```

该命令只选样，不运行模型；后续按评测流程审核选择、装配和冻结。
