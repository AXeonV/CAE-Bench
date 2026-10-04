# 二维瞬态不可压缩流测试点与标答（出题材料）

本文件与 [DESIGN.md](DESIGN.md) 仅供出题使用，不进入解题材料。输入只含条件与场数据，不含下列配方或参考公式。

ν=μ/ρ；速度单位 m/s、压力 Pa、加速度 m/s²、时间 s。P 表示相对边周期连接；D 表示给定速度。所有点采用面积平均压力为零。
通道取跨壁坐标 s∈[0,H]、z=s/H、流向单位向量 e；`q∞=U₀+(U₁−U₀)z+aH²z(1−z)/(2ν)`，`u∞=e q∞`、`p=0`。

## 初始条件与解析标答

下列通道配方只生成初始**节点值**；连续初值一律为相邻跨壁层之间的分片线性插值，不直接使用配方函数作为连续标答。
`u=e[q∞+Σ bₙ sin(nπs/H) exp(−ν(nπ/H)²t)]`，`bₙ=(2/H)∫₀ᴴ(q₀−q∞)sin(nπs/H)ds`，`p=0`。
系数按初始分片线性区间精确积分，求和 1,024 项；每例记录截断尾界。t=0 直接复制初值。

| 初值配方 | 节点流向速度 q₀(z) |
|---|---|
| zero | 0 |
| linear | z |
| modes | 0.6 sin(πz) − 0.3 sin(3πz) + 0.2 sin(7πz) |
| plate | 0.8（0.2<z<0.55）；−0.5（0.55≤z<0.8）；其余为 0 |
| pulse | 0.9 max(1−|z−0.35|/0.12,0) |
| oscillatory | 0.45 sin(2πz) + 0.25 sin(9πz) − 0.15 sin(13πz) |
| reverse | 0.7−1.4z |
| double_pulse | 0.8 max(1−|z−0.25|/0.1,0) − 0.6 max(1−|z−0.7|/0.15,0) |

二维周期点有两类：同一 Laplace 特征值的叠加涡旋，以及斜向剪切波；均包含常数平移速度 c。
叠加涡旋令 `κ=2πm/L`，`X=κ(x−x₀−cₓt)+φₓ`，`Y=κ(y−y₀−cᵧt)+φᵧ`，`f=(sin,cos)`，
`ψ=e^(−2νκ²t) f(X)ᵀ C f(Y)/κ`；`u=c+(ψ_y,−ψ_x)`，
`p=ρ[e^(−4νκ²t)ΣCᵢⱼ²/2−(|u−c|²+2κ²ψ²)/2]`。C 只有左上项非零时退化为单涡旋。
剪切波令 `k=2π(wₓ,wᵧ)/L`、`d=(kᵧ,−kₓ)/|k|`，
`u=c+A d sin(k·(x−x₀−ct)+φ) e^(−ν|k|²t)`，`p=0`。
这两类初值都是题目规定的低阶周期三角多项式。完整推导与独立参考实现见 [DESIGN.md](DESIGN.md) 和 `author/oracle.py`。

## 测试点总览

