# RC2 全量实际数据契约审计

审计结论：82题、647个正式输入及96个样例角色均已逐份覆盖。实际输入与当前公开声明的所检项目通过，未发现新增明确文档／数据冲突。95个实际存在的公开完整输出文件，其数组、dtype、shape、有限值、key集合与固定轴均通过；smoke-test 的另一个角色是允许的 reference-only numerical 样例，不记缺文件。

本报告只陈述已经检查的声明、数据与覆盖；参考数值资格和解轨迹物理保证为“资料不足，未完成”，不能将其合并成完整数值通过。格式样例已明确为 format，不承担数值答案承诺。没有执行求解器、制造参考、调用收费模型或修改题目源材料。

## 依据与覆盖方法

- 依据当前主 checkout 每题 instruction.md、DATA.md 与 docs/CONTRACT.md；JSON保存三文档版本摘要。实际输入路径采用 asset-audit.json/data-inventory 指向的真实装配来源，不以主checkout缺少cases误判HF缺数据。
- 对全部743份manifest枚举物理声明、参数（含单位和值）、条件 role/variable/operator/data、输出quantity/kind/unit/value_kind、位置/实体/Physical Group及采样组合。JSON `tasks[].claims` 将每个实值及分支映射到文档行号与全部出现它的manifest；`inputs`保留每份材料实际时间轴、所有输入数组全量读取的min/max/shape和MSH节点数/类型/范围。
- 独立全读实际输入HDF5数组，核对field引用的T/N/component轴、时间递增及区间覆盖、IDs递增和真实网格实体/Physical Group、uniform空间值、constant帧数、固定域moving-wall法向速度、适用正值/分数范围/构象SPD。温度状态范围、Boussinesq适用不等式及统计窗整数样本数另核。带温度variable的outward_heat_flux按带符号热流解释，不误作正温度。
- 24道CC题的全部正式和样例显式坐标、终止时刻、N范围与实体谱标量位置均逐项对照公开定义；没有把单元中心观测冒充平均值。基础PDE核对初值单元常数、Darcy双线性中心点、反应扩散完整初态/输出子集、不可压投影前t=0记录、守恒平均派生quantity等公开声明。
- 输入标签开放规则按公开声明处理：smoke回传及cfd-2.1输入quantity是标签，不能把未枚举标签误报成缺定义；输出quantity仍受逐题定义约束。
- 正式case判据对齐复用 scoring-map.json（该记录枚举全部647正式case）；公开输出检查是独立读取95个文件，并不沿用自消费成功作为语义通过理由。

## 分类结果

1. 明确文档／数据冲突：本次所检项目没有确认的新冲突。
2. 范围覆盖不足：见下列明细。它们表示公开允许而本轮实际材料未触达的分支，不把“没有覆盖所有合法组合”直接判成数据错误。
3. 参考数值未认证：全量参考数值、作者生产者/出处资格、离散收敛、资源达标以及时间轨迹上的全湿/无回流/唯一有限迹等，均不由本次只读输入审计认证。最小后续是回到来源/参考资格流程提交独立证据；不得由格式样例或结构自消费替代。
4. 资料不足：没有缺失实际输入或当前三文档；上述轨迹及参考资格所需独立解证据未在本审计重认证。

## 可定位的覆盖缺口

