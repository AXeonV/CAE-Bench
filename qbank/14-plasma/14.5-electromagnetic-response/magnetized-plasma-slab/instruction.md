# 14.5.2 分层磁化等离子体单频响应

实现可复用求解器，覆盖[DATA](DATA.md)声明的整个问题族。提交冻结后处理多个未见算例，不按某个几何、初态或参数固定输出。

采用Re[F(x)exp(−iωt)]。层从x=0依次到H=Σh，两侧为相同ε、μ的无等离子体半空间，无右入射。背景磁场Bx沿+x且全空间恒定。每层的横向u满足m(ν−iω)u=q(E+u×Bx e_x)，J=n q u；纵向场和速度为零。Maxwell为∇×E=iωμH场、∇×H场=J−iωεE；界面Ey、Ez、Hy、Hz连续，无自由面电流。入射／反射振幅定义于x=0，透射振幅定义于x=H。左侧E=Ei exp(ikx)+Er exp(−ikx)，右侧E=Et exp(ik(x−H))，k=ωsqrt(εμ)，波阻抗Z=sqrt(μ/ε)，各行波H场=传播单位方向×E/Z。R=|Er|²/|Ei|²，T=|Et|²/|Ei|²，不按各偏振分别除入射分量。输出层内场包含所有反射与透射；不求随机粒子、热运动、非线性密度或纵向电静波。

模型及材料响应由题目固定，考生负责内部离散、求积、积分、线性／非线性求解与精度控制；语言和软件自由。覆盖完整契约的解析或降阶实现同样有效。输入字段和所有算例变化、输出定义见DATA，通用读写见[CONTRACT](../../../../docs/CONTRACT.md)。

## 运行与资源

入口`python solve.py --input /path/problem.json --output /path/result.h5`，可用此入口封装C++等实现。每例Linux AMD64，180秒墙钟（包含启动与I/O）、2个逻辑CPU、2048MB、0GPU。程序正常退出并写完HDF5；无独立输出字节上限，内存和DATA规模限制仍适用。逐例求解环境不联网；生成程序阶段网络由运行环境提供。

Agent生成预算3600秒，镜像构建预算1800秒。环境提供Python3、NumPy、SciPy、h5py、Gmsh、jsonschema及C++、OpenMP、OpenMPI、HDF5开发库，不要求使用Python。仅保证串行HDF5写出，可用MPI计算后由一个进程汇总。稳态／单频输出轴仅作存储标记。 输入规模见DATA；资源与阈值是设计目标，正式数据阶段另行校准。

## 评分

每例正常退出、输出结构合法且全部quantity、时刻、对象和分量均满足`|结果−参考|≤atol+rtol·|参考|`得1分，否则0分；等号接受，未通过分量不作豁免。不做去均值、相位对齐、自动重排或最佳拟合。

| quantity | atol | rtol | 单位 |
|---|---|---|---|
| `reflected_amplitude` | 1e-07 | 0.003 | `V/m` |
| `transmitted_amplitude` | 1e-07 | 0.003 | `V/m` |
| `electric_amplitude` | 1e-07 | 0.003 | `V/m` |
| `magnetic_amplitude` | 1e-09 | 0.003 | `A/m` |
| `reflectance` | 1e-07 | 0.003 | `1` |
| `transmittance` | 1e-07 | 0.003 | `1` |

总成绩为通过有效例数／有效例数。输入、参考、配置或判题工具错误属于基础设施错误，不计考生失分；无有效例不产生成绩。校验工具只检查契约，不检查方程是否求对。
