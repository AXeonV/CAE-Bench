# 第二章发行装配就绪审计

只读复用本地已有选择；未下载、连接 Titan、组装、启动求解器或模型。此报告不授予干净机器发行认证。

## 推荐范围

26题44例进入内部RC装配：2.1.1和2.1.3各10例，加CFDCodeBench24题各1例。FOAM51及其他41道能力候选暂缓：参考数值资格未完成（其中3题仅远端新增）。无case的97题排除。

CFD24的资源并非完全空白：已有4CPU/8192MiB离线Docker生产表示测量，且本轮核对配置摘要；旧盘点的provisional标签应以此具体证据补充。C19保留用户已接受的NMSE例外；C20—22保留只有同求解器加密、缺少不同求解器验证的限制。全部CFD题唯一输入已公开，不提供未见输入泛化证明。

本轮对26题44例实际执行原checkout运行时的strict verify、输入验证、参考输出验证和参考自判分；全部通过。自判分不重新证明数值正确；CFD历史索引的参考摘要已逐题绑定。

## 每题现有选择

|题号/套件|task|选定例数|结论|
|---|---|---:|---|
|2.1.1|newtonian-incompressible-steady-2d|10|进入内部RC|
|2.1.2|newtonian-incompressible-transient-2d|10|暂缓|
|2.1.3|newtonian-incompressible-steady-3d|10|进入内部RC|
|2.1.4|newtonian-incompressible-transient-3d|10|暂缓|
|2.1.5|generalized-newtonian-incompressible-steady-2d|8|暂缓|
|2.1.6|generalized-newtonian-incompressible-transient-2d|8|暂缓|
|2.1.7|generalized-newtonian-incompressible-steady-3d|7|暂缓|
|2.1.8|generalized-newtonian-incompressible-transient-3d|8|暂缓|
|2.1.9|newtonian-isothermal-compressible-steady-2d|3|暂缓|
|2.1.10|newtonian-isothermal-compressible-transient-2d|5|暂缓|
|2.1.11|newtonian-isothermal-compressible-steady-3d|3|暂缓|
|2.1.12|newtonian-isothermal-compressible-transient-3d|5|暂缓|
|2.2.1|newtonian-lowmach-steady-2d|10|暂缓|
|2.2.2|newtonian-lowmach-transient-2d|10|暂缓|
|2.2.3|newtonian-lowmach-steady-3d|10|暂缓|
|2.2.4|newtonian-lowmach-transient-3d|10|暂缓|
|2.2.5|inviscid-compressible-steady-2d|10|暂缓|
|2.2.6|inviscid-compressible-transient-2d|10|暂缓|
|2.2.7|inviscid-compressible-steady-3d|10|暂缓|
|2.2.8|inviscid-compressible-transient-3d|10|暂缓|
|2.2.9|newtonian-compressible-steady-2d|0|暂缓|
|2.2.10|newtonian-compressible-transient-2d|5|暂缓|
|2.2.11|newtonian-compressible-steady-3d|0|暂缓|
|2.2.12|newtonian-compressible-transient-3d|5|暂缓|
|2.3.1|rans-steady-2d|8|暂缓|
|2.3.2|rans-steady-3d|7|暂缓|
|2.3.3|urans-transient-3d|10|暂缓|
|2.3.4|resolved-statistics-3d|10|暂缓|
|2.3.5|isothermal-rans-3d|7|暂缓|
|2.4.1|thermal-rans-3d|9|暂缓|
|2.4.2|thermal-urans-3d|4|暂缓|
|2.4.3|thermal-statistics-3d|10|暂缓|
|2.4.4|compressible-thermal-rans-3d|0|暂缓|
|2.5.3|immiscible-interface-2d|10|暂缓|
|2.5.4|immiscible-interface-3d|10|暂缓|
|2.8.2|gas-film|10|暂缓|
|2.9.1|fully-wet-steady|3|暂缓|
|2.9.2|fully-wet-transient|9|暂缓|
|2.9.3|wetting-drying|7|暂缓|
|2.10.3|transition-gas|10|暂缓|
|2.10.4|free-molecular|10|暂缓|
|2.11.1|viscoelastic-steady|9|暂缓|
|2.11.2|viscoelastic-transient|9|暂缓|
|2.12.1|fb-basic-obliqueshock-7|1|暂缓|
|2.12.2|fb-basic-obliqueshock-6|1|暂缓|
|2.12.3|fb-basic-obliqueshock-3|1|暂缓|
|2.12.4|fb-basic-obliqueshock-5|1|暂缓|
|2.12.5|fb-basic-obliqueshock-2|1|暂缓|
|2.12.6|fb-basic-obliqueshock-4|1|暂缓|
|2.12.7|fb-basic-obliqueshock-1|1|暂缓|
|2.12.8|fb-basic-obliqueshock-9|1|暂缓|
|2.12.9|fb-basic-obliqueshock-10|1|暂缓|
|2.12.10|fb-basic-obliqueshock-8|1|暂缓|
|2.12.51|fb-basic-forwardstep-7|1|暂缓|
|2.12.52|fb-basic-forwardstep-6|1|暂缓|
|2.12.53|fb-basic-forwardstep-3|1|暂缓|
|2.12.54|fb-basic-forwardstep-5|1|暂缓|
|2.12.55|fb-basic-forwardstep-2|1|暂缓|
|2.12.56|fb-basic-forwardstep-4|1|暂缓|
|2.12.57|fb-basic-forwardstep-1|1|暂缓|
|2.12.58|fb-basic-forwardstep-9|1|暂缓|
|2.12.59|fb-basic-forwardstep-10|1|暂缓|
|2.12.60|fb-basic-forwardstep-8|1|暂缓|
|2.12.71|fb-basic-wedge-7|1|暂缓|
|2.12.72|fb-basic-wedge-6|1|暂缓|
|2.12.73|fb-basic-wedge-3|1|暂缓|
|2.12.74|fb-basic-wedge-5|1|暂缓|
|2.12.75|fb-basic-wedge-2|1|暂缓|
|2.12.76|fb-basic-wedge-4|1|暂缓|
|2.12.77|fb-basic-wedge-1|1|暂缓|
|2.12.78|fb-basic-wedge-9|1|暂缓|
|2.12.79|fb-basic-wedge-10|1|暂缓|
|2.12.80|fb-basic-wedge-8|1|暂缓|
|2.12.87|fb-basic-shallowwaterwithsquarebump-1|1|暂缓|
|2.12.91|fb-basic-cavity-7|1|暂缓|
|2.12.92|fb-basic-cavity-6|1|暂缓|
|2.12.93|fb-basic-cavity-3|1|暂缓|
|2.12.94|fb-basic-cavity-5|1|暂缓|
|2.12.95|fb-basic-cavity-2|1|暂缓|
|2.12.96|fb-basic-cavity-4|1|暂缓|
|2.12.97|fb-basic-cavity-1|1|暂缓|
|2.12.98|fb-basic-cavity-9|1|暂缓|
|2.12.99|fb-basic-cavity-10|1|暂缓|
|2.12.100|fb-basic-cavity-8|1|暂缓|
|2.12.101|fb-basic-cylinder-7|1|暂缓|
|2.12.102|fb-basic-cylinder-6|1|暂缓|
|2.12.103|fb-basic-cylinder-3|1|暂缓|
|2.12.104|fb-basic-cylinder-5|1|暂缓|
|2.12.105|fb-basic-cylinder-2|1|暂缓|
|2.12.106|fb-basic-cylinder-4|1|暂缓|
|2.12.107|fb-basic-cylinder-1|1|暂缓|
|2.12.108|fb-basic-cylinder-9|1|暂缓|
|2.12.109|fb-basic-cylinder-10|1|暂缓|
|2.12.110|fb-basic-cylinder-8|1|暂缓|
|cfdcodebench|cc-1d-burgers-equation|1|进入内部RC|
|cfdcodebench|cc-1d-diffusion|1|进入内部RC|
|cfdcodebench|cc-1d-euler-shock-tube|1|进入内部RC|
|cfdcodebench|cc-1d-linear-convection|1|进入内部RC|
|cfdcodebench|cc-1d-nonlinear-convection|1|进入内部RC|
|cfdcodebench|cc-2d-burgers-equation|1|进入内部RC|
|cfdcodebench|cc-2d-convection|1|进入内部RC|
|cfdcodebench|cc-2d-diffusion|1|进入内部RC|
|cfdcodebench|cc-2d-inviscid-burgers|1|进入内部RC|
|cfdcodebench|cc-2d-laplace-equation|1|进入内部RC|
|cfdcodebench|cc-2d-linear-convection|1|进入内部RC|
|cfdcodebench|cc-2d-navier-stokes-cavity|1|进入内部RC|
|cfdcodebench|cc-2d-navier-stokes-channel|1|进入内部RC|
|cfdcodebench|cc-2d-poisson-equation|1|进入内部RC|
|cfdcodebench|cc-2d-steady-heat-equation|1|进入内部RC|
|cfdcodebench|cc-2d-unsteady-heat-equation|1|进入内部RC|
|cfdcodebench|cc-fully-developed-turbulent-channel-flow|1|进入内部RC|
|cfdcodebench|cc-lid-driven-cavity|1|进入内部RC|
|cfdcodebench|cc-flow-past-circular-cylinder|1|进入内部RC|
|cfdcodebench|cc-1d-kdv-burgers-equation|1|进入内部RC|
|cfdcodebench|cc-2d-rayleigh-benard-convection|1|进入内部RC|
|cfdcodebench|cc-2d-shear-flow-with-tracer|1|进入内部RC|
|cfdcodebench|cc-pipe-flow-disk-evp|1|进入内部RC|
|cfdcodebench|cc-lane-emden-equation|1|进入内部RC|

