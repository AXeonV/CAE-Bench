# 一维可压缩 Navier–Stokes

本文与 [DATA.md](DATA.md) 共同定义求解要求。DATA.md 中的字段、位置、数组关联和采样规则也是题目的一部分。

## 数学问题

定义域为 [-1,1] m。

求密度 ρ、速度 v 和热力学压力 p：

\[\partial_t\rho+\nabla\cdot(\rho v)=0,\]
\[\partial_t(\rho v)+\nabla\cdot(\rho v\otimes v+pI)=\nabla\cdot Q,\]
\[\partial_tE+\nabla\cdot((E+p)v)=\sum_j\partial_j\!\left(\sum_i v_i Q_{ij}\right),\]
\[E=\frac{p}{\gamma-1}+\frac12\rho|v|^2,\qquad
Q_{ij}=\rho\left[\eta+\left(\zeta+\frac{\eta}{3}\right)\delta_{ij}\right]\partial_jv_i.\]

Q 为黏性动量通量张量，(∇·Q)_i=∑_j∂_jQ_ij；I 为本题空间维数的单位矩阵。i、j 遍历本题空间维数，δ_ij 为 Kronecker 符号。E 为单位体积总能量，γ 为比热比，η、ζ 为固定运动学黏性系数（m²/s）。这是密度加权、按方向定义的 黏性模型；不添加未给出的交叉导数或热传导项。

初始 ρ、v、p 在各单元内分别为给定常数，由它们构造初始守恒量。记平均_K(f)=|K|⁻¹∫_K f，矢量按分量平均；|K| 为原输入单元 K 的长度、面积或体积。以下“平均”均指平均_K。输出采用守恒量的单元平均后反算的状态：ρ_out=平均(ρ)，v_out=平均(ρv)/ρ_out，p_out=(γ−1)[平均(E)−|平均(ρv)|²/(2ρ_out)]。这些定义在 t=0 与输入相同；在非均匀场中 v_out 和 p_out 无须等于 v、p 的体积平均值。

## 初始与边界条件

周期配置：两端的 ρ、v、p 及所需导数周期相等。外推配置：两端 ∂_nρ=∂_nv=∂_np=0，黏性通量采用同一零梯度条件；不施加反射或固定环境压力。初值为随机场或分片常数激波管。

## 输入范围

输入遵守[通用数据协议](../../docs/CONTRACT.md)，采用 Gmsh 网格、JSON 元数据和 HDF5 场。采样值的连续含义见 [DATA.md](DATA.md)。

1024 个等长线单元；周期条件下 0≤t≤1 s，外推条件下 0≤t≤2 s。所有初始值有限，ρ、p 严格正。周期条件允许 (η,ζ)∈{(10⁻⁸,10⁻⁸),(0.01,0.01),(0.1,0.1)}，外推条件仅允许 (η,ζ)=(10⁻⁸,10⁻⁸)。

| 参数 | 定义与支持值 |
|---|---|
| `gamma` | γ=5/3；单位 `1` |
| `shear_viscosity` | η：密度加权定向模型的运动学剪切系数；单位 `m2/s` |
| `bulk_viscosity` | ζ：密度加权定向模型的运动学体系数；单位 `m2/s` |

初值、参数和请求时刻以输入为准；ID 只表示实体身份，不表示空间次序。

程序自行选择语言、库、空间离散、内部固定/自适应时间步及收敛策略；不得改变方程、域、条件、单位或输出时刻。

## 输出与提交

接口：`python solve.py --input problem.json --output result.h5`。Python 入口可以调用其他语言实现，题面不要求核心计算使用 Python。

输入中的包内文件路径相对 `problem.json` 所在目录解析。读取 JSON 声明的文件和数组引用；按每个输出的 `location` 与 `time_axis` 排列空间行和时间行，将结果写入其 `array` 指定的 HDF5 键。IDs 和时间轴原样复制，结果保存到 `--output` 指定路径。

输出 `density[T,N,1]`（kg/m3）、`velocity[T,N,1]`（m/s）、`pressure[T,N,1]`（Pa），并原样附带输入的 IDs 和 `times`；N 为要求输出的位置数量，T 为请求时刻数。字段均为 float64，具体 quantity、location、value_kind、分量顺序和时间轴见 [DATA.md](DATA.md)。

公开输入输出样例位于 `samples/01/` 与 `samples/02/`，数值文件在数据准备后提供。判分规则、误差阈值、执行时限及内存限制：**后续补充**。当前尚未接入评测。
