# 追加本地遗漏检查

本轮只读检索 git worktree 列表及 D:/Code 下已知相关 checkout 的限定元数据；未搬运数据、未下载、未远端连接、未新验收。

## 重要补充：独立组合 Benchmark 克隆

`D:\Code\CAE-Bench-OJ-ch02-benchmark` 不在当前仓库的 `git worktree list`，但本地已有大量装配产物。当前分支 `benchmark/combined-cae-pde-foam-cfd`，HEAD `09890baebc264d1993fa89f6476a54c4167dcb02`。

既有 `benchmarks/combined/readiness.json` 快照：2026-10-21T22:06:03.381129+00:00，此历史快照只说明消费准备状态，不是本轮数值资格认定。

| 套件 | 历史范围题数 | 已准备题数 | 已准备正式 case |
|---|---:|---:|---:|
| cfdcodebench | 24 | 24 | 24 |
| chapter02 | 40 | 40 | 329 |
| foambench | 126 | 51 | 51 |
| pdebench | 11 | 11 | 210 |

**第二章40题/329例中309例明确为Titan未验证候选，另20例为既有参考；不得把本地存在或prepared称为数值验收。** 这些输入已在本地，无需先去HF或Titan重取。

第1章11个PDEBench family已有210正式输入/参考；样例另计且可能重叠，既有暂定容差/资源仍需复核。FOAMBench本地有51个一case题，另外75题不能由此推断缺少原生资产；要接续源目录/远端账本。

## 逐题现存正式数据