| 测试点 | 类型／主要变化 | 左／右／下／上 | ν / ρ | 域 (x₀,y₀; Lx,Ly) | 节点／三角形 | 输出个数／首个正时刻／末时刻 |
|---|---|---|---|---|---|---|
| 01-rest | zero | P/P/D/D | 0.01 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 25 / 32 | 7 / 0.1 / 30 |
| 02-start-couette | zero | P/P/D/D | 0.01 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 1089 / 2048 | 7 / 0.1 / 30 |
| 03-start-poiseuille | zero | P/P/D/D | 0.01 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 1089 / 2048 | 7 / 0.1 / 30 |
| 04-start-combined | zero | P/P/D/D | 0.01 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 2401 / 4608 | 7 / 0.1 / 30 |
| 05-reverse-drive | zero | P/P/D/D | 0.01 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 1089 / 2048 | 7 / 0.1 / 30 |
| 06-start-counter-walls | zero | P/P/D/D | 0.01 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 1089 / 2048 | 7 / 0.1 / 30 |
| 07-stop-shear | linear | P/P/D/D | 0.01 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 1089 / 2048 | 7 / 0.1 / 30 |
| 08-decay-multiple-modes | modes | P/P/D/D | 0.01 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 1089 / 2048 | 7 / 0.1 / 30 |
| 09-signed-piecewise-profile | plate | P/P/D/D | 0.01 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 4225 / 8192 | 7 / 0.1 / 30 |
| 10-vertical-start | zero | D/D/P/P | 0.01 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 1089 / 2048 | 7 / 0.1 / 30 |
| 11-shifted-sparse-binary | zero | P/P/D/D | 0.005 / 1.0 | (-1, 2); (2, 0.5) | 2401 / 4608 | 7 / 0.05 / 15 |
| 12-fast-viscous-start | zero | P/P/D/D | 0.05 / 2 | (0.0, 0.0); (1.0, 1.0) | 1089 / 2048 | 7 / 0.02 / 6 |
| 13-periodic-vortex | 单涡旋 | P/P/P/P | 0.01 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 1089 / 2048 | 6 / 0.01 / 1 |
| 14-advected-vortex | 单涡旋 | P/P/P/P | 0.017 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 1089 / 2048 | 6 / 0.01 / 1 |
| 15-oblique-advection | 单涡旋 | P/P/P/P | 0.015 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 2401 / 4608 | 6 / 0.01 / 1 |
| 16-two-wave-vortex | 单涡旋 | P/P/P/P | 0.011 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 4225 / 8192 | 6 / 0.005 / 0.4 |
| 17-scaled-density-vortex | 单涡旋 | P/P/P/P | 0.036 / 2 | (1, -2); (2, 2) | 2401 / 4608 | 6 / 0.02 / 2 |
| 18-sparse-binary-vortex | 单涡旋 | P/P/P/P | 0.016 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 2401 / 4608 | 6 / 0.01 / 1 |
| 19-driven-nonzero-initial | modes | P/P/D/D | 0.015 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 4225 / 8192 | 8 / 0.0666667 / 20 |
| 20-vertical-local-pulse | pulse | D/D/P/P | 0.01 / 0.5 | (1, -2); (1.0, 1.0) | 4225 / 8192 | 7 / 0.1 / 30 |
| 21-oscillatory-counter-drive | oscillatory | P/P/D/D | 0.01 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 4225 / 8192 | 8 / 0.1 / 30 |
| 22-reverse-initial-shear | reverse | P/P/D/D | 0.02 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 2401 / 4608 | 7 / 0.05 / 15 |
| 23-double-local-pulses | double_pulse | P/P/D/D | 0.005 / 2 | (0.0, 0.0); (2, 0.5) | 4225 / 8192 | 7 / 0.05 / 15 |
| 24-initial-counter-walls | modes | P/P/D/D | 0.02 / 1.0 | (0.0, 0.0); (0.5, 2) | 2401 / 4608 | 7 / 0.2 / 60 |
| 25-mixed-vortex-matrix | 叠加涡旋 | P/P/P/P | 0.025 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 2401 / 4608 | 8 / 0.005 / 0.8 |
| 26-mixed-two-wave | 叠加涡旋 | P/P/P/P | 0.02 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 4225 / 8192 | 8 / 0.005 / 0.4 |
| 27-mixed-scaled-density | 叠加涡旋 | P/P/P/P | 0.04 / 2 | (-2, 1); (2, 2) | 2401 / 4608 | 8 / 0.01 / 2 |
| 28-mixed-sparse-binary | 叠加涡旋 | P/P/P/P | 0.025 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 4225 / 8192 | 8 / 0.005 / 0.7 |
| 29-oblique-periodic-shear | 斜向剪切波 | P/P/P/P | 0.015 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 2401 / 4608 | 8 / 0.005 / 1 |
| 30-crosswise-periodic-shear | 斜向剪切波 | P/P/P/P | 0.015 / 2 | (0.0, 0.0); (1.0, 1.0) | 2401 / 4608 | 8 / 0.005 / 1 |
| 31-horizontal-periodic-shear | 斜向剪切波 | P/P/P/P | 0.014 / 1.0 | (2, -2); (0.5, 0.5) | 1089 / 2048 | 8 / 0.0025 / 0.5 |
| 32-diagonal-periodic-shear | 斜向剪切波 | P/P/P/P | 0.015 / 1.0 | (0.0, 0.0); (1.0, 1.0) | 4225 / 8192 | 8 / 0.005 / 1 |