- **newtonian-incompressible-transient-2d**：公开允许 previous 采样，实际集仅 constant/linear；公开允许 hold 外推，实际集仅 forbid。对照 `qbank\02-fluid-mechanics\2.1-single-phase-flow\newtonian-incompressible-transient-2d\DATA.md` 中条件/输入采样定义；实际反例锚点 `D:\Code\CAE-Bench-OJ-ch02-benchmark\qbank\02-fluid-mechanics\2.1-single-phase-flow\newtonian-incompressible-transient-2d\cases\001\problem.json`（该例及本题全部其余输入均未出现列出分支）。最小后续：补充有独立数值来源的真实算例并重新冻结选样，或在范围声明中如实标记本轮未覆盖；不凭当前通过收窄/扩大题意。
- **newtonian-incompressible-transient-3d**：公开允许 previous 采样，实际集仅 constant/linear；公开允许 hold 外推，实际集仅 forbid。对照 `qbank\02-fluid-mechanics\2.1-single-phase-flow\newtonian-incompressible-transient-3d\DATA.md` 中条件/输入采样定义；实际反例锚点 `D:\Code\CAE-Bench-OJ-ch02-benchmark\qbank\02-fluid-mechanics\2.1-single-phase-flow\newtonian-incompressible-transient-3d\cases\001\problem.json`（该例及本题全部其余输入均未出现列出分支）。最小后续：补充有独立数值来源的真实算例并重新冻结选样，或在范围声明中如实标记本轮未覆盖；不凭当前通过收窄/扩大题意。
- **generalized-newtonian-incompressible-transient-2d**：公开允许 previous 采样，实际集仅 constant/linear；公开允许 hold 外推，实际集仅 forbid。对照 `qbank\02-fluid-mechanics\2.1-single-phase-flow\generalized-newtonian-incompressible-transient-2d\DATA.md` 中条件/输入采样定义；实际反例锚点 `D:\Code\CAE-Bench-OJ-ch02-benchmark\qbank\02-fluid-mechanics\2.1-single-phase-flow\generalized-newtonian-incompressible-transient-2d\cases\001\problem.json`（该例及本题全部其余输入均未出现列出分支）。最小后续：补充有独立数值来源的真实算例并重新冻结选样，或在范围声明中如实标记本轮未覆盖；不凭当前通过收窄/扩大题意。
- **generalized-newtonian-incompressible-transient-3d**：公开允许 previous 采样，实际集仅 constant/linear；公开允许 hold 外推，实际集仅 forbid。对照 `qbank\02-fluid-mechanics\2.1-single-phase-flow\generalized-newtonian-incompressible-transient-3d\DATA.md` 中条件/输入采样定义；实际反例锚点 `D:\Code\CAE-Bench-OJ-ch02-benchmark\qbank\02-fluid-mechanics\2.1-single-phase-flow\generalized-newtonian-incompressible-transient-3d\cases\001\problem.json`（该例及本题全部其余输入均未出现列出分支）。最小后续：补充有独立数值来源的真实算例并重新冻结选样，或在范围声明中如实标记本轮未覆盖；不凭当前通过收窄/扩大题意。
- **newtonian-isothermal-compressible-transient-2d**：公开允许 previous 采样，实际集仅 constant/linear；公开允许 hold 外推，实际集仅 forbid。对照 `qbank\02-fluid-mechanics\2.1-single-phase-flow\newtonian-isothermal-compressible-transient-2d\DATA.md` 中条件/输入采样定义；实际反例锚点 `D:\Code\CAE-Bench-OJ-ch02-benchmark\qbank\02-fluid-mechanics\2.1-single-phase-flow\newtonian-isothermal-compressible-transient-2d\cases\001\problem.json`（该例及本题全部其余输入均未出现列出分支）。最小后续：补充有独立数值来源的真实算例并重新冻结选样，或在范围声明中如实标记本轮未覆盖；不凭当前通过收窄/扩大题意。
- **newtonian-isothermal-compressible-transient-3d**：公开允许 previous 采样，实际集仅 constant/linear；公开允许 hold 外推，实际集仅 forbid。对照 `qbank\02-fluid-mechanics\2.1-single-phase-flow\newtonian-isothermal-compressible-transient-3d\DATA.md` 中条件/输入采样定义；实际反例锚点 `D:\Code\CAE-Bench-OJ-ch02-benchmark\qbank\02-fluid-mechanics\2.1-single-phase-flow\newtonian-isothermal-compressible-transient-3d\cases\001\problem.json`（该例及本题全部其余输入均未出现列出分支）。最小后续：补充有独立数值来源的真实算例并重新冻结选样，或在范围声明中如实标记本轮未覆盖；不凭当前通过收窄/扩大题意。
- **inviscid-compressible-transient-2d**：未出现公开条件分支：source/heat_source/assign。对照 `qbank\02-fluid-mechanics\2.2-single-phase-energy\inviscid-compressible-transient-2d\DATA.md` 中条件/输入采样定义；实际反例锚点 `D:\Code\CAE-Bench-OJ-ch02-benchmark\qbank\02-fluid-mechanics\2.2-single-phase-energy\inviscid-compressible-transient-2d\cases\001\problem.json`（该例及本题全部其余输入均未出现列出分支）。最小后续：补充有独立数值来源的真实算例并重新冻结选样，或在范围声明中如实标记本轮未覆盖；不凭当前通过收窄/扩大题意。
- **inviscid-compressible-transient-3d**：未出现公开条件分支：source/heat_source/assign。对照 `qbank\02-fluid-mechanics\2.2-single-phase-energy\inviscid-compressible-transient-3d\DATA.md` 中条件/输入采样定义；实际反例锚点 `D:\Code\CAE-Bench-OJ-ch02-benchmark\qbank\02-fluid-mechanics\2.2-single-phase-energy\inviscid-compressible-transient-3d\cases\001\problem.json`（该例及本题全部其余输入均未出现列出分支）。最小后续：补充有独立数值来源的真实算例并重新冻结选样，或在范围声明中如实标记本轮未覆盖；不凭当前通过收窄/扩大题意。
- **newtonian-compressible-transient-2d**：未出现公开条件分支：source/acceleration/assign, source/heat_source/assign。对照 `qbank\02-fluid-mechanics\2.2-single-phase-energy\newtonian-compressible-transient-2d\DATA.md` 中条件/输入采样定义；实际反例锚点 `D:\Code\CAE-Bench-OJ-ch02-benchmark\qbank\02-fluid-mechanics\2.2-single-phase-energy\newtonian-compressible-transient-2d\cases\001\problem.json`（该例及本题全部其余输入均未出现列出分支）。最小后续：补充有独立数值来源的真实算例并重新冻结选样，或在范围声明中如实标记本轮未覆盖；不凭当前通过收窄/扩大题意。
- **newtonian-compressible-transient-3d**：未出现公开条件分支：source/acceleration/assign, source/heat_source/assign。对照 `qbank\02-fluid-mechanics\2.2-single-phase-energy\newtonian-compressible-transient-3d\DATA.md` 中条件/输入采样定义；实际反例锚点 `D:\Code\CAE-Bench-OJ-ch02-benchmark\qbank\02-fluid-mechanics\2.2-single-phase-energy\newtonian-compressible-transient-3d\cases\001\problem.json`（该例及本题全部其余输入均未出现列出分支）。最小后续：补充有独立数值来源的真实算例并重新冻结选样，或在范围声明中如实标记本轮未覆盖；不凭当前通过收窄/扩大题意。
- **thermal-rans-3d**：未出现公开条件分支：source/heat_source/assign。对照 `qbank\02-fluid-mechanics\2.4-turbulent-energy\thermal-rans-3d\DATA.md` 中条件/输入采样定义；实际反例锚点 `D:\Code\CAE-Bench-OJ-ch02-benchmark\qbank\02-fluid-mechanics\2.4-turbulent-energy\thermal-rans-3d\cases\001\problem.json`（该例及本题全部其余输入均未出现列出分支）。最小后续：补充有独立数值来源的真实算例并重新冻结选样，或在范围声明中如实标记本轮未覆盖；不凭当前通过收窄/扩大题意。
- **thermal-urans-3d**：未出现公开条件分支：source/acceleration/assign, source/heat_source/assign。对照 `qbank\02-fluid-mechanics\2.4-turbulent-energy\thermal-urans-3d\DATA.md` 中条件/输入采样定义；实际反例锚点 `D:\Code\CAE-Bench-OJ-ch02-benchmark\qbank\02-fluid-mechanics\2.4-turbulent-energy\thermal-urans-3d\cases\001\problem.json`（该例及本题全部其余输入均未出现列出分支）。最小后续：补充有独立数值来源的真实算例并重新冻结选样，或在范围声明中如实标记本轮未覆盖；不凭当前通过收窄/扩大题意。
- **viscoelastic-steady**：公开 velocity_inlet/conformation 与 traction_outlet 未出现；实际边界只有 velocity_wall。对照 `qbank\02-fluid-mechanics\2.11-memory-fluids\viscoelastic-steady\DATA.md` 中条件/输入采样定义；实际反例锚点 `D:\Code\CAE-Bench-OJ-ch02-benchmark\qbank\02-fluid-mechanics\2.11-memory-fluids\viscoelastic-steady\cases\001\problem.json`（该例及本题全部其余输入均未出现列出分支）。最小后续：补充有独立数值来源的真实算例并重新冻结选样，或在范围声明中如实标记本轮未覆盖；不凭当前通过收窄/扩大题意。
- **viscoelastic-transient**：公开 velocity_inlet/conformation 与 traction_outlet 未出现；实际边界只有 velocity_wall。对照 `qbank\02-fluid-mechanics\2.11-memory-fluids\viscoelastic-transient\DATA.md` 中条件/输入采样定义；实际反例锚点 `D:\Code\CAE-Bench-OJ-ch02-benchmark\qbank\02-fluid-mechanics\2.11-memory-fluids\viscoelastic-transient\cases\001\problem.json`（该例及本题全部其余输入均未出现列出分支）。最小后续：补充有独立数值来源的真实算例并重新冻结选样，或在范围声明中如实标记本轮未覆盖；不凭当前通过收窄/扩大题意。
- **newtonian-compressible-steady-2d**：未出现公开条件分支：source/acceleration/assign。对照 `qbank\02-fluid-mechanics\2.2-single-phase-energy\newtonian-compressible-steady-2d\DATA.md` 中条件/输入采样定义；实际反例锚点 `D:\Code\CAE-Bench-OJ\runs\release-assembly-rc2\new-flow-stage\qbank\02-fluid-mechanics\2.2-single-phase-energy\newtonian-compressible-steady-2d\cases\001\problem.json`（该例及本题全部其余输入均未出现列出分支）。最小后续：补充有独立数值来源的真实算例并重新冻结选样，或在范围声明中如实标记本轮未覆盖；不凭当前通过收窄/扩大题意。
- **newtonian-compressible-steady-3d**：未出现公开条件分支：source/acceleration/assign。对照 `qbank\02-fluid-mechanics\2.2-single-phase-energy\newtonian-compressible-steady-3d\DATA.md` 中条件/输入采样定义；实际反例锚点 `D:\Code\CAE-Bench-OJ\runs\release-assembly-rc2\new-flow-stage\qbank\02-fluid-mechanics\2.2-single-phase-energy\newtonian-compressible-steady-3d\cases\001\problem.json`（该例及本题全部其余输入均未出现列出分支）。最小后续：补充有独立数值来源的真实算例并重新冻结选样，或在范围声明中如实标记本轮未覆盖；不凭当前通过收窄/扩大题意。
- **compressible-thermal-rans-3d**：未出现公开条件分支：source/acceleration/assign。对照 `qbank\02-fluid-mechanics\2.4-turbulent-energy\compressible-thermal-rans-3d\DATA.md` 中条件/输入采样定义；实际反例锚点 `D:\Code\CAE-Bench-OJ\runs\release-assembly-rc2\new-flow-stage\qbank\02-fluid-mechanics\2.4-turbulent-energy\compressible-thermal-rans-3d\cases\001\problem.json`（该例及本题全部其余输入均未出现列出分支）。最小后续：补充有独立数值来源的真实算例并重新冻结选样，或在范围声明中如实标记本轮未覆盖；不凭当前通过收窄/扩大题意。

## 逐题覆盖账本

每题下列条件/采样/输出列的是全部实际材料的并集，不是代表样例。每个分支的全部manifest路径、准确数组shape和值范围可在同名JSON条目追溯。

### 1. smoke-test

- 文档：`qbank/00-basic-tests/0.1-io/smoke-test/DATA.md`、`instruction.md`；正式 11，样例 1；覆盖实值/分支声明 84 项、输入场数组 19 个、实际网格引用 12 个。
- 条件：`boundary/temperature/dirichlet`；`initial/temperature/assign`；`material/conductivity/assign`；`source/heat_source/assign`
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`cell_temperature/scalar/K/mesh/element/average`；`edge_flux/scalar/W/mesh/element/integral`；`face_pressure/scalar/Pa/mesh/element/average`；`left_temperature/scalar/K/mesh/node/point`；`mask/scalar/1/mesh/node/point`；`probe_temperature/scalar/K/points//point`；`region_label/scalar/1/mesh/node/point`；`species/components/1/mesh/node/point`；`stress/tensor/Pa/mesh/node/point`；`temperature/scalar/K/mesh/node/point`；`velocity/vector/m/s/mesh/node/point`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 0/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 2. case-grading-test

- 文档：`qbank/00-basic-tests/0.2-grading/case-grading-test/DATA.md`、`instruction.md`；正式 6，样例 2；覆盖实值/分支声明 15 项、输入场数组 8 个、实际网格引用 8 个。
- 条件：无；模型固定条件在DATA完整定义。
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`velocity/vector/m/s/mesh/node/point`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 2/2 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 3. darcy-flow-2d

- 文档：`qbank/01-prescribed-pdes/1.1-elliptic/darcy-flow-2d/DATA.md`、`instruction.md`；正式 20，样例 2；覆盖实值/分支声明 37 项、输入场数组 22 个、实际网格引用 22 个。
- 条件：`boundary/state/cell_coupled_dirichlet`；`material/state/assign`；`source/state/assign`
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`state/scalar/1/mesh/element/average`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 2/2 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 4. heat-conduction-steady-2d

- 文档：`qbank/01-prescribed-pdes/1.1-elliptic/heat-conduction-steady-2d/DATA.md`、`instruction.md`；正式 32，样例 2；覆盖实值/分支声明 116 项、输入场数组 170 个、实际网格引用 34 个。
- 条件：`boundary/temperature/dirichlet`；`boundary/temperature/normal_derivative`；`boundary/temperature/normal_flux`；`boundary/temperature/robin`；`source/temperature/polynomial`
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`temperature/scalar/K/mesh/node/point`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 2/2 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 5. diffusion-sorption-1d

- 文档：`qbank/01-prescribed-pdes/1.2-diffusion-reaction/diffusion-sorption-1d/DATA.md`、`instruction.md`；正式 16，样例 2；覆盖实值/分支声明 33 项、输入场数组 18 个、实际网格引用 18 个。
- 条件：`boundary/concentration/cell_coupled_dirichlet`；`boundary/concentration/outlet_cell_coupling`；`initial/concentration/assign`
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`concentration/scalar/1/mesh/element/average`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 2/2 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 6. heat-conduction-transient-2d

