# 2.1.3 算例出题报告

已发布范围仍以[发布记录](data-evidence/supplement/publication.json)为准：72 例，固定提交 `d78adb9290bc3531223ce29b140b0fd633d0bcd4`。以下是当前制作批次的数值记录，通过数量不等于已发布数量。

当前快照：完成 100/100，通过 72，未通过 28；未完成项不计为失败。

## 参考生产预算与计量

当前每次原生求解申请 2 CPU、4g 内存、3600 秒，20 路制作。具体离散和迭代上限见[作者配置](README.md#求解器配置)。本报告耗时来自共享环境中的参考生产，不代表考生资源可行性验证。

耗时统一取原生工具回执的 `seconds`，不混用适配器外围计时；复用项记录历史运行的实际配额和耗时。迭代上限来自各次原生配置，OpenFOAM 的稳态伪时间每次增加 1，因此 endTime 对应 SIMPLE 外迭代上限。每个网格级别分别列出两套求解器；“—”表示未记录或不适用，不代表零。运行中条目显示最后观测值，正常退出也不单独代表算例通过。

线性残差保留求解器原生口径，不能跨软件直接比较。Elmer 的非线性绝对更新量单列，不冒充方程残差；OpenFOAM 的 SIMPLE 外迭代编号、最后一轮各次线性求解残差及连续性指标分别保存。误差比为绝对差除以判分允许误差，超过 1 表示不通过；制作参考另有精度余量要求。

机器可读明细与日志摘要绑定见 [production-report.json](data-evidence/supplement/production-report.json)，可逐例查看完整输出误差、OpenFOAM 线性求解初始／最终残差、线性迭代数和运行身份。快照时间与批次代码摘要也保存在该文件。

## 结果汇总

| 工况族 | 候选 | 通过 | 未通过 | 未完成 |
|---|---:|---:|---:|---:|
| hydrostatic | 18 | 18 | 0 | 0 |
| couette | 20 | 20 | 0 | 0 |
| periodic-duct | 20 | 12 | 8 | 0 |
| cavity | 24 | 10 | 14 | 0 |
| plug | 18 | 12 | 6 | 0 |

通过集的几何覆盖：box 70 例、obstacle 2 例。候选设计覆盖不等于通过集覆盖。


| 最后一次尝试的未通过原因 | 数量 | 算例 |
|---|---:|---|
| 原生求解超时 | 6 | 051-periodic-duct-13, 056-periodic-duct-18, 084-plug-02, 087-plug-05, 090-plug-08, 093-plug-11 |
| 交叉判分未通过 | 11 | 052-periodic-duct-14, 053-periodic-duct-15, 054-periodic-duct-16, 057-periodic-duct-19, 058-periodic-duct-20, 061-cavity-03, 062-cavity-04, 066-cavity-08, 070-cavity-12, 081-cavity-23, 082-cavity-24 |
| 参考精度余量不足 | 9 | 055-periodic-duct-17, 067-cavity-09, 069-cavity-11, 073-cavity-15, 074-cavity-16, 076-cavity-18, 077-cavity-19, 078-cavity-20, 080-cavity-22 |
| 原生求解异常退出 | 2 | 096-plug-14, 099-plug-17 |

原因按最后一次尝试归类，不将此前粗网格失败重复计数。交叉判分通过还须满足参考制作精度余量：最大误差比不超过 0.35，或适用的解析一致性误差比不超过 0.25。未通过者不得当作就绪参考；超差尚不能归因于某一套求解器，仍需检查离散、收敛和转换。


## 逐例记录

### 001-hydrostatic-01：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 4.0/4g/600.0 | 100/3000 | 12.05 | 17 | 6.103e-12 | 4.706e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 0.7669 | 1 | Ux=0; Uy=0; Uz=0; p[1]=0; p[2]=0 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 3.84e-13 | m/s | 3.84e-10 |
| 12 | answer_pressure | 2.809e-09 | Pa | 2.772e-12 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 5.512e-13 | Pa | 5.512e-12 |
| 12 | answer_mean_pressure | 3.492e-10 | Pa | 3.446e-13 |
| 12 | answer_shear | 1.973e-12 | 1/s | 1.973e-10 |
| 12 | answer_force3 | 5.239e-10 | N | 5.218e-10 |
| 12 | answer_volume_flow3 | 0 | m3/s | 0 |
| 12 | answer_mass_flow3 | 0 | kg/s | 0 |
| 12 | answer_force4 | 4.948e-10 | N | 3.649e-10 |
| 12 | answer_volume_flow4 | 0 | m3/s | 0 |
| 12 | answer_mass_flow4 | 0 | kg/s | 0 |

### 002-hydrostatic-02：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 4.0/4g/600.0 | 100/3000 | 11.8 | 17 | 3.254e-12 | 9.388e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 0.8174 | 1 | Ux=0; Uy=0; Uz=0; p[1]=0; p[2]=0 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 4.497e-13 | m/s | 4.497e-10 |
| 12 | answer_pressure | 1.297e-09 | Pa | 1.081e-08 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 1.253e-12 | Pa | 1.253e-11 |
| 12 | answer_mean_pressure | 5.39e-11 | Pa | 4.9e-10 |
| 12 | answer_shear | 2.224e-12 | 1/s | 2.224e-10 |
| 12 | answer_force3 | 2.414e-13 | N | 2.414e-10 |
| 12 | answer_volume_flow3 | 0 | m3/s | 0 |
| 12 | answer_mass_flow3 | 0 | kg/s | 0 |
| 12 | answer_force4 | 2.967e-13 | N | 2.967e-10 |
| 12 | answer_volume_flow4 | 0 | m3/s | 0 |
| 12 | answer_mass_flow4 | 0 | kg/s | 0 |

### 003-hydrostatic-03：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 4.0/4g/600.0 | 100/3000 | 13 | 17 | 7.619e-12 | 4.695e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 0.9682 | 1 | Ux=0; Uy=0; Uz=0; p[1]=0; p[2]=0 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 1.641e-13 | m/s | 1.641e-10 |
| 12 | answer_pressure | 2.505e-09 | Pa | 2.489e-08 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 3.393e-12 | Pa | 3.393e-11 |
| 12 | answer_mean_pressure | 3.601e-10 | Pa | 3.429e-09 |
| 12 | answer_shear | 5.31e-13 | 1/s | 5.31e-11 |
| 12 | answer_force3 | 5.001e-10 | N | 8.336e-08 |
| 12 | answer_volume_flow3 | 0 | m3/s | 0 |
| 12 | answer_mass_flow3 | 0 | kg/s | 0 |
| 12 | answer_force4 | 5.001e-10 | N | 8.335e-08 |
| 12 | answer_volume_flow4 | 0 | m3/s | 0 |
| 12 | answer_mass_flow4 | 0 | kg/s | 0 |

### 004-hydrostatic-04：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 4.0/4g/600.0 | 100/3000 | 12.65 | 18 | 4.852e-12 | 7.057e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 0.8685 | 1 | Ux=0; Uy=0; Uz=0; p[1]=0; p[2]=0 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 1.68e-14 | m/s | 1.68e-11 |
| 12 | answer_pressure | 3.197e-08 | Pa | 2.642e-07 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 3.246e-08 | Pa | 2.793e-07 |
| 12 | answer_mean_pressure | 4.037e-11 | Pa | 3.23e-10 |
| 12 | answer_shear | 2.576e-13 | 1/s | 2.576e-11 |
| 12 | answer_force3 | 1.415e-09 | N | 1.415e-06 |
| 12 | answer_volume_flow3 | 0 | m3/s | 0 |
| 12 | answer_mass_flow3 | 0 | kg/s | 0 |
| 12 | answer_force4 | 1.131e-12 | N | 5.549e-10 |
| 12 | answer_volume_flow4 | 0 | m3/s | 0 |
| 12 | answer_mass_flow4 | 0 | kg/s | 0 |

### 005-hydrostatic-05：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 4.0/4g/600.0 | 100/3000 | 14.31 | 23 | 1.551e-12 | 2.613e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 0.9183 | 1 | Ux=0; Uy=0; Uz=0; p[1]=0; p[2]=0 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 1.75e-13 | m/s | 1.75e-10 |
| 12 | answer_pressure | 3.173e-10 | Pa | 2.644e-09 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 3.246e-06 | Pa | 1.905e-06 |
| 12 | answer_mean_pressure | 2.5e-07 | Pa | 4.921e-08 |
| 12 | answer_shear | 8.667e-13 | 1/s | 8.667e-11 |
| 12 | answer_force3 | 2.021e-10 | N | 9.778e-09 |
| 12 | answer_volume_flow3 | 0 | m3/s | 0 |
| 12 | answer_mass_flow3 | 0 | kg/s | 0 |
| 12 | answer_force4 | 8.449e-12 | N | 8.449e-09 |
| 12 | answer_volume_flow4 | 0 | m3/s | 0 |
| 12 | answer_mass_flow4 | 0 | kg/s | 0 |

### 006-hydrostatic-06：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 4.0/4g/600.0 | 100/3000 | 13.75 | 21 | 4.328e-12 | 7.649e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 0.8174 | 1 | Ux=0; Uy=0; Uz=0; p[1]=0; p[2]=0 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 8.662e-14 | m/s | 8.662e-11 |
| 12 | answer_pressure | 2.5e-06 | Pa | 2.465e-09 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 3.333e-06 | Pa | 3.286e-09 |
| 12 | answer_mean_pressure | 5.821e-11 | Pa | 5.738e-14 |
| 12 | answer_shear | 3.697e-13 | 1/s | 3.697e-11 |
| 12 | answer_force3 | 1.033e-09 | N | 9.98e-09 |
| 12 | answer_volume_flow3 | 0 | m3/s | 0 |
| 12 | answer_mass_flow3 | 0 | kg/s | 0 |
| 12 | answer_force4 | 9.968e-12 | N | 9.968e-09 |
| 12 | answer_volume_flow4 | 0 | m3/s | 0 |
| 12 | answer_mass_flow4 | 0 | kg/s | 0 |

### 007-hydrostatic-07：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 4.0/4g/600.0 | 100/3000 | 11.1 | 16 | 2.382e-12 | 7.83e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 1.069 | 1 | Ux=0; Uy=0; Uz=0; p[1]=0; p[2]=0 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 2.917e-13 | m/s | 2.917e-10 |
| 12 | answer_pressure | 2.797e-09 | Pa | 2.741e-08 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 3.057e-09 | Pa | 3.011e-08 |
| 12 | answer_mean_pressure | 2.115e-10 | Pa | 2.063e-09 |
| 12 | answer_shear | 3.657e-12 | 1/s | 3.657e-10 |
| 12 | answer_force3 | 2.293e-10 | N | 6.962e-08 |
| 12 | answer_volume_flow3 | 0 | m3/s | 0 |
| 12 | answer_mass_flow3 | 0 | kg/s | 0 |
| 12 | answer_force4 | 2.293e-10 | N | 6.965e-08 |
| 12 | answer_volume_flow4 | 0 | m3/s | 0 |
| 12 | answer_mass_flow4 | 0 | kg/s | 0 |

### 008-hydrostatic-08：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 4.0/4g/600.0 | 100/3000 | 12.8 | 17 | 3.798e-12 | 9.412e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 0.8181 | 1 | Ux=0; Uy=0; Uz=0; p[1]=0; p[2]=0 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 3.636e-12 | m/s | 3.636e-09 |
| 12 | answer_pressure | 1.302e-09 | Pa | 1.085e-08 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 3.057e-08 | Pa | 3.011e-07 |
| 12 | answer_mean_pressure | 5.364e-11 | Pa | 4.877e-10 |
| 12 | answer_shear | 1.882e-11 | 1/s | 1.882e-09 |
| 12 | answer_force3 | 7.577e-13 | N | 7.577e-10 |
| 12 | answer_volume_flow3 | 0 | m3/s | 0 |
| 12 | answer_mass_flow3 | 0 | kg/s | 0 |
| 12 | answer_force4 | 8.672e-13 | N | 8.672e-10 |
| 12 | answer_volume_flow4 | 0 | m3/s | 0 |
| 12 | answer_mass_flow4 | 0 | kg/s | 0 |

### 009-hydrostatic-09：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 4.0/4g/600.0 | 100/3000 | 12.85 | 18 | 3.599e-12 | 4.228e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 0.8681 | 1 | Ux=0; Uy=0; Uz=0; p[1]=0; p[2]=0 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 1.108e-11 | m/s | 1.108e-08 |
| 12 | answer_pressure | 1.46e-10 | Pa | 1.35e-09 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 2.508e-12 | Pa | 2.508e-11 |
| 12 | answer_mean_pressure | 2.411e-11 | Pa | 2.296e-10 |
| 12 | answer_shear | 3.48e-11 | 1/s | 3.48e-09 |
| 12 | answer_force3 | 3.291e-13 | N | 1.578e-10 |
| 12 | answer_volume_flow3 | 0 | m3/s | 0 |
| 12 | answer_mass_flow3 | 0 | kg/s | 0 |
| 12 | answer_force4 | 1.182e-13 | N | 1.182e-10 |
| 12 | answer_volume_flow4 | 0 | m3/s | 0 |
| 12 | answer_mass_flow4 | 0 | kg/s | 0 |

### 010-hydrostatic-10：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 4.0/4g/600.0 | 100/3000 | 12.7 | 19 | 3.924e-12 | 6.339e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 1.019 | 1 | Ux=0; Uy=0; Uz=0; p[1]=0; p[2]=0 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 5.4e-12 | m/s | 5.4e-09 |
| 12 | answer_pressure | 4.441e-16 | Pa | 3.67e-15 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 7.23e-12 | Pa | 7.23e-11 |
| 12 | answer_mean_pressure | 3.939e-11 | Pa | 2.251e-10 |
| 12 | answer_shear | 4.665e-11 | 1/s | 4.665e-09 |
| 12 | answer_force3 | 5.509e-13 | N | 5.509e-10 |
| 12 | answer_volume_flow3 | 0 | m3/s | 0 |
| 12 | answer_mass_flow3 | 0 | kg/s | 0 |
| 12 | answer_force4 | 6.253e-13 | N | 5.247e-10 |
| 12 | answer_volume_flow4 | 0 | m3/s | 0 |
| 12 | answer_mass_flow4 | 0 | kg/s | 0 |

### 011-hydrostatic-11：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 4.0/4g/600.0 | 100/3000 | 14.4 | 23 | 9.995e-13 | 1.172e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 0.9168 | 1 | Ux=0; Uy=0; Uz=0; p[1]=0; p[2]=0 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 2.812e-13 | m/s | 2.812e-10 |
| 12 | answer_pressure | 1.601e-10 | Pa | 1.58e-13 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 5.821e-11 | Pa | 2.865e-10 |
| 12 | answer_mean_pressure | 2.5e-07 | Pa | 2.479e-10 |
| 12 | answer_shear | 1.358e-12 | 1/s | 1.358e-10 |
| 12 | answer_force3 | 3.75e-07 | N | 6.42e-09 |
| 12 | answer_volume_flow3 | 0 | m3/s | 0 |
| 12 | answer_mass_flow3 | 0 | kg/s | 0 |
| 12 | answer_force4 | 3.75e-07 | N | 1.265e-08 |
| 12 | answer_volume_flow4 | 0 | m3/s | 0 |
| 12 | answer_mass_flow4 | 0 | kg/s | 0 |

### 012-hydrostatic-12：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 4.0/4g/600.0 | 100/3000 | 14.15 | 22 | 1.512e-12 | 4.515e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 0.8175 | 1 | Ux=0; Uy=0; Uz=0; p[1]=0; p[2]=0 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 1.83e-14 | m/s | 1.83e-11 |
| 12 | answer_pressure | 2.501e-06 | Pa | 1.866e-06 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 3.412e-12 | Pa | 3.412e-11 |
| 12 | answer_mean_pressure | 2.527e-11 | Pa | 1.209e-11 |
| 12 | answer_shear | 1.255e-13 | 1/s | 1.255e-11 |
| 12 | answer_force3 | 1.327e-12 | N | 1.327e-09 |
| 12 | answer_volume_flow3 | 0 | m3/s | 0 |
| 12 | answer_mass_flow3 | 0 | kg/s | 0 |
| 12 | answer_force4 | 1.478e-12 | N | 1.478e-09 |
| 12 | answer_volume_flow4 | 0 | m3/s | 0 |
| 12 | answer_mass_flow4 | 0 | kg/s | 0 |

### 013-hydrostatic-13：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 15.96 | 17 | 2.687e-12 | 4.671e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 0.8169 | 1 | Ux=0; Uy=0; Uz=0; p[1]=0; p[2]=0 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 5.622e-15 | m/s | 5.622e-12 |
| 12 | answer_pressure | 5.174e-05 | Pa | 0.0005105 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_shear | 7.31e-14 | 1/s | 7.31e-12 |

### 014-hydrostatic-14：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 16.41 | 16 | 4.13e-12 | 8.066e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 0.8672 | 1 | Ux=0; Uy=0; Uz=0; p[1]=0; p[2]=0 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 5.532e-15 | m/s | 5.532e-12 |
| 12 | answer_pressure | 0.0001517 | Pa | 0.001289 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_shear | 8.737e-14 | 1/s | 8.737e-12 |

### 015-hydrostatic-15：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 16.31 | 18 | 2.454e-12 | 4.184e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 0.7665 | 1 | Ux=0; Uy=0; Uz=0; p[1]=0; p[2]=0 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 8.429e-16 | m/s | 8.429e-13 |
| 12 | answer_pressure | 0.001405 | Pa | 0.01253 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_shear | 1.243e-14 | 1/s | 1.243e-12 |

### 016-hydrostatic-16：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 16.45 | 19 | 5.537e-12 | 5.287e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 0.8174 | 1 | Ux=0; Uy=0; Uz=0; p[1]=0; p[2]=0 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 1.654e-14 | m/s | 1.654e-11 |
| 12 | answer_pressure | 0.001929 | Pa | 1.904e-06 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_shear | 1.898e-13 | 1/s | 1.898e-11 |

### 017-hydrostatic-17：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 18.48 | 23 | 6.287e-12 | 6.276e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 0.8169 | 1 | Ux=0; Uy=0; Uz=0; p[1]=0; p[2]=0 | — | 0 |
| 24 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 193.4 | 24 | 5.248e-12 | 1.213e-10 | 0 |
| 24 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 1.22 | 1 | Ux=0; Uy=0; Uz=0; p[1]=0; p[2]=0 | — | 0 |
| 32 | elmer | 2.0/4g/3600.0 | 100/3000 | 836.6 | 23 | 8.398e-12 | 3.129e-10 | 0 |
| 32 | openfoam | 2.0/4g/3600.0 | 12000/— | 4.598 | 1 | Ux=0; Uy=0; Uz=0; p[1]=0; p[2]=0 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 8.503e-16 | m/s | 8.503e-13 |
| 12 | answer_pressure | 0.3587 | Pa | 1.828 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_shear | 1.959e-14 | 1/s | 1.959e-12 |
| 24 | answer_velocity | 8.647e-16 | m/s | 8.647e-13 |
| 24 | answer_pressure | 0.08196 | Pa | 0.4606 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_shear | 1.218e-14 | 1/s | 1.218e-12 |
| 32 | answer_velocity | 3.554e-16 | m/s | 3.554e-13 |
| 32 | answer_pressure | 0.06874 | Pa | 0.2759 |
| 32 | answer_density | 0 | kg/m3 | 0 |
| 32 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 32 | answer_shear | 4.371e-15 | 1/s | 4.371e-13 |

### 018-hydrostatic-18：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 20.42 | 24 | 4.546e-12 | 1.223e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 0.7668 | 1 | Ux=0; Uy=0; Uz=0; p[1]=0; p[2]=0 | — | 0 |
| 24 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 235 | 24 | 5.327e-12 | 1.952e-10 | 0 |
| 24 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 1.17 | 1 | Ux=0; Uy=0; Uz=0; p[1]=0; p[2]=0 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 1.356e-16 | m/s | 1.356e-13 |
| 12 | answer_pressure | 0.5191 | Pa | 1.134 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_shear | 7.113e-16 | 1/s | 7.113e-14 |
| 24 | answer_velocity | 9.166e-17 | m/s | 9.166e-14 |
| 24 | answer_pressure | 0.146 | Pa | 0.2895 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_shear | 3.356e-15 | 1/s | 3.356e-13 |

### 019-couette-01：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 22.32 | 14 | 4.212e-12 | 9.74e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 97.74 | 12000 | Ux=3.068e-16; Uy=7.646e-13; Uz=2.999e-16; p[1]=5.528e-12; p[2]=5.363e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 1e-09 | m/s | 8.892e-07 |
| 12 | answer_pressure | 0 | Pa | 0 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 1.799e-09 | Pa | 1.798e-08 |
| 12 | answer_mean_pressure | 0 | Pa | 0 |
| 12 | answer_shear | 2.683e-09 | 1/s | 2.596e-07 |
| 12 | answer_force3 | 3.6e-10 | N | 3.445e-07 |
| 12 | answer_volume_flow3 | 0 | m3/s | 0 |
| 12 | answer_mass_flow3 | 0 | kg/s | 0 |
| 12 | answer_force4 | 3.6e-09 | N | 3.445e-06 |
| 12 | answer_volume_flow4 | 0 | m3/s | 0 |
| 12 | answer_mass_flow4 | 0 | kg/s | 0 |

### 020-couette-02：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 32.66 | 15 | 1.426e-12 | 4.714e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 111.6 | 12000 | Ux=3.102e-16; Uy=2.176e-16; Uz=8.089e-13; p[1]=5.943e-12; p[2]=5.604e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 1e-09 | m/s | 7.194e-07 |
| 12 | answer_pressure | 9.028e-11 | Pa | 7.524e-10 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 3.57e-10 | Pa | 3.561e-09 |
| 12 | answer_mean_pressure | 2.665e-14 | Pa | 2.22e-13 |
| 12 | answer_shear | 1.18e-08 | 1/s | 1.087e-06 |
| 12 | answer_force3 | 5.418e-14 | N | 2.858e-11 |
| 12 | answer_volume_flow3 | 0 | m3/s | 0 |
| 12 | answer_mass_flow3 | 0 | kg/s | 0 |
| 12 | answer_force4 | 3.6e-09 | N | 2.875e-06 |
| 12 | answer_volume_flow4 | 0 | m3/s | 0 |
| 12 | answer_mass_flow4 | 0 | kg/s | 0 |

### 021-couette-03：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 55.14 | 16 | 6.451e-12 | 3.382e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 128.3 | 12000 | Ux=5.011e-13; Uy=7.24e-13; Uz=3.597e-16; p[1]=9.622e-12; p[2]=9.124e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 6.002e-13 | m/s | 5.455e-10 |
| 12 | answer_pressure | 1.093e-11 | Pa | 9.936e-11 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 9.584e-11 | Pa | 8.94e-10 |
| 12 | answer_mean_pressure | 0 | Pa | 0 |
| 12 | answer_shear | 1.513e-11 | 1/s | 1.351e-09 |
| 12 | answer_force3 | 7.46e-13 | N | 1.57e-10 |
| 12 | answer_volume_flow3 | 0 | m3/s | 0 |
| 12 | answer_mass_flow3 | 0 | kg/s | 0 |
| 12 | answer_force4 | 2.544e-12 | N | 2.313e-10 |
| 12 | answer_volume_flow4 | 0 | m3/s | 0 |
| 12 | answer_mass_flow4 | 0 | kg/s | 0 |

### 022-couette-04：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 46.42 | 21 | 4.814e-12 | 3.03e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 71.45 | 12000 | Ux=2.582e-16; Uy=2.581e-16; Uz=2.465e-16; p[1]=5.391e-12; p[2]=5.387e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 2.17e-09 | m/s | 8.948e-07 |
| 12 | answer_pressure | 2.328e-11 | Pa | 2.328e-10 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 2.122e-06 | Pa | 1.359e-05 |
| 12 | answer_mean_pressure | 4.695e-12 | Pa | 4.695e-11 |
| 12 | answer_shear | 1.624e-07 | 1/s | 1.057e-05 |
| 12 | answer_force3 | 4.259e-08 | N | 7.284e-07 |
| 12 | answer_volume_flow3 | 0 | m3/s | 0 |
| 12 | answer_mass_flow3 | 0 | kg/s | 0 |
| 12 | answer_force4 | 3.641e-06 | N | 5.812e-05 |
| 12 | answer_volume_flow4 | 2.155e-09 | m3/s | 0.002155 |
| 12 | answer_mass_flow4 | 2.155e-08 | kg/s | 0.02155 |

### 023-couette-05：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 39.76 | 14 | 4.521e-12 | 7.736e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 94.66 | 12000 | Ux=1.658e-16; Uy=1.974e-16; Uz=8.997e-13; p[1]=6.069e-12; p[2]=5.981e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 1.205e-09 | m/s | 9.691e-07 |
| 12 | answer_pressure | 1.943e-10 | Pa | 1.619e-09 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 1.212e-07 | Pa | 1.107e-06 |
| 12 | answer_mean_pressure | 0 | Pa | 0 |
| 12 | answer_shear | 6.145e-09 | 1/s | 5.893e-07 |
| 12 | answer_force3 | 8.192e-08 | N | 9.838e-06 |
| 12 | answer_volume_flow3 | 0 | m3/s | 0 |
| 12 | answer_mass_flow3 | 0 | kg/s | 0 |
| 12 | answer_force4 | 4.768e-07 | N | 4.367e-05 |
| 12 | answer_volume_flow4 | 0 | m3/s | 0 |
| 12 | answer_mass_flow4 | 0 | kg/s | 0 |

### 024-couette-06：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 39.81 | 15 | 7.202e-12 | 5.631e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 106.7 | 12000 | Ux=7.697e-13; Uy=9.456e-13; Uz=3.189e-16; p[1]=7.529e-12; p[2]=7.384e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 1e-09 | m/s | 7.273e-07 |
| 12 | answer_pressure | 1.455e-11 | Pa | 1.436e-14 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 3.507e-07 | Pa | 2.597e-06 |
| 12 | answer_mean_pressure | 0 | Pa | 0 |
| 12 | answer_shear | 1.2e-09 | 1/s | 1.132e-07 |
| 12 | answer_force3 | 7.2e-08 | N | 1.946e-06 |
| 12 | answer_volume_flow3 | 0 | m3/s | 0 |
| 12 | answer_mass_flow3 | 0 | kg/s | 0 |
| 12 | answer_force4 | 7.2e-07 | N | 1.946e-05 |
| 12 | answer_volume_flow4 | 1.171e-19 | m3/s | 1.171e-13 |
| 12 | answer_mass_flow4 | 1.171e-16 | kg/s | 1.171e-10 |

### 025-couette-07：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 58.72 | 16 | 8.442e-12 | 3.725e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 92.35 | 12000 | Ux=3.428e-16; Uy=3.666e-16; Uz=3.42e-16; p[1]=5.017e-12; p[2]=4.743e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 4.26e-10 | m/s | 3.589e-07 |
| 12 | answer_pressure | 5.134e-12 | Pa | 5.134e-11 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 3.912e-10 | Pa | 3.91e-09 |
| 12 | answer_mean_pressure | 4.009e-26 | Pa | 4.009e-25 |
| 12 | answer_shear | 8.539e-09 | 1/s | 7.529e-07 |
| 12 | answer_force3 | 3.435e-11 | N | 3.339e-08 |
| 12 | answer_volume_flow3 | 0 | m3/s | 0 |
| 12 | answer_mass_flow3 | 0 | kg/s | 0 |
| 12 | answer_force4 | 1.553e-09 | N | 1.456e-06 |
| 12 | answer_volume_flow4 | 8.315e-10 | m3/s | 0.0008315 |
| 12 | answer_mass_flow4 | 8.315e-10 | kg/s | 0.0008315 |

### 026-couette-08：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 56.15 | 16 | 9.815e-12 | 7.125e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 114.6 | 12000 | Ux=5.033e-16; Uy=2.039e-16; Uz=8.601e-13; p[1]=4.909e-12; p[2]=4.715e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 2.524e-09 | m/s | 7.885e-07 |
| 12 | answer_pressure | 1.609e-09 | Pa | 1.341e-08 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 1.701e-09 | Pa | 1.694e-08 |
| 12 | answer_mean_pressure | 1.773e-12 | Pa | 1.478e-11 |
| 12 | answer_shear | 1.518e-08 | 1/s | 1.132e-06 |
| 12 | answer_force3 | 1.903e-09 | N | 1.36e-06 |
| 12 | answer_volume_flow3 | 0 | m3/s | 0 |
| 12 | answer_mass_flow3 | 0 | kg/s | 0 |
| 12 | answer_force4 | 1.34e-09 | N | 1.224e-06 |
| 12 | answer_volume_flow4 | 0 | m3/s | 0 |
| 12 | answer_mass_flow4 | 0 | kg/s | 0 |

### 027-couette-09：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 36.49 | 14 | 3.597e-12 | 8.707e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 107.8 | 12000 | Ux=9.528e-13; Uy=3.231e-13; Uz=2.555e-16; p[1]=6.828e-12; p[2]=6.183e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 1e-09 | m/s | 8.765e-07 |
| 12 | answer_pressure | 5.158e-13 | Pa | 4.689e-12 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 3.298e-10 | Pa | 3.297e-09 |
| 12 | answer_mean_pressure | 0 | Pa | 0 |
| 12 | answer_shear | 4.8e-09 | 1/s | 4.529e-07 |
| 12 | answer_force3 | 1.08e-10 | N | 1.052e-07 |
| 12 | answer_volume_flow3 | 0 | m3/s | 0 |
| 12 | answer_mass_flow3 | 0 | kg/s | 0 |
| 12 | answer_force4 | 1.08e-09 | N | 1.052e-06 |
| 12 | answer_volume_flow4 | 0 | m3/s | 0 |
| 12 | answer_mass_flow4 | 0 | kg/s | 0 |

### 028-couette-10：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 43.3 | 15 | 9.028e-12 | 5.852e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 92.2 | 12000 | Ux=3.24e-16; Uy=6.85e-13; Uz=2.949e-16; p[1]=7.749e-12; p[2]=7.534e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 1e-09 | m/s | 7.32e-07 |
| 12 | answer_pressure | 8.534e-13 | Pa | 8.534e-12 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 7.177e-13 | Pa | 7.173e-12 |
| 12 | answer_mean_pressure | 1.544e-13 | Pa | 1.544e-12 |
| 12 | answer_shear | 1.074e-09 | 1/s | 1.006e-07 |
| 12 | answer_force3 | 1.215e-10 | N | 1.145e-07 |
| 12 | answer_volume_flow3 | 0 | m3/s | 0 |
| 12 | answer_mass_flow3 | 0 | kg/s | 0 |
| 12 | answer_force4 | 1.215e-09 | N | 1.145e-06 |
| 12 | answer_volume_flow4 | 0 | m3/s | 0 |
| 12 | answer_mass_flow4 | 0 | kg/s | 0 |

### 029-couette-11：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 41.8 | 16 | 4.078e-12 | 8.191e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 89.45 | 12000 | Ux=3.04e-16; Uy=1.914e-16; Uz=6.665e-13; p[1]=5.652e-12; p[2]=5.335e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 2.679e-14 | m/s | 2.679e-11 |
| 12 | answer_pressure | 1.557e-09 | Pa | 1.537e-12 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 2.831e-10 | Pa | 2.018e-09 |
| 12 | answer_mean_pressure | 0 | Pa | 0 |
| 12 | answer_shear | 2.11e-11 | 1/s | 1.802e-09 |
| 12 | answer_force3 | 1.848e-11 | N | 4.471e-10 |
| 12 | answer_volume_flow3 | 0 | m3/s | 0 |
| 12 | answer_mass_flow3 | 0 | kg/s | 0 |
| 12 | answer_force4 | 1.978e-11 | N | 4.786e-10 |
| 12 | answer_volume_flow4 | 0 | m3/s | 0 |
| 12 | answer_mass_flow4 | 0 | kg/s | 0 |

### 030-couette-12：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 68.83 | 21 | 6.738e-12 | 4.653e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 125.6 | 12000 | Ux=9.66e-13; Uy=4.536e-13; Uz=3.423e-16; p[1]=6.628e-12; p[2]=6.506e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 4.731e-14 | m/s | 4.731e-11 |
| 12 | answer_pressure | 1.5e-07 | Pa | 4.412e-07 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 1.5e-07 | Pa | 4.412e-07 |
| 12 | answer_mean_pressure | 4.148e-10 | Pa | 8.921e-10 |
| 12 | answer_shear | 2.937e-11 | 1/s | 2.368e-09 |
| 12 | answer_force3 | 2.767e-12 | N | 1.297e-09 |
| 12 | answer_volume_flow3 | 0 | m3/s | 0 |
| 12 | answer_mass_flow3 | 0 | kg/s | 0 |
| 12 | answer_force4 | 6.245e-12 | N | 1.738e-09 |
| 12 | answer_volume_flow4 | 0 | m3/s | 0 |
| 12 | answer_mass_flow4 | 0 | kg/s | 0 |

### 031-couette-13：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 52.02 | 15 | 4.11e-12 | 5.996e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 86.04 | 12000 | Ux=3.994e-16; Uy=5.254e-16; Uz=4.184e-16; p[1]=9.982e-12; p[2]=9.616e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 1.245e-10 | m/s | 1.002e-07 |
| 12 | answer_pressure | 3.2e-10 | Pa | 3.194e-09 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 4.871e-10 | Pa | 4.854e-09 |
| 12 | answer_mean_pressure | 7.067e-18 | Pa | 7.067e-17 |
| 12 | answer_shear | 6.496e-10 | 1/s | 6.285e-08 |
| 12 | answer_force3 | 9.736e-10 | N | 6.548e-07 |
| 12 | answer_volume_flow3 | 0 | m3/s | 0 |
| 12 | answer_mass_flow3 | 0 | kg/s | 0 |
| 12 | answer_force4 | 9.74e-10 | N | 6.55e-07 |
| 12 | answer_volume_flow4 | 4.006e-11 | m3/s | 4.006e-05 |
| 12 | answer_mass_flow4 | 4.006e-11 | kg/s | 4.006e-05 |

### 032-couette-14：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 39.89 | 15 | 4.75e-12 | 4.587e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 87.19 | 12000 | Ux=1.366e-16; Uy=1.734e-16; Uz=3.474e-13; p[1]=9.587e-12; p[2]=9.165e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 9.094e-10 | m/s | 6.119e-07 |
| 12 | answer_pressure | 2.024e-11 | Pa | 1.687e-10 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 2.008e-11 | Pa | 2.008e-10 |
| 12 | answer_mean_pressure | 3.02e-14 | Pa | 2.517e-13 |
| 12 | answer_shear | 1.953e-08 | 1/s | 1.668e-06 |
| 12 | answer_force3 | 3.556e-11 | N | 3.551e-08 |
| 12 | answer_volume_flow3 | 0 | m3/s | 0 |
| 12 | answer_mass_flow3 | 0 | kg/s | 0 |
| 12 | answer_force4 | 6.153e-11 | N | 6.131e-08 |
| 12 | answer_volume_flow4 | 0 | m3/s | 0 |
| 12 | answer_mass_flow4 | 0 | kg/s | 0 |

### 033-couette-15：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 4.0/4g/600.0 | 100/3000 | 15.56 | 17 | 3.525e-12 | 4.79e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 103.4 | 12000 | Ux=7.814e-13; Uy=4.275e-13; Uz=3.12e-16; p[1]=5.851e-12; p[2]=5.866e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 4.187e-12 | m/s | 4.187e-09 |
| 12 | answer_pressure | 2.498e-09 | Pa | 2.482e-08 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 3.333e-09 | Pa | 3.306e-08 |
| 12 | answer_mean_pressure | 3.602e-10 | Pa | 3.431e-09 |
| 12 | answer_shear | 1.479e-11 | 1/s | 1.32e-09 |
| 12 | answer_force3 | 7.075e-10 | N | 5.919e-08 |
| 12 | answer_volume_flow3 | 0 | m3/s | 0 |
| 12 | answer_mass_flow3 | 0 | kg/s | 0 |
| 12 | answer_force4 | 6.971e-13 | N | 6.971e-10 |
| 12 | answer_volume_flow4 | 1.952e-19 | m3/s | 1.952e-13 |
| 12 | answer_mass_flow4 | 1.952e-18 | kg/s | 1.952e-12 |

### 034-couette-16：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 4.0/4g/600.0 | 100/3000 | 15.06 | 17 | 7.721e-12 | 5.145e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 70.15 | 12000 | Ux=3.208e-16; Uy=3.256e-16; Uz=3.235e-16; p[1]=5.511e-12; p[2]=5.269e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 4.304e-09 | m/s | 1.523e-06 |
| 12 | answer_pressure | 3.201e-09 | Pa | 3.159e-12 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 5.02e-09 | Pa | 7.889e-12 |
| 12 | answer_mean_pressure | 3.492e-10 | Pa | 3.446e-13 |
| 12 | answer_shear | 6.598e-08 | 1/s | 5.202e-06 |
| 12 | answer_force3 | 4.948e-10 | N | 1.171e-12 |
| 12 | answer_volume_flow3 | 0 | m3/s | 0 |
| 12 | answer_mass_flow3 | 0 | kg/s | 0 |
| 12 | answer_force4 | 5.661e-09 | N | 1.402e-11 |
| 12 | answer_volume_flow4 | 7.459e-10 | m3/s | 0.0007459 |
| 12 | answer_mass_flow4 | 7.459e-09 | kg/s | 0.007458 |

### 035-couette-17：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 4.0/4g/600.0 | 100/3000 | 16.77 | 14 | 6.572e-12 | 7.689e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 100.4 | 12000 | Ux=4.859e-16; Uy=1.841e-16; Uz=8.414e-13; p[1]=5.57e-12; p[2]=5.123e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 5.55e-10 | m/s | 4.738e-07 |
| 12 | answer_pressure | 5.284e-11 | Pa | 4.403e-10 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 3.133e-09 | Pa | 3.129e-08 |
| 12 | answer_mean_pressure | 2.118e-13 | Pa | 1.765e-12 |
| 12 | answer_shear | 8.658e-09 | 1/s | 8.304e-07 |
| 12 | answer_force3 | 1.045e-09 | N | 9.289e-07 |
| 12 | answer_volume_flow3 | 0 | m3/s | 0 |
| 12 | answer_mass_flow3 | 0 | kg/s | 0 |
| 12 | answer_force4 | 4.645e-09 | N | 4.13e-06 |
| 12 | answer_volume_flow4 | 0 | m3/s | 0 |
| 12 | answer_mass_flow4 | 0 | kg/s | 0 |

### 036-couette-18：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 4.0/4g/600.0 | 100/3000 | 18.32 | 21 | 7.217e-12 | 3.828e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 94.9 | 12000 | Ux=3.378e-13; Uy=8.974e-13; Uz=3.903e-16; p[1]=9.318e-12; p[2]=8.641e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 1.466e-12 | m/s | 1.466e-09 |
| 12 | answer_pressure | 2.498e-07 | Pa | 9e-07 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 3.333e-07 | Pa | 1.299e-06 |
| 12 | answer_mean_pressure | 2.502e-08 | Pa | 4.241e-08 |
| 12 | answer_shear | 1.017e-11 | 1/s | 9.594e-10 |
| 12 | answer_force3 | 4.788e-10 | N | 4.707e-08 |
| 12 | answer_volume_flow3 | 0 | m3/s | 0 |
| 12 | answer_mass_flow3 | 0 | kg/s | 0 |
| 12 | answer_force4 | 1.03e-12 | N | 2.392e-11 |
| 12 | answer_volume_flow4 | 9.368e-19 | m3/s | 9.368e-13 |
| 12 | answer_mass_flow4 | 9.368e-16 | kg/s | 9.368e-10 |

### 037-couette-19：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 4.0/4g/600.0 | 100/3000 | 14.21 | 16 | 3.062e-12 | 3.591e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 78.83 | 12000 | Ux=2.907e-16; Uy=8.283e-13; Uz=3.027e-16; p[1]=8.151e-12; p[2]=7.718e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 1.2e-12 | m/s | 9.967e-10 |
| 12 | answer_pressure | 3.197e-10 | Pa | 3.19e-09 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 3.333e-10 | Pa | 3.328e-09 |
| 12 | answer_mean_pressure | 2.115e-11 | Pa | 2.11e-10 |
| 12 | answer_shear | 6.394e-11 | 1/s | 5.041e-09 |
| 12 | answer_force3 | 1.614e-10 | N | 1.614e-07 |
| 12 | answer_volume_flow3 | 0 | m3/s | 0 |
| 12 | answer_mass_flow3 | 0 | kg/s | 0 |
| 12 | answer_force4 | 1.327e-15 | N | 1.321e-12 |
| 12 | answer_volume_flow4 | 0 | m3/s | 0 |
| 12 | answer_mass_flow4 | 0 | kg/s | 0 |

### 038-couette-20：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 4.0/4g/600.0 | 100/3000 | 14.91 | 16 | 7.361e-12 | 5.609e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 89.93 | 12000 | Ux=2.861e-16; Uy=1.83e-16; Uz=9.353e-13; p[1]=7.654e-12; p[2]=7.142e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 4.506e-12 | m/s | 4.506e-09 |
| 12 | answer_pressure | 1.8e-12 | Pa | 1.5e-11 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 3.118e-13 | Pa | 2.598e-12 |
| 12 | answer_mean_pressure | 3.153e-13 | Pa | 2.628e-12 |
| 12 | answer_shear | 3.962e-11 | 1/s | 2.954e-09 |
| 12 | answer_force3 | 3.273e-13 | N | 1.393e-11 |
| 12 | answer_volume_flow3 | 0 | m3/s | 0 |
| 12 | answer_mass_flow3 | 0 | kg/s | 0 |
| 12 | answer_force4 | 3.535e-13 | N | 1.504e-11 |
| 12 | answer_volume_flow4 | 0 | m3/s | 0 |
| 12 | answer_mass_flow4 | 0 | kg/s | 0 |

### 039-periodic-duct-01：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 24.08 | 15 | 5.997e-12 | 5.957e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 104.2 | 12000 | Ux=4.15e-16; Uy=7.566e-13; Uz=8.108e-13; p[1]=7.798e-12; p[2]=7.646e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.0006 | m/s | 0.4192 |
| 12 | answer_pressure | 0 | Pa | 0 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 040-periodic-duct-02：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 25.18 | 16 | 3.124e-12 | 3.171e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 103.4 | 12000 | Ux=5.172e-13; Uy=3.948e-16; Uz=6.167e-13; p[1]=6.255e-12; p[2]=5.857e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 544 | 16 | 6.106e-12 | 3.37e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 1495 | 12000 | Ux=7.22e-13; Uy=4.334e-15; Uz=4.449e-13; p[1]=7.672e-12; p[2]=6.822e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.0012 | m/s | 0.6916 |
| 12 | answer_pressure | 3.775e-13 | Pa | 3.146e-12 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.000225 | m/s | 0.1213 |
| 24 | answer_pressure | 1.694e-13 | Pa | 1.412e-12 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 041-periodic-duct-03：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 32.97 | 16 | 4.167e-12 | 4.504e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 133.2 | 12000 | Ux=5.958e-13; Uy=4.661e-13; Uz=3.454e-16; p[1]=9.256e-12; p[2]=8.917e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 1123 | 16 | 1.972e-12 | 4.615e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 1724 | 12000 | Ux=5.928e-13; Uy=5.261e-13; Uz=3.815e-16; p[1]=8.683e-12; p[2]=8.463e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.0007517 | m/s | 0.4293 |
| 12 | answer_pressure | 3.534e-12 | Pa | 3.213e-11 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.0001806 | m/s | 0.1028 |
| 24 | answer_pressure | 7.945e-13 | Pa | 7.223e-12 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 042-periodic-duct-04：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 32.36 | 17 | 7.074e-12 | 3.806e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 93.54 | 12000 | Ux=2.72e-16; Uy=2.795e-16; Uz=4.309e-13; p[1]=4.761e-12; p[2]=4.653e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 1352 | 34 | 2.808e-12 | 1.286e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 1430 | 12000 | Ux=3.582e-16; Uy=3.533e-16; Uz=4.628e-13; p[1]=8.353e-12; p[2]=8.275e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.004674 | m/s | 1.21 |
| 12 | answer_pressure | 8.575e-11 | Pa | 8.575e-10 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.0008763 | m/s | 0.2024 |
| 24 | answer_pressure | 1.765e-11 | Pa | 1.765e-10 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 043-periodic-duct-05：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 23.33 | 15 | 9.505e-13 | 5.957e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 90.43 | 12000 | Ux=3.709e-16; Uy=3.824e-16; Uz=4.324e-13; p[1]=5.959e-12; p[2]=6.219e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.0005842 | m/s | 0.4114 |
| 12 | answer_pressure | 3.029e-13 | Pa | 2.524e-12 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 044-periodic-duct-06：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 23.39 | 15 | 1.636e-13 | 4.618e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 105.5 | 12000 | Ux=9.058e-13; Uy=6.659e-13; Uz=2.385e-16; p[1]=9.837e-12; p[2]=9.605e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.0002248 | m/s | 0.1817 |
| 12 | answer_pressure | 0 | Pa | 0 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 045-periodic-duct-07：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 31.27 | 16 | 1.089e-13 | 6.343e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 90.48 | 12000 | Ux=4.077e-16; Uy=3.781e-16; Uz=8.967e-13; p[1]=4.485e-12; p[2]=4.415e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 652.1 | 16 | 6.176e-12 | 6.468e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 1450 | 12000 | Ux=4.55e-15; Uy=4.565e-15; Uz=6.415e-13; p[1]=7.708e-12; p[2]=6.872e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.002201 | m/s | 0.9374 |
| 12 | answer_pressure | 7.089e-14 | Pa | 7.089e-13 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.0004127 | m/s | 0.1607 |
| 24 | answer_pressure | 5.48e-14 | Pa | 5.48e-13 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 046-periodic-duct-08：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 45.52 | 17 | 6.821e-12 | 3.807e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 121.8 | 12000 | Ux=5.015e-16; Uy=4.6e-16; Uz=9.806e-13; p[1]=7.812e-12; p[2]=7.395e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 2135 | 17 | 7.488e-12 | 3.882e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 1619 | 12000 | Ux=1.372e-15; Uy=1.484e-15; Uz=4.708e-13; p[1]=7.345e-12; p[2]=6.791e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.004402 | m/s | 1.191 |
| 12 | answer_pressure | 2.638e-13 | Pa | 2.198e-12 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.0008254 | m/s | 0.1995 |
| 24 | answer_pressure | 7.017e-14 | Pa | 5.847e-13 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 047-periodic-duct-09：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 23.08 | 15 | 5.096e-12 | 4.754e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 103.2 | 12000 | Ux=3.27e-13; Uy=3.428e-13; Uz=3.011e-16; p[1]=7.417e-12; p[2]=7.449e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.0002392 | m/s | 0.1887 |
| 12 | answer_pressure | 1.327e-13 | Pa | 1.206e-12 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 048-periodic-duct-10：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 26.8 | 16 | 1.95e-12 | 3.171e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 100.7 | 12000 | Ux=3.456e-16; Uy=4.673e-13; Uz=9.894e-13; p[1]=9.489e-12; p[2]=9.111e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 686.2 | 16 | 6.035e-12 | 3.235e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 1341 | 12000 | Ux=4.117e-16; Uy=5.857e-13; Uz=5.376e-13; p[1]=7.529e-12; p[2]=7.332e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.0012 | m/s | 0.6916 |
| 12 | answer_pressure | 1.502e-14 | Pa | 1.502e-13 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.000225 | m/s | 0.1213 |
| 24 | answer_pressure | 3.059e-14 | Pa | 3.059e-13 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 049-periodic-duct-11：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 33.97 | 16 | 4.366e-12 | 7.535e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 110.9 | 12000 | Ux=5.632e-13; Uy=3.727e-16; Uz=3.439e-13; p[1]=7.451e-12; p[2]=7.068e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 889.4 | 19 | 4.456e-12 | 4.087e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 1521 | 12000 | Ux=5.35e-13; Uy=4.381e-16; Uz=5.464e-13; p[1]=9.939e-12; p[2]=9.624e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.0024 | m/s | 0.9717 |
| 12 | answer_pressure | 0 | Pa | 0 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.00045 | m/s | 0.1661 |
| 24 | answer_pressure | 0 | Pa | 0 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 050-periodic-duct-12：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 26.26 | 16 | 4.889e-12 | 6.018e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 107 | 12000 | Ux=7.793e-13; Uy=7.44e-13; Uz=2.187e-16; p[1]=6.358e-12; p[2]=6.217e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 347.9 | 15 | 7.216e-12 | 8.742e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 1470 | 12000 | Ux=5.925e-13; Uy=6.635e-13; Uz=2.85e-16; p[1]=7.624e-12; p[2]=7.477e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.0006485 | m/s | 0.4248 |
| 12 | answer_pressure | 7.381e-12 | Pa | 6.71e-11 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.0001159 | m/s | 0.08288 |
| 24 | answer_pressure | 3.651e-12 | Pa | 3.319e-11 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 051-periodic-duct-13：未通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 36.24 | 15 | 8.796e-12 | 3.872e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 15 | 1810 | Ux=4.376e-13; Uy=4.25e-13; Uz=6.337e-13; p[1]=7.727e-12; p[2]=7.727e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 1320 | 15 | 7.116e-12 | 4.018e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 485.8 | 5151 | Ux=3.718e-13; Uy=3.646e-13; Uz=3.582e-13; p[1]=8.962e-12; p[2]=8.962e-12 | — | 0 |
| 32 | elmer | 2.0/4g/3600.0 | 100/3000 | 3600 | 14 | 1.499e-05 | 4.449e-09 | 124 |
| 32 | openfoam | — | —/— | — | — | — | — | — |

n=32：elmer failed with 124: /home/zhouzhiyu/code/docker/work/caeoj-2-1-3-supplement/production/native/051-periodic-duct-13/31965860205a/elmer-n32/execution.log


| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.003125 | m/s | 2.874 |
| 12 | answer_pressure | 6.912e-06 | Pa | 6.912e-05 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.00134 | m/s | 1.226 |
| 24 | answer_pressure | 7.578e-06 | Pa | 7.578e-05 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 052-periodic-duct-14：未通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 16 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 64.65 | 15 | 2.238e-12 | 7.774e-10 | 0 |
| 16 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 13.8 | 697 | Ux=6.072e-13; Uy=6.4e-13; Uz=8.036e-13; p[1]=8.628e-12; p[2]=8.628e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 666.9 | 15 | 1.446e-12 | 7.844e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 142.4 | 1367 | Ux=6.474e-13; Uy=6.728e-13; Uz=2.732e-13; p[1]=9.374e-12; p[2]=9.374e-12 | — | 0 |
| 32 | elmer | 2.0/4g/3600.0 | 100/3000 | 1859 | 15 | 9.559e-12 | 7.882e-10 | 0 |
| 32 | openfoam | 2.0/4g/3600.0 | 12000/— | 665.7 | 2244 | Ux=6.639e-13; Uy=6.86e-13; Uz=3.267e-13; p[1]=9.289e-12; p[2]=9.289e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 16 | answer_velocity | 0.005398 | m/s | 4.479 |
| 16 | answer_pressure | 9.814e-05 | Pa | 0.0008179 |
| 16 | answer_density | 0 | kg/m3 | 0 |
| 16 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.002984 | m/s | 2.453 |
| 24 | answer_pressure | 5.34e-05 | Pa | 0.000445 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 32 | answer_velocity | 0.002433 | m/s | 1.994 |
| 32 | answer_pressure | 8.056e-05 | Pa | 0.0006713 |
| 32 | answer_density | 0 | kg/m3 | 0 |
| 32 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 053-periodic-duct-15：未通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 20.88 | 15 | 2.244e-12 | 4.676e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 2.221 | 202 | Ux=2.893e-13; Uy=9.627e-13; Uz=5.525e-13; p[1]=9.722e-12; p[2]=9.722e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 318.6 | 15 | 8.727e-12 | 4.723e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 67.88 | 684 | Ux=4.045e-13; Uy=3.855e-13; Uz=6.626e-13; p[1]=9.852e-12; p[2]=9.852e-12 | — | 0 |
| 32 | elmer | 2.0/4g/3600.0 | 100/3000 | 996.9 | 15 | 7.817e-12 | 4.738e-10 | 0 |
| 32 | openfoam | 2.0/4g/3600.0 | 12000/— | 355.7 | 1157 | Ux=4.223e-13; Uy=4.122e-13; Uz=6.888e-13; p[1]=9.745e-12; p[2]=9.744e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.005559 | m/s | 4.9 |
| 12 | answer_pressure | 0.00378 | Pa | 0.03443 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.002544 | m/s | 2.223 |
| 24 | answer_pressure | 0.0004549 | Pa | 0.004143 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 32 | answer_velocity | 0.001512 | m/s | 1.316 |
| 32 | answer_pressure | 0.001353 | Pa | 0.01232 |
| 32 | answer_density | 0 | kg/m3 | 0 |
| 32 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 054-periodic-duct-16：未通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 26.8 | 16 | 7.991e-13 | 9.429e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 4.378 | 481 | Ux=5.26e-13; Uy=5.191e-13; Uz=5.117e-13; p[1]=7.483e-12; p[2]=7.483e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 566.9 | 16 | 3.809e-12 | 9.414e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 144 | 1426 | Ux=6.286e-13; Uy=6.25e-13; Uz=8.522e-13; p[1]=7.868e-12; p[2]=7.868e-12 | — | 0 |
| 32 | elmer | 2.0/4g/3600.0 | 100/3000 | 1709 | 16 | 9.24e-12 | 9.404e-10 | 0 |
| 32 | openfoam | 2.0/4g/3600.0 | 12000/— | 744.8 | 2317 | Ux=6.502e-13; Uy=6.459e-13; Uz=9.145e-13; p[1]=9.056e-12; p[2]=9.057e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.01907 | m/s | 10.36 |
| 12 | answer_pressure | 0.002484 | Pa | 2.451e-06 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.008284 | m/s | 4.406 |
| 24 | answer_pressure | 0.000675 | Pa | 6.661e-07 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 32 | answer_velocity | 0.005833 | m/s | 3.089 |
| 32 | answer_pressure | 0.000412 | Pa | 4.065e-07 |
| 32 | answer_density | 0 | kg/m3 | 0 |
| 32 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 055-periodic-duct-17：未通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 24.88 | 17 | 1.949e-12 | 5.753e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 10 | 1122 | Ux=3.244e-13; Uy=3.65e-13; Uz=2.97e-13; p[1]=8.121e-12; p[2]=8.121e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 632 | 17 | 2.684e-12 | 5.212e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 316 | 3042 | Ux=4.54e-13; Uy=4.891e-13; Uz=5.505e-13; p[1]=7.635e-12; p[2]=7.635e-12 | — | 0 |
| 32 | elmer | 2.0/4g/3600.0 | 100/3000 | 2280 | 17 | 4.25e-12 | 7.019e-10 | 0 |
| 32 | openfoam | 2.0/4g/3600.0 | 12000/— | 1187 | 4795 | Ux=5.014e-13; Uy=5.331e-13; Uz=6.308e-13; p[1]=9.564e-12; p[2]=9.564e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.003463 | m/s | 2.981 |
| 12 | answer_pressure | 0.02441 | Pa | 0.2023 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.001493 | m/s | 1.276 |
| 24 | answer_pressure | 0.003315 | Pa | 0.02749 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 32 | answer_velocity | 0.00101 | m/s | 0.8621 |
| 32 | answer_pressure | 0.005113 | Pa | 0.0424 |
| 32 | answer_density | 0 | kg/m3 | 0 |
| 32 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 056-periodic-duct-18：未通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 16 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 94.08 | 15 | 1.926e-12 | 9.307e-10 | 0 |
| 16 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 64.45 | 2123 | Ux=4.505e-13; Uy=5.033e-13; Uz=3.553e-13; p[1]=9.324e-12; p[2]=9.324e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 1293 | 15 | 9.313e-12 | 8.605e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 360.7 | 3809 | Ux=8.047e-13; Uy=9.597e-13; Uz=9.637e-13; p[1]=9.372e-12; p[2]=9.372e-12 | — | 0 |
| 32 | elmer | 2.0/4g/3600.0 | 100/3000 | 3600 | 9 | 1.689e-11 | 3.696e-06 | 124 |
| 32 | openfoam | — | —/— | — | — | — | — | — |

n=32：elmer failed with 124: /home/zhouzhiyu/code/docker/work/caeoj-2-1-3-supplement/production/native/056-periodic-duct-18/31965860205a/elmer-n32/execution.log


| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 16 | answer_velocity | 0.003418 | m/s | 3.07 |
| 16 | answer_pressure | 0.00374 | Pa | 0.03399 |
| 16 | answer_density | 0 | kg/m3 | 0 |
| 16 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.001816 | m/s | 1.622 |
| 24 | answer_pressure | 0.003881 | Pa | 0.03528 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 057-periodic-duct-19：未通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 25.04 | 16 | 9.091e-12 | 5.098e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 4.377 | 498 | Ux=5.071e-13; Uy=3.281e-13; Uz=4.578e-13; p[1]=7.917e-12; p[2]=7.917e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 703.6 | 16 | 4.152e-12 | 5.267e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 137.7 | 1379 | Ux=5.972e-13; Uy=5.109e-13; Uz=2.859e-13; p[1]=9.701e-12; p[2]=9.701e-12 | — | 0 |
| 32 | elmer | 2.0/4g/3600.0 | 100/3000 | 2362 | 16 | 6.642e-12 | 5.313e-10 | 0 |
| 32 | openfoam | 2.0/4g/3600.0 | 12000/— | 655.2 | 2182 | Ux=6.273e-13; Uy=5.565e-13; Uz=3.489e-13; p[1]=9.933e-12; p[2]=9.933e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.0232 | m/s | 13.28 |
| 12 | answer_pressure | 0.001155 | Pa | 0.01155 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.009375 | m/s | 5.089 |
| 24 | answer_pressure | 0.0001768 | Pa | 0.001768 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 32 | answer_velocity | 0.005677 | m/s | 3.05 |
| 32 | answer_pressure | 1.903e-05 | Pa | 0.0001902 |
| 32 | answer_density | 0 | kg/m3 | 0 |
| 32 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 058-periodic-duct-20：未通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 25.24 | 16 | 7.789e-12 | 6.486e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 4.677 | 556 | Ux=3.266e-13; Uy=4.066e-13; Uz=4.18e-13; p[1]=9.027e-12; p[2]=9.027e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 607.1 | 16 | 8.015e-12 | 6.608e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 140 | 1554 | Ux=6.703e-13; Uy=5.291e-13; Uz=7.341e-13; p[1]=7.835e-12; p[2]=7.835e-12 | — | 0 |
| 32 | elmer | 2.0/4g/3600.0 | 100/3000 | 2509 | 16 | 3.316e-12 | 6.633e-10 | 0 |
| 32 | openfoam | 2.0/4g/3600.0 | 12000/— | 696 | 2478 | Ux=7.597e-13; Uy=5.691e-13; Uz=8.15e-13; p[1]=8.808e-12; p[2]=8.808e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.01923 | m/s | 10.39 |
| 12 | answer_pressure | 0.0002104 | Pa | 0.001753 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.008536 | m/s | 4.375 |
| 24 | answer_pressure | 8.253e-05 | Pa | 0.0006879 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 32 | answer_velocity | 0.006102 | m/s | 3.113 |
| 32 | answer_pressure | 6.488e-05 | Pa | 0.0005408 |
| 32 | answer_density | 0 | kg/m3 | 0 |
| 32 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 059-cavity-01：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 17.93 | 15 | 6.593e-12 | 5.072e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 1.922 | 130 | Ux=2.562e-13; Uy=3.557e-13; Uz=4.462e-13; p[1]=5.928e-12; p[2]=5.928e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 253 | 15 | 8.059e-12 | 4.678e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 44.14 | 452 | Ux=4.233e-13; Uy=5.896e-13; Uz=2.849e-13; p[1]=8.402e-12; p[2]=8.402e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.0005759 | m/s | 0.5542 |
| 12 | answer_pressure | 0.002144 | Pa | 2.116e-06 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.0001496 | m/s | 0.1442 |
| 24 | answer_pressure | 0.0004793 | Pa | 4.73e-07 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 060-cavity-02：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 16.61 | 16 | 7.964e-12 | 5.439e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 2.022 | 176 | Ux=9.74e-13; Uy=3.661e-13; Uz=4.148e-13; p[1]=9.378e-12; p[2]=9.378e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 265.8 | 16 | 6.113e-12 | 3.462e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 66.53 | 617 | Ux=5.103e-13; Uy=6.116e-13; Uz=5.981e-13; p[1]=8.906e-12; p[2]=8.906e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.001136 | m/s | 1.076 |
| 12 | answer_pressure | 0.01024 | Pa | 0.08556 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.0003152 | m/s | 0.3088 |
| 24 | answer_pressure | 0.007911 | Pa | 0.06592 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 061-cavity-03：未通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 21.68 | 20 | 8.908e-12 | 3.269e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 2.678 | 165 | Ux=4.306e-13; Uy=3.657e-13; Uz=7.053e-13; p[1]=9.152e-12; p[2]=9.152e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 439.2 | 20 | 8.258e-12 | 7.857e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 58.79 | 575 | Ux=6.509e-13; Uy=6.022e-13; Uz=8.382e-13; p[1]=9.749e-12; p[2]=9.749e-12 | — | 0 |
| 32 | elmer | 2.0/4g/3600.0 | 100/3000 | 1616 | 20 | 8.017e-12 | 5.296e-10 | 0 |
| 32 | openfoam | 2.0/4g/3600.0 | 12000/— | 316.7 | 980 | Ux=6.871e-13; Uy=6.465e-13; Uz=2.709e-13; p[1]=9.461e-12; p[2]=9.461e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.008146 | m/s | 6.978 |
| 12 | answer_pressure | 1.295 | Pa | 11.33 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.001834 | m/s | 1.62 |
| 24 | answer_pressure | 0.3678 | Pa | 3.439 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 32 | answer_velocity | 0.001051 | m/s | 0.931 |
| 32 | answer_pressure | 0.1251 | Pa | 1.222 |
| 32 | answer_density | 0 | kg/m3 | 0 |
| 32 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 062-cavity-04：未通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 22.99 | 20 | 9.338e-12 | 9.599e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 2.327 | 155 | Ux=8.097e-13; Uy=4.122e-13; Uz=3.477e-13; p[1]=6.049e-12; p[2]=6.049e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 434.3 | 21 | 9.878e-12 | 7.253e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 58.09 | 542 | Ux=3.134e-13; Uy=5.585e-13; Uz=5.93e-13; p[1]=9.259e-12; p[2]=9.259e-12 | — | 0 |
| 32 | elmer | 2.0/4g/3600.0 | 100/3000 | 1114 | 22 | 9.722e-12 | 5.037e-10 | 0 |
| 32 | openfoam | 2.0/4g/3600.0 | 12000/— | 277.6 | 925 | Ux=3.38e-13; Uy=5.815e-13; Uz=6.385e-13; p[1]=9.81e-12; p[2]=9.81e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.00452 | m/s | 3.575 |
| 12 | answer_pressure | 1.707 | Pa | 4.984 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.001231 | m/s | 0.9873 |
| 24 | answer_pressure | 0.6085 | Pa | 1.808 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 32 | answer_velocity | 0.0006721 | m/s | 0.5402 |
| 32 | answer_pressure | 0.1349 | Pa | 1.287 |
| 32 | answer_density | 0 | kg/m3 | 0 |
| 32 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 063-cavity-05：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 19.13 | 19 | 7.789e-12 | 3.677e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 2.63 | 149 | Ux=3.212e-13; Uy=3.277e-13; Uz=3.828e-13; p[1]=9.26e-12; p[2]=9.26e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 327.6 | 18 | 9.472e-12 | 8.956e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 55.1 | 519 | Ux=5.787e-13; Uy=5.878e-13; Uz=5.831e-13; p[1]=6.703e-12; p[2]=6.703e-12 | — | 0 |
| 32 | elmer | 2.0/4g/3600.0 | 100/3000 | 916.8 | 18 | 7.111e-12 | 8.049e-10 | 0 |
| 32 | openfoam | 2.0/4g/3600.0 | 12000/— | 230.1 | 887 | Ux=6.218e-13; Uy=6.312e-13; Uz=5.954e-13; p[1]=7.262e-12; p[2]=7.263e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.0005736 | m/s | 0.5517 |
| 12 | answer_pressure | 0.2266 | Pa | 1.709 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.0001563 | m/s | 0.1515 |
| 24 | answer_pressure | 0.0782 | Pa | 0.591 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 32 | answer_velocity | 9.799e-05 | m/s | 0.09436 |
| 32 | answer_pressure | 0.03023 | Pa | 0.2289 |
| 32 | answer_density | 0 | kg/m3 | 0 |
| 32 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 064-cavity-06：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 20.94 | 20 | 6.354e-12 | 6.144e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 1.771 | 130 | Ux=2.501e-13; Uy=3.188e-13; Uz=2.679e-13; p[1]=6.645e-12; p[2]=6.645e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 295.7 | 20 | 7.045e-12 | 5.164e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 51.71 | 450 | Ux=4.635e-13; Uy=5.739e-13; Uz=4.711e-13; p[1]=9.308e-12; p[2]=9.308e-12 | — | 0 |
| 32 | elmer | 2.0/4g/3600.0 | 100/3000 | 984.5 | 20 | 7.822e-12 | 7.285e-10 | 0 |
| 32 | openfoam | 2.0/4g/3600.0 | 12000/— | 211.3 | 767 | Ux=5.083e-13; Uy=6.243e-13; Uz=5.155e-13; p[1]=8.05e-12; p[2]=8.051e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.00189 | m/s | 1.782 |
| 12 | answer_pressure | 1.381 | Pa | 0.001363 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.0004485 | m/s | 0.4239 |
| 24 | answer_pressure | 0.3165 | Pa | 0.0003123 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 32 | answer_velocity | 0.0003252 | m/s | 0.3072 |
| 32 | answer_pressure | 0.2047 | Pa | 0.000202 |
| 32 | answer_density | 0 | kg/m3 | 0 |
| 32 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 065-cavity-07：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 18.79 | 15 | 5.825e-12 | 7.444e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 2.121 | 173 | Ux=3.849e-13; Uy=4.46e-13; Uz=2.591e-13; p[1]=7.51e-12; p[2]=7.511e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 293.2 | 15 | 9.924e-12 | 5.736e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 73.84 | 609 | Ux=5.707e-13; Uy=6.18e-13; Uz=6.12e-13; p[1]=9.293e-12; p[2]=9.295e-12 | — | 0 |
| 32 | elmer | 2.0/4g/3600.0 | 100/3000 | 745.5 | 15 | 9.863e-12 | 5.576e-10 | 0 |
| 32 | openfoam | 2.0/4g/3600.0 | 12000/— | 351.4 | 1040 | Ux=6.099e-13; Uy=6.519e-13; Uz=7.099e-13; p[1]=8.34e-12; p[2]=8.348e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.00178 | m/s | 1.666 |
| 12 | answer_pressure | 0.002841 | Pa | 0.02832 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.0005044 | m/s | 0.4745 |
| 24 | answer_pressure | 0.0006895 | Pa | 0.00688 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 32 | answer_velocity | 0.0002971 | m/s | 0.2796 |
| 32 | answer_pressure | 0.0006734 | Pa | 0.006718 |
| 32 | answer_density | 0 | kg/m3 | 0 |
| 32 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 066-cavity-08：未通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 21.76 | 17 | 2.366e-12 | 5.262e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 2.275 | 124 | Ux=3.928e-13; Uy=3.268e-13; Uz=4.811e-13; p[1]=9.759e-12; p[2]=9.759e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 308 | 17 | 7.212e-12 | 4.513e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 40.71 | 430 | Ux=5.979e-13; Uy=4.432e-13; Uz=6.818e-13; p[1]=9.413e-12; p[2]=9.413e-12 | — | 0 |
| 32 | elmer | 2.0/4g/3600.0 | 100/3000 | 1129 | 16 | 5.006e-12 | 9.078e-10 | 0 |
| 32 | openfoam | 2.0/4g/3600.0 | 12000/— | 192 | 727 | Ux=6.432e-13; Uy=4.672e-13; Uz=7.179e-13; p[1]=9.843e-12; p[2]=9.843e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.01397 | m/s | 11.48 |
| 12 | answer_pressure | 0.03381 | Pa | 0.2809 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.003519 | m/s | 2.995 |
| 24 | answer_pressure | 0.01698 | Pa | 0.1414 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 32 | answer_velocity | 0.001301 | m/s | 1.115 |
| 32 | answer_pressure | 0.009956 | Pa | 0.08346 |
| 32 | answer_density | 0 | kg/m3 | 0 |
| 32 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 067-cavity-09：未通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 24.58 | 14 | 7.542e-12 | 5.881e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 3.041 | 152 | Ux=3.724e-13; Uy=3.446e-13; Uz=4.039e-13; p[1]=6.648e-12; p[2]=6.648e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 269.7 | 14 | 6.134e-12 | 4.485e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 48.98 | 523 | Ux=5.541e-13; Uy=5.934e-13; Uz=6.651e-13; p[1]=9.61e-12; p[2]=9.61e-12 | — | 0 |
| 32 | elmer | 2.0/4g/3600.0 | 100/3000 | 1341 | 14 | 4.072e-12 | 4.247e-10 | 0 |
| 32 | openfoam | 2.0/4g/3600.0 | 12000/— | 276.2 | 888 | Ux=5.883e-13; Uy=6.434e-13; Uz=7.364e-13; p[1]=8.445e-12; p[2]=8.445e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.002779 | m/s | 2.624 |
| 12 | answer_pressure | 0.001525 | Pa | 0.01388 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.0006846 | m/s | 0.6549 |
| 24 | answer_pressure | 0.0005043 | Pa | 0.004587 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 32 | answer_velocity | 0.0003763 | m/s | 0.3604 |
| 32 | answer_pressure | 0.0001547 | Pa | 0.001407 |
| 32 | answer_density | 0 | kg/m3 | 0 |
| 32 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 068-cavity-10：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 26.31 | 15 | 7.107e-12 | 3.732e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 3.189 | 149 | Ux=2.771e-13; Uy=4.295e-13; Uz=3.653e-13; p[1]=8.725e-12; p[2]=8.726e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 272.4 | 15 | 3.125e-12 | 3.285e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 62.17 | 519 | Ux=4.607e-13; Uy=6.165e-13; Uz=9.563e-13; p[1]=9.957e-12; p[2]=9.957e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.001051 | m/s | 0.9887 |
| 12 | answer_pressure | 0.001142 | Pa | 0.01139 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.0002731 | m/s | 0.2565 |
| 24 | answer_pressure | 0.0004554 | Pa | 0.004543 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 069-cavity-11：未通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 2.0/4g/3600.0 | 100/3000 | 38.93 | 20 | 9.306e-12 | 4.912e-10 | 0 |
| 12 | openfoam（复用） | 2.0/4g/3600.0 | 12000/— | 3.495 | 132 | Ux=2.078e-13; Uy=3.134e-13; Uz=3.177e-13; p[1]=9.432e-12; p[2]=9.432e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 294.2 | 20 | 3.307e-12 | 4.026e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 56.2 | 455 | Ux=5.74e-13; Uy=5.796e-13; Uz=5.699e-13; p[1]=7.189e-12; p[2]=7.19e-12 | — | 0 |
| 32 | elmer | 2.0/4g/3600.0 | 100/3000 | 961.1 | 20 | 8.415e-12 | 5.394e-10 | 0 |
| 32 | openfoam | 2.0/4g/3600.0 | 12000/— | 240.6 | 775 | Ux=6.853e-13; Uy=6.422e-13; Uz=6.117e-13; p[1]=8.895e-12; p[2]=8.896e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.002735 | m/s | 2.3 |
| 12 | answer_pressure | 1.138 | Pa | 0.001123 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.0007493 | m/s | 0.6507 |
| 24 | answer_pressure | 0.3319 | Pa | 0.0003275 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 32 | answer_velocity | 0.0004683 | m/s | 0.3967 |
| 32 | answer_pressure | 0.1827 | Pa | 0.0001803 |
| 32 | answer_density | 0 | kg/m3 | 0 |
| 32 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 070-cavity-12：未通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer | 2.0/4g/3600.0 | 100/3000 | 42.72 | 21 | 9.898e-12 | 5.938e-10 | 0 |
| 12 | openfoam | 2.0/4g/3600.0 | 12000/— | 4 | 175 | Ux=6.264e-13; Uy=9.097e-13; Uz=3.995e-13; p[1]=6.335e-12; p[2]=6.336e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 269.8 | 21 | 9.35e-12 | 6.555e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 76.77 | 611 | Ux=8.968e-13; Uy=2.776e-13; Uz=6.084e-13; p[1]=9.371e-12; p[2]=9.372e-12 | — | 0 |
| 32 | elmer | 2.0/4g/3600.0 | 100/3000 | 1123 | 21 | 9.033e-12 | 5.092e-10 | 0 |
| 32 | openfoam | 2.0/4g/3600.0 | 12000/— | 328 | 1042 | Ux=9.554e-13; Uy=9.842e-13; Uz=6.442e-13; p[1]=9.748e-12; p[2]=9.749e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.005679 | m/s | 5.262 |
| 12 | answer_pressure | 5.225 | Pa | 7.654 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.00131 | m/s | 1 |
| 24 | answer_pressure | 1.317 | Pa | 3.998 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 32 | answer_velocity | 0.0006365 | m/s | 0.5724 |
| 32 | answer_pressure | 0.8521 | Pa | 1.575 |
| 32 | answer_density | 0 | kg/m3 | 0 |
| 32 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 071-cavity-13：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer | 2.0/4g/3600.0 | 100/3000 | 34.76 | 13 | 7.123e-12 | 4.374e-10 | 0 |
| 12 | openfoam | 2.0/4g/3600.0 | 12000/— | 4.047 | 167 | Ux=8.932e-13; Uy=7.852e-13; Uz=3.696e-13; p[1]=6.58e-12; p[2]=6.58e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 284.7 | 13 | 3.37e-12 | 4.529e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 67.77 | 585 | Ux=8.606e-13; Uy=9.599e-13; Uz=5.947e-13; p[1]=8.445e-12; p[2]=8.445e-12 | — | 0 |
| 32 | elmer | 2.0/4g/3600.0 | 100/3000 | 974.5 | 13 | 2.286e-12 | 4.746e-10 | 0 |
| 32 | openfoam | 2.0/4g/3600.0 | 12000/— | 271.4 | 998 | Ux=8.635e-13; Uy=9.935e-13; Uz=6.229e-13; p[1]=9.69e-12; p[2]=9.69e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.001638 | m/s | 1.598 |
| 12 | answer_pressure | 1.341e-05 | Pa | 0.0001341 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.0004099 | m/s | 0.4019 |
| 24 | answer_pressure | 3.295e-06 | Pa | 3.295e-05 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 32 | answer_velocity | 0.000132 | m/s | 0.1296 |
| 32 | answer_pressure | 1.998e-06 | Pa | 1.998e-05 |
| 32 | answer_density | 0 | kg/m3 | 0 |
| 32 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 072-cavity-14：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer | 2.0/4g/3600.0 | 100/3000 | 34.6 | 14 | 6.999e-13 | 6.96e-10 | 0 |
| 12 | openfoam | 2.0/4g/3600.0 | 12000/— | 3.805 | 154 | Ux=3.275e-13; Uy=3.127e-13; Uz=5.12e-13; p[1]=8.722e-12; p[2]=8.722e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 311.2 | 14 | 8.616e-12 | 7.687e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 57.32 | 506 | Ux=5.672e-13; Uy=4.946e-13; Uz=6.671e-13; p[1]=9.763e-12; p[2]=9.763e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.001267 | m/s | 1.171 |
| 12 | answer_pressure | 2.943e-05 | Pa | 0.0002452 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.0003248 | m/s | 0.3015 |
| 24 | answer_pressure | 3.383e-05 | Pa | 0.0002819 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 073-cavity-15：未通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer | 2.0/4g/3600.0 | 100/3000 | 36.77 | 15 | 4.458e-13 | 7.594e-10 | 0 |
| 12 | openfoam | 2.0/4g/3600.0 | 12000/— | 4.411 | 152 | Ux=9.183e-13; Uy=2.368e-13; Uz=3.275e-13; p[1]=9.751e-12; p[2]=9.751e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 271 | 15 | 5.928e-12 | 6.978e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 51.7 | 515 | Ux=3.741e-13; Uy=3.806e-13; Uz=5.747e-13; p[1]=9.734e-12; p[2]=9.734e-12 | — | 0 |
| 32 | elmer | 2.0/4g/3600.0 | 100/3000 | 707.1 | 15 | 8.852e-12 | 6.888e-10 | 0 |
| 32 | openfoam | 2.0/4g/3600.0 | 12000/— | 279.1 | 872 | Ux=4.028e-13; Uy=4.126e-13; Uz=6.269e-13; p[1]=8.098e-12; p[2]=8.098e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.003579 | m/s | 3.413 |
| 12 | answer_pressure | 0.001972 | Pa | 0.01797 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.0007996 | m/s | 0.7703 |
| 24 | answer_pressure | 0.0005467 | Pa | 0.004981 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 32 | answer_velocity | 0.0005197 | m/s | 0.5008 |
| 32 | answer_pressure | 0.0002642 | Pa | 0.002408 |
| 32 | answer_density | 0 | kg/m3 | 0 |
| 32 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 074-cavity-16：未通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer | 2.0/4g/3600.0 | 100/3000 | 32.38 | 16 | 4.647e-12 | 7.167e-10 | 0 |
| 12 | openfoam | 2.0/4g/3600.0 | 12000/— | 3.901 | 133 | Ux=2.814e-13; Uy=3.465e-13; Uz=6.991e-13; p[1]=8.186e-12; p[2]=8.186e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 300.1 | 16 | 6.244e-12 | 6.092e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 52.25 | 455 | Ux=4.921e-13; Uy=5.685e-13; Uz=3.977e-13; p[1]=9.947e-12; p[2]=9.947e-12 | — | 0 |
| 32 | elmer | 2.0/4g/3600.0 | 100/3000 | 780.1 | 17 | 7.935e-12 | 1.917e-10 | 0 |
| 32 | openfoam | 2.0/4g/3600.0 | 12000/— | 181.7 | 771 | Ux=5.622e-13; Uy=6.387e-13; Uz=4.91e-13; p[1]=9.755e-12; p[2]=9.755e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.005568 | m/s | 4.086 |
| 12 | answer_pressure | 0.005656 | Pa | 5.581e-06 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.001438 | m/s | 1.063 |
| 24 | answer_pressure | 0.001333 | Pa | 1.315e-06 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 32 | answer_velocity | 0.0007988 | m/s | 0.5907 |
| 32 | answer_pressure | 0.0008845 | Pa | 8.729e-07 |
| 32 | answer_density | 0 | kg/m3 | 0 |
| 32 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 075-cavity-17：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer | 2.0/4g/3600.0 | 100/3000 | 32.07 | 17 | 1.253e-12 | 3.202e-10 | 0 |
| 12 | openfoam | 2.0/4g/3600.0 | 12000/— | 3.838 | 159 | Ux=3.24e-13; Uy=3.265e-13; Uz=3.189e-13; p[1]=8.993e-12; p[2]=8.992e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 266.9 | 16 | 9.833e-12 | 6.889e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 64.96 | 525 | Ux=5.683e-13; Uy=5.696e-13; Uz=5.175e-13; p[1]=8.082e-12; p[2]=8.082e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.0008192 | m/s | 0.7955 |
| 12 | answer_pressure | 0.004724 | Pa | 0.03929 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.0002102 | m/s | 0.2033 |
| 24 | answer_pressure | 0.001352 | Pa | 0.01125 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 076-cavity-18：未通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 16 | elmer | 2.0/4g/3600.0 | 100/3000 | 96.62 | 18 | 6.742e-12 | 4.603e-10 | 0 |
| 16 | openfoam | 2.0/4g/3600.0 | 12000/— | 9.987 | 263 | Ux=2.879e-13; Uy=4.617e-13; Uz=4.717e-13; p[1]=7.673e-12; p[2]=7.673e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 361.6 | 18 | 7.631e-12 | 5.739e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 56.17 | 531 | Ux=3.644e-13; Uy=5.694e-13; Uz=5.717e-13; p[1]=7.666e-12; p[2]=7.666e-12 | — | 0 |
| 32 | elmer | 2.0/4g/3600.0 | 100/3000 | 1145 | 18 | 9.579e-12 | 3.914e-10 | 0 |
| 32 | openfoam | 2.0/4g/3600.0 | 12000/— | 177.8 | 888 | Ux=4.054e-13; Uy=6.25e-13; Uz=6.388e-13; p[1]=9.448e-12; p[2]=9.448e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 16 | answer_velocity | 0.002513 | m/s | 2.309 |
| 16 | answer_pressure | 0.01984 | Pa | 0.1793 |
| 16 | answer_density | 0 | kg/m3 | 0 |
| 16 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.001247 | m/s | 1.15 |
| 24 | answer_pressure | 0.01453 | Pa | 0.1328 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 32 | answer_velocity | 0.0007951 | m/s | 0.7345 |
| 32 | answer_pressure | 0.01469 | Pa | 0.1339 |
| 32 | answer_density | 0 | kg/m3 | 0 |
| 32 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 077-cavity-19：未通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer | 2.0/4g/3600.0 | 100/3000 | 34.37 | 15 | 5.482e-12 | 4.116e-10 | 0 |
| 12 | openfoam | 2.0/4g/3600.0 | 12000/— | 3.746 | 129 | Ux=9.647e-13; Uy=5.297e-13; Uz=3.023e-13; p[1]=7.552e-12; p[2]=7.551e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 310.3 | 15 | 2.048e-12 | 4.751e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 46.49 | 404 | Ux=4.241e-13; Uy=3.034e-13; Uz=5.361e-13; p[1]=9.639e-12; p[2]=9.639e-12 | — | 0 |
| 32 | elmer | 2.0/4g/3600.0 | 100/3000 | 656.2 | 15 | 8.701e-12 | 4.904e-10 | 0 |
| 32 | openfoam | 2.0/4g/3600.0 | 12000/— | 179 | 668 | Ux=5.141e-13; Uy=3.946e-13; Uz=6.039e-13; p[1]=9.511e-12; p[2]=9.511e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.004182 | m/s | 3.973 |
| 12 | answer_pressure | 0.0003479 | Pa | 0.003478 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.001586 | m/s | 1.491 |
| 24 | answer_pressure | 8.583e-05 | Pa | 0.0008582 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 32 | answer_velocity | 0.0009058 | m/s | 0.8493 |
| 32 | answer_pressure | 3.773e-05 | Pa | 0.0003773 |
| 32 | answer_density | 0 | kg/m3 | 0 |
| 32 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 078-cavity-20：未通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer | 2.0/4g/3600.0 | 100/3000 | 33.98 | 15 | 9.612e-12 | 7.777e-10 | 0 |
| 12 | openfoam | 2.0/4g/3600.0 | 12000/— | 3.904 | 119 | Ux=6.557e-13; Uy=5.026e-13; Uz=5.332e-13; p[1]=9.02e-12; p[2]=9.02e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 232.6 | 15 | 5.046e-12 | 9.069e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 37 | 375 | Ux=4.441e-13; Uy=8.705e-13; Uz=9.103e-13; p[1]=9.262e-12; p[2]=9.262e-12 | — | 0 |
| 32 | elmer | 2.0/4g/3600.0 | 100/3000 | 556.7 | 15 | 9.524e-12 | 9.409e-10 | 0 |
| 32 | openfoam | 2.0/4g/3600.0 | 12000/— | 190.5 | 626 | Ux=5.389e-13; Uy=9.448e-13; Uz=9.683e-13; p[1]=9.288e-12; p[2]=9.289e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.005428 | m/s | 4.706 |
| 12 | answer_pressure | 0.0006912 | Pa | 0.005759 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.001639 | m/s | 1.465 |
| 24 | answer_pressure | 0.0002913 | Pa | 0.002427 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 32 | answer_velocity | 0.0007018 | m/s | 0.6434 |
| 32 | answer_pressure | 0.0002178 | Pa | 0.001815 |
| 32 | answer_density | 0 | kg/m3 | 0 |
| 32 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 079-cavity-21：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer | 2.0/4g/3600.0 | 100/3000 | 35.38 | 17 | 5.407e-12 | 6.091e-10 | 0 |
| 12 | openfoam | 2.0/4g/3600.0 | 12000/— | 3.492 | 123 | Ux=6.012e-13; Uy=2.945e-13; Uz=6.521e-13; p[1]=4.222e-12; p[2]=4.222e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 277.4 | 17 | 7.696e-12 | 5.976e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 43.81 | 419 | Ux=9.815e-13; Uy=5.748e-13; Uz=2.958e-13; p[1]=6.843e-12; p[2]=6.843e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.001037 | m/s | 1.002 |
| 12 | answer_pressure | 0.04768 | Pa | 4.705e-05 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.0002456 | m/s | 0.2375 |
| 24 | answer_pressure | 0.01241 | Pa | 1.225e-05 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 080-cavity-22：未通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 16 | elmer | 2.0/4g/3600.0 | 100/3000 | 74.95 | 18 | 6.606e-12 | 6.141e-10 | 0 |
| 16 | openfoam | 2.0/4g/3600.0 | 12000/— | 7.069 | 221 | Ux=7.009e-13; Uy=8.954e-13; Uz=4.365e-13; p[1]=9.356e-12; p[2]=9.355e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 251.6 | 18 | 9.74e-12 | 5.624e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 51.51 | 454 | Ux=7.811e-13; Uy=9.982e-13; Uz=5.612e-13; p[1]=8.987e-12; p[2]=8.988e-12 | — | 0 |
| 32 | elmer | 2.0/4g/3600.0 | 100/3000 | 437.8 | 18 | 8.327e-12 | 5.277e-10 | 0 |
| 32 | openfoam | 2.0/4g/3600.0 | 12000/— | 165.9 | 767 | Ux=8.186e-13; Uy=2.937e-13; Uz=6.182e-13; p[1]=9.807e-12; p[2]=9.809e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 16 | answer_velocity | 0.0008904 | m/s | 0.877 |
| 16 | answer_pressure | 0.1449 | Pa | 1.406 |
| 16 | answer_density | 0 | kg/m3 | 0 |
| 16 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.00064 | m/s | 0.6302 |
| 24 | answer_pressure | 0.1257 | Pa | 1.029 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 32 | answer_velocity | 0.0003036 | m/s | 0.2985 |
| 32 | answer_pressure | 0.07033 | Pa | 0.6865 |
| 32 | answer_density | 0 | kg/m3 | 0 |
| 32 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 081-cavity-23：未通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer | 2.0/4g/3600.0 | 100/3000 | 50.03 | 35 | 2.496e-12 | 9.847e-10 | 0 |
| 12 | openfoam | 2.0/4g/3600.0 | 12000/— | 2.579 | 108 | Ux=3.134e-13; Uy=5.722e-13; Uz=3.795e-13; p[1]=9.969e-12; p[2]=9.97e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 364.5 | 24 | 8.202e-12 | 7.111e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 43.66 | 358 | Ux=5.528e-13; Uy=7.815e-13; Uz=6.277e-13; p[1]=8.675e-12; p[2]=8.675e-12 | — | 0 |
| 32 | elmer | 2.0/4g/3600.0 | 100/3000 | 676.8 | 32 | 6.465e-12 | 4.864e-10 | 0 |
| 32 | openfoam | 2.0/4g/3600.0 | 12000/— | 116 | 604 | Ux=6.156e-13; Uy=8.421e-13; Uz=6.815e-13; p[1]=9.606e-12; p[2]=9.606e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.006595 | m/s | 5.963 |
| 12 | answer_pressure | 52.31 | Pa | 63.11 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.001703 | m/s | 1.571 |
| 24 | answer_pressure | 24.24 | Pa | 27.28 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 32 | answer_velocity | 0.0006042 | m/s | 0.5621 |
| 32 | answer_pressure | 9.621 | Pa | 17.85 |
| 32 | answer_density | 0 | kg/m3 | 0 |
| 32 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 082-cavity-24：未通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer | 2.0/4g/3600.0 | 100/3000 | 50.99 | 47 | 4.706e-13 | 9.21e-10 | 0 |
| 12 | openfoam | 2.0/4g/3600.0 | 12000/— | 3.445 | 116 | Ux=3.839e-13; Uy=3.193e-13; Uz=4.854e-13; p[1]=9.175e-12; p[2]=9.175e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 456.1 | 45 | 7.301e-13 | 6.89e-10 | 0 |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 47.82 | 388 | Ux=5.97e-13; Uy=5.595e-13; Uz=8.463e-13; p[1]=9.707e-12; p[2]=9.707e-12 | — | 0 |
| 32 | elmer | 2.0/4g/3600.0 | 100/3000 | 1410 | 100 | 2.515e-12 | 2.856e-09 | 0 |
| 32 | openfoam | 2.0/4g/3600.0 | 12000/— | 103.5 | 656 | Ux=6.614e-13; Uy=6.229e-13; Uz=9.681e-13; p[1]=9.262e-12; p[2]=9.263e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.02227 | m/s | 14.61 |
| 12 | answer_pressure | 881.2 | Pa | 20.94 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 24 | answer_velocity | 0.004973 | m/s | 3.532 |
| 24 | answer_pressure | 419.2 | Pa | 10.46 |
| 24 | answer_density | 0 | kg/m3 | 0 |
| 24 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 32 | answer_velocity | 0.002879 | m/s | 2.058 |
| 32 | answer_pressure | 93.23 | Pa | 18.5 |
| 32 | answer_density | 0 | kg/m3 | 0 |
| 32 | answer_dynamic_viscosity | 0 | Pa.s | 0 |

### 083-plug-01：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 1.0/2g/600.0 | 100/3000 | 41.74 | 15 | 2.746e-12 | 4.825e-10 | 0 |
| 12 | openfoam | 2.0/4g/3600.0 | 12000/— | 762.5 | 12000 | Ux=0.003786; Uy=3.873e-13; Uz=4.891e-13; p[1]=6.64e-12; p[2]=6.895e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 1.12e-12 | m/s | 1.12e-09 |
| 12 | answer_pressure | 0 | Pa | 0 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 2.424e-12 | Pa | 2.424e-11 |
| 12 | answer_mean_pressure | 0 | Pa | 0 |
| 12 | answer_shear | 4.945e-12 | 1/s | 4.945e-10 |
| 12 | answer_force3 | 1.155e-13 | N | 1.155e-10 |
| 12 | answer_volume_flow3 | 1.337e-16 | m3/s | 1.337e-10 |
| 12 | answer_mass_flow3 | 1.337e-16 | kg/s | 1.337e-10 |
| 12 | answer_force4 | 7.644e-14 | N | 7.644e-11 |
| 12 | answer_volume_flow4 | 1.336e-16 | m3/s | 1.336e-10 |
| 12 | answer_mass_flow4 | 1.336e-16 | kg/s | 1.336e-10 |
| 12 | answer_volume_flow1 | 3.469e-18 | m3/s | 1.153e-14 |
| 12 | answer_mass_flow1 | 3.469e-18 | kg/s | 1.153e-14 |
| 12 | answer_volume_flow2 | 6.939e-18 | m3/s | 2.305e-14 |
| 12 | answer_mass_flow2 | 6.939e-18 | kg/s | 2.305e-14 |

### 084-plug-02：未通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 1.0/2g/600.0 | 100/3000 | 50.92 | 16 | 6.421e-12 | 4.272e-10 | 0 |
| 12 | openfoam | 2.0/4g/3600.0 | 12000/— | 757.7 | 12000 | Ux=7.206e-13; Uy=0.003438; Uz=9.615e-13; p[1]=4.021e-12; p[2]=3.925e-12 | — | 0 |
| 24 | elmer | — | 100/3000 | — | — | — | — | — |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 3600 | 7993 | Ux=3.536e-13 | — | 124 |

n=24：openfoam failed with 124: /home/zhouzhiyu/code/docker/work/caeoj-2-1-3-supplement/production/native/084-plug-02/31965860205a/openfoam-n24/execution.log


| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.001529 | m/s | 0.9464 |
| 12 | answer_pressure | 0.01381 | Pa | 0.1166 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 0.01773 | Pa | 0.1503 |
| 12 | answer_mean_pressure | 0.0005195 | Pa | 0.004365 |
| 12 | answer_shear | 0.01816 | 1/s | 1.784 |
| 12 | answer_force3 | 0.003078 | N | 0.1464 |
| 12 | answer_volume_flow3 | 7.769e-23 | m3/s | 7.769e-17 |
| 12 | answer_mass_flow3 | 7.769e-23 | kg/s | 7.769e-17 |
| 12 | answer_force4 | 0.0454 | N | 2.334 |
| 12 | answer_volume_flow4 | 3.126e-22 | m3/s | 3.126e-16 |
| 12 | answer_mass_flow4 | 3.126e-22 | kg/s | 3.126e-16 |
| 12 | answer_volume_flow1 | 3.469e-18 | m3/s | 1.153e-14 |
| 12 | answer_mass_flow1 | 3.469e-18 | kg/s | 1.153e-14 |
| 12 | answer_volume_flow2 | 0.0007479 | m3/s | 2.424 |
| 12 | answer_mass_flow2 | 0.0007479 | kg/s | 2.424 |

### 085-plug-03：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 1.0/2g/600.0 | 100/3000 | 55.34 | 16 | 8.578e-12 | 5.803e-10 | 0 |
| 12 | openfoam | 2.0/4g/3600.0 | 12000/— | 743.8 | 12000 | Ux=8.77e-13; Uy=4.985e-13; Uz=0.004071; p[1]=6.291e-12; p[2]=5.99e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 1.91e-12 | m/s | 1.91e-09 |
| 12 | answer_pressure | 2.144e-10 | Pa | 1.949e-09 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 1.181e-10 | Pa | 1.181e-09 |
| 12 | answer_mean_pressure | 2.438e-11 | Pa | 2.216e-10 |
| 12 | answer_shear | 2.101e-11 | 1/s | 2.101e-09 |
| 12 | answer_force3 | 3.094e-11 | N | 5.204e-09 |
| 12 | answer_volume_flow3 | 0 | m3/s | 0 |
| 12 | answer_mass_flow3 | 0 | kg/s | 0 |
| 12 | answer_force4 | 3.118e-11 | N | 2.834e-09 |
| 12 | answer_volume_flow4 | 0 | m3/s | 0 |
| 12 | answer_mass_flow4 | 0 | kg/s | 0 |
| 12 | answer_volume_flow1 | 2.776e-17 | m3/s | 1.156e-14 |
| 12 | answer_mass_flow1 | 4.441e-16 | kg/s | 1.85e-14 |
| 12 | answer_volume_flow2 | 2.776e-17 | m3/s | 1.156e-14 |
| 12 | answer_mass_flow2 | 4.441e-16 | kg/s | 1.85e-14 |

### 086-plug-04：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 1.0/2g/600.0 | 100/3000 | 50.72 | 17 | 3.14e-12 | 3.541e-10 | 0 |
| 12 | openfoam | 2.0/4g/3600.0 | 12000/— | 1289 | 12000 | Ux=0.00702; Uy=0.002705; Uz=2.694e-13; p[1]=4.665e-12; p[2]=4.675e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 4.801e-09 | m/s | 1.439e-06 |
| 12 | answer_pressure | 2e-10 | Pa | 2e-09 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 5.16e-10 | Pa | 5.16e-09 |
| 12 | answer_mean_pressure | 6.16e-12 | Pa | 6.16e-11 |
| 12 | answer_shear | 1.301e-11 | 1/s | 1.301e-09 |
| 12 | answer_force3 | 5.154e-11 | N | 5.154e-08 |
| 12 | answer_volume_flow3 | 2.155e-09 | m3/s | 0.002155 |
| 12 | answer_mass_flow3 | 2.155e-08 | kg/s | 0.02155 |
| 12 | answer_force4 | 1.138e-10 | N | 1.138e-07 |
| 12 | answer_volume_flow4 | 2.155e-09 | m3/s | 0.002155 |
| 12 | answer_mass_flow4 | 2.155e-08 | kg/s | 0.02155 |
| 12 | answer_volume_flow1 | 3.446e-09 | m3/s | 1.913e-06 |
| 12 | answer_mass_flow1 | 3.446e-08 | kg/s | 1.914e-06 |
| 12 | answer_volume_flow2 | 3.446e-09 | m3/s | 1.913e-06 |
| 12 | answer_mass_flow2 | 3.446e-08 | kg/s | 1.914e-06 |

### 087-plug-05：未通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 1.0/2g/600.0 | 100/3000 | 48.91 | 21 | 2.027e-12 | 7.501e-10 | 0 |
| 12 | openfoam | 2.0/4g/3600.0 | 12000/— | 1301 | 12000 | Ux=0.002597; Uy=0.006566; Uz=4.148e-13; p[1]=4.376e-12; p[2]=4.159e-12 | — | 0 |
| 24 | elmer | — | 100/3000 | — | — | — | — | — |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 3600 | 4826 | — | — | 124 |

n=24：openfoam failed with 124: /home/zhouzhiyu/code/docker/work/caeoj-2-1-3-supplement/production/native/087-plug-05/31965860205a/openfoam-n24/execution.log


| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.003735 | m/s | 3.178 |
| 12 | answer_pressure | 1.591 | Pa | 0.9228 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 3.65 | Pa | 26.74 |
| 12 | answer_mean_pressure | 0.1689 | Pa | 0.1567 |
| 12 | answer_shear | 0.1318 | 1/s | 11.65 |
| 12 | answer_force3 | 1.654 | N | 41.31 |
| 12 | answer_volume_flow3 | 2.228e-18 | m3/s | 2.228e-12 |
| 12 | answer_mass_flow3 | 2.228e-15 | kg/s | 2.228e-09 |
| 12 | answer_force4 | 14.54 | N | 14.55 |
| 12 | answer_volume_flow4 | 2.375e-18 | m3/s | 2.375e-12 |
| 12 | answer_mass_flow4 | 2.375e-15 | kg/s | 2.375e-09 |
| 12 | answer_volume_flow1 | 1.084e-10 | m3/s | 4.796e-07 |
| 12 | answer_mass_flow1 | 1.084e-07 | kg/s | 4.817e-07 |
| 12 | answer_volume_flow2 | 0.002226 | m3/s | 8.965 |
| 12 | answer_mass_flow2 | 2.226 | kg/s | 9.001 |

### 088-plug-06：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 1.0/2g/600.0 | 100/3000 | 38.31 | 16 | 5.098e-12 | 3.004e-10 | 0 |
| 12 | openfoam | 2.0/4g/3600.0 | 12000/— | 709.7 | 12000 | Ux=4.275e-13; Uy=6.607e-13; Uz=0.003787; p[1]=6.659e-12; p[2]=7.084e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 1.072e-13 | m/s | 1.072e-10 |
| 12 | answer_pressure | 4.366e-11 | Pa | 4.308e-14 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 2.037e-10 | Pa | 7.033e-10 |
| 12 | answer_mean_pressure | 0 | Pa | 0 |
| 12 | answer_shear | 1.248e-12 | 1/s | 1.248e-10 |
| 12 | answer_force3 | 5.594e-11 | N | 5.594e-08 |
| 12 | answer_volume_flow3 | 7.244e-23 | m3/s | 7.244e-17 |
| 12 | answer_mass_flow3 | 7.244e-20 | kg/s | 7.244e-14 |
| 12 | answer_force4 | 2.277e-11 | N | 2.277e-08 |
| 12 | answer_volume_flow4 | 8.117e-23 | m3/s | 8.117e-17 |
| 12 | answer_mass_flow4 | 8.117e-20 | kg/s | 8.117e-14 |
| 12 | answer_volume_flow1 | 1.388e-17 | m3/s | 2.309e-14 |
| 12 | answer_mass_flow1 | 1.421e-14 | kg/s | 2.368e-14 |
| 12 | answer_volume_flow2 | 1.388e-17 | m3/s | 2.309e-14 |
| 12 | answer_mass_flow2 | 1.421e-14 | kg/s | 2.368e-14 |

### 089-plug-07：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 1.0/2g/600.0 | 100/3000 | 35.66 | 16 | 6.328e-12 | 5.791e-10 | 0 |
| 12 | openfoam | 2.0/4g/3600.0 | 12000/— | 1276 | 12000 | Ux=0.003458; Uy=0.008952; Uz=7.026e-13; p[1]=6.408e-12; p[2]=6.888e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 1.262e-09 | m/s | 6.008e-07 |
| 12 | answer_pressure | 1.371e-11 | Pa | 1.371e-10 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 1.653e-11 | Pa | 1.653e-10 |
| 12 | answer_mean_pressure | 2.838e-12 | Pa | 2.838e-11 |
| 12 | answer_shear | 1.351e-11 | 1/s | 1.351e-09 |
| 12 | answer_force3 | 1.666e-12 | N | 1.666e-09 |
| 12 | answer_volume_flow3 | 8.315e-10 | m3/s | 0.0008315 |
| 12 | answer_mass_flow3 | 8.315e-10 | kg/s | 0.0008315 |
| 12 | answer_force4 | 5.145e-12 | N | 5.145e-09 |
| 12 | answer_volume_flow4 | 8.315e-10 | m3/s | 0.0008315 |
| 12 | answer_mass_flow4 | 8.315e-10 | kg/s | 0.0008315 |
| 12 | answer_volume_flow1 | 5.073e-10 | m3/s | 8.441e-07 |
| 12 | answer_mass_flow1 | 5.073e-10 | kg/s | 8.441e-07 |
| 12 | answer_volume_flow2 | 5.073e-10 | m3/s | 8.441e-07 |
| 12 | answer_mass_flow2 | 5.073e-10 | kg/s | 8.441e-07 |

### 090-plug-08：未通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 1.0/2g/600.0 | 100/3000 | 41.26 | 17 | 9.949e-12 | 3.612e-10 | 0 |
| 12 | openfoam | 2.0/4g/3600.0 | 12000/— | 1283 | 12000 | Ux=0.01598; Uy=0.004337; Uz=7.792e-13; p[1]=4.822e-12; p[2]=4.656e-12 | — | 0 |
| 24 | elmer | — | 100/3000 | — | — | — | — | — |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 3600 | 4687 | — | — | 124 |

n=24：openfoam failed with 124: /home/zhouzhiyu/code/docker/work/caeoj-2-1-3-supplement/production/native/090-plug-08/31965860205a/openfoam-n24/execution.log


| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.00199 | m/s | 1.552 |
| 12 | answer_pressure | 0.01528 | Pa | 0.129 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 0.004602 | Pa | 0.04494 |
| 12 | answer_mean_pressure | 0.0005319 | Pa | 0.004469 |
| 12 | answer_shear | 0.06732 | 1/s | 6.307 |
| 12 | answer_force3 | 0.001607 | N | 0.07647 |
| 12 | answer_volume_flow3 | 2.056e-18 | m3/s | 2.056e-12 |
| 12 | answer_mass_flow3 | 2.056e-18 | kg/s | 2.056e-12 |
| 12 | answer_force4 | 0.01602 | N | 0.8503 |
| 12 | answer_volume_flow4 | 2.274e-18 | m3/s | 2.274e-12 |
| 12 | answer_mass_flow4 | 2.274e-18 | kg/s | 2.274e-12 |
| 12 | answer_volume_flow1 | 4.856e-09 | m3/s | 1.011e-06 |
| 12 | answer_mass_flow1 | 4.856e-09 | kg/s | 1.011e-06 |
| 12 | answer_volume_flow2 | 0.0009983 | m3/s | 0.2075 |
| 12 | answer_mass_flow2 | 0.0009983 | kg/s | 0.2075 |

### 091-plug-09：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 1.0/2g/600.0 | 100/3000 | 30.17 | 15 | 2.25e-12 | 4.825e-10 | 0 |
| 12 | openfoam | 2.0/4g/3600.0 | 12000/— | 706.1 | 12000 | Ux=5.814e-13; Uy=4.12e-13; Uz=0.004263; p[1]=4.542e-12; p[2]=4.126e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 7.207e-13 | m/s | 7.207e-10 |
| 12 | answer_pressure | 7.949e-13 | Pa | 7.227e-12 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 9.601e-13 | Pa | 8.728e-12 |
| 12 | answer_mean_pressure | 3.418e-13 | Pa | 3.108e-12 |
| 12 | answer_shear | 4.88e-12 | 1/s | 4.88e-10 |
| 12 | answer_force3 | 8.011e-13 | N | 5.429e-11 |
| 12 | answer_volume_flow3 | 2.932e-20 | m3/s | 2.932e-14 |
| 12 | answer_mass_flow3 | 2.932e-19 | kg/s | 2.932e-13 |
| 12 | answer_force4 | 9.49e-13 | N | 6.431e-11 |
| 12 | answer_volume_flow4 | 9.179e-20 | m3/s | 9.179e-14 |
| 12 | answer_mass_flow4 | 9.179e-19 | kg/s | 9.179e-13 |
| 12 | answer_volume_flow1 | 6.939e-18 | m3/s | 3.07e-14 |
| 12 | answer_mass_flow1 | 8.327e-17 | kg/s | 3.699e-14 |
| 12 | answer_volume_flow2 | 6.939e-18 | m3/s | 3.07e-14 |
| 12 | answer_mass_flow2 | 8.327e-17 | kg/s | 3.699e-14 |

### 092-plug-10：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 1.0/2g/600.0 | 100/3000 | 33.85 | 15 | 1.377e-12 | 9.65e-10 | 0 |
| 12 | openfoam | 2.0/4g/3600.0 | 12000/— | 706.3 | 12000 | Ux=0.004037; Uy=3.389e-13; Uz=9.265e-13; p[1]=4.162e-12; p[2]=3.985e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 1e-09 | m/s | 6.25e-07 |
| 12 | answer_pressure | 1.005e-12 | Pa | 1.005e-11 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 1.228e-12 | Pa | 1.228e-11 |
| 12 | answer_mean_pressure | 3.489e-13 | Pa | 3.489e-12 |
| 12 | answer_shear | 2.317e-12 | 1/s | 2.317e-10 |
| 12 | answer_force3 | 3.237e-13 | N | 3.237e-10 |
| 12 | answer_volume_flow3 | 1.434e-18 | m3/s | 1.434e-12 |
| 12 | answer_mass_flow3 | 1.434e-17 | kg/s | 1.434e-11 |
| 12 | answer_force4 | 1.284e-12 | N | 1.284e-09 |
| 12 | answer_volume_flow4 | 1.31e-18 | m3/s | 1.31e-12 |
| 12 | answer_mass_flow4 | 1.31e-17 | kg/s | 1.31e-11 |
| 12 | answer_volume_flow1 | 6.939e-18 | m3/s | 1.539e-14 |
| 12 | answer_mass_flow1 | 1.11e-16 | kg/s | 2.467e-14 |
| 12 | answer_volume_flow2 | 7.5e-10 | m3/s | 1.663e-06 |
| 12 | answer_mass_flow2 | 7.5e-09 | kg/s | 1.666e-06 |

### 093-plug-11：未通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 1.0/2g/600.0 | 100/3000 | 36.24 | 21 | 7.662e-13 | 7.626e-10 | 0 |
| 12 | openfoam | 2.0/4g/3600.0 | 12000/— | 704.8 | 12000 | Ux=3.146e-13; Uy=0.004036; Uz=7.245e-13; p[1]=3.819e-12; p[2]=3.425e-12 | — | 0 |
| 24 | elmer | — | 100/3000 | — | — | — | — | — |
| 24 | openfoam | 2.0/4g/3600.0 | 12000/— | 3600 | 8068 | Ux=4.661e-13 | — | 124 |

n=24：openfoam failed with 124: /home/zhouzhiyu/code/docker/work/caeoj-2-1-3-supplement/production/native/093-plug-11/31965860205a/openfoam-n24/execution.log


| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.0005778 | m/s | 0.5745 |
| 12 | answer_pressure | 0.1328 | Pa | 0.0001311 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 0.3803 | Pa | 3.663 |
| 12 | answer_mean_pressure | 0.0004825 | Pa | 4.766e-07 |
| 12 | answer_shear | 0.01665 | 1/s | 1.638 |
| 12 | answer_force3 | 1.006 | N | 2.061 |
| 12 | answer_volume_flow3 | 1.454e-21 | m3/s | 1.454e-15 |
| 12 | answer_mass_flow3 | 1.454e-18 | kg/s | 1.454e-12 |
| 12 | answer_force4 | 1.004 | N | 2.077 |
| 12 | answer_volume_flow4 | 1.71e-21 | m3/s | 1.71e-15 |
| 12 | answer_mass_flow4 | 1.71e-18 | kg/s | 1.71e-12 |
| 12 | answer_volume_flow1 | 0 | m3/s | 0 |
| 12 | answer_mass_flow1 | 0 | kg/s | 0 |
| 12 | answer_volume_flow2 | 5.156e-08 | m3/s | 4.293e-05 |
| 12 | answer_mass_flow2 | 5.156e-05 | kg/s | 4.297e-05 |

### 094-plug-12：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 1.0/2g/600.0 | 100/3000 | 33.41 | 17 | 3.4e-12 | 3.686e-10 | 0 |
| 12 | openfoam | 2.0/4g/3600.0 | 12000/— | 714.7 | 12000 | Ux=3.948e-13; Uy=6.988e-13; Uz=0.004005; p[1]=5.037e-12; p[2]=4.362e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 7.488e-14 | m/s | 7.488e-11 |
| 12 | answer_pressure | 4.396e-11 | Pa | 3.996e-10 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 1.332e-10 | Pa | 1.332e-09 |
| 12 | answer_mean_pressure | 8.42e-12 | Pa | 7.655e-11 |
| 12 | answer_shear | 4.721e-12 | 1/s | 4.721e-10 |
| 12 | answer_force3 | 3.629e-11 | N | 8.327e-09 |
| 12 | answer_volume_flow3 | 0 | m3/s | 0 |
| 12 | answer_mass_flow3 | 0 | kg/s | 0 |
| 12 | answer_force4 | 1.354e-11 | N | 4.164e-09 |
| 12 | answer_volume_flow4 | 0 | m3/s | 0 |
| 12 | answer_mass_flow4 | 0 | kg/s | 0 |
| 12 | answer_volume_flow1 | 0 | m3/s | 0 |
| 12 | answer_mass_flow1 | 0 | kg/s | 0 |
| 12 | answer_volume_flow2 | 1.388e-17 | m3/s | 1.156e-14 |
| 12 | answer_mass_flow2 | 1.421e-14 | kg/s | 1.184e-14 |

### 095-plug-13：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 1.0/2g/600.0 | 100/3000 | 27.11 | 15 | 5.058e-12 | 4.825e-10 | 0 |
| 12 | openfoam | 2.0/4g/3600.0 | 12000/— | 1276 | 12000 | Ux=0.008559; Uy=0.003111; Uz=6.833e-13; p[1]=3.937e-12; p[2]=3.313e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 8.502e-10 | m/s | 6.58e-07 |
| 12 | answer_pressure | 9.498e-14 | Pa | 9.498e-13 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 6.783e-14 | Pa | 6.783e-13 |
| 12 | answer_mean_pressure | 2.992e-14 | Pa | 2.992e-13 |
| 12 | answer_shear | 1.009e-11 | 1/s | 1.009e-09 |
| 12 | answer_force3 | 4.478e-14 | N | 4.478e-11 |
| 12 | answer_volume_flow3 | 9.055e-11 | m3/s | 9.055e-05 |
| 12 | answer_mass_flow3 | 9.055e-11 | kg/s | 9.055e-05 |
| 12 | answer_force4 | 8.271e-14 | N | 8.271e-11 |
| 12 | answer_volume_flow4 | 9.055e-11 | m3/s | 9.055e-05 |
| 12 | answer_mass_flow4 | 9.055e-11 | kg/s | 9.055e-05 |
| 12 | answer_volume_flow1 | 2.89e-10 | m3/s | 4.809e-07 |
| 12 | answer_mass_flow1 | 2.89e-10 | kg/s | 4.809e-07 |
| 12 | answer_volume_flow2 | 1.704e-09 | m3/s | 2.835e-06 |
| 12 | answer_mass_flow2 | 1.704e-09 | kg/s | 2.835e-06 |

### 096-plug-14：未通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 1.0/2g/600.0 | 100/3000 | 33.64 | 22 | 4.432e-12 | 8.141e-10 | 0 |
| 12 | openfoam | 2.0/4g/3600.0 | 12000/— | 1250 | 12000 | Ux=0.002947; Uy=0.007634; Uz=2.369e-13; p[1]=5.942e-12; p[2]=5.45e-12 | — | 0 |
| 24 | elmer | 2.0/4g/3600.0 | 100/3000 | 298.9 | 7 | 6.622e-05 | 0.01152 | 1 |
| 24 | openfoam | — | —/— | — | — | — | — | — |

n=24：elmer failed with 1: /home/zhouzhiyu/code/docker/work/caeoj-2-1-3-supplement/production/native/096-plug-14/31965860205a/elmer-n24/execution.log


n=24，elmer 原生日志：ERROR:: IterSolve: Numerical Error: Too many iterations were needed.


| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 0.2123 | m/s | 71.1 |
| 12 | answer_pressure | 0.005411 | Pa | 0.04527 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 0.02077 | Pa | 0.1755 |
| 12 | answer_mean_pressure | 0.008476 | Pa | 0.07088 |
| 12 | answer_shear | 2.457 | 1/s | 71.08 |
| 12 | answer_force3 | 0.03515 | N | 1.121 |
| 12 | answer_volume_flow3 | 8.918e-22 | m3/s | 8.918e-16 |
| 12 | answer_mass_flow3 | 8.918e-22 | kg/s | 8.918e-16 |
| 12 | answer_force4 | 0.00735 | N | 0.3946 |
| 12 | answer_volume_flow4 | 8.817e-21 | m3/s | 8.817e-15 |
| 12 | answer_mass_flow4 | 8.817e-21 | kg/s | 8.817e-15 |
| 12 | answer_volume_flow1 | 1.484e-10 | m3/s | 3.29e-07 |
| 12 | answer_mass_flow1 | 1.484e-10 | kg/s | 3.29e-07 |
| 12 | answer_volume_flow2 | 0.01012 | m3/s | 18.33 |
| 12 | answer_mass_flow2 | 0.01012 | kg/s | 18.33 |

### 097-plug-15：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 1.0/2g/600.0 | 100/3000 | 24.66 | 16 | 2.582e-12 | 5.79e-10 | 0 |
| 12 | openfoam | 2.0/4g/3600.0 | 12000/— | 698 | 12000 | Ux=7.547e-13; Uy=6.539e-13; Uz=0.003923; p[1]=4.94e-12; p[2]=4.533e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 4.939e-13 | m/s | 4.939e-10 |
| 12 | answer_pressure | 8.571e-13 | Pa | 7.792e-12 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 7.319e-13 | Pa | 6.653e-12 |
| 12 | answer_mean_pressure | 2.122e-13 | Pa | 1.929e-12 |
| 12 | answer_shear | 5.533e-12 | 1/s | 5.533e-10 |
| 12 | answer_force3 | 1.612e-13 | N | 5.05e-11 |
| 12 | answer_volume_flow3 | 1.099e-19 | m3/s | 1.099e-13 |
| 12 | answer_mass_flow3 | 1.099e-18 | kg/s | 1.099e-12 |
| 12 | answer_force4 | 1.088e-12 | N | 9.104e-11 |
| 12 | answer_volume_flow4 | 1.003e-19 | m3/s | 1.003e-13 |
| 12 | answer_mass_flow4 | 1.003e-18 | kg/s | 1.003e-12 |
| 12 | answer_volume_flow1 | 2.776e-17 | m3/s | 3.081e-14 |
| 12 | answer_mass_flow1 | 2.22e-16 | kg/s | 2.467e-14 |
| 12 | answer_volume_flow2 | 2.776e-17 | m3/s | 3.081e-14 |
| 12 | answer_mass_flow2 | 2.22e-16 | kg/s | 2.467e-14 |

### 098-plug-16：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 1.0/2g/600.0 | 100/3000 | 23.34 | 17 | 2.081e-12 | 3.474e-10 | 0 |
| 12 | openfoam | 2.0/4g/3600.0 | 12000/— | 1211 | 12000 | Ux=0.003771; Uy=0.0107; Uz=5.9e-13; p[1]=4.44e-12; p[2]=3.999e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 2.524e-09 | m/s | 7.885e-07 |
| 12 | answer_pressure | 0 | Pa | 0 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 1.349e-12 | Pa | 1.349e-11 |
| 12 | answer_mean_pressure | 0 | Pa | 0 |
| 12 | answer_shear | 2.306e-12 | 1/s | 2.306e-10 |
| 12 | answer_force3 | 6.981e-15 | N | 6.981e-12 |
| 12 | answer_volume_flow3 | 7.459e-10 | m3/s | 0.0007459 |
| 12 | answer_mass_flow3 | 7.459e-09 | kg/s | 0.007458 |
| 12 | answer_force4 | 5.102e-14 | N | 5.102e-11 |
| 12 | answer_volume_flow4 | 7.459e-10 | m3/s | 0.0007459 |
| 12 | answer_mass_flow4 | 7.459e-09 | kg/s | 0.007458 |
| 12 | answer_volume_flow1 | 2.428e-09 | m3/s | 1.011e-06 |
| 12 | answer_mass_flow1 | 2.428e-08 | kg/s | 1.012e-06 |
| 12 | answer_volume_flow2 | 2.428e-09 | m3/s | 1.011e-06 |
| 12 | answer_mass_flow2 | 2.428e-08 | kg/s | 1.012e-06 |

### 099-plug-17：未通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer | 2.0/4g/3600.0 | 100/3000 | 12.92 | 2 | 5.244e+20 | 53.72 | 1 |
| 12 | openfoam | — | —/— | — | — | — | — | — |

n=12：elmer failed with 1: /home/zhouzhiyu/code/docker/work/caeoj-2-1-3-supplement/production/native/099-plug-17/31965860205a/elmer-n12/execution.log


n=12，elmer 原生日志：ERROR:: IterSolve: Numerical Error: System diverged over maximum tolerance.


### 100-plug-18：通过

| 网格每轴段数 | 求解器 | 实际 CPU／内存／时限秒 | 迭代上限：外／线性 | 墙钟秒 | 外迭代编号 | 最终线性残差 | Elmer 绝对更新量 | 退出码 |
|---:|---|---|---|---:|---:|---|---:|---:|
| 12 | elmer（复用） | 1.0/2g/600.0 | 100/3000 | 19.93 | 15 | 2.737e-12 | 9.999e-10 | 0 |
| 12 | openfoam | 2.0/4g/3600.0 | 12000/— | 682.6 | 12000 | Ux=1.981e-13; Uy=1.645e-13; Uz=0.004515; p[1]=5.12e-12; p[2]=3.153e-12 | — | 0 |

| 网格每轴段数 | 输出数组 | 最大绝对差 | 单位 | 最大误差比 |
|---:|---|---:|---|---:|
| 12 | answer_velocity | 1e-09 | m/s | 6.25e-07 |
| 12 | answer_pressure | 7.666e-11 | Pa | 6.969e-10 |
| 12 | answer_density | 0 | kg/m3 | 0 |
| 12 | answer_dynamic_viscosity | 0 | Pa.s | 0 |
| 12 | answer_traction | 6.922e-11 | Pa | 6.293e-10 |
| 12 | answer_mean_pressure | 2.935e-11 | Pa | 2.668e-10 |
| 12 | answer_shear | 1.63e-12 | 1/s | 1.63e-10 |
| 12 | answer_force3 | 5.753e-11 | N | 5.656e-09 |
| 12 | answer_volume_flow3 | 6.935e-22 | m3/s | 6.935e-16 |
| 12 | answer_mass_flow3 | 6.935e-19 | kg/s | 6.935e-13 |
| 12 | answer_force4 | 5.833e-11 | N | 5.735e-09 |
| 12 | answer_volume_flow4 | 9.38e-22 | m3/s | 9.38e-16 |
| 12 | answer_mass_flow4 | 9.38e-19 | kg/s | 9.38e-13 |
| 12 | answer_volume_flow1 | 1.388e-17 | m3/s | 1.156e-14 |
| 12 | answer_mass_flow1 | 1.421e-14 | kg/s | 1.184e-14 |
| 12 | answer_volume_flow2 | 2e-09 | m3/s | 1.665e-06 |
| 12 | answer_mass_flow2 | 2e-06 | kg/s | 1.667e-06 |