## 每例初值、驱动、边界方程与参考范围

### 01-rest

`s=y−(0)`，`H=1`，`e=(1,0)`，`a=0 e`。
`q∞=0+(0)z+(0)z(1−z)`。
初始节点值 `u₀=e q₀(z)`，`q₀=0`；正时间参考为上述初值积分级数。
- left：与 right 周期连接，u、p 及对应导数相等。
- right：与 left 周期连接，u、p 及对应导数相等。
- bottom：u=0 e（t>0）。
- top：u=0 e（t>0）。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
输出时刻：`[0, 0.1, 0.3, 1, 3, 10, 30]` s。
网格：n=4，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/01-rest/analytic.json`。

### 02-start-couette

`s=y−(0)`，`H=1`，`e=(1,0)`，`a=0 e`。
`q∞=0+(1)z+(0)z(1−z)`。
初始节点值 `u₀=e q₀(z)`，`q₀=0`；正时间参考为上述初值积分级数。
- left：与 right 周期连接，u、p 及对应导数相等。
- right：与 left 周期连接，u、p 及对应导数相等。
- bottom：u=0 e（t>0）。
- top：u=1 e（t>0）。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
输出时刻：`[0, 0.1, 0.3, 1, 3, 10, 30]` s。
网格：n=32，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/02-start-couette/analytic.json`。

### 03-start-poiseuille

`s=y−(0)`，`H=1`，`e=(1,0)`，`a=0.08 e`。
`q∞=0+(0)z+(4)z(1−z)`。
初始节点值 `u₀=e q₀(z)`，`q₀=0`；正时间参考为上述初值积分级数。
- left：与 right 周期连接，u、p 及对应导数相等。
- right：与 left 周期连接，u、p 及对应导数相等。
- bottom：u=0 e（t>0）。
- top：u=0 e（t>0）。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
输出时刻：`[0, 0.1, 0.3, 1, 3, 10, 30]` s。
网格：n=32，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/03-start-poiseuille/analytic.json`。

### 04-start-combined

`s=y−(0)`，`H=1`，`e=(1,0)`，`a=0.032 e`。
`q∞=0+(0.6)z+(1.6)z(1−z)`。
初始节点值 `u₀=e q₀(z)`，`q₀=0`；正时间参考为上述初值积分级数。
- left：与 right 周期连接，u、p 及对应导数相等。
- right：与 left 周期连接，u、p 及对应导数相等。
- bottom：u=0 e（t>0）。
- top：u=0.6 e（t>0）。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
输出时刻：`[0, 0.1, 0.3, 1, 3, 10, 30]` s。
网格：n=48，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/04-start-combined/analytic.json`。

### 05-reverse-drive

`s=y−(0)`，`H=1`，`e=(1,0)`，`a=-0.08 e`。
`q∞=0+(0)z+(-4)z(1−z)`。
初始节点值 `u₀=e q₀(z)`，`q₀=0`；正时间参考为上述初值积分级数。
- left：与 right 周期连接，u、p 及对应导数相等。
- right：与 left 周期连接，u、p 及对应导数相等。
- bottom：u=0 e（t>0）。
- top：u=0 e（t>0）。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
输出时刻：`[0, 0.1, 0.3, 1, 3, 10, 30]` s。
网格：n=32，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/05-reverse-drive/analytic.json`。

### 06-start-counter-walls

`s=y−(0)`，`H=1`，`e=(1,0)`，`a=0 e`。
`q∞=-0.6+(1.2)z+(0)z(1−z)`。
初始节点值 `u₀=e q₀(z)`，`q₀=0`；正时间参考为上述初值积分级数。
- left：与 right 周期连接，u、p 及对应导数相等。
- right：与 left 周期连接，u、p 及对应导数相等。
- bottom：u=-0.6 e（t>0）。
- top：u=0.6 e（t>0）。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
输出时刻：`[0, 0.1, 0.3, 1, 3, 10, 30]` s。
网格：n=32，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/06-start-counter-walls/analytic.json`。

### 07-stop-shear

