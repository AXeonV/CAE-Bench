# 瞬态测试设计（出题材料）

初始配方仅用于生成节点值；连续初始条件始终是该网格上的分片线性场。
所有正时间标答来自连续方程特征函数展开，不来自 baseline。

解析解公式见 [DESIGN.md：初始场及解析标答](DESIGN.md#初始场及解析标答)，计算实现见 [author/oracle.py](author/oracle.py)。24 点共用该级数公式，各点的边界条件决定特征函数，初始场决定积分系数。初始节点值的具体配方见 [author/catalog.py](author/catalog.py) 的 `initial_values`。

| 测试点 | 初始节点场配方 | 左／右／下／上 | 节点 | 三角形 | 最早输出／末时刻 s |
|---|---|---|---|---|---|
| 01-zero | zero | dirichlet / dirichlet / dirichlet / dirichlet | 9 | 8 | 0.003 / 0.08 |
| 02-insulated-constant | constant | normal_derivative / normal_derivative / normal_derivative / normal_derivative | 169 | 288 | 0.003 / 0.08 |
| 03-smooth-cooling | sine | dirichlet / dirichlet / dirichlet / dirichlet | 2401 | 4608 | 0.003 / 0.08 |
| 04-polynomial-bump | bubble | dirichlet / dirichlet / dirichlet / dirichlet | 2401 | 4608 | 0.003 / 0.08 |
| 05-two-hotspots | lobes | dirichlet / dirichlet / dirichlet / dirichlet | 2401 | 4608 | 0.003 / 0.08 |
| 06-localized-hotspot | narrow | dirichlet / dirichlet / dirichlet / dirichlet | 4225 | 8192 | 0.003 / 0.08 |
| 07-signed-pattern | signed | dirichlet / dirichlet / dirichlet / dirichlet | 2401 | 4608 | 0.003 / 0.08 |
| 08-short-wavelength | wave | dirichlet / dirichlet / dirichlet / dirichlet | 4225 | 8192 | 0.003 / 0.09 |
| 09-dirichlet-neumann | lobes | dirichlet / normal_derivative / dirichlet / normal_derivative | 2401 | 4608 | 0.003 / 0.08 |
| 10-reversed-natural | signed | normal_derivative / dirichlet / normal_derivative / dirichlet | 2401 | 4608 | 0.003 / 0.08 |
| 11-one-insulated-axis | bubble | dirichlet / dirichlet / normal_derivative / normal_derivative | 2401 | 4608 | 0.003 / 0.08 |
| 12-other-insulated-axis | sine | normal_flux / normal_flux / dirichlet / dirichlet | 2401 | 4608 | 0.003 / 0.08 |
| 13-four-robin | lobes | robin / robin / robin / robin | 2401 | 4608 | 0.003 / 0.08 |
| 14-dirichlet-robin | bubble | dirichlet / robin / dirichlet / robin | 2401 | 4608 | 0.003 / 0.08 |
| 15-four-operators | signed | dirichlet / normal_derivative / normal_flux / robin | 2401 | 4608 | 0.003 / 0.08 |
| 16-robin-flux | lobes | normal_flux / robin / robin / normal_flux | 2401 | 4608 | 0.003 / 0.08 |
| 17-weak-robin | constant | robin / robin / robin / robin | 2401 | 4608 | 0.003 / 0.08 |
| 18-fast-diffusion | bubble | robin / dirichlet / normal_flux / normal_derivative | 2401 | 4608 | 7.5e-05 / 0.002 |
| 19-slow-diffusion | signed | normal_derivative / robin / dirichlet / normal_flux | 2401 | 4608 | 1.2 / 32 |
| 20-shifted-rectangle | lobes | dirichlet / normal_flux / robin / normal_derivative | 2145 | 4096 | 0.012 / 0.32 |
| 21-sparse-binary | bubble | normal_flux / dirichlet / normal_derivative / robin | 1353 | 2560 | 0.003 / 0.08 |
| 22-unstructured | lobes | robin / normal_derivative / normal_flux / dirichlet | 2798 | 5402 | 0.003 / 0.08 |
| 23-initial-boundary-layer | plate | dirichlet / dirichlet / dirichlet / dirichlet | 7921 | 15488 | 0.003 / 0.08 |
| 24-insulated-gradient | gradient | normal_derivative / normal_flux / normal_flux / normal_derivative | 2401 | 4608 | 0.003 / 0.12 |