- 文档：`qbank/01-prescribed-pdes/1.2-diffusion-reaction/heat-conduction-transient-2d/DATA.md`、`instruction.md`；正式 24，样例 2；覆盖实值/分支声明 59 项、输入场数组 26 个、实际网格引用 26 个。
- 条件：`boundary/temperature/dirichlet`；`boundary/temperature/normal_derivative`；`boundary/temperature/normal_flux`；`boundary/temperature/robin`；`initial/temperature/assign`
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`temperature/scalar/K/mesh/node/point`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 2/2 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 7. reaction-diffusion-1d

- 文档：`qbank/01-prescribed-pdes/1.2-diffusion-reaction/reaction-diffusion-1d/DATA.md`、`instruction.md`；正式 32，样例 2；覆盖实值/分支声明 28 项、输入场数组 34 个、实际网格引用 34 个。
- 条件：`boundary/state/periodic`；`initial/state/assign`
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`state/scalar/1/mesh/element/average`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 2/2 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 8. reaction-diffusion-2d

- 文档：`qbank/01-prescribed-pdes/1.2-diffusion-reaction/reaction-diffusion-2d/DATA.md`、`instruction.md`；正式 16，样例 2；覆盖实值/分支声明 36 项、输入场数组 36 个、实际网格引用 18 个。
- 条件：`boundary/activator/normal_flux`；`boundary/inhibitor/normal_flux`；`initial/activator/assign`；`initial/inhibitor/assign`
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`activator/scalar/1/mesh/element/average`；`inhibitor/scalar/1/mesh/element/average`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 2/2 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 9. advection-1d

- 文档：`qbank/01-prescribed-pdes/1.3-scalar-transport/advection-1d/DATA.md`、`instruction.md`；正式 24，样例 2；覆盖实值/分支声明 28 项、输入场数组 26 个、实际网格引用 26 个。
- 条件：`boundary/state/periodic`；`initial/state/assign`
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`state/scalar/1/mesh/element/average`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 2/2 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 10. shallow-water-2d

- 文档：`qbank/01-prescribed-pdes/1.4-hyperbolic/shallow-water-2d/DATA.md`、`instruction.md`；正式 16，样例 2；覆盖实值/分支声明 32 项、输入场数组 36 个、实际网格引用 18 个。
- 条件：`boundary/depth_momentum/extrapolate`；`initial/depth/assign`；`initial/momentum/assign`
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`depth/scalar/m/mesh/element/average`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 2/2 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 11. burgers-1d

- 文档：`qbank/01-prescribed-pdes/1.5-advection-diffusion/burgers-1d/DATA.md`、`instruction.md`；正式 24，样例 2；覆盖实值/分支声明 32 项、输入场数组 26 个、实际网格引用 26 个。
- 条件：`boundary/state/periodic`；`initial/state/assign`
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`state/scalar/m/s/mesh/element/average`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 2/2 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 12. incompressible-navier-stokes-2d

- 文档：`qbank/01-prescribed-pdes/1.6-constrained-systems/incompressible-navier-stokes-2d/DATA.md`、`instruction.md`；正式 16，样例 2；覆盖实值/分支声明 41 项、输入场数组 126 个、实际网格引用 18 个。
- 条件：`boundary/kinematic_pressure/mean`；`boundary/velocity/dirichlet`；`initial/tracer/assign`；`initial/velocity/project_preserve_snapshot`；`source/velocity/tracer_force`
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`velocity/vector/m/s/points//point`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 2/2 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 13. compressible-navier-stokes-1d

- 文档：`qbank/01-prescribed-pdes/1.7-coupled-systems/compressible-navier-stokes-1d/DATA.md`、`instruction.md`；正式 16，样例 2；覆盖实值/分支声明 47 项、输入场数组 54 个、实际网格引用 18 个。
- 条件：`boundary/fluid_state/extrapolate`；`boundary/fluid_state/periodic`；`initial/density/assign`；`initial/pressure/assign`；`initial/velocity/assign`
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`conservative_pressure/scalar/Pa/mesh/element/average`；`density/scalar/kg/m3/mesh/element/average`；`mass_weighted_velocity/vector/m/s/mesh/element/average`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 2/2 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 14. compressible-navier-stokes-2d

- 文档：`qbank/01-prescribed-pdes/1.7-coupled-systems/compressible-navier-stokes-2d/DATA.md`、`instruction.md`；正式 24，样例 2；覆盖实值/分支声明 46 项、输入场数组 78 个、实际网格引用 26 个。
- 条件：`boundary/fluid_state/periodic`；`initial/density/assign`；`initial/pressure/assign`；`initial/velocity/assign`
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`conservative_pressure/scalar/Pa/mesh/element/average`；`density/scalar/kg/m3/mesh/element/average`；`mass_weighted_velocity/vector/m/s/mesh/element/average`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 2/2 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 15. compressible-navier-stokes-3d

- 文档：`qbank/01-prescribed-pdes/1.7-coupled-systems/compressible-navier-stokes-3d/DATA.md`、`instruction.md`；正式 6，样例 2；覆盖实值/分支声明 43 项、输入场数组 24 个、实际网格引用 8 个。
- 条件：`boundary/fluid_state/periodic`；`initial/density/assign`；`initial/pressure/assign`；`initial/velocity/assign`
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`conservative_pressure/scalar/Pa/mesh/element/average`；`density/scalar/kg/m3/mesh/element/average`；`mass_weighted_velocity/vector/m/s/mesh/element/average`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 2/2 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 16. newtonian-incompressible-steady-2d

- 文档：`qbank/02-fluid-mechanics/2.1-single-phase-flow/newtonian-incompressible-steady-2d/DATA.md`、`instruction.md`；正式 10，样例 1；覆盖实值/分支声明 140 项、输入场数组 29 个、实际网格引用 11 个。
- 条件：`boundary/flow/flow_rate`；`boundary/flow/moving_wall`；`boundary/flow/no_slip`；`boundary/flow/periodic`；`boundary/flow/pressure_outlet`；`boundary/flow/slip`；`boundary/flow/symmetry`；`boundary/flow/traction`；`boundary/flow/velocity`；`source/velocity/acceleration`
- 输入采样：`piecewise_constant/constant/forbid`；`piecewise_linear/constant/forbid`；`uniform/constant/forbid`；`uniform/constant/hold`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`density/scalar/kg/m3/aggregate//average`；`density/scalar/kg/m3/mesh/element/average`；`density/scalar/kg/m3/mesh/node/point`；`density/scalar/kg/m3/points//point`；`dynamic_viscosity/scalar/Pa.s/aggregate//average`；`dynamic_viscosity/scalar/Pa.s/mesh/element/average`；`dynamic_viscosity/scalar/Pa.s/mesh/node/point`；`dynamic_viscosity/scalar/Pa.s/points//point`；`force/vector/N/m/aggregate//integral`；`mass_flow/scalar/kg/(m.s)/aggregate//integral`；`pressure/scalar/Pa/aggregate//average`；`pressure/scalar/Pa/mesh/element/average`；`pressure/scalar/Pa/mesh/node/point`；`pressure/scalar/Pa/points//point`；`shear_rate/scalar/1/s/aggregate//average`；`shear_rate/scalar/1/s/mesh/element/average`；`shear_rate/scalar/1/s/mesh/node/point`；`shear_rate/scalar/1/s/points//point`；`traction/vector/Pa/mesh/element/average`；`velocity/vector/m/s/aggregate//average`；`velocity/vector/m/s/mesh/element/average`；`velocity/vector/m/s/mesh/node/point`；`velocity/vector/m/s/points//point`；`volume_flow/scalar/m2/s/aggregate//integral`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 17. newtonian-incompressible-steady-3d

- 文档：`qbank/02-fluid-mechanics/2.1-single-phase-flow/newtonian-incompressible-steady-3d/DATA.md`、`instruction.md`；正式 10，样例 1；覆盖实值/分支声明 139 项、输入场数组 25 个、实际网格引用 11 个。
- 条件：`boundary/flow/flow_rate`；`boundary/flow/moving_wall`；`boundary/flow/no_slip`；`boundary/flow/periodic`；`boundary/flow/pressure_outlet`；`boundary/flow/slip`；`boundary/flow/symmetry`；`boundary/flow/traction`；`boundary/flow/velocity`；`source/velocity/acceleration`
- 输入采样：`piecewise_constant/constant/forbid`；`piecewise_linear/constant/forbid`；`uniform/constant/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`density/scalar/kg/m3/mesh/element/average`；`density/scalar/kg/m3/points//point`；`dynamic_viscosity/scalar/Pa.s/mesh/element/average`；`dynamic_viscosity/scalar/Pa.s/points//point`；`force/vector/N/aggregate//integral`；`mass_flow/scalar/kg/s/aggregate//integral`；`pressure/scalar/Pa/aggregate//average`；`pressure/scalar/Pa/mesh/element/average`；`pressure/scalar/Pa/points//point`；`shear_rate/scalar/1/s/points//point`；`traction/vector/Pa/mesh/element/average`；`velocity/vector/m/s/mesh/element/average`；`velocity/vector/m/s/points//point`；`volume_flow/scalar/m3/s/aggregate//integral`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 18. cc-1d-burgers-equation