`s=y−(0)`，`H=1`，`e=(1,0)`，`a=0 e`。
`q∞=0+(0)z+(0)z(1−z)`。
初始节点值 `u₀=e q₀(z)`，`q₀=z`；正时间参考为上述初值积分级数。
- left：与 right 周期连接，u、p 及对应导数相等。
- right：与 left 周期连接，u、p 及对应导数相等。
- bottom：u=0 e（t>0）。
- top：u=0 e（t>0）。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
输出时刻：`[0, 0.1, 0.3, 1, 3, 10, 30]` s。
网格：n=32，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/07-stop-shear/analytic.json`。

### 08-decay-multiple-modes

`s=y−(0)`，`H=1`，`e=(1,0)`，`a=0 e`。
`q∞=0+(0)z+(0)z(1−z)`。
初始节点值 `u₀=e q₀(z)`，`q₀=0.6 sin(πz) − 0.3 sin(3πz) + 0.2 sin(7πz)`；正时间参考为上述初值积分级数。
- left：与 right 周期连接，u、p 及对应导数相等。
- right：与 left 周期连接，u、p 及对应导数相等。
- bottom：u=0 e（t>0）。
- top：u=0 e（t>0）。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
输出时刻：`[0, 0.1, 0.3, 1, 3, 10, 30]` s。
网格：n=32，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/08-decay-multiple-modes/analytic.json`。

### 09-signed-piecewise-profile

`s=y−(0)`，`H=1`，`e=(1,0)`，`a=0 e`。
`q∞=0+(0)z+(0)z(1−z)`。
初始节点值 `u₀=e q₀(z)`，`q₀=0.8（0.2<z<0.55）；−0.5（0.55≤z<0.8）；其余为 0`；正时间参考为上述初值积分级数。
- left：与 right 周期连接，u、p 及对应导数相等。
- right：与 left 周期连接，u、p 及对应导数相等。
- bottom：u=0 e（t>0）。
- top：u=0 e（t>0）。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
输出时刻：`[0, 0.1, 0.3, 1, 3, 10, 30]` s。
网格：n=64，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/09-signed-piecewise-profile/analytic.json`。

### 10-vertical-start

`s=x−(0)`，`H=1`，`e=(0,1)`，`a=0.04 e`。
`q∞=0+(0.5)z+(2)z(1−z)`。
初始节点值 `u₀=e q₀(z)`，`q₀=0`；正时间参考为上述初值积分级数。
- left：u=0 e（t>0）。
- right：u=0.5 e（t>0）。
- bottom：与 top 周期连接，u、p 及对应导数相等。
- top：与 bottom 周期连接，u、p 及对应导数相等。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
输出时刻：`[0, 0.1, 0.3, 1, 3, 10, 30]` s。
网格：n=32，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/10-vertical-start/analytic.json`。

### 11-shifted-sparse-binary

`s=y−(2)`，`H=0.5`，`e=(1,0)`，`a=0 e`。
`q∞=0+(0.8)z+(0)z(1−z)`。
初始节点值 `u₀=e q₀(z)`，`q₀=0`；正时间参考为上述初值积分级数。
- left：与 right 周期连接，u、p 及对应导数相等。
- right：与 left 周期连接，u、p 及对应导数相等。
- bottom：u=0 e（t>0）。
- top：u=0.8 e（t>0）。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
输出时刻：`[0, 0.05, 0.15, 0.5, 1.5, 5, 15]` s。
网格：n=48，稀疏 tag，MSH 4.1 binary；全部参考参数及来源另存 `reference/11-shifted-sparse-binary/analytic.json`。

### 12-fast-viscous-start

`s=y−(0)`，`H=1`，`e=(1,0)`，`a=0 e`。
`q∞=0+(1)z+(0)z(1−z)`。
初始节点值 `u₀=e q₀(z)`，`q₀=0`；正时间参考为上述初值积分级数。
- left：与 right 周期连接，u、p 及对应导数相等。
- right：与 left 周期连接，u、p 及对应导数相等。
- bottom：u=0 e（t>0）。
- top：u=1 e（t>0）。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
输出时刻：`[0, 0.02, 0.06, 0.2, 0.6, 2, 6]` s。
网格：n=32，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/12-fast-viscous-start/analytic.json`。

### 13-periodic-vortex

`a=(0,0)`，`c=(0.0, 0.0)`。
叠加涡旋：`C=[[1,0],[0,0]]`、`m=1`、`φ=(0.0, 0.0)`；初值和参考由上述 ψ、u、p 公式生成。
- left/right：u、p 及对应导数周期相等。
- bottom/top：u、p 及对应导数周期相等。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
输出时刻：`[0, 0.01, 0.03, 0.1, 0.3, 1]` s。
网格：n=32，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/13-periodic-vortex/analytic.json`。

