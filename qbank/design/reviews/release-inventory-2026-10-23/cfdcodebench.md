# 另工作树：CFDCodeBench 24题（待用户确认纳入）

当前主分支102个有题面目录之外的既有资产；位于 codex/cfdcodebench-release 工作树，现有路径全部在2.13-cfdcodebench。本稿保留原归属，不擅自移动／合并；需检查与第1章及第2章问题族的重叠。每题当前选择一个原始工况，另作format样例，不增加独立case数。主分支2.13目录实际已有24例cases/reference和装配回执，但缺题面及manifest；另一工作树有题面和manifest但没有正式payload。二者须关联，不能各自当作完整题。历史资源仍provisional。本轮仅查文件与记录，未复验数值。

早期qbank-assembly快照只有23例、排除C19；后续completion-pipeline报告24已验证且C19获接受。两阶段证据保留，不用旧23例快照覆盖后续材料。

|编号|题目|原始case|稳定case ID|本地输入／参考|样例|
|---|---|---|---|---|---|
|C01|[一维周期黏性 Burgers](../../../../work/cfdcodebench-pr-20261020/qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-1d-burgers-equation/instruction.md)|C01-base|`case-5390882b3086ee073725ac72`|均存在|01（format，同例）|
|C02|[一维矩形初态扩散](../../../../work/cfdcodebench-pr-20261020/qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-1d-diffusion/instruction.md)|C02-base|`case-9ff31700aa9f29249ea3ed44`|均存在|01（format，同例）|
|C03|[理想气体激波管](../../../../work/cfdcodebench-pr-20261020/qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-1d-euler-shock-tube/instruction.md)|C03-base|`case-28f510a4a44974560c6d0173`|均存在|01（format，同例）|
|C04|[一维周期对流扩散](../../../../work/cfdcodebench-pr-20261020/qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-1d-linear-convection/instruction.md)|C04-base|`case-3a5317962ebd9952803bf4a4`|均存在|01（format，同例）|
|C05|[一维非线性熵输运](../../../../work/cfdcodebench-pr-20261020/qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-1d-nonlinear-convection/instruction.md)|C05-base|`case-3d51485d43e942d046f0ffa1`|均存在|01（format，同例）|
|C06|[二维黏性 Burgers](../../../../work/cfdcodebench-pr-20261020/qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-burgers-equation/instruction.md)|C06-base|`case-fc80694115ec194556222d1c`|均存在|01（format，同例）|
|C07|[二维对角熵输运（终时 0.32）](../../../../work/cfdcodebench-pr-20261020/qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-convection/instruction.md)|C07-base|`case-d1f7ff870daaa6c0afcc590a`|均存在|01（format，同例）|
|C08|[二维矩形初态扩散](../../../../work/cfdcodebench-pr-20261020/qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-diffusion/instruction.md)|C08-base|`case-5184524280c8e692870618a4`|均存在|01（format，同例）|
|C09|[二维对角熵输运（终时 0.40）](../../../../work/cfdcodebench-pr-20261020/qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-inviscid-burgers/instruction.md)|C09-base|`case-704821710cfe0edbe6ef1df9`|均存在|01（format，同例）|
|C10|[矩形混合边界 Laplace 势](../../../../work/cfdcodebench-pr-20261020/qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-laplace-equation/instruction.md)|C10-base|`case-1b37c21a82fc6c79b15c2b97`|均存在|01（format，同例）|
|C11|[二维线性脉冲平移](../../../../work/cfdcodebench-pr-20261020/qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-linear-convection/instruction.md)|C11-base|`case-f2da240f1c6b1d7092a18f87`|均存在|01（format，同例）|
|C12|[不可压盖驱方腔（黏度 0.01）](../../../../work/cfdcodebench-pr-20261020/qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-navier-stokes-cavity/instruction.md)|C12-base|`case-5a50e5aa6abcd56bbe5c98ae`|均存在|01（format，同例）|
|C13|[周期通道启动流](../../../../work/cfdcodebench-pr-20261020/qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-navier-stokes-channel/instruction.md)|C13-base|`case-16d26ea0dfec27aa05740026`|均存在|01（format，同例）|
|C14|[双 Gaussian 源 Poisson 势](../../../../work/cfdcodebench-pr-20261020/qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-poisson-equation/instruction.md)|C14-base|`case-3cba5b83636f310810de3bfe`|均存在|01（format，同例）|
|C15|[四边恒温矩形稳态传热](../../../../work/cfdcodebench-pr-20261020/qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-steady-heat-equation/instruction.md)|C15-base|`case-04e385900f33962af70318f0`|均存在|01（format，同例）|
|C16|[Gaussian 初温与持续热源](../../../../work/cfdcodebench-pr-20261020/qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-unsteady-heat-equation/instruction.md)|C16-base|`case-df5cb01460655c0e7683fc47`|均存在|01（format，同例）|
|C17|[Cess 闭合双壁湍流通道](../../../../work/cfdcodebench-pr-20261020/qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-fully-developed-turbulent-channel-flow/instruction.md)|C17-base|`case-a2505f8e6cd8d72951d2eb72`|均存在|01（format，同例）|
|C18|[不可压盖驱方腔（黏度 0.1）](../../../../work/cfdcodebench-pr-20261020/qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-lid-driven-cavity/instruction.md)|C18-base|`case-2e84a351917193882c861a23`|均存在|01（format，同例）|
|C19|[圆柱外圆环涡量流函数流动](../../../../work/cfdcodebench-pr-20261020/qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-flow-past-circular-cylinder/instruction.md)|C19-base|`case-8c324d7724ce2f3aa6d6e7ee`|均存在|01（format，同例）|
|C20|[周期 KdV–Burgers](../../../../work/cfdcodebench-pr-20261020/qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-1d-kdv-burgers-equation/instruction.md)|C20-base|`case-6fecc6bf178d5d92bbcee935`|均存在|01（format，同例）|
|C21|[二维 Rayleigh–Bénard 对流](../../../../work/cfdcodebench-pr-20261020/qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-rayleigh-benard-convection/instruction.md)|C21-base|`case-98e927bc60fb44792c1ad75b`|均存在|01（format，同例）|
|C22|[周期剪切流与被动示踪剂](../../../../work/cfdcodebench-pr-20261020/qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-shear-flow-with-tracer/instruction.md)|C22-base|`case-887658c521f21ab1f95cfc3f`|均存在|01（format，同例）|
|C23|[圆管扰动的最右增长率](../../../../work/cfdcodebench-pr-20261020/qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-pipe-flow-disk-evp/instruction.md)|C23-base|`case-0cd3ba14ec4c3394600134b2`|均存在|01（format，同例）|
|C24|[Lane–Emden 正基态](../../../../work/cfdcodebench-pr-20261020/qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-lane-emden-equation/instruction.md)|C24-base|`case-d0737353898e08938bf00a94`|均存在|01（format，同例）|