- 文档：`qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-1d-burgers-equation/DATA.md`、`instruction.md`；正式 1，样例 1；覆盖实值/分支声明 16 项、输入场数组 2 个、实际网格引用 0 个。
- 条件：无；模型固定条件在DATA完整定义。
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`u/scalar/1/points//point`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 19. cc-1d-diffusion

- 文档：`qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-1d-diffusion/DATA.md`、`instruction.md`；正式 1，样例 1；覆盖实值/分支声明 16 项、输入场数组 2 个、实际网格引用 0 个。
- 条件：无；模型固定条件在DATA完整定义。
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`u/scalar/1/points//point`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 20. cc-1d-euler-shock-tube

- 文档：`qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-1d-euler-shock-tube/DATA.md`、`instruction.md`；正式 1，样例 1；覆盖实值/分支声明 18 项、输入场数组 2 个、实际网格引用 0 个。
- 条件：无；模型固定条件在DATA完整定义。
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`E/scalar/1/points//point`；`rho/scalar/1/points//point`；`u/scalar/1/points//point`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 21. cc-1d-linear-convection

- 文档：`qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-1d-linear-convection/DATA.md`、`instruction.md`；正式 1，样例 1；覆盖实值/分支声明 16 项、输入场数组 2 个、实际网格引用 0 个。
- 条件：无；模型固定条件在DATA完整定义。
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`u/scalar/1/points//point`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 22. cc-1d-nonlinear-convection

- 文档：`qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-1d-nonlinear-convection/DATA.md`、`instruction.md`；正式 1，样例 1；覆盖实值/分支声明 16 项、输入场数组 2 个、实际网格引用 0 个。
- 条件：无；模型固定条件在DATA完整定义。
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`u/scalar/1/points//point`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 23. cc-2d-burgers-equation

- 文档：`qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-burgers-equation/DATA.md`、`instruction.md`；正式 1，样例 1；覆盖实值/分支声明 17 项、输入场数组 2 个、实际网格引用 0 个。
- 条件：无；模型固定条件在DATA完整定义。
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`u/scalar/1/points//point`；`v/scalar/1/points//point`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 24. cc-2d-convection

- 文档：`qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-convection/DATA.md`、`instruction.md`；正式 1，样例 1；覆盖实值/分支声明 17 项、输入场数组 2 个、实际网格引用 0 个。
- 条件：无；模型固定条件在DATA完整定义。
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`u/scalar/1/points//point`；`v/scalar/1/points//point`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 25. cc-2d-diffusion

- 文档：`qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-diffusion/DATA.md`、`instruction.md`；正式 1，样例 1；覆盖实值/分支声明 16 项、输入场数组 2 个、实际网格引用 0 个。
- 条件：无；模型固定条件在DATA完整定义。
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`u/scalar/1/points//point`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 26. cc-2d-inviscid-burgers

- 文档：`qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-inviscid-burgers/DATA.md`、`instruction.md`；正式 1，样例 1；覆盖实值/分支声明 17 项、输入场数组 2 个、实际网格引用 0 个。
- 条件：无；模型固定条件在DATA完整定义。
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`u/scalar/1/points//point`；`v/scalar/1/points//point`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 27. cc-2d-laplace-equation

- 文档：`qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-laplace-equation/DATA.md`、`instruction.md`；正式 1，样例 1；覆盖实值/分支声明 16 项、输入场数组 2 个、实际网格引用 0 个。
- 条件：无；模型固定条件在DATA完整定义。
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`p/scalar/1/points//point`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 28. cc-2d-linear-convection

- 文档：`qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-linear-convection/DATA.md`、`instruction.md`；正式 1，样例 1；覆盖实值/分支声明 16 项、输入场数组 2 个、实际网格引用 0 个。
- 条件：无；模型固定条件在DATA完整定义。
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`u/scalar/1/points//point`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 29. cc-2d-navier-stokes-cavity

- 文档：`qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-navier-stokes-cavity/DATA.md`、`instruction.md`；正式 1，样例 1；覆盖实值/分支声明 18 项、输入场数组 2 个、实际网格引用 0 个。
- 条件：无；模型固定条件在DATA完整定义。
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`p/scalar/1/points//point`；`u/scalar/1/points//point`；`v/scalar/1/points//point`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 30. cc-2d-navier-stokes-channel

- 文档：`qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-navier-stokes-channel/DATA.md`、`instruction.md`；正式 1，样例 1；覆盖实值/分支声明 16 项、输入场数组 2 个、实际网格引用 0 个。
- 条件：无；模型固定条件在DATA完整定义。
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`u/scalar/1/points//point`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 31. cc-2d-poisson-equation

- 文档：`qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-poisson-equation/DATA.md`、`instruction.md`；正式 1，样例 1；覆盖实值/分支声明 16 项、输入场数组 2 个、实际网格引用 0 个。
- 条件：无；模型固定条件在DATA完整定义。
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`p/scalar/1/points//point`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 32. cc-2d-steady-heat-equation

- 文档：`qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-steady-heat-equation/DATA.md`、`instruction.md`；正式 1，样例 1；覆盖实值/分支声明 16 项、输入场数组 2 个、实际网格引用 0 个。
- 条件：无；模型固定条件在DATA完整定义。
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`T/scalar/1/points//point`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 33. cc-2d-unsteady-heat-equation

- 文档：`qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-unsteady-heat-equation/DATA.md`、`instruction.md`；正式 1，样例 1；覆盖实值/分支声明 16 项、输入场数组 2 个、实际网格引用 0 个。
- 条件：无；模型固定条件在DATA完整定义。
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`T/scalar/1/points//point`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 34. cc-fully-developed-turbulent-channel-flow

- 文档：`qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-fully-developed-turbulent-channel-flow/DATA.md`、`instruction.md`；正式 1，样例 1；覆盖实值/分支声明 16 项、输入场数组 2 个、实际网格引用 0 个。
- 条件：无；模型固定条件在DATA完整定义。
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`u/scalar/1/points//point`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 35. cc-lid-driven-cavity

- 文档：`qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-lid-driven-cavity/DATA.md`、`instruction.md`；正式 1，样例 1；覆盖实值/分支声明 18 项、输入场数组 2 个、实际网格引用 0 个。
- 条件：无；模型固定条件在DATA完整定义。
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`p/scalar/1/points//point`；`u/scalar/1/points//point`；`v/scalar/1/points//point`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 36. cc-flow-past-circular-cylinder

- 文档：`qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-flow-past-circular-cylinder/DATA.md`、`instruction.md`；正式 1，样例 1；覆盖实值/分支声明 17 项、输入场数组 2 个、实际网格引用 0 个。
- 条件：无；模型固定条件在DATA完整定义。
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`omega/scalar/1/points//point`；`psi/scalar/1/points//point`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 37. cc-1d-kdv-burgers-equation

- 文档：`qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-1d-kdv-burgers-equation/DATA.md`、`instruction.md`；正式 1，样例 1；覆盖实值/分支声明 16 项、输入场数组 2 个、实际网格引用 0 个。
- 条件：无；模型固定条件在DATA完整定义。
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`u/scalar/1/points//point`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 38. cc-2d-rayleigh-benard-convection

- 文档：`qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-rayleigh-benard-convection/DATA.md`、`instruction.md`；正式 1，样例 1；覆盖实值/分支声明 19 项、输入场数组 2 个、实际网格引用 0 个。
- 条件：无；模型固定条件在DATA完整定义。
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`b/scalar/1/points//point`；`p/scalar/1/points//point`；`u/scalar/1/points//point`；`w/scalar/1/points//point`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 39. cc-2d-shear-flow-with-tracer

- 文档：`qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-shear-flow-with-tracer/DATA.md`、`instruction.md`；正式 1，样例 1；覆盖实值/分支声明 19 项、输入场数组 2 个、实际网格引用 0 个。
- 条件：无；模型固定条件在DATA完整定义。
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`p/scalar/1/points//point`；`s/scalar/1/points//point`；`u/scalar/1/points//point`；`w/scalar/1/points//point`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 40. cc-pipe-flow-disk-evp

- 文档：`qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-pipe-flow-disk-evp/DATA.md`、`instruction.md`；正式 1，样例 1；覆盖实值/分支声明 16 项、输入场数组 2 个、实际网格引用 0 个。
- 条件：无；模型固定条件在DATA完整定义。
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`s/scalar/1/entities//point`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 41. cc-lane-emden-equation

- 文档：`qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-lane-emden-equation/DATA.md`、`instruction.md`；正式 1，样例 1；覆盖实值/分支声明 16 项、输入场数组 2 个、实际网格引用 0 个。
- 条件：无；模型固定条件在DATA完整定义。
- 输入采样：按逐题DATA定义，不隐含增添sampling。
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`f/scalar/1/points//point`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 42. newtonian-incompressible-transient-2d