## 消费闭包与分发注意

- 现有ZIP在来源checkout的dist/<task>-agent.zip，Harbor闭包在runs/harbor/tasks/<task>；各题绝对路径、manifest/zip摘要、case ID、样例数量、许可路径在同名JSON。
- 来源checkout为D:/Code/CAE-Bench-OJ-ch02-benchmark，HEAD 09890baebc264d1993fa89f6476a54c4167dcb02。
- 本轮验证使用来源checkout的现有.venv与src；src/caeoj消费运行时与当前主分支逐文件相同；JSON runtime_source_differences列出的9项差异集中于作者数据装配、format-sample辅助、打包及Harbor judge。整合须保留当前修复题机制，再做发行消费验证。
- CFD上游BSD-3-Clause原文位于2.13-cfdcodebench/author/UPSTREAM-LICENSE.txt，发行必须将其作为NOTICE/许可材料保留；仅复制公开ZIP未证明许可证已进入ZIP。
- 公开ZIP路径检查未发现author/reference目录，不代替完整泄漏审计。不得复制作者生产者、隐藏参考和gold结果到考生包。
- 受托判分端需要隐藏reference和grading，团队内可交付独立verifier载荷；应与agent ZIP区分权限。
- 来源checkout原生公开包已含固定输入format样例，真实答案私有；禁止用随机格式样例当作物理reference。
