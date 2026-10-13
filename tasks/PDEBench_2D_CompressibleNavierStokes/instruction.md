# 二维可压缩 Navier–Stokes

数学问题与字段契约在本文及 [DATA.md](DATA.md) 中定义；判例、参考数据、误差阈值、时限、内存及完整样例后续补充。

## 数学问题

定义域为 [0,1]×[0,1] m²。

求密度 ρ、速度 v 和热力学压力 p：

\[\partial_t\rho+\nabla\cdot(\rho v)=0,\]
\[\partial_t(\rho v)+\nabla\cdot(\rho v\otimes v+pI)=\nabla\cdot\tau,\]
\[\partial_tE+\nabla\cdot((E+p)v)=\nabla\cdot(\tau v),\]
\[E=\frac{p}{\gamma-1}+\frac12\rho|v|^2,\qquad
\tau=\eta\left(\nabla v+(\nabla v)^T-\frac23(\nabla\cdot v)I\right)+\zeta(\nabla\cdot v)I.\]

E 为单位体积总能量，γ 为比热比，η、ζ 为常动力剪切和体黏度。没有热传导、体力或额外能量源项。较低维问题按三维气体的不变方向约化，故应力中的 2/3 不改为 2/D。

初始 ρ、v、p 在各单元内分别为给定常数；由它们逐单元构造初始动量与总能量。正密度和正内能为物理解的要求，禁止把原始变量的单元平均值自动解释成“由平均守恒量反算得到的值”。

## 初始与边界条件

两个方向均周期：ρ、v、p 及所需导数周期相等。

## 输入范围

输入遵守[通用数据协议](../../docs/CONTRACT.md)，采用 Gmsh 网格、JSON 元数据和 NPZ 场。采样值的连续含义见 [DATA.md](DATA.md)。

128×128 或 512×512 个等长矩形单元；0≤t≤1 s；所有初始值有限，ρ、p 严格正；(η,ζ)∈{(10⁻⁸,10⁻⁸),(0.01,0.01),(0.1,0.1)}。

| 参数 | 定义与支持值 |
|---|---|
| `gamma` | γ=5/3；单位 `1` |
| `shear_viscosity` | η：本题定义为常动力剪切黏度；单位 `Pa.s` |
| `bulk_viscosity` | ζ：本题定义为常动力体黏度；单位 `Pa.s` |

初值、参数和请求时刻以输入为准；ID 只表示实体身份，不表示空间次序。

程序自行选择语言、库、空间离散、内部固定/自适应时间步及收敛策略；不得改变方程、域、条件、单位或输出时刻。

## 输出与提交

接口：`python solve.py --input problem.json --output result.npz`。Python 入口可以调用其他语言实现，题面不要求核心计算使用 Python。

输出 `density[T,N,1]`（kg/m3）、`velocity[T,N,2]`（m/s）、`pressure[T,N,1]`（Pa），并原样附带输入的 IDs 和 `times`；N 为要求输出的位置数量，T 为请求时刻数。字段均为 float64，具体 quantity、location、value_kind、分量顺序和时间轴见 [DATA.md](DATA.md)。

判分规则与误差阈值：**后续补充**。测试点数、执行时限、内存及完整输入输出样例：**后续补充**。目前不能将该目录作为可发布、可判分任务使用。