## 证据与限制

- 题面与选择：`work/cfdcodebench-pr-20261020/qbank/02-fluid-mechanics/2.13-cfdcodebench/*/data-manifest.json`。
- 本地24例：`runs/cfdcodebench-local-20261019/local-pool/`。
- 历史资格：`runs/cfdcodebench-local-20261019/certification.json`。
- 后续流水线：`runs/cfdcodebench-local-20261019/completion-pipeline.json`。
- C19流场重建、C20—22同引擎收敛、C23条件数等限制须随题保留；历史标签不等于新发行验收通过。

逐题原始限制：

- cc-2d-unsteady-heat-equation：[{"steady_comparison_uniform_transient_bound": 3.636429214230108e-06, "method": "sum of absolute heat-mode coefficients; higher modes exponentially suppressed"}]
- cc-flow-past-circular-cylinder：["OpenFOAM psi/omega are reconstructed from velocity; reconstruction and exterior streamfunction closure require separate audit", "Pairwise differences are verification evidence, not a rigorous exact-solution error bound; prior NRMSE<=0.01 failures are retained in historical evidence."]
- cc-1d-kdv-burgers-equation：["Space/time checks use the same Dedalus engine and equation configuration; not an independent solver cross-validation"]
- cc-2d-rayleigh-benard-convection：["Space/time checks use the same Dedalus engine and equation configuration; not an independent solver cross-validation"]
- cc-2d-shear-flow-with-tracer：["Space/time checks use the same Dedalus engine and equation configuration; not an independent solver cross-validation"]
- cc-pipe-flow-disk-evp：[{"independent_Galerkin_mass_condition": 55200661980102.74, "note": "Ill-conditioning recorded; convergence at order32/48 is required along with residuals"}]

另已找到完整本地副本：`D:/Code/CAE-Bench-OJ-ch02-benchmark/qbank/02-fluid-mechanics/2.13-cfdcodebench/`，24题题面、manifest、正式输入和参考齐全；逐题stable case ID与另一工作树一致。可优先作为现成资产，未做新装配。