- 文档：`qbank/02-fluid-mechanics/2.1-single-phase-flow/newtonian-incompressible-transient-2d/DATA.md`、`instruction.md`；正式 10，样例 1；覆盖实值/分支声明 103 项、输入场数组 27 个、实际网格引用 11 个。
- 条件：`boundary/flow/flow_rate`；`boundary/flow/moving_wall`；`boundary/flow/no_slip`；`boundary/flow/periodic`；`boundary/flow/pressure_outlet`；`boundary/flow/slip`；`boundary/flow/symmetry`；`boundary/flow/traction`；`boundary/flow/velocity`；`initial/velocity/assign`；`source/velocity/acceleration`
- 输入采样：`piecewise_constant/constant/forbid`；`piecewise_constant/linear/forbid`；`piecewise_linear/constant/forbid`；`piecewise_linear/linear/forbid`；`uniform/constant/forbid`；`uniform/linear/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`density/scalar/kg/m3/mesh/element/average`；`dynamic_viscosity/scalar/Pa.s/mesh/element/average`；`force/vector/N/m/aggregate//integral`；`mass_flow/scalar/kg/(m.s)/aggregate//integral`；`pressure/scalar/Pa/mesh/element/average`；`shear_rate/scalar/1/s/mesh/element/average`；`traction/vector/Pa/mesh/element/average`；`velocity/vector/m/s/mesh/element/average`；`volume_flow/scalar/m2/s/aggregate//integral`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；公开允许 previous 采样，实际集仅 constant/linear；公开允许 hold 外推，实际集仅 forbid

### 43. newtonian-incompressible-transient-3d

- 文档：`qbank/02-fluid-mechanics/2.1-single-phase-flow/newtonian-incompressible-transient-3d/DATA.md`、`instruction.md`；正式 10，样例 1；覆盖实值/分支声明 104 项、输入场数组 27 个、实际网格引用 11 个。
- 条件：`boundary/flow/flow_rate`；`boundary/flow/moving_wall`；`boundary/flow/no_slip`；`boundary/flow/periodic`；`boundary/flow/pressure_outlet`；`boundary/flow/slip`；`boundary/flow/symmetry`；`boundary/flow/traction`；`boundary/flow/velocity`；`initial/velocity/assign`；`source/velocity/acceleration`
- 输入采样：`piecewise_constant/constant/forbid`；`piecewise_constant/linear/forbid`；`piecewise_linear/constant/forbid`；`piecewise_linear/linear/forbid`；`uniform/constant/forbid`；`uniform/linear/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`density/scalar/kg/m3/mesh/element/average`；`dynamic_viscosity/scalar/Pa.s/mesh/element/average`；`force/vector/N/aggregate//integral`；`mass_flow/scalar/kg/s/aggregate//integral`；`pressure/scalar/Pa/mesh/element/average`；`shear_rate/scalar/1/s/mesh/element/average`；`traction/vector/Pa/mesh/element/average`；`velocity/vector/m/s/mesh/element/average`；`volume_flow/scalar/m3/s/aggregate//integral`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；公开允许 previous 采样，实际集仅 constant/linear；公开允许 hold 外推，实际集仅 forbid

### 44. generalized-newtonian-incompressible-steady-2d

- 文档：`qbank/02-fluid-mechanics/2.1-single-phase-flow/generalized-newtonian-incompressible-steady-2d/DATA.md`、`instruction.md`；正式 8，样例 1；覆盖实值/分支声明 100 项、输入场数组 13 个、实际网格引用 9 个。
- 条件：`boundary/flow/flow_rate`；`boundary/flow/moving_wall`；`boundary/flow/no_slip`；`boundary/flow/periodic`；`boundary/flow/pressure_outlet`；`boundary/flow/slip`；`boundary/flow/symmetry`；`boundary/flow/velocity`；`source/velocity/acceleration`
- 输入采样：`piecewise_constant/constant/forbid`；`piecewise_linear/constant/forbid`；`uniform/constant/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`density/scalar/kg/m3/mesh/element/average`；`dynamic_viscosity/scalar/Pa.s/mesh/element/average`；`force/vector/N/m/aggregate//integral`；`mass_flow/scalar/kg/(m.s)/aggregate//integral`；`pressure/scalar/Pa/mesh/element/average`；`shear_rate/scalar/1/s/mesh/element/average`；`traction/vector/Pa/mesh/element/average`；`velocity/vector/m/s/mesh/element/average`；`volume_flow/scalar/m2/s/aggregate//integral`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 45. generalized-newtonian-incompressible-transient-2d

- 文档：`qbank/02-fluid-mechanics/2.1-single-phase-flow/generalized-newtonian-incompressible-transient-2d/DATA.md`、`instruction.md`；正式 8，样例 1；覆盖实值/分支声明 105 项、输入场数组 22 个、实际网格引用 9 个。
- 条件：`boundary/flow/flow_rate`；`boundary/flow/moving_wall`；`boundary/flow/no_slip`；`boundary/flow/periodic`；`boundary/flow/pressure_outlet`；`boundary/flow/slip`；`boundary/flow/symmetry`；`boundary/flow/velocity`；`initial/velocity/assign`；`source/velocity/acceleration`
- 输入采样：`piecewise_constant/constant/forbid`；`piecewise_constant/linear/forbid`；`piecewise_linear/constant/forbid`；`piecewise_linear/linear/forbid`；`uniform/linear/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`density/scalar/kg/m3/mesh/element/average`；`dynamic_viscosity/scalar/Pa.s/mesh/element/average`；`force/vector/N/m/aggregate//integral`；`mass_flow/scalar/kg/(m.s)/aggregate//integral`；`pressure/scalar/Pa/mesh/element/average`；`shear_rate/scalar/1/s/mesh/element/average`；`traction/vector/Pa/mesh/element/average`；`velocity/vector/m/s/mesh/element/average`；`volume_flow/scalar/m2/s/aggregate//integral`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；公开允许 previous 采样，实际集仅 constant/linear；公开允许 hold 外推，实际集仅 forbid

### 46. generalized-newtonian-incompressible-steady-3d

- 文档：`qbank/02-fluid-mechanics/2.1-single-phase-flow/generalized-newtonian-incompressible-steady-3d/DATA.md`、`instruction.md`；正式 7，样例 1；覆盖实值/分支声明 93 项、输入场数组 13 个、实际网格引用 8 个。
- 条件：`boundary/flow/flow_rate`；`boundary/flow/moving_wall`；`boundary/flow/no_slip`；`boundary/flow/pressure_outlet`；`boundary/flow/slip`；`boundary/flow/symmetry`；`boundary/flow/velocity`；`source/velocity/acceleration`
- 输入采样：`piecewise_constant/constant/forbid`；`piecewise_linear/constant/forbid`；`uniform/constant/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`density/scalar/kg/m3/mesh/element/average`；`dynamic_viscosity/scalar/Pa.s/mesh/element/average`；`force/vector/N/aggregate//integral`；`mass_flow/scalar/kg/s/aggregate//integral`；`pressure/scalar/Pa/mesh/element/average`；`shear_rate/scalar/1/s/mesh/element/average`；`traction/vector/Pa/mesh/element/average`；`velocity/vector/m/s/mesh/element/average`；`volume_flow/scalar/m3/s/aggregate//integral`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 47. generalized-newtonian-incompressible-transient-3d

- 文档：`qbank/02-fluid-mechanics/2.1-single-phase-flow/generalized-newtonian-incompressible-transient-3d/DATA.md`、`instruction.md`；正式 8，样例 1；覆盖实值/分支声明 106 项、输入场数组 22 个、实际网格引用 9 个。
- 条件：`boundary/flow/flow_rate`；`boundary/flow/moving_wall`；`boundary/flow/no_slip`；`boundary/flow/periodic`；`boundary/flow/pressure_outlet`；`boundary/flow/slip`；`boundary/flow/symmetry`；`boundary/flow/velocity`；`initial/velocity/assign`；`source/velocity/acceleration`
- 输入采样：`piecewise_constant/constant/forbid`；`piecewise_constant/linear/forbid`；`piecewise_linear/constant/forbid`；`piecewise_linear/linear/forbid`；`uniform/linear/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`density/scalar/kg/m3/mesh/element/average`；`dynamic_viscosity/scalar/Pa.s/mesh/element/average`；`force/vector/N/aggregate//integral`；`mass_flow/scalar/kg/s/aggregate//integral`；`pressure/scalar/Pa/mesh/element/average`；`shear_rate/scalar/1/s/mesh/element/average`；`traction/vector/Pa/mesh/element/average`；`velocity/vector/m/s/mesh/element/average`；`volume_flow/scalar/m3/s/aggregate//integral`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；公开允许 previous 采样，实际集仅 constant/linear；公开允许 hold 外推，实际集仅 forbid

### 48. newtonian-isothermal-compressible-steady-2d

- 文档：`qbank/02-fluid-mechanics/2.1-single-phase-flow/newtonian-isothermal-compressible-steady-2d/DATA.md`、`instruction.md`；正式 3，样例 1；覆盖实值/分支声明 57 项、输入场数组 4 个、实际网格引用 4 个。
- 条件：`boundary/flow/moving_wall`；`boundary/flow/no_slip`
- 输入采样：`piecewise_constant/constant/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`density/scalar/kg/m3/mesh/element/average`；`dynamic_viscosity/scalar/Pa.s/mesh/element/average`；`force/vector/N/m/aggregate//integral`；`mass_flow/scalar/kg/(m.s)/aggregate//integral`；`pressure/scalar/Pa/mesh/element/average`；`shear_rate/scalar/1/s/mesh/element/average`；`traction/vector/Pa/mesh/element/average`；`velocity/vector/m/s/mesh/element/average`；`volume_flow/scalar/m2/s/aggregate//integral`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 49. newtonian-isothermal-compressible-transient-2d