| 题目路径（相对该克隆qbank） | 正式输入 | 参考 |
|---|---:|---:|
| `01-prescribed-pdes/1.1-elliptic/darcy-flow-2d` | 20 | 20 |
| `01-prescribed-pdes/1.2-diffusion-reaction/diffusion-sorption-1d` | 16 | 16 |
| `01-prescribed-pdes/1.2-diffusion-reaction/reaction-diffusion-1d` | 32 | 32 |
| `01-prescribed-pdes/1.2-diffusion-reaction/reaction-diffusion-2d` | 16 | 16 |
| `01-prescribed-pdes/1.3-scalar-transport/advection-1d` | 24 | 24 |
| `01-prescribed-pdes/1.4-hyperbolic/shallow-water-2d` | 16 | 16 |
| `01-prescribed-pdes/1.5-advection-diffusion/burgers-1d` | 24 | 24 |
| `01-prescribed-pdes/1.6-constrained-systems/incompressible-navier-stokes-2d` | 16 | 16 |
| `01-prescribed-pdes/1.7-coupled-systems/compressible-navier-stokes-1d` | 16 | 16 |
| `01-prescribed-pdes/1.7-coupled-systems/compressible-navier-stokes-2d` | 24 | 24 |
| `01-prescribed-pdes/1.7-coupled-systems/compressible-navier-stokes-3d` | 6 | 6 |
| `02-fluid-mechanics/2.1-single-phase-flow/generalized-newtonian-incompressible-steady-2d` | 8 | 8 |
| `02-fluid-mechanics/2.1-single-phase-flow/generalized-newtonian-incompressible-steady-3d` | 7 | 7 |
| `02-fluid-mechanics/2.1-single-phase-flow/generalized-newtonian-incompressible-transient-2d` | 8 | 8 |
| `02-fluid-mechanics/2.1-single-phase-flow/generalized-newtonian-incompressible-transient-3d` | 8 | 8 |
| `02-fluid-mechanics/2.1-single-phase-flow/newtonian-incompressible-steady-2d` | 10 | 10 |
| `02-fluid-mechanics/2.1-single-phase-flow/newtonian-incompressible-steady-3d` | 10 | 10 |
| `02-fluid-mechanics/2.1-single-phase-flow/newtonian-incompressible-transient-2d` | 10 | 10 |
| `02-fluid-mechanics/2.1-single-phase-flow/newtonian-incompressible-transient-3d` | 10 | 10 |
| `02-fluid-mechanics/2.1-single-phase-flow/newtonian-isothermal-compressible-steady-2d` | 3 | 3 |
| `02-fluid-mechanics/2.1-single-phase-flow/newtonian-isothermal-compressible-steady-3d` | 3 | 3 |
| `02-fluid-mechanics/2.1-single-phase-flow/newtonian-isothermal-compressible-transient-2d` | 5 | 5 |
| `02-fluid-mechanics/2.1-single-phase-flow/newtonian-isothermal-compressible-transient-3d` | 5 | 5 |
| `02-fluid-mechanics/2.10-rarefied-gas/free-molecular` | 10 | 10 |
| `02-fluid-mechanics/2.10-rarefied-gas/transition-gas` | 10 | 10 |
| `02-fluid-mechanics/2.11-memory-fluids/viscoelastic-steady` | 9 | 9 |
| `02-fluid-mechanics/2.11-memory-fluids/viscoelastic-transient` | 9 | 9 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-cavity-1` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-cavity-10` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-cavity-2` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-cavity-3` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-cavity-4` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-cavity-5` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-cavity-6` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-cavity-7` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-cavity-8` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-cavity-9` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-cylinder-1` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-cylinder-10` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-cylinder-2` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-cylinder-3` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-cylinder-4` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-cylinder-5` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-cylinder-6` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-cylinder-7` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-cylinder-8` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-cylinder-9` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-forwardstep-1` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-forwardstep-10` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-forwardstep-2` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-forwardstep-3` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-forwardstep-4` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-forwardstep-5` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-forwardstep-6` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-forwardstep-7` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-forwardstep-8` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-forwardstep-9` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-obliqueshock-1` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-obliqueshock-10` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-obliqueshock-2` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-obliqueshock-3` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-obliqueshock-4` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-obliqueshock-5` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-obliqueshock-6` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-obliqueshock-7` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-obliqueshock-8` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-obliqueshock-9` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-shallowwaterwithsquarebump-1` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-wedge-1` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-wedge-10` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-wedge-2` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-wedge-3` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-wedge-4` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-wedge-5` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-wedge-6` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-wedge-7` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-wedge-8` | 1 | 1 |
| `02-fluid-mechanics/2.12-foambench/fb-basic-wedge-9` | 1 | 1 |
| `02-fluid-mechanics/2.13-cfdcodebench/cc-1d-burgers-equation` | 1 | 1 |
| `02-fluid-mechanics/2.13-cfdcodebench/cc-1d-diffusion` | 1 | 1 |
| `02-fluid-mechanics/2.13-cfdcodebench/cc-1d-euler-shock-tube` | 1 | 1 |
| `02-fluid-mechanics/2.13-cfdcodebench/cc-1d-kdv-burgers-equation` | 1 | 1 |
| `02-fluid-mechanics/2.13-cfdcodebench/cc-1d-linear-convection` | 1 | 1 |
| `02-fluid-mechanics/2.13-cfdcodebench/cc-1d-nonlinear-convection` | 1 | 1 |
| `02-fluid-mechanics/2.13-cfdcodebench/cc-2d-burgers-equation` | 1 | 1 |
| `02-fluid-mechanics/2.13-cfdcodebench/cc-2d-convection` | 1 | 1 |
| `02-fluid-mechanics/2.13-cfdcodebench/cc-2d-diffusion` | 1 | 1 |
| `02-fluid-mechanics/2.13-cfdcodebench/cc-2d-inviscid-burgers` | 1 | 1 |
| `02-fluid-mechanics/2.13-cfdcodebench/cc-2d-laplace-equation` | 1 | 1 |
| `02-fluid-mechanics/2.13-cfdcodebench/cc-2d-linear-convection` | 1 | 1 |
| `02-fluid-mechanics/2.13-cfdcodebench/cc-2d-navier-stokes-cavity` | 1 | 1 |
| `02-fluid-mechanics/2.13-cfdcodebench/cc-2d-navier-stokes-channel` | 1 | 1 |
| `02-fluid-mechanics/2.13-cfdcodebench/cc-2d-poisson-equation` | 1 | 1 |
| `02-fluid-mechanics/2.13-cfdcodebench/cc-2d-rayleigh-benard-convection` | 1 | 1 |
| `02-fluid-mechanics/2.13-cfdcodebench/cc-2d-shear-flow-with-tracer` | 1 | 1 |
| `02-fluid-mechanics/2.13-cfdcodebench/cc-2d-steady-heat-equation` | 1 | 1 |
| `02-fluid-mechanics/2.13-cfdcodebench/cc-2d-unsteady-heat-equation` | 1 | 1 |
| `02-fluid-mechanics/2.13-cfdcodebench/cc-flow-past-circular-cylinder` | 1 | 1 |
| `02-fluid-mechanics/2.13-cfdcodebench/cc-fully-developed-turbulent-channel-flow` | 1 | 1 |
| `02-fluid-mechanics/2.13-cfdcodebench/cc-lane-emden-equation` | 1 | 1 |
| `02-fluid-mechanics/2.13-cfdcodebench/cc-lid-driven-cavity` | 1 | 1 |
| `02-fluid-mechanics/2.13-cfdcodebench/cc-pipe-flow-disk-evp` | 1 | 1 |
| `02-fluid-mechanics/2.2-single-phase-energy/inviscid-compressible-steady-2d` | 10 | 10 |
| `02-fluid-mechanics/2.2-single-phase-energy/inviscid-compressible-steady-3d` | 10 | 10 |
| `02-fluid-mechanics/2.2-single-phase-energy/inviscid-compressible-transient-2d` | 10 | 10 |
| `02-fluid-mechanics/2.2-single-phase-energy/inviscid-compressible-transient-3d` | 10 | 10 |
| `02-fluid-mechanics/2.2-single-phase-energy/newtonian-compressible-transient-2d` | 5 | 5 |
| `02-fluid-mechanics/2.2-single-phase-energy/newtonian-compressible-transient-3d` | 5 | 5 |
| `02-fluid-mechanics/2.2-single-phase-energy/newtonian-lowmach-steady-2d` | 10 | 10 |
| `02-fluid-mechanics/2.2-single-phase-energy/newtonian-lowmach-steady-3d` | 10 | 10 |
| `02-fluid-mechanics/2.2-single-phase-energy/newtonian-lowmach-transient-2d` | 10 | 10 |
| `02-fluid-mechanics/2.2-single-phase-energy/newtonian-lowmach-transient-3d` | 10 | 10 |
| `02-fluid-mechanics/2.3-turbulent-flow/isothermal-rans-3d` | 7 | 7 |
| `02-fluid-mechanics/2.3-turbulent-flow/rans-steady-2d` | 8 | 8 |
| `02-fluid-mechanics/2.3-turbulent-flow/rans-steady-3d` | 7 | 7 |
| `02-fluid-mechanics/2.3-turbulent-flow/resolved-statistics-3d` | 10 | 10 |
| `02-fluid-mechanics/2.3-turbulent-flow/urans-transient-3d` | 10 | 10 |
| `02-fluid-mechanics/2.4-turbulent-energy/thermal-rans-3d` | 9 | 9 |
| `02-fluid-mechanics/2.4-turbulent-energy/thermal-statistics-3d` | 10 | 10 |
| `02-fluid-mechanics/2.4-turbulent-energy/thermal-urans-3d` | 4 | 4 |
| `02-fluid-mechanics/2.5-interface-flow/immiscible-interface-2d` | 10 | 10 |
| `02-fluid-mechanics/2.5-interface-flow/immiscible-interface-3d` | 10 | 10 |
| `02-fluid-mechanics/2.8-thin-film/gas-film` | 10 | 10 |
| `02-fluid-mechanics/2.9-shallow-water/fully-wet-steady` | 3 | 3 |
| `02-fluid-mechanics/2.9-shallow-water/fully-wet-transient` | 9 | 9 |
| `02-fluid-mechanics/2.9-shallow-water/wetting-drying` | 7 | 7 |