### 14-advected-vortex

`a=(0,0)`，`c=(0.7, 0)`。
叠加涡旋：`C=[[1,0],[0,0]]`、`m=1`、`φ=(0.0, 0.0)`；初值和参考由上述 ψ、u、p 公式生成。
- left/right：u、p 及对应导数周期相等。
- bottom/top：u、p 及对应导数周期相等。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
输出时刻：`[0, 0.01, 0.03, 0.1, 0.3, 1]` s。
网格：n=32，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/14-advected-vortex/analytic.json`。

### 15-oblique-advection

`a=(0,0)`，`c=(0.4, -0.3)`。
叠加涡旋：`C=[[1,0],[0,0]]`、`m=1`、`φ=(0.3, 0.7)`；初值和参考由上述 ψ、u、p 公式生成。
- left/right：u、p 及对应导数周期相等。
- bottom/top：u、p 及对应导数周期相等。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
输出时刻：`[0, 0.01, 0.04, 0.12, 0.4, 1]` s。
网格：n=48，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/15-oblique-advection/analytic.json`。

### 16-two-wave-vortex

`a=(0,0)`，`c=(-0.2, 0.3)`。
叠加涡旋：`C=[[0.6,0],[0,0]]`、`m=2`、`φ=(0.0, 0.0)`；初值和参考由上述 ψ、u、p 公式生成。
- left/right：u、p 及对应导数周期相等。
- bottom/top：u、p 及对应导数周期相等。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
输出时刻：`[0, 0.005, 0.015, 0.05, 0.15, 0.4]` s。
网格：n=64，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/16-two-wave-vortex/analytic.json`。

### 17-scaled-density-vortex

`a=(0,0)`，`c=(0.3, 0.3)`。
叠加涡旋：`C=[[1.2,0],[0,0]]`、`m=1`、`φ=(0.4, -0.2)`；初值和参考由上述 ψ、u、p 公式生成。
- left/right：u、p 及对应导数周期相等。
- bottom/top：u、p 及对应导数周期相等。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
输出时刻：`[0, 0.02, 0.08, 0.24, 0.8, 2]` s。
网格：n=48，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/17-scaled-density-vortex/analytic.json`。

### 18-sparse-binary-vortex

`a=(0,0)`，`c=(-0.4, 0.2)`。
叠加涡旋：`C=[[1,0],[0,0]]`、`m=1`、`φ=(-0.2, 0.6)`；初值和参考由上述 ψ、u、p 公式生成。
- left/right：u、p 及对应导数周期相等。
- bottom/top：u、p 及对应导数周期相等。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
输出时刻：`[0, 0.01, 0.03, 0.1, 0.3, 1]` s。
网格：n=48，稀疏 tag，MSH 4.1 binary；全部参考参数及来源另存 `reference/18-sparse-binary-vortex/analytic.json`。

### 19-driven-nonzero-initial

`s=y−(0)`，`H=1`，`e=(1,0)`，`a=0.08 e`。
`q∞=0.2+(-0.6)z+(2.66667)z(1−z)`。
初始节点值 `u₀=e q₀(z)`，`q₀=0.6 sin(πz) − 0.3 sin(3πz) + 0.2 sin(7πz)`；正时间参考为上述初值积分级数。
- left：与 right 周期连接，u、p 及对应导数相等。
- right：与 left 周期连接，u、p 及对应导数相等。
- bottom：u=0.2 e（t>0）。
- top：u=-0.4 e（t>0）。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
输出时刻：`[0, 0.0666666667, 0.133333333, 0.4, 1.13333333, 2.86666667, 7.33333333, 20]` s。
网格：n=64，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/19-driven-nonzero-initial/analytic.json`。

### 20-vertical-local-pulse

`s=x−(1)`，`H=1`，`e=(0,1)`，`a=0.03 e`。
`q∞=0+(-0.4)z+(1.5)z(1−z)`。
初始节点值 `u₀=e q₀(z)`，`q₀=0.9 max(1−|z−0.35|/0.12,0)`；正时间参考为上述初值积分级数。
- left：u=0 e（t>0）。
- right：u=-0.4 e（t>0）。
- bottom：与 top 周期连接，u、p 及对应导数相等。
- top：与 bottom 周期连接，u、p 及对应导数相等。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
输出时刻：`[0, 0.1, 0.3, 1, 3, 10, 30]` s。
网格：n=64，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/20-vertical-local-pulse/analytic.json`。