- 文档：`qbank/02-fluid-mechanics/2.1-single-phase-flow/newtonian-isothermal-compressible-transient-2d/DATA.md`、`instruction.md`；正式 5，样例 1；覆盖实值/分支声明 72 项、输入场数组 18 个、实际网格引用 6 个。
- 条件：`boundary/flow/moving_wall`；`boundary/flow/no_slip`；`boundary/flow/slip`；`initial/density/assign`；`initial/velocity/assign`；`source/velocity/acceleration`
- 输入采样：`piecewise_constant/constant/forbid`；`piecewise_constant/linear/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`density/scalar/kg/m3/mesh/element/average`；`dynamic_viscosity/scalar/Pa.s/mesh/element/average`；`force/vector/N/m/aggregate//integral`；`mass_flow/scalar/kg/(m.s)/aggregate//integral`；`pressure/scalar/Pa/mesh/element/average`；`shear_rate/scalar/1/s/mesh/element/average`；`traction/vector/Pa/mesh/element/average`；`velocity/vector/m/s/mesh/element/average`；`volume_flow/scalar/m2/s/aggregate//integral`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；公开允许 previous 采样，实际集仅 constant/linear；公开允许 hold 外推，实际集仅 forbid

### 50. newtonian-isothermal-compressible-steady-3d

- 文档：`qbank/02-fluid-mechanics/2.1-single-phase-flow/newtonian-isothermal-compressible-steady-3d/DATA.md`、`instruction.md`；正式 3，样例 1；覆盖实值/分支声明 57 项、输入场数组 4 个、实际网格引用 4 个。
- 条件：`boundary/flow/moving_wall`；`boundary/flow/no_slip`
- 输入采样：`piecewise_constant/constant/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`density/scalar/kg/m3/mesh/element/average`；`dynamic_viscosity/scalar/Pa.s/mesh/element/average`；`force/vector/N/aggregate//integral`；`mass_flow/scalar/kg/s/aggregate//integral`；`pressure/scalar/Pa/mesh/element/average`；`shear_rate/scalar/1/s/mesh/element/average`；`traction/vector/Pa/mesh/element/average`；`velocity/vector/m/s/mesh/element/average`；`volume_flow/scalar/m3/s/aggregate//integral`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 51. newtonian-isothermal-compressible-transient-3d

- 文档：`qbank/02-fluid-mechanics/2.1-single-phase-flow/newtonian-isothermal-compressible-transient-3d/DATA.md`、`instruction.md`；正式 5，样例 1；覆盖实值/分支声明 72 项、输入场数组 18 个、实际网格引用 6 个。
- 条件：`boundary/flow/moving_wall`；`boundary/flow/no_slip`；`boundary/flow/slip`；`initial/density/assign`；`initial/velocity/assign`；`source/velocity/acceleration`
- 输入采样：`piecewise_constant/constant/forbid`；`piecewise_constant/linear/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`density/scalar/kg/m3/mesh/element/average`；`dynamic_viscosity/scalar/Pa.s/mesh/element/average`；`force/vector/N/aggregate//integral`；`mass_flow/scalar/kg/s/aggregate//integral`；`pressure/scalar/Pa/mesh/element/average`；`shear_rate/scalar/1/s/mesh/element/average`；`traction/vector/Pa/mesh/element/average`；`velocity/vector/m/s/mesh/element/average`；`volume_flow/scalar/m3/s/aggregate//integral`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；公开允许 previous 采样，实际集仅 constant/linear；公开允许 hold 外推，实际集仅 forbid

### 52. newtonian-lowmach-steady-2d

- 文档：`qbank/02-fluid-mechanics/2.2-single-phase-energy/newtonian-lowmach-steady-2d/DATA.md`、`instruction.md`；正式 10，样例 1；覆盖实值/分支声明 66 项、输入场数组 57 个、实际网格引用 11 个。
- 条件：`boundary/temperature/outward_heat_flux`；`boundary/temperature/temperature`；`boundary/velocity/moving_wall`；`source/acceleration/assign`；`source/heat_source/assign`
- 输入采样：`piecewise_constant/constant/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`pressure/scalar/Pa/mesh/element/average`；`temperature/scalar/K/mesh/element/average`；`velocity/vector/m/s/mesh/element/average`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 53. newtonian-lowmach-transient-2d

- 文档：`qbank/02-fluid-mechanics/2.2-single-phase-energy/newtonian-lowmach-transient-2d/DATA.md`、`instruction.md`；正式 10，样例 1；覆盖实值/分支声明 73 项、输入场数组 79 个、实际网格引用 11 个。
- 条件：`boundary/temperature/outward_heat_flux`；`boundary/temperature/temperature`；`boundary/velocity/moving_wall`；`initial/temperature/assign`；`initial/velocity/assign`；`source/acceleration/assign`；`source/heat_source/assign`
- 输入采样：`piecewise_constant/constant/forbid`；`piecewise_constant/linear/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`pressure/scalar/Pa/mesh/element/average`；`temperature/scalar/K/mesh/element/average`；`velocity/vector/m/s/mesh/element/average`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 54. newtonian-lowmach-steady-3d

- 文档：`qbank/02-fluid-mechanics/2.2-single-phase-energy/newtonian-lowmach-steady-3d/DATA.md`、`instruction.md`；正式 10，样例 1；覆盖实值/分支声明 67 项、输入场数组 59 个、实际网格引用 11 个。
- 条件：`boundary/temperature/outward_heat_flux`；`boundary/temperature/temperature`；`boundary/velocity/moving_wall`；`source/acceleration/assign`；`source/heat_source/assign`
- 输入采样：`piecewise_constant/constant/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`pressure/scalar/Pa/mesh/element/average`；`temperature/scalar/K/mesh/element/average`；`velocity/vector/m/s/mesh/element/average`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 55. newtonian-lowmach-transient-3d

- 文档：`qbank/02-fluid-mechanics/2.2-single-phase-energy/newtonian-lowmach-transient-3d/DATA.md`、`instruction.md`；正式 10，样例 1；覆盖实值/分支声明 74 项、输入场数组 81 个、实际网格引用 11 个。
- 条件：`boundary/temperature/outward_heat_flux`；`boundary/temperature/temperature`；`boundary/velocity/moving_wall`；`initial/temperature/assign`；`initial/velocity/assign`；`source/acceleration/assign`；`source/heat_source/assign`
- 输入采样：`piecewise_constant/constant/forbid`；`piecewise_constant/linear/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`pressure/scalar/Pa/mesh/element/average`；`temperature/scalar/K/mesh/element/average`；`velocity/vector/m/s/mesh/element/average`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 56. inviscid-compressible-steady-2d

- 文档：`qbank/02-fluid-mechanics/2.2-single-phase-energy/inviscid-compressible-steady-2d/DATA.md`、`instruction.md`；正式 10，样例 1；覆盖实值/分支声明 40 项、输入场数组 11 个、实际网格引用 11 个。
- 条件：`boundary/velocity/slip_wall`；`source/acceleration/assign`
- 输入采样：`piecewise_constant/constant/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`density/scalar/kg/m3/mesh/element/average`；`pressure/scalar/Pa/mesh/element/average`；`temperature/scalar/K/mesh/element/average`；`velocity/vector/m/s/mesh/element/average`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 57. inviscid-compressible-transient-2d

- 文档：`qbank/02-fluid-mechanics/2.2-single-phase-energy/inviscid-compressible-transient-2d/DATA.md`、`instruction.md`；正式 10，样例 1；覆盖实值/分支声明 54 项、输入场数组 34 个、实际网格引用 11 个。
- 条件：`boundary/velocity/slip_wall`；`initial/density/assign`；`initial/temperature/assign`；`initial/velocity/assign`；`source/acceleration/assign`
- 输入采样：`piecewise_constant/constant/forbid`；`piecewise_constant/linear/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`density/scalar/kg/m3/mesh/element/average`；`pressure/scalar/Pa/mesh/element/average`；`temperature/scalar/K/mesh/element/average`；`velocity/vector/m/s/mesh/element/average`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；未出现公开条件分支：source/heat_source/assign

### 58. inviscid-compressible-steady-3d

