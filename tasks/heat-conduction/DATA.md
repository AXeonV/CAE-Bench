# 热传导题的输入说明

本题使用[通用数据协议](../../docs/CONTRACT.md)。这里仅规定本题的字段和数学含义，不增加协议字段。

## 文件与参数

输入由 `problem.json`、Gmsh `mesh.msh`、NumPy `input.npz` 组成，可附 `mesh.geo`。

`physics.parameters` 给出 `conductivity=k`、`x0`、`y0`、`length_x=Lx`、`length_y=Ly`。若四边全为法向导数／热流，还给 `mean_temperature`，表示 `∫Ω T dΩ / |Ω|`，不是节点平均温度。稳态时间轴为 `times=float64([0.0])`。

Physical Groups：域 `(2,1)`，左/右/下/上 `(1,2)/(1,3)/(1,4)/(1,5)`；对应位置名为 `domain/left/right/bottom/top`，位置实体均为 element。输出位置 `nodes` 包含全部网格节点。各字段行序对应其位置的递增 IDs，tag 可以不连续。

## 源项与边界函数

令 `u=(x−x0)/Lx`，`v=(y−y0)/Ly`。

源项条件 `role=source`、`location=domain`、`operator=polynomial`，`data.coefficients.field` 指向 C，定义：

`q(x,y)=Σ C[i,j]u^i v^j`，i,j=0,1,2，i+j>2 的系数为零。

每条边恰有一条 `role=boundary` 条件，`operator` 取题面四种之一，`data.coefficients.field` 指向 c，定义：

`g(s)=Σ c[i]s^i`，i=0,…,4。左右边 **s=v**，上下边 **s=u**，与线段连接方向无关。向外法向分别为 left=(−1,0)、right=(1,0)、bottom=(0,−1)、top=(0,1)。Robin 的 `data.alpha`、`data.beta` 是带单位的常数。

系数采用 NumPy [`numpy.polynomial.polynomial`](https://numpy.org/doc/stable/reference/generated/numpy.polynomial.polynomial.polyval2d.html) 的**升幂顺序**。源项数组 shape `[1,域三角形数,3,3]`，标签 `c00,c01,c02,c10,…,c22`；每条边的数组 shape `[1,边线段数,5]`，标签 `c0,…,c4`。字段为 `kind=components`、`value_kind=average`，单位同 q 或 g。

所有域单元的 C 相同，同一边各线段的 c 相同。常系数的单元平均就是该系数；它们定义**连续多项式，不是函数采样值**。例如 C[0,0]=2、C[1,0]=3、C[0,1]=−1，其余为零，表示 `q=2+3u−v`；c=[1,2,0,0,0] 表示 `g=1+2s`。

Dirichlet 角点值保证一致。角点邻接 Dirichlet 和其他边时，节点温度取 Dirichlet 值，其他条件施加于对应边的内部，不额外施加角点方程。

## 输出与诊断

输出 NPZ 只包含 `node_ids`、`times`、`temperature`。前两者原样复制输入；温度为 float64，shape `[1,节点数,1]`，按 `node_ids` 行序，单位 K。

可用 `caeoj validate-input problem.json` 和 `caeoj validate-output --input problem.json --output result.npz` 检查读写格式。它们只检查结构，不验证物理、参数范围、条件相容性或纠正答案。