### 21-oscillatory-counter-drive

`s=y−(0)`，`H=1`，`e=(1,0)`，`a=-0.04 e`。
`q∞=-0.3+(0.6)z+(-2)z(1−z)`。
初始节点值 `u₀=e q₀(z)`，`q₀=0.45 sin(2πz) + 0.25 sin(9πz) − 0.15 sin(13πz)`；正时间参考为上述初值积分级数。
- left：与 right 周期连接，u、p 及对应导数相等。
- right：与 left 周期连接，u、p 及对应导数相等。
- bottom：u=-0.3 e（t>0）。
- top：u=0.3 e（t>0）。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
输出时刻：`[0, 0.1, 0.17, 0.4, 1.3, 5.7, 16, 30]` s。
网格：n=64，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/21-oscillatory-counter-drive/analytic.json`。

### 22-reverse-initial-shear

`s=y−(0)`，`H=1`，`e=(1,0)`，`a=0.04 e`。
`q∞=0.6+(-0.8)z+(1)z(1−z)`。
初始节点值 `u₀=e q₀(z)`，`q₀=0.7−1.4z`；正时间参考为上述初值积分级数。
- left：与 right 周期连接，u、p 及对应导数相等。
- right：与 left 周期连接，u、p 及对应导数相等。
- bottom：u=0.6 e（t>0）。
- top：u=-0.2 e（t>0）。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
输出时刻：`[0, 0.05, 0.15, 0.5, 1.5, 5, 15]` s。
网格：n=48，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/22-reverse-initial-shear/analytic.json`。

### 23-double-local-pulses

`s=y−(0)`，`H=0.5`，`e=(1,0)`，`a=0 e`。
`q∞=-0.2+(0.6)z+(0)z(1−z)`。
初始节点值 `u₀=e q₀(z)`，`q₀=0.8 max(1−|z−0.25|/0.1,0) − 0.6 max(1−|z−0.7|/0.15,0)`；正时间参考为上述初值积分级数。
- left：与 right 周期连接，u、p 及对应导数相等。
- right：与 left 周期连接，u、p 及对应导数相等。
- bottom：u=-0.2 e（t>0）。
- top：u=0.4 e（t>0）。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
输出时刻：`[0, 0.05, 0.15, 0.5, 1.5, 5, 15]` s。
网格：n=64，稀疏 tag，MSH 4.1 binary；全部参考参数及来源另存 `reference/23-double-local-pulses/analytic.json`。

### 24-initial-counter-walls

`s=y−(0)`，`H=2`，`e=(1,0)`，`a=-0.016 e`。
`q∞=-0.8+(1.6)z+(-1.6)z(1−z)`。
初始节点值 `u₀=e q₀(z)`，`q₀=0.6 sin(πz) − 0.3 sin(3πz) + 0.2 sin(7πz)`；正时间参考为上述初值积分级数。
- left：与 right 周期连接，u、p 及对应导数相等。
- right：与 left 周期连接，u、p 及对应导数相等。
- bottom：u=-0.8 e（t>0）。
- top：u=0.8 e（t>0）。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
输出时刻：`[0, 0.2, 0.6, 2, 6, 20, 60]` s。
网格：n=48，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/24-initial-counter-walls/analytic.json`。

### 25-mixed-vortex-matrix

`a=(0,0)`，`c=(0.4, -0.2)`。
叠加涡旋：`C=[[0.7,0.2],[-0.3,0.5]]`、`m=1`、`φ=(0.2, 0.5)`；初值和参考由上述 ψ、u、p 公式生成。
- left/right：u、p 及对应导数周期相等。
- bottom/top：u、p 及对应导数周期相等。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
输出时刻：`[0, 0.005, 0.012, 0.027, 0.061, 0.14, 0.33, 0.8]` s。
网格：n=48，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/25-mixed-vortex-matrix/analytic.json`。

### 26-mixed-two-wave

