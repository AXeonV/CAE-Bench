# 二维稳态不可压缩流测试点与标答（出题材料）

本文件与 [DESIGN.md](DESIGN.md) 仅供出题使用，不进入解题材料。输入只含条件与场数据，不含下列配方或参考公式。

ν=μ/ρ；速度单位 m/s、压力 Pa、加速度 m/s²、时间 s。P 表示相对边周期连接；D 表示给定速度。所有点采用面积平均压力为零。
通道取跨壁坐标 s∈[0,H]、z=s/H、流向单位向量 e；`q∞=U₀+(U₁−U₀)z+aH²z(1−z)/(2ν)`，`u∞=e q∞`、`p=0`。

方腔使用 Ghia 1982 Re=100 的已发表中线数据；按壁速、尺度、旋转或反射变换坐标与矢量分量。只比较所发表的中线分量，不生成全场或压力标答。来源和表格见 [DESIGN.md](DESIGN.md#ghia-方腔中线)。

## 测试点总览

| 测试点 | 类型／主要变化 | 左／右／下／上 | ν / ρ | 域 (x₀,y₀; Lx,Ly) | 节点／三角形 |
|---|---|---|---|---|---|
| 01-rest | 通道 | P/P/D/D | 0.01 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 25 / 32 |
| 02-couette | 通道 | P/P/D/D | 0.01 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 1089 / 2048 |
| 03-poiseuille | 通道 | P/P/D/D | 0.01 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 1089 / 2048 |
| 04-couette-poiseuille | 通道 | P/P/D/D | 0.01 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 4225 / 8192 |
| 05-reverse-pressure-drive | 通道 | P/P/D/D | 0.01 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 1089 / 2048 |
| 06-counter-moving-walls | 通道 | P/P/D/D | 0.01 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 1089 / 2048 |
| 07-vertical-channel | 通道 | D/D/P/P | 0.01 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 1089 / 2048 |
| 08-long-shifted-channel | 通道 | P/P/D/D | 0.005 / 1.0 | (-1, 2); (2, 0.5) | 1089 / 2048 |
| 09-sparse-channel | 通道 | P/P/D/D | 0.01 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 2401 / 4608 |
| 10-density-viscosity | 通道 | P/P/D/D | 0.02 / 2 | (0.0, 0.0); (1.0, 1.0) | 1089 / 2048 |
| 11-low-re-channel | 通道 | P/P/D/D | 0.05 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 1089 / 2048 |
| 12-opposing-shear-and-drive | 通道 | P/P/D/D | 0.01 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 1089 / 2048 |
| 13-cavity-32 | 方腔 top + | D/D/D/D | 0.01 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 1089 / 2048 |
| 14-cavity-48 | 方腔 top + | D/D/D/D | 0.01 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 2401 / 4608 |
| 15-cavity-64-sparse | 方腔 top + | D/D/D/D | 0.01 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 4225 / 8192 |
| 16-cavity-scaled-shifted | 方腔 top + | D/D/D/D | 0.01 / 2 | (1, -2); (2, 2) | 2401 / 4608 |
| 17-zero-net-flux | 通道 | P/P/D/D | 0.01 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 2401 / 4608 |
| 18-interior-reversal | 通道 | P/P/D/D | 0.01 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 4225 / 8192 |
| 19-moving-both-driven | 通道 | P/P/D/D | 0.01 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 2401 / 4608 |
| 20-vertical-negative | 通道 | D/D/P/P | 0.01 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 2401 / 4608 |
| 21-wide-cross-section | 通道 | P/P/D/D | 0.02 / 1.0 | (0.0, 0.0); (0.5, 2) | 4225 / 8192 |
| 22-thin-driven-channel | 通道 | P/P/D/D | 0.005 / 0.5 | (0.0, 0.0); (2, 0.5) | 2401 / 4608 |
| 23-weak-drive | 通道 | P/P/D/D | 0.05 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 289 / 512 |
| 24-asymmetric-shifted | 通道 | P/P/D/D | 0.02 / 1.0 | (-2, -1); (0.5, 1) | 625 / 1152 |
| 25-cavity-top-reverse | 方腔 top − | D/D/D/D | 0.01 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 2401 / 4608 |
| 26-cavity-bottom-positive | 方腔 bottom + | D/D/D/D | 0.01 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 2401 / 4608 |
| 27-cavity-bottom-negative | 方腔 bottom − | D/D/D/D | 0.01 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 2401 / 4608 |
| 28-cavity-left-positive | 方腔 left + | D/D/D/D | 0.01 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 2401 / 4608 |
| 29-cavity-left-negative | 方腔 left − | D/D/D/D | 0.01 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 4225 / 8192 |
| 30-cavity-right-positive | 方腔 right + | D/D/D/D | 0.01 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 2401 / 4608 |
| 31-cavity-right-negative | 方腔 right − | D/D/D/D | 0.01 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 4225 / 8192 |
| 32-cavity-small-shifted | 方腔 bottom − | D/D/D/D | 0.005 / 0.5 | (-2, 1.5); (0.5, 0.5) | 2401 / 4608 |

## 每例驱动、边界方程与参考范围

### 01-rest

`s=y−(0)`，`H=1`，`e=(1,0)`，`a=0 e`。
`q∞=0+(0)z+(0)z(1−z)`。
参考为 `u=e q∞`、`p=0`。
- left：与 right 周期连接，u、p 及对应导数相等。
- right：与 left 周期连接，u、p 及对应导数相等。
- bottom：u=0 e。
- top：u=0 e。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
网格：n=4，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/01-rest/analytic.json`。

### 02-couette

`s=y−(0)`，`H=1`，`e=(1,0)`，`a=0 e`。
`q∞=0+(1)z+(0)z(1−z)`。
参考为 `u=e q∞`、`p=0`。
- left：与 right 周期连接，u、p 及对应导数相等。
- right：与 left 周期连接，u、p 及对应导数相等。
- bottom：u=0 e。
- top：u=1 e。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
网格：n=32，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/02-couette/analytic.json`。

### 03-poiseuille

`s=y−(0)`，`H=1`，`e=(1,0)`，`a=0.08 e`。
`q∞=0+(0)z+(4)z(1−z)`。
参考为 `u=e q∞`、`p=0`。
- left：与 right 周期连接，u、p 及对应导数相等。
- right：与 left 周期连接，u、p 及对应导数相等。
- bottom：u=0 e。
- top：u=0 e。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
网格：n=32，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/03-poiseuille/analytic.json`。

### 04-couette-poiseuille

`s=y−(0)`，`H=1`，`e=(1,0)`，`a=0.032 e`。
`q∞=0+(0.6)z+(1.6)z(1−z)`。
参考为 `u=e q∞`、`p=0`。
- left：与 right 周期连接，u、p 及对应导数相等。
- right：与 left 周期连接，u、p 及对应导数相等。
- bottom：u=0 e。
- top：u=0.6 e。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
网格：n=64，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/04-couette-poiseuille/analytic.json`。

### 05-reverse-pressure-drive

`s=y−(0)`，`H=1`，`e=(1,0)`，`a=-0.08 e`。
`q∞=0+(0)z+(-4)z(1−z)`。
参考为 `u=e q∞`、`p=0`。
- left：与 right 周期连接，u、p 及对应导数相等。
- right：与 left 周期连接，u、p 及对应导数相等。
- bottom：u=0 e。
- top：u=0 e。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
网格：n=32，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/05-reverse-pressure-drive/analytic.json`。

### 06-counter-moving-walls

`s=y−(0)`，`H=1`，`e=(1,0)`，`a=0 e`。
`q∞=-0.6+(1.2)z+(0)z(1−z)`。
参考为 `u=e q∞`、`p=0`。
- left：与 right 周期连接，u、p 及对应导数相等。
- right：与 left 周期连接，u、p 及对应导数相等。
- bottom：u=-0.6 e。
- top：u=0.6 e。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
网格：n=32，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/06-counter-moving-walls/analytic.json`。

### 07-vertical-channel

`s=x−(0)`，`H=1`，`e=(0,1)`，`a=0.04 e`。
`q∞=0+(0.5)z+(2)z(1−z)`。
参考为 `u=e q∞`、`p=0`。
- left：u=0 e。
- right：u=0.5 e。
- bottom：与 top 周期连接，u、p 及对应导数相等。
- top：与 bottom 周期连接，u、p 及对应导数相等。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
网格：n=32，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/07-vertical-channel/analytic.json`。

### 08-long-shifted-channel

`s=y−(2)`，`H=0.5`，`e=(1,0)`，`a=0 e`。
`q∞=0+(0.8)z+(0)z(1−z)`。
参考为 `u=e q∞`、`p=0`。
- left：与 right 周期连接，u、p 及对应导数相等。
- right：与 left 周期连接，u、p 及对应导数相等。
- bottom：u=0 e。
- top：u=0.8 e。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
网格：n=32，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/08-long-shifted-channel/analytic.json`。

### 09-sparse-channel

`s=y−(0)`，`H=1`，`e=(1,0)`，`a=0.08 e`。
`q∞=0+(0)z+(4)z(1−z)`。
参考为 `u=e q∞`、`p=0`。
- left：与 right 周期连接，u、p 及对应导数相等。
- right：与 left 周期连接，u、p 及对应导数相等。
- bottom：u=0 e。
- top：u=0 e。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
网格：n=48，稀疏 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/09-sparse-channel/analytic.json`。

### 10-density-viscosity

`s=y−(0)`，`H=1`，`e=(1,0)`，`a=0.16 e`。
`q∞=0+(0)z+(4)z(1−z)`。
参考为 `u=e q∞`、`p=0`。
- left：与 right 周期连接，u、p 及对应导数相等。
- right：与 left 周期连接，u、p 及对应导数相等。
- bottom：u=0 e。
- top：u=0 e。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
网格：n=32，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/10-density-viscosity/analytic.json`。

### 11-low-re-channel

`s=y−(0)`，`H=1`，`e=(1,0)`，`a=0 e`。
`q∞=0+(1)z+(0)z(1−z)`。
参考为 `u=e q∞`、`p=0`。
- left：与 right 周期连接，u、p 及对应导数相等。
- right：与 left 周期连接，u、p 及对应导数相等。
- bottom：u=0 e。
- top：u=1 e。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
网格：n=32，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/11-low-re-channel/analytic.json`。

### 12-opposing-shear-and-drive

`s=y−(0)`，`H=1`，`e=(1,0)`，`a=0.094 e`。
`q∞=0+(-0.4)z+(4.7)z(1−z)`。
参考为 `u=e q∞`、`p=0`。
- left：与 right 周期连接，u、p 及对应导数相等。
- right：与 left 周期连接，u、p 及对应导数相等。
- bottom：u=0 e。
- top：u=-0.4 e。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
网格：n=32，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/12-opposing-shear-and-drive/analytic.json`。

### 13-cavity-32

`a=(0,0)`；Re=100。运动边开区间为恒定壁速，两个端点为零。
- left：`u=(0, 0)`。
- right：`u=(0, 0)`。
- bottom：`u=(0, 0)`。
- top：`u=(1, 0)`。
归一化坐标变换 `x̂=M ξ+b`，`M=[[1, 0], [0, 1]]`、`b=[0, 0]`；速度同乘 M 和壁速幅值 1。
只输出两个清单中的中线分量；坐标显式存于 NPZ，采样点 IDs 不代表网格 tag。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
网格：n=32，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/13-cavity-32/analytic.json`。

### 14-cavity-48

`a=(0,0)`；Re=100。运动边开区间为恒定壁速，两个端点为零。
- left：`u=(0, 0)`。
- right：`u=(0, 0)`。
- bottom：`u=(0, 0)`。
- top：`u=(1, 0)`。
归一化坐标变换 `x̂=M ξ+b`，`M=[[1, 0], [0, 1]]`、`b=[0, 0]`；速度同乘 M 和壁速幅值 1。
只输出两个清单中的中线分量；坐标显式存于 NPZ，采样点 IDs 不代表网格 tag。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
网格：n=48，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/14-cavity-48/analytic.json`。

### 15-cavity-64-sparse

`a=(0,0)`；Re=100。运动边开区间为恒定壁速，两个端点为零。
- left：`u=(0, 0)`。
- right：`u=(0, 0)`。
- bottom：`u=(0, 0)`。
- top：`u=(1, 0)`。
归一化坐标变换 `x̂=M ξ+b`，`M=[[1, 0], [0, 1]]`、`b=[0, 0]`；速度同乘 M 和壁速幅值 1。
只输出两个清单中的中线分量；坐标显式存于 NPZ，采样点 IDs 不代表网格 tag。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
网格：n=64，稀疏 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/15-cavity-64-sparse/analytic.json`。

### 16-cavity-scaled-shifted

`a=(0,0)`；Re=100。运动边开区间为恒定壁速，两个端点为零。
- left：`u=(0, 0)`。
- right：`u=(0, 0)`。
- bottom：`u=(0, 0)`。
- top：`u=(0.5, 0)`。
归一化坐标变换 `x̂=M ξ+b`，`M=[[1, 0], [0, 1]]`、`b=[0, 0]`；速度同乘 M 和壁速幅值 0.5。
只输出两个清单中的中线分量；坐标显式存于 NPZ，采样点 IDs 不代表网格 tag。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
网格：n=48，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/16-cavity-scaled-shifted/analytic.json`。

### 17-zero-net-flux

`s=y−(0)`，`H=1`，`e=(1,0)`，`a=0.048 e`。
`q∞=-0.4+(0)z+(2.4)z(1−z)`。
参考为 `u=e q∞`、`p=0`。
- left：与 right 周期连接，u、p 及对应导数相等。
- right：与 left 周期连接，u、p 及对应导数相等。
- bottom：u=-0.4 e。
- top：u=-0.4 e。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
网格：n=48，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/17-zero-net-flux/analytic.json`。

### 18-interior-reversal

`s=y−(0)`，`H=1`，`e=(1,0)`，`a=0.08 e`。
`q∞=-0.7+(0.9)z+(4)z(1−z)`。
参考为 `u=e q∞`、`p=0`。
- left：与 right 周期连接，u、p 及对应导数相等。
- right：与 left 周期连接，u、p 及对应导数相等。
- bottom：u=-0.7 e。
- top：u=0.2 e。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
网格：n=64，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/18-interior-reversal/analytic.json`。

### 19-moving-both-driven

`s=y−(0)`，`H=1`，`e=(1,0)`，`a=-0.064 e`。
`q∞=0.3+(0.4)z+(-3.2)z(1−z)`。
参考为 `u=e q∞`、`p=0`。
- left：与 right 周期连接，u、p 及对应导数相等。
- right：与 left 周期连接，u、p 及对应导数相等。
- bottom：u=0.3 e。
- top：u=0.7 e。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
网格：n=48，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/19-moving-both-driven/analytic.json`。

### 20-vertical-negative

`s=x−(0)`，`H=1`，`e=(0,1)`，`a=0.032 e`。
`q∞=-0.2+(-0.6)z+(1.6)z(1−z)`。
参考为 `u=e q∞`、`p=0`。
- left：u=-0.2 e。
- right：u=-0.8 e。
- bottom：与 top 周期连接，u、p 及对应导数相等。
- top：与 bottom 周期连接，u、p 及对应导数相等。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
网格：n=48，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/20-vertical-negative/analytic.json`。

### 21-wide-cross-section

`s=y−(0)`，`H=2`，`e=(1,0)`，`a=0 e`。
`q∞=-0.6+(1.2)z+(0)z(1−z)`。
参考为 `u=e q∞`、`p=0`。
- left：与 right 周期连接，u、p 及对应导数相等。
- right：与 left 周期连接，u、p 及对应导数相等。
- bottom：u=-0.6 e。
- top：u=0.6 e。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
网格：n=64，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/21-wide-cross-section/analytic.json`。

### 22-thin-driven-channel

`s=y−(0)`，`H=0.5`，`e=(1,0)`，`a=0.12 e`。
`q∞=0+(0)z+(3)z(1−z)`。
参考为 `u=e q∞`、`p=0`。
- left：与 right 周期连接，u、p 及对应导数相等。
- right：与 left 周期连接，u、p 及对应导数相等。
- bottom：u=0 e。
- top：u=0 e。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
网格：n=48，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/22-thin-driven-channel/analytic.json`。

### 23-weak-drive

`s=y−(0)`，`H=1`，`e=(1,0)`，`a=0.0004 e`。
`q∞=0.002+(-0.005)z+(0.004)z(1−z)`。
参考为 `u=e q∞`、`p=0`。
- left：与 right 周期连接，u、p 及对应导数相等。
- right：与 left 周期连接，u、p 及对应导数相等。
- bottom：u=0.002 e。
- top：u=-0.003 e。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
网格：n=16，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/23-weak-drive/analytic.json`。

### 24-asymmetric-shifted

`s=y−(-1)`，`H=1`，`e=(1,0)`，`a=-0.04 e`。
`q∞=0.4+(-0.6)z+(-1)z(1−z)`。
参考为 `u=e q∞`、`p=0`。
- left：与 right 周期连接，u、p 及对应导数相等。
- right：与 left 周期连接，u、p 及对应导数相等。
- bottom：u=0.4 e。
- top：u=-0.2 e。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
网格：n=24，稀疏 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/24-asymmetric-shifted/analytic.json`。

### 25-cavity-top-reverse

`a=(0,0)`；Re=100。运动边开区间为恒定壁速，两个端点为零。
- left：`u=(0, 0)`。
- right：`u=(0, 0)`。
- bottom：`u=(0, 0)`。
- top：`u=(-1, 0)`。
归一化坐标变换 `x̂=M ξ+b`，`M=[[-1, 0], [0, 1]]`、`b=[1, 0]`；速度同乘 M 和壁速幅值 1。
只输出两个清单中的中线分量；坐标显式存于 NPZ，采样点 IDs 不代表网格 tag。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
网格：n=48，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/25-cavity-top-reverse/analytic.json`。

### 26-cavity-bottom-positive

`a=(0,0)`；Re=100。运动边开区间为恒定壁速，两个端点为零。
- left：`u=(0, 0)`。
- right：`u=(0, 0)`。
- bottom：`u=(1, 0)`。
- top：`u=(0, 0)`。
归一化坐标变换 `x̂=M ξ+b`，`M=[[1, 0], [0, -1]]`、`b=[0, 1]`；速度同乘 M 和壁速幅值 1。
只输出两个清单中的中线分量；坐标显式存于 NPZ，采样点 IDs 不代表网格 tag。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
网格：n=48，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/26-cavity-bottom-positive/analytic.json`。

### 27-cavity-bottom-negative

`a=(0,0)`；Re=100。运动边开区间为恒定壁速，两个端点为零。
- left：`u=(0, 0)`。
- right：`u=(0, 0)`。
- bottom：`u=(-1, 0)`。
- top：`u=(0, 0)`。
归一化坐标变换 `x̂=M ξ+b`，`M=[[-1, 0], [0, -1]]`、`b=[1, 1]`；速度同乘 M 和壁速幅值 1。
只输出两个清单中的中线分量；坐标显式存于 NPZ，采样点 IDs 不代表网格 tag。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
网格：n=48，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/27-cavity-bottom-negative/analytic.json`。

### 28-cavity-left-positive

`a=(0,0)`；Re=100。运动边开区间为恒定壁速，两个端点为零。
- left：`u=(0, 1)`。
- right：`u=(0, 0)`。
- bottom：`u=(0, 0)`。
- top：`u=(0, 0)`。
归一化坐标变换 `x̂=M ξ+b`，`M=[[0, -1], [1, 0]]`、`b=[1, 0]`；速度同乘 M 和壁速幅值 1。
只输出两个清单中的中线分量；坐标显式存于 NPZ，采样点 IDs 不代表网格 tag。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
网格：n=48，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/28-cavity-left-positive/analytic.json`。

### 29-cavity-left-negative

`a=(0,0)`；Re=100。运动边开区间为恒定壁速，两个端点为零。
- left：`u=(0, -1)`。
- right：`u=(0, 0)`。
- bottom：`u=(0, 0)`。
- top：`u=(0, 0)`。
归一化坐标变换 `x̂=M ξ+b`，`M=[[0, -1], [-1, 0]]`、`b=[1, 1]`；速度同乘 M 和壁速幅值 1。
只输出两个清单中的中线分量；坐标显式存于 NPZ，采样点 IDs 不代表网格 tag。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
网格：n=64，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/29-cavity-left-negative/analytic.json`。

### 30-cavity-right-positive

`a=(0,0)`；Re=100。运动边开区间为恒定壁速，两个端点为零。
- left：`u=(0, 0)`。
- right：`u=(0, 1)`。
- bottom：`u=(0, 0)`。
- top：`u=(0, 0)`。
归一化坐标变换 `x̂=M ξ+b`，`M=[[0, 1], [1, 0]]`、`b=[0, 0]`；速度同乘 M 和壁速幅值 1。
只输出两个清单中的中线分量；坐标显式存于 NPZ，采样点 IDs 不代表网格 tag。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
网格：n=48，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/30-cavity-right-positive/analytic.json`。

### 31-cavity-right-negative

`a=(0,0)`；Re=100。运动边开区间为恒定壁速，两个端点为零。
- left：`u=(0, 0)`。
- right：`u=(0, -1)`。
- bottom：`u=(0, 0)`。
- top：`u=(0, 0)`。
归一化坐标变换 `x̂=M ξ+b`，`M=[[0, 1], [-1, 0]]`、`b=[0, 1]`；速度同乘 M 和壁速幅值 1。
只输出两个清单中的中线分量；坐标显式存于 NPZ，采样点 IDs 不代表网格 tag。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
网格：n=64，稀疏 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/31-cavity-right-negative/analytic.json`。

### 32-cavity-small-shifted

`a=(0,0)`；Re=100。运动边开区间为恒定壁速，两个端点为零。
- left：`u=(0, 0)`。
- right：`u=(0, 0)`。
- bottom：`u=(-1, 0)`。
- top：`u=(0, 0)`。
归一化坐标变换 `x̂=M ξ+b`，`M=[[-1, 0], [0, -1]]`、`b=[1, 1]`；速度同乘 M 和壁速幅值 1。
只输出两个清单中的中线分量；坐标显式存于 NPZ，采样点 IDs 不代表网格 tag。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
网格：n=48，稀疏 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/32-cavity-small-shifted/analytic.json`。
