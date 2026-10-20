# 第二章每题十例：设计草案清单

排除2.1.1、2.1.3。以下是630项工况提案，不是630个已制作输入，更不是已计算参考。

数值参数、现成生产者匹配和转换尚未完成的条目明确暂缓。全部工况完成设计前不启动批量计算；不恢复旧FOAMBench任务。

| 题号 | 工况族 | 草案 | 数值参数已固定 | 逐例设计 |
|---|---|---:|---:|---|
| 2.1.2 | closed_flow | 10 | 3 | [design.json](../../2.1-single-phase-flow/newtonian-incompressible-transient-2d/author/chapter02-ten-20261020/design.json) |
| 2.1.4 | closed_flow | 10 | 3 | [design.json](../../2.1-single-phase-flow/newtonian-incompressible-transient-3d/author/chapter02-ten-20261020/design.json) |
| 2.1.5 | generalized_flow | 10 | 0 | [design.json](../../2.1-single-phase-flow/generalized-newtonian-incompressible-steady-2d/author/chapter02-ten-20261020/design.json) |
| 2.1.6 | generalized_flow | 10 | 0 | [design.json](../../2.1-single-phase-flow/generalized-newtonian-incompressible-transient-2d/author/chapter02-ten-20261020/design.json) |
| 2.1.7 | generalized_flow | 10 | 0 | [design.json](../../2.1-single-phase-flow/generalized-newtonian-incompressible-steady-3d/author/chapter02-ten-20261020/design.json) |
| 2.1.8 | generalized_flow | 10 | 0 | [design.json](../../2.1-single-phase-flow/generalized-newtonian-incompressible-transient-3d/author/chapter02-ten-20261020/design.json) |
| 2.1.9 | isothermal_compressible | 10 | 0 | [design.json](../../2.1-single-phase-flow/newtonian-isothermal-compressible-steady-2d/author/chapter02-ten-20261020/design.json) |
| 2.1.10 | isothermal_compressible | 10 | 0 | [design.json](../../2.1-single-phase-flow/newtonian-isothermal-compressible-transient-2d/author/chapter02-ten-20261020/design.json) |
| 2.1.11 | isothermal_compressible | 10 | 0 | [design.json](../../2.1-single-phase-flow/newtonian-isothermal-compressible-steady-3d/author/chapter02-ten-20261020/design.json) |
| 2.1.12 | isothermal_compressible | 10 | 0 | [design.json](../../2.1-single-phase-flow/newtonian-isothermal-compressible-transient-3d/author/chapter02-ten-20261020/design.json) |
| 2.2.1 | lowmach_energy | 10 | 0 | [design.json](../../2.2-single-phase-energy/newtonian-lowmach-steady-2d/author/chapter02-ten-20261020/design.json) |
| 2.2.2 | lowmach_energy | 10 | 0 | [design.json](../../2.2-single-phase-energy/newtonian-lowmach-transient-2d/author/chapter02-ten-20261020/design.json) |
| 2.2.3 | lowmach_energy | 10 | 0 | [design.json](../../2.2-single-phase-energy/newtonian-lowmach-steady-3d/author/chapter02-ten-20261020/design.json) |
| 2.2.4 | lowmach_energy | 10 | 0 | [design.json](../../2.2-single-phase-energy/newtonian-lowmach-transient-3d/author/chapter02-ten-20261020/design.json) |
| 2.2.5 | euler_equilibrium | 10 | 0 | [design.json](../../2.2-single-phase-energy/inviscid-compressible-steady-2d/author/chapter02-ten-20261020/design.json) |
| 2.2.6 | euler_transient | 10 | 0 | [design.json](../../2.2-single-phase-energy/inviscid-compressible-transient-2d/author/chapter02-ten-20261020/design.json) |
| 2.2.7 | euler_equilibrium | 10 | 0 | [design.json](../../2.2-single-phase-energy/inviscid-compressible-steady-3d/author/chapter02-ten-20261020/design.json) |
| 2.2.8 | euler_transient | 10 | 0 | [design.json](../../2.2-single-phase-energy/inviscid-compressible-transient-3d/author/chapter02-ten-20261020/design.json) |
| 2.2.9 | compressible_energy | 10 | 0 | [design.json](../../2.2-single-phase-energy/newtonian-compressible-steady-2d/author/chapter02-ten-20261020/design.json) |
| 2.2.10 | compressible_energy | 10 | 0 | [design.json](../../2.2-single-phase-energy/newtonian-compressible-transient-2d/author/chapter02-ten-20261020/design.json) |
| 2.2.11 | compressible_energy | 10 | 0 | [design.json](../../2.2-single-phase-energy/newtonian-compressible-steady-3d/author/chapter02-ten-20261020/design.json) |
| 2.2.12 | compressible_energy | 10 | 0 | [design.json](../../2.2-single-phase-energy/newtonian-compressible-transient-3d/author/chapter02-ten-20261020/design.json) |
| 2.3.1 | turbulent_flow | 10 | 0 | [design.json](../../2.3-turbulent-flow/rans-steady-2d/author/chapter02-ten-20261020/design.json) |
| 2.3.2 | turbulent_flow | 10 | 0 | [design.json](../../2.3-turbulent-flow/rans-steady-3d/author/chapter02-ten-20261020/design.json) |
| 2.3.3 | turbulent_flow | 10 | 0 | [design.json](../../2.3-turbulent-flow/urans-transient-3d/author/chapter02-ten-20261020/design.json) |
| 2.3.4 | turbulent_flow | 10 | 0 | [design.json](../../2.3-turbulent-flow/resolved-statistics-3d/author/chapter02-ten-20261020/design.json) |
| 2.3.5 | turbulent_flow | 10 | 0 | [design.json](../../2.3-turbulent-flow/isothermal-rans-3d/author/chapter02-ten-20261020/design.json) |
| 2.4.1 | lowmach_energy | 10 | 0 | [design.json](../../2.4-turbulent-energy/thermal-rans-3d/author/chapter02-ten-20261020/design.json) |
| 2.4.2 | lowmach_energy | 10 | 0 | [design.json](../../2.4-turbulent-energy/thermal-urans-3d/author/chapter02-ten-20261020/design.json) |
| 2.4.3 | lowmach_energy | 10 | 0 | [design.json](../../2.4-turbulent-energy/thermal-statistics-3d/author/chapter02-ten-20261020/design.json) |
| 2.4.4 | compressible_energy | 10 | 0 | [design.json](../../2.4-turbulent-energy/compressible-thermal-rans-3d/author/chapter02-ten-20261020/design.json) |
| 2.5.1 | free_surface | 10 | 0 | [design.json](../../2.5-interface-flow/free-surface-2d/author/chapter02-ten-20261020/design.json) |
| 2.5.2 | free_surface | 10 | 0 | [design.json](../../2.5-interface-flow/free-surface-3d/author/chapter02-ten-20261020/design.json) |
| 2.5.3 | immiscible | 10 | 0 | [design.json](../../2.5-interface-flow/immiscible-interface-2d/author/chapter02-ten-20261020/design.json) |
| 2.5.4 | immiscible | 10 | 0 | [design.json](../../2.5-interface-flow/immiscible-interface-3d/author/chapter02-ten-20261020/design.json) |
| 2.5.5 | capillary | 10 | 0 | [design.json](../../2.5-interface-flow/capillary-wetting-2d/author/chapter02-ten-20261020/design.json) |
| 2.5.6 | capillary | 10 | 0 | [design.json](../../2.5-interface-flow/capillary-wetting-3d/author/chapter02-ten-20261020/design.json) |
| 2.6.1 | dispersed | 10 | 0 | [design.json](../../2.6-dispersed-flow/passive-particles-3d/author/chapter02-ten-20261020/design.json) |
| 2.6.2 | dispersed | 10 | 0 | [design.json](../../2.6-dispersed-flow/coupled-particles-3d/author/chapter02-ten-20261020/design.json) |
| 2.6.3 | dispersed | 10 | 0 | [design.json](../../2.6-dispersed-flow/bubbles-droplets-3d/author/chapter02-ten-20261020/design.json) |
| 2.6.4 | dispersed | 10 | 0 | [design.json](../../2.6-dispersed-flow/dense-dispersed-3d/author/chapter02-ten-20261020/design.json) |
| 2.7.1 | exchange | 10 | 0 | [design.json](../../2.7-phase-change-flow/interphase-exchange-3d/author/chapter02-ten-20261020/design.json) |
| 2.7.2 | evaporation | 10 | 0 | [design.json](../../2.7-phase-change-flow/evaporation-condensation-2d/author/chapter02-ten-20261020/design.json) |
| 2.7.3 | boiling | 10 | 0 | [design.json](../../2.7-phase-change-flow/boiling-3d/author/chapter02-ten-20261020/design.json) |
| 2.7.4 | cavitation | 10 | 0 | [design.json](../../2.7-phase-change-flow/cavitation-3d/author/chapter02-ten-20261020/design.json) |
| 2.7.5 | melting | 10 | 0 | [design.json](../../2.7-phase-change-flow/melting-solidification-2d/author/chapter02-ten-20261020/design.json) |
| 2.8.1 | liquid_film | 10 | 0 | [design.json](../../2.8-thin-film/liquid-lubrication/author/chapter02-ten-20261020/design.json) |
| 2.8.2 | gas_film | 10 | 0 | [design.json](../../2.8-thin-film/gas-film/author/chapter02-ten-20261020/design.json) |
| 2.8.3 | thermal_film | 10 | 0 | [design.json](../../2.8-thin-film/thermal-film/author/chapter02-ten-20261020/design.json) |
| 2.8.4 | nonnewtonian_film | 10 | 0 | [design.json](../../2.8-thin-film/nonnewtonian-film/author/chapter02-ten-20261020/design.json) |
| 2.9.1 | shallow_steady | 10 | 0 | [design.json](../../2.9-shallow-water/fully-wet-steady/author/chapter02-ten-20261020/design.json) |
| 2.9.2 | shallow_transient | 10 | 0 | [design.json](../../2.9-shallow-water/fully-wet-transient/author/chapter02-ten-20261020/design.json) |
| 2.9.3 | wetdry | 10 | 0 | [design.json](../../2.9-shallow-water/wetting-drying/author/chapter02-ten-20261020/design.json) |
| 2.9.4 | two_layer | 10 | 0 | [design.json](../../2.9-shallow-water/two-layer/author/chapter02-ten-20261020/design.json) |
| 2.10.1 | slip_gas | 10 | 0 | [design.json](../../2.10-rarefied-gas/isothermal-slip/author/chapter02-ten-20261020/design.json) |
| 2.10.2 | slip_gas | 10 | 0 | [design.json](../../2.10-rarefied-gas/thermal-slip/author/chapter02-ten-20261020/design.json) |
| 2.10.3 | kinetic_gas | 10 | 0 | [design.json](../../2.10-rarefied-gas/transition-gas/author/chapter02-ten-20261020/design.json) |
| 2.10.4 | kinetic_gas | 10 | 0 | [design.json](../../2.10-rarefied-gas/free-molecular/author/chapter02-ten-20261020/design.json) |
| 2.11.1 | viscoelastic | 10 | 0 | [design.json](../../2.11-memory-fluids/viscoelastic-steady/author/chapter02-ten-20261020/design.json) |
| 2.11.2 | viscoelastic | 10 | 0 | [design.json](../../2.11-memory-fluids/viscoelastic-transient/author/chapter02-ten-20261020/design.json) |
| 2.11.3 | thixotropic | 10 | 0 | [design.json](../../2.11-memory-fluids/thixotropic-transient/author/chapter02-ten-20261020/design.json) |
| 2.11.4 | thermal_generalized | 10 | 0 | [design.json](../../2.11-memory-fluids/thermal-generalized-newtonian/author/chapter02-ten-20261020/design.json) |
| 2.11.5 | viscoelastic | 10 | 0 | [design.json](../../2.11-memory-fluids/thermal-viscoelastic/author/chapter02-ten-20261020/design.json) |