`a=(0,0)`，`c=(-0.4, 0.3)`。
叠加涡旋：`C=[[0.3,-0.2],[0.25,0.35]]`、`m=2`、`φ=(-0.4, 0.8)`；初值和参考由上述 ψ、u、p 公式生成。
- left/right：u、p 及对应导数周期相等。
- bottom/top：u、p 及对应导数周期相等。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
输出时刻：`[0, 0.005, 0.009, 0.02, 0.043, 0.09, 0.18, 0.4]` s。
网格：n=64，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/26-mixed-two-wave/analytic.json`。

### 27-mixed-scaled-density

`a=(0,0)`，`c=(0.2, 0.2)`。
叠加涡旋：`C=[[0.4,0.3],[0.2,-0.5]]`、`m=1`、`φ=(0.0, 0.0)`；初值和参考由上述 ψ、u、p 公式生成。
- left/right：u、p 及对应导数周期相等。
- bottom/top：u、p 及对应导数周期相等。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
输出时刻：`[0, 0.01, 0.028, 0.08, 0.22, 0.62, 1.3, 2]` s。
网格：n=48，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/27-mixed-scaled-density/analytic.json`。

### 28-mixed-sparse-binary

`a=(0,0)`，`c=(0.3, -0.3)`。
叠加涡旋：`C=[[0.55,-0.4],[0.3,0.2]]`、`m=1`、`φ=(0.6, -0.3)`；初值和参考由上述 ψ、u、p 公式生成。
- left/right：u、p 及对应导数周期相等。
- bottom/top：u、p 及对应导数周期相等。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
输出时刻：`[0, 0.005, 0.011, 0.029, 0.073, 0.18, 0.43, 0.7]` s。
网格：n=64，稀疏 tag，MSH 4.1 binary；全部参考参数及来源另存 `reference/28-mixed-sparse-binary/analytic.json`。

### 29-oblique-periodic-shear

`a=(0,0)`，`c=(0.5, -0.2)`。
剪切波：`A=0.8`、`w=(1, 2)`、`φ=0.4`；初值和参考由上述剪切公式取 t=0 或输出时刻。
- left/right：u、p 及对应导数周期相等。
- bottom/top：u、p 及对应导数周期相等。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
输出时刻：`[0, 0.005, 0.015, 0.04, 0.1, 0.25, 0.6, 1]` s。
网格：n=48，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/29-oblique-periodic-shear/analytic.json`。

### 30-crosswise-periodic-shear

`a=(0,0)`，`c=(-0.4, 0.6)`。
剪切波：`A=0.7`、`w=(2, -1)`、`φ=-0.7`；初值和参考由上述剪切公式取 t=0 或输出时刻。
- left/right：u、p 及对应导数周期相等。
- bottom/top：u、p 及对应导数周期相等。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
输出时刻：`[0, 0.005, 0.017, 0.053, 0.12, 0.28, 0.55, 1]` s。
网格：n=48，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/30-crosswise-periodic-shear/analytic.json`。

### 31-horizontal-periodic-shear

`a=(0,0)`，`c=(0.2, 0.4)`。
剪切波：`A=0.9`、`w=(0, 2)`、`φ=0`；初值和参考由上述剪切公式取 t=0 或输出时刻。
- left/right：u、p 及对应导数周期相等。
- bottom/top：u、p 及对应导数周期相等。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
输出时刻：`[0, 0.0025, 0.006, 0.0145, 0.0375, 0.095, 0.235, 0.5]` s。
网格：n=32，连续 tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/31-horizontal-periodic-shear/analytic.json`。

### 32-diagonal-periodic-shear

`a=(0,0)`，`c=(0.35, 0.35)`。
剪切波：`A=0.8`、`w=(1, -1)`、`φ=1.1`；初值和参考由上述剪切公式取 t=0 或输出时刻。
- left/right：u、p 及对应导数周期相等。
- bottom/top：u、p 及对应导数周期相等。
- 压力规范：`∫Ω p dΩ / |Ω| = 0`。
输出时刻：`[0, 0.005, 0.013, 0.037, 0.093, 0.21, 0.48, 1]` s。
网格：n=64，稀疏 tag，MSH 4.1 binary；全部参考参数及来源另存 `reference/32-diagonal-periodic-shear/analytic.json`。