逐case名称、manifest选中ID与摘要见 `extra-findings.json`。这批记录必须与主清单按task/case身份去重，而不能直接累加题数。

## 额外资产入口

- `benchmarks/chapter02-existing/selection.json`：40题329例的固定选择、offline_pool路径、摘要、现有参考资格。
- `benchmarks/combined/scope.json` / `readiness.json`：chapter02、PDEBench、CFDCodeBench、FOAMBench组合范围。
- `work/ch02-pools`、`ch02-fixed-pools`、`ch02-coverage-pools`、`random-format-pools`：原始/修复/覆盖/随机格式样例离线池。公开样例输出在此克隆为随机格式，不是科学参考。
- `work/hf-pdebench`：既有本地HF缓存；只登记存在，未重新下载。
- `work/titan-candidates/cases`、`inventory.json`：已取回Titan候选。
- `work/foam-staged`、`foam-wall-staged`、`foam-shallow-staged`：FOAMBench本地适配产物。
- `work/retired-numerical-sample-references`：历史退役样例参考，不能默认为现行公开材料。
- `runs/chapter02-benchmark`：输入修复、消费链、Linux闭包证据；不替代数值验证。
- `D:/Code/CAE-Bench-OJ-211`：另有2.1.1完整100输入/100参考；需与extra80/211补充选择去重。
- `D:/Code/foambench-reference-staging`：OpenFOAM10镜像分层/归档等环境缓存，不是新数值case。
- `D:/Code/.caeoj-transfer/feelpp-v0.111.0`：环境传输目录；未读取内容或移动。

第0章：限定检查多个checkout的qbank/00-basic-tests没有HDF5；不据此认定缺例，因为基础测试可能采用其他数据格式。未遍历私人主目录全盘、未查看凭据。

## 环境暂存目录的有界复核

`D:/Code/.caeoj-transfer` 根目录仅 `feelpp-v0.111.0`。其 `transfer-status.json` 明确 `solver_started: false`，状态为 `completed_after_import_identity_review`，镜像 `sha256:c5a7643109973d30c9b2a1adb9a2d18579129bbfba28bb659254a0fa9489de95`，OCI归档2,800,476,160字节；`source/`仅Feel++求解器实现头文件/源文件片段，未发现独立题面/case批次目录。

`D:/Code/foambench-reference-staging/image-acquisition.json` 记录官方 `openfoam/openfoam10-paraview510`，manifest `sha256:d6ff1f9a2e7bc3c9177f373bebbdeb542fd8b49144afc24d5e3a3cd9bfae253d`，归档3,233,669,120字节且镜像层摘要已验证。限定根目录为镜像层、tar与镜像获取元数据，未发现新增数值case。没有解包这些大型环境归档。