- 文档：`qbank/02-fluid-mechanics/2.2-single-phase-energy/inviscid-compressible-steady-3d/DATA.md`、`instruction.md`；正式 10，样例 1；覆盖实值/分支声明 40 项、输入场数组 11 个、实际网格引用 11 个。
- 条件：`boundary/velocity/slip_wall`；`source/acceleration/assign`
- 输入采样：`piecewise_constant/constant/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`density/scalar/kg/m3/mesh/element/average`；`pressure/scalar/Pa/mesh/element/average`；`temperature/scalar/K/mesh/element/average`；`velocity/vector/m/s/mesh/element/average`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 59. inviscid-compressible-transient-3d

- 文档：`qbank/02-fluid-mechanics/2.2-single-phase-energy/inviscid-compressible-transient-3d/DATA.md`、`instruction.md`；正式 10，样例 1；覆盖实值/分支声明 54 项、输入场数组 34 个、实际网格引用 11 个。
- 条件：`boundary/velocity/slip_wall`；`initial/density/assign`；`initial/temperature/assign`；`initial/velocity/assign`；`source/acceleration/assign`
- 输入采样：`piecewise_constant/constant/forbid`；`piecewise_constant/linear/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`density/scalar/kg/m3/mesh/element/average`；`pressure/scalar/Pa/mesh/element/average`；`temperature/scalar/K/mesh/element/average`；`velocity/vector/m/s/mesh/element/average`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；未出现公开条件分支：source/heat_source/assign

### 60. newtonian-compressible-transient-2d

- 文档：`qbank/02-fluid-mechanics/2.2-single-phase-energy/newtonian-compressible-transient-2d/DATA.md`、`instruction.md`；正式 5，样例 1；覆盖实值/分支声明 66 项、输入场数组 41 个、实际网格引用 6 个。
- 条件：`boundary/temperature/outward_heat_flux`；`boundary/temperature/temperature`；`boundary/velocity/moving_wall`；`initial/density/assign`；`initial/temperature/assign`；`initial/velocity/assign`
- 输入采样：`piecewise_constant/constant/forbid`；`piecewise_constant/linear/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`density/scalar/kg/m3/mesh/element/average`；`pressure/scalar/Pa/mesh/element/average`；`temperature/scalar/K/mesh/element/average`；`velocity/vector/m/s/mesh/element/average`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；未出现公开条件分支：source/acceleration/assign, source/heat_source/assign

### 61. newtonian-compressible-transient-3d

- 文档：`qbank/02-fluid-mechanics/2.2-single-phase-energy/newtonian-compressible-transient-3d/DATA.md`、`instruction.md`；正式 5，样例 1；覆盖实值/分支声明 67 项、输入场数组 42 个、实际网格引用 6 个。
- 条件：`boundary/temperature/outward_heat_flux`；`boundary/temperature/temperature`；`boundary/velocity/moving_wall`；`initial/density/assign`；`initial/temperature/assign`；`initial/velocity/assign`
- 输入采样：`piecewise_constant/constant/forbid`；`piecewise_constant/linear/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`density/scalar/kg/m3/mesh/element/average`；`pressure/scalar/Pa/mesh/element/average`；`temperature/scalar/K/mesh/element/average`；`velocity/vector/m/s/mesh/element/average`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；未出现公开条件分支：source/acceleration/assign, source/heat_source/assign

### 62. rans-steady-2d

- 文档：`qbank/02-fluid-mechanics/2.3-turbulent-flow/rans-steady-2d/DATA.md`、`instruction.md`；正式 8，样例 1；覆盖实值/分支声明 38 项、输入场数组 26 个、实际网格引用 9 个。
- 条件：`boundary/velocity/moving_wall`；`source/acceleration/assign`
- 输入采样：`piecewise_constant/constant/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`pressure/scalar/Pa/mesh/element/average`；`velocity/vector/m/s/mesh/element/average`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 63. rans-steady-3d

- 文档：`qbank/02-fluid-mechanics/2.3-turbulent-flow/rans-steady-3d/DATA.md`、`instruction.md`；正式 7，样例 1；覆盖实值/分支声明 38 项、输入场数组 20 个、实际网格引用 8 个。
- 条件：`boundary/velocity/moving_wall`；`source/acceleration/assign`
- 输入采样：`piecewise_constant/constant/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`pressure/scalar/Pa/mesh/element/average`；`velocity/vector/m/s/mesh/element/average`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 64. urans-transient-3d

- 文档：`qbank/02-fluid-mechanics/2.3-turbulent-flow/urans-transient-3d/DATA.md`、`instruction.md`；正式 10，样例 1；覆盖实值/分支声明 54 项、输入场数组 63 个、实际网格引用 11 个。
- 条件：`boundary/velocity/moving_wall`；`initial/turbulence_length_scale/assign`；`initial/turbulent_kinetic_energy/assign`；`initial/velocity/assign`；`source/acceleration/assign`
- 输入采样：`piecewise_constant/constant/forbid`；`piecewise_constant/linear/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`pressure/scalar/Pa/mesh/element/average`；`velocity/vector/m/s/mesh/element/average`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 65. resolved-statistics-3d

- 文档：`qbank/02-fluid-mechanics/2.3-turbulent-flow/resolved-statistics-3d/DATA.md`、`instruction.md`；正式 10，样例 1；覆盖实值/分支声明 51 项、输入场数组 41 个、实际网格引用 11 个。
- 条件：`boundary/velocity/moving_wall`；`initial/velocity/assign`；`source/acceleration/assign`
- 输入采样：`piecewise_constant/constant/forbid`；`piecewise_constant/linear/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`pressure/scalar/Pa/mesh/element/average`；`velocity/vector/m/s/mesh/element/average`；`velocity_covariance/tensor/m2/s2/mesh/element/average`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 66. isothermal-rans-3d

- 文档：`qbank/02-fluid-mechanics/2.3-turbulent-flow/isothermal-rans-3d/DATA.md`、`instruction.md`；正式 7，样例 1；覆盖实值/分支声明 41 项、输入场数组 20 个、实际网格引用 8 个。
- 条件：`boundary/velocity/moving_wall`；`source/acceleration/assign`
- 输入采样：`piecewise_constant/constant/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`density/scalar/kg/m3/mesh/element/average`；`pressure/scalar/Pa/mesh/element/average`；`velocity/vector/m/s/mesh/element/average`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 67. thermal-rans-3d

- 文档：`qbank/02-fluid-mechanics/2.4-turbulent-energy/thermal-rans-3d/DATA.md`、`instruction.md`；正式 9，样例 1；覆盖实值/分支声明 63 项、输入场数组 54 个、实际网格引用 10 个。
- 条件：`boundary/temperature/outward_heat_flux`；`boundary/temperature/temperature`；`boundary/velocity/moving_wall`；`source/acceleration/assign`
- 输入采样：`piecewise_constant/constant/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`pressure/scalar/Pa/mesh/element/average`；`temperature/scalar/K/mesh/element/average`；`velocity/vector/m/s/mesh/element/average`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；未出现公开条件分支：source/heat_source/assign

### 68. thermal-urans-3d

- 文档：`qbank/02-fluid-mechanics/2.4-turbulent-energy/thermal-urans-3d/DATA.md`、`instruction.md`；正式 4，样例 1；覆盖实值/分支声明 72 项、输入场数组 47 个、实际网格引用 5 个。
- 条件：`boundary/temperature/outward_heat_flux`；`boundary/temperature/temperature`；`boundary/velocity/moving_wall`；`initial/temperature/assign`；`initial/turbulence_length_scale/assign`；`initial/turbulent_kinetic_energy/assign`；`initial/velocity/assign`
- 输入采样：`piecewise_constant/constant/forbid`；`piecewise_constant/linear/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`pressure/scalar/Pa/mesh/element/average`；`temperature/scalar/K/mesh/element/average`；`velocity/vector/m/s/mesh/element/average`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；未出现公开条件分支：source/acceleration/assign, source/heat_source/assign

### 69. thermal-statistics-3d

- 文档：`qbank/02-fluid-mechanics/2.4-turbulent-energy/thermal-statistics-3d/DATA.md`、`instruction.md`；正式 10，样例 1；覆盖实值/分支声明 86 项、输入场数组 81 个、实际网格引用 11 个。
- 条件：`boundary/temperature/outward_heat_flux`；`boundary/temperature/temperature`；`boundary/velocity/moving_wall`；`initial/temperature/assign`；`initial/velocity/assign`；`source/acceleration/assign`；`source/heat_source/assign`
- 输入采样：`piecewise_constant/constant/forbid`；`piecewise_constant/linear/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`pressure/scalar/Pa/mesh/element/average`；`temperature/scalar/K/mesh/element/average`；`temperature_variance/scalar/K2/mesh/element/average`；`turbulent_heat_flux/vector/K.m/s/mesh/element/average`；`velocity/vector/m/s/mesh/element/average`；`velocity_covariance/tensor/m2/s2/mesh/element/average`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 70. immiscible-interface-2d

- 文档：`qbank/02-fluid-mechanics/2.5-interface-flow/immiscible-interface-2d/DATA.md`、`instruction.md`；正式 10，样例 1；覆盖实值/分支声明 51 项、输入场数组 33 个、实际网格引用 11 个。
- 条件：`boundary/flow/wall`；`initial/alpha/assign`；`initial/velocity/assign`；`source/acceleration/assign`
- 输入采样：`piecewise_constant/constant/forbid`；`piecewise_constant/linear/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`alpha/scalar/1/mesh/element/average`；`pressure/scalar/Pa/mesh/element/average`；`velocity/vector/m/s/mesh/element/average`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 71. immiscible-interface-3d

- 文档：`qbank/02-fluid-mechanics/2.5-interface-flow/immiscible-interface-3d/DATA.md`、`instruction.md`；正式 10，样例 1；覆盖实值/分支声明 51 项、输入场数组 33 个、实际网格引用 11 个。
- 条件：`boundary/flow/wall`；`initial/alpha/assign`；`initial/velocity/assign`；`source/acceleration/assign`
- 输入采样：`piecewise_constant/constant/forbid`；`piecewise_constant/linear/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`alpha/scalar/1/mesh/element/average`；`pressure/scalar/Pa/mesh/element/average`；`velocity/vector/m/s/mesh/element/average`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 72. gas-film

