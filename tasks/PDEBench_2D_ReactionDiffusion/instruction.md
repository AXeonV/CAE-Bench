# 二维 FitzHugh–Nagumo 反应扩散

本文与 [DATA.md](DATA.md) 共同定义求解要求。DATA.md 中的字段、位置、数组关联和采样规则也是题目的一部分。

## 数学问题

定义域为 [-1,1]×[-1,1] m²。

求无量纲激活量 u 和抑制量 v：

\[\partial_tu=D_u\Delta u+a(u-u^3-k-v),\qquad
\partial_tv=D_v\Delta v+b(u-v).\]

D_u、D_v 为扩散系数，a、b 为反应速率，k 为反应偏置。

## 初始与边界条件

四边均为零法向通量：−D_u∇u·n=−D_v∇v·n=0。初值为输入给出的两个分片常数场；允许正负值。

## 输入范围

输入遵守[通用数据协议](../../docs/CONTRACT.md)，采用 Gmsh 网格、JSON 元数据和 HDF5 场。采样值的连续含义见 [DATA.md](DATA.md)。

512×512 个等长矩形单元提供完整初值；输出选择其中 128×128 个细单元，选择由 domain 的 IDs 明确给出；0≤t≤5 s；两个初始场均有限，允许正负值；只支持参数表中的固定配置。

| 参数 | 定义与支持值 |
|---|---|
| `activator_diffusivity` | D_u=10⁻³；单位 `m2/s` |
| `inhibitor_diffusivity` | D_v=5×10⁻³；单位 `m2/s` |
| `reaction_offset` | k=5×10⁻³；单位 `1` |
| `activator_rate` | a=1；单位 `1/s` |
| `inhibitor_rate` | b=1；单位 `1/s` |

初值、参数和请求时刻以输入为准；ID 只表示实体身份，不表示空间次序。

程序自行选择语言、库、空间离散、内部固定/自适应时间步及收敛策略；不得改变方程、域、条件、单位或输出时刻。

## 输出与提交

接口：`python solve.py --input problem.json --output result.h5`。Python 入口可以调用其他语言实现，题面不要求核心计算使用 Python。

输入中的包内文件路径相对 `problem.json` 所在目录解析。读取 JSON 声明的文件和数组引用；按每个输出的 `location` 与 `time_axis` 排列空间行和时间行，将结果写入其 `array` 指定的 HDF5 键。IDs 和时间轴原样复制，结果保存到 `--output` 指定路径。

输出 `activator[T,N,1]`（1）、`inhibitor[T,N,1]`（1），并原样附带输入的 IDs 和 `times`；N 为要求输出的位置数量，T 为请求时刻数。字段均为 float64，具体 quantity、location、value_kind、分量顺序和时间轴见 [DATA.md](DATA.md)。

公开输入输出样例位于 `samples/01/` 与 `samples/02/`，数值文件在数据准备后提供。判分规则、误差阈值、执行时限及内存限制：**后续补充**。当前尚未接入评测。
