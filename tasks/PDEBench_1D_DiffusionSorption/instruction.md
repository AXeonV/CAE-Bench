# 一维 Freundlich 迟滞扩散

数学问题与字段契约在本文及 [DATA.md](DATA.md) 中定义；判例、参考数据、误差阈值、时限、内存及完整样例后续补充。

## 数学问题

定义域为 [0,1] m。

求非负归一化浓度 c：

\[R_\varepsilon(c)\partial_tc=D\partial_{xx}c,\qquad
R_\varepsilon(c)=1+\frac{1-\phi}{\phi}\rho_s k_f n_f(c+\varepsilon)^{n_f-1}.\]

φ 为孔隙率，ρ_s 为固相密度，k_f、n_f 为 Freundlich 参数，ε 为固定正则化浓度。浓度以入口浓度尺度归一化。c=0 时采用上述有限的 R_ε(0)，不把负浓度裁剪成零来改变方程。

## 初始与边界条件

设输入原网格单元宽 h=1/1024 m，C_i(t) 是连续浓度在第 i 个原单元上的平均值，按几何从左向右编号 i=1,…,1024（不按 ID 推断）。采用以下非局部边界值：

\[c(0,t)=\tfrac12(c_{in}+C_1(t)),\qquad
c(1,t)=\tfrac12\left[C_{1024}(t)-\frac{\ell}{h}(C_{1024}(t)-C_{1023}(t))\right].\]

c_in=1，ℓ 为输入给出的出口耦合长度。条件在 t>0 生效，t=0 取输入常数初值。这里的 C_i 由原始输出单元定义，即使程序使用另一张内部网格，也按原单元积分。程序可自主选择空间与时间数值方法。

## 输入范围

输入遵守[通用数据协议](../../docs/CONTRACT.md)，采用 Gmsh 网格、JSON 元数据和 NPZ 场。采样值的连续含义见 [DATA.md](DATA.md)。

1024 个等长线单元；0≤t≤500 s；整域初始浓度为 [0,0.2] 中一个常数；只支持参数表中的固定物理配置。

| 参数 | 定义与支持值 |
|---|---|
| `diffusivity` | D=5×10⁻⁴；单位 `m2/s` |
| `porosity` | φ=0.29；单位 `1` |
| `solid_density` | ρ_s=2880；单位 `kg/m3` |
| `freundlich_coefficient` | k_f=3.5×10⁻⁴，针对本题归一化浓度；单位 `m3/kg` |
| `freundlich_exponent` | n_f=0.874；单位 `1` |
| `concentration_shift` | ε=10⁻⁶；单位 `1` |
| `inlet_concentration` | c_in=1；单位 `1` |
| `outlet_length` | ℓ=5×10⁻⁴，出口耦合长度；单位 `m` |

初值、参数和请求时刻以输入为准；ID 只表示实体身份，不表示空间次序。

程序自行选择语言、库、空间离散、内部固定/自适应时间步及收敛策略；不得改变方程、域、条件、单位或输出时刻。

## 输出与提交

接口：`python solve.py --input problem.json --output result.npz`。Python 入口可以调用其他语言实现，题面不要求核心计算使用 Python。

输出 `concentration[T,N,1]`（1），并原样附带输入的 IDs 和 `times`；N 为要求输出的位置数量，T 为请求时刻数。字段均为 float64，具体 quantity、location、value_kind、分量顺序和时间轴见 [DATA.md](DATA.md)。

判分规则与误差阈值：**后续补充**。测试点数、执行时限、内存及完整输入输出样例：**后续补充**。目前不能将该目录作为可发布、可判分任务使用。