- 文档：`qbank/02-fluid-mechanics/2.8-thin-film/gas-film/DATA.md`、`instruction.md`；正式 10，样例 1；覆盖实值/分支声明 144 项、输入场数组 852 个、实际网格引用 11 个。
- 条件：`boundary/pressure/film_pressure`；`initial/pressure/assign`；`material/gap/geometry`；`material/lower_velocity/geometry`；`material/upper_velocity/geometry`
- 输入采样：`piecewise_constant/linear/forbid`；`piecewise_linear/constant/forbid`；`piecewise_linear/linear/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`density/scalar/kg/m3/mesh/node/point`；`film_flux/vector/m2/s/mesh/node/point`；`load/scalar/N/aggregate//integral`；`pressure/scalar/Pa/mesh/node/point`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 73. fully-wet-steady

- 文档：`qbank/02-fluid-mechanics/2.9-shallow-water/fully-wet-steady/DATA.md`、`instruction.md`；正式 3，样例 1；覆盖实值/分支声明 48 项、输入场数组 12 个、实际网格引用 4 个。
- 条件：`boundary/water/water_reservoir`；`boundary/water/water_wall`；`material/bed/geometry`
- 输入采样：`piecewise_constant/constant/forbid`；`piecewise_linear/constant/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`depth/scalar/m/mesh/node/point`；`velocity/vector/m/s/mesh/node/point`；`water_flux/vector/m2/s/mesh/node/point`；`water_volume/scalar/m3/aggregate//integral`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 74. fully-wet-transient

- 文档：`qbank/02-fluid-mechanics/2.9-shallow-water/fully-wet-transient/DATA.md`、`instruction.md`；正式 9，样例 1；覆盖实值/分支声明 56 项、输入场数组 32 个、实际网格引用 10 个。
- 条件：`boundary/water/water_reservoir`；`boundary/water/water_wall`；`initial/depth/assign`；`initial/velocity/assign`；`material/bed/geometry`
- 输入采样：`piecewise_constant/constant/forbid`；`piecewise_constant/linear/forbid`；`piecewise_linear/constant/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`depth/scalar/m/mesh/node/point`；`velocity/vector/m/s/mesh/node/point`；`water_flux/vector/m2/s/mesh/node/point`；`water_volume/scalar/m3/aggregate//integral`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 75. wetting-drying

- 文档：`qbank/02-fluid-mechanics/2.9-shallow-water/wetting-drying/DATA.md`、`instruction.md`；正式 7，样例 1；覆盖实值/分支声明 56 项、输入场数组 26 个、实际网格引用 8 个。
- 条件：`boundary/water/water_reservoir`；`boundary/water/water_wall`；`initial/depth/assign`；`initial/velocity/assign`；`material/bed/geometry`
- 输入采样：`piecewise_constant/constant/forbid`；`piecewise_constant/linear/forbid`；`piecewise_linear/constant/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`depth/scalar/m/mesh/node/point`；`velocity/vector/m/s/mesh/node/point`；`water_flux/vector/m2/s/mesh/node/point`；`water_volume/scalar/m3/aggregate//integral`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 76. transition-gas

- 文档：`qbank/02-fluid-mechanics/2.10-rarefied-gas/transition-gas/DATA.md`、`instruction.md`；正式 10，样例 1；覆盖实值/分支声明 60 项、输入场数组 40 个、实际网格引用 11 个。
- 条件：`boundary/gas/gas_reservoir`；`boundary/gas/gas_wall`
- 输入采样：`piecewise_constant/constant/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`density/scalar/kg/m3/mesh/node/point`；`heat_flux/vector/W/m2/mesh/element/average`；`pressure/scalar/Pa/mesh/node/point`；`temperature/scalar/K/mesh/node/point`；`traction/vector/Pa/mesh/element/average`；`velocity/vector/m/s/mesh/node/point`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 77. free-molecular

- 文档：`qbank/02-fluid-mechanics/2.10-rarefied-gas/free-molecular/DATA.md`、`instruction.md`；正式 10，样例 1；覆盖实值/分支声明 60 项、输入场数组 40 个、实际网格引用 11 个。
- 条件：`boundary/gas/gas_reservoir`；`boundary/gas/gas_wall`
- 输入采样：`piecewise_constant/constant/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`density/scalar/kg/m3/mesh/node/point`；`heat_flux/vector/W/m2/mesh/element/average`；`pressure/scalar/Pa/mesh/node/point`；`temperature/scalar/K/mesh/node/point`；`traction/vector/Pa/mesh/element/average`；`velocity/vector/m/s/mesh/node/point`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；没有从本次条件表抽取中发现缺席分支（不等于参数空间穷尽）。

### 78. viscoelastic-steady

- 文档：`qbank/02-fluid-mechanics/2.11-memory-fluids/viscoelastic-steady/DATA.md`、`instruction.md`；正式 9，样例 1；覆盖实值/分支声明 41 项、输入场数组 27 个、实际网格引用 10 个。
- 条件：`boundary/velocity/velocity_wall`
- 输入采样：`piecewise_constant/constant/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`conformation/tensor/1/mesh/node/point`；`polymer_stress/tensor/Pa/mesh/node/point`；`pressure/scalar/Pa/mesh/node/point`；`traction/vector/Pa/mesh/element/average`；`velocity/vector/m/s/mesh/node/point`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；公开 velocity_inlet/conformation 与 traction_outlet 未出现；实际边界只有 velocity_wall

### 79. viscoelastic-transient

- 文档：`qbank/02-fluid-mechanics/2.11-memory-fluids/viscoelastic-transient/DATA.md`、`instruction.md`；正式 9，样例 1；覆盖实值/分支声明 53 项、输入场数组 44 个、实际网格引用 10 个。
- 条件：`boundary/velocity/velocity_wall`；`initial/conformation/assign`；`initial/velocity/assign`
- 输入采样：`piecewise_constant/linear/forbid`；`piecewise_linear/constant/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`conformation/tensor/1/mesh/node/point`；`polymer_stress/tensor/Pa/mesh/node/point`；`pressure/scalar/Pa/mesh/node/point`；`traction/vector/Pa/mesh/element/average`；`velocity/vector/m/s/mesh/node/point`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；公开 velocity_inlet/conformation 与 traction_outlet 未出现；实际边界只有 velocity_wall

### 80. newtonian-compressible-steady-2d

- 文档：`qbank/02-fluid-mechanics/2.2-single-phase-energy/newtonian-compressible-steady-2d/DATA.md`、`instruction.md`；正式 4，样例 1；覆盖实值/分支声明 60 项、输入场数组 22 个、实际网格引用 5 个。
- 条件：`boundary/temperature/outward_heat_flux`；`boundary/temperature/temperature`；`boundary/velocity/moving_wall`；`source/heat_source/assign`
- 输入采样：`piecewise_constant/constant/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`density/scalar/kg/m3/mesh/element/average`；`pressure/scalar/Pa/mesh/element/average`；`temperature/scalar/K/mesh/element/average`；`velocity/vector/m/s/mesh/element/average`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；未出现公开条件分支：source/acceleration/assign

### 81. newtonian-compressible-steady-3d

- 文档：`qbank/02-fluid-mechanics/2.2-single-phase-energy/newtonian-compressible-steady-3d/DATA.md`、`instruction.md`；正式 3，样例 1；覆盖实值/分支声明 60 项、输入场数组 20 个、实际网格引用 4 个。
- 条件：`boundary/temperature/outward_heat_flux`；`boundary/temperature/temperature`；`boundary/velocity/moving_wall`；`source/heat_source/assign`
- 输入采样：`piecewise_constant/constant/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`density/scalar/kg/m3/mesh/element/average`；`pressure/scalar/Pa/mesh/element/average`；`temperature/scalar/K/mesh/element/average`；`velocity/vector/m/s/mesh/element/average`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；未出现公开条件分支：source/acceleration/assign

### 82. compressible-thermal-rans-3d

- 文档：`qbank/02-fluid-mechanics/2.4-turbulent-energy/compressible-thermal-rans-3d/DATA.md`、`instruction.md`；正式 4，样例 1；覆盖实值/分支声明 60 项、输入场数组 23 个、实际网格引用 5 个。
- 条件：`boundary/temperature/outward_heat_flux`；`boundary/temperature/temperature`；`boundary/velocity/moving_wall`；`source/heat_source/assign`
- 输入采样：`piecewise_constant/constant/forbid`
- 输出（quantity/kind/unit/location-kind/entity/value_kind）：`density/scalar/kg/m3/mesh/element/average`；`pressure/scalar/Pa/mesh/element/average`；`temperature/scalar/K/mesh/element/average`；`velocity/vector/m/s/mesh/element/average`
- 检查结论：声明与实际输入所检项目一致；数值/轨迹保证未认证。公开完整输出 1/1 个角色；未出现公开条件分支：source/acceleration/assign
