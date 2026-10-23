# 第十九章：22 个真实来源的修复题建设清单

用户授权：将已筛选的22个来源落实为22道可实际运行、问题描述完整的源码修复题；已有Chrono题计入22道。目标时段为香港时间2026-10-23今夜，持续工作直到完成。当前模型Benchmark不是本轮默认交付项，不为验收自动调用收费考生。

本表是本批题号、来源与完成状态的唯一清单；候选筛选不是完成证明。各题详细版本、数据与实际验收证据进入本题author材料。本轮执行状态与续作入口为`runs/authoring/repair-22/status.json`。

## 验收口径

每题完成须同时满足：

1. 题面与DATA公开说明问题族、物理／数学语义、API及修改边界、全部输入输出、资源和评分；通过独立设计与考生审阅。
2. 使用固定真实源码基线，离线公开包可安装、构建及执行；不将作者自编替代程序冒充原求解器。
3. 实际重放缺陷版与参考修复版，证明目标错误可检出，非触发／回归行为得到检验。
4. 参考由有出处的实际求解器或适用的公开解析依据生产，并完成独立正确性核查；容差有数值依据。
5. 全部正式case与公开样例通过实际数据审计；可信编译及逐例判题真实执行，参考提交通过全部所选case。
6. 数据按现有HF流程入池并固定提交取回核验；公开／隐藏身份明确。验收证据覆盖当前最终版本。

未满足时保留具体缺口，不以目录、模板、上游合并、静态检查或历史上游成绩标记完成。真实源码故障、参考不充分或构建资源问题不能靠悄悄缩减目标或虚构验收解决。

## 逐题清单

题号为本轮规划分配；独立设计审阅后若需调整，保持来源一一对应并记录原因。slug避免仓库名成为物理语义。

| 编号 | slug／拟题 | 原始来源 | 任务及独立核查方向 | 状态 |
|---|---|---|---|---|
| 19.1.1 | constrained-assembly-repair／距离约束加速度与反力 | projectchrono/chrono#846 | 瞬时约束动力学、位置速度回归；约束微分与闭式单摆 | 已完成；[验收记录](reviews/chrono-846-repair-implementation.md) |
| 19.1.2 | hysteretic-trial-state-repair／滞回材料试探状态恢复 | OpenSees/OpenSees#1817 | 试探／提交／回滚后的应力与切线；分段本构和状态序列对照 | 已完成；[验收记录](../19-solver-repair/19.1-constraints/hysteretic-trial-state-repair/author/README.md) |
| 19.2.1 | spatial-beam-transform-repair／空间梁方向变换 | KratosMultiphysics/Kratos#14657 | 局部全局变换、挠度与旋转协变；闭式梁及独立矩阵核对 | 已完成；[验收记录](../19-solver-repair/19.2-operators/spatial-beam-transform-repair/author/README.md) |
| 19.2.2 | grand-potential-derivatives-repair／巨势烧结材料一致导数 | idaholab/moose#30236 | 材料导数及Jacobian；独立符号／数值微分和残量测试 | 待实施 |
| 19.3.1 | migration-soret-scaling-repair／电迁移与热扩散密度缩放 | ElmerCSC/elmerfem#870 | 漂移／热扩散弱式、密度缩放；解析稳态与单位一致性 | 待实施 |
| 19.3.2 | surface-flow-constraint-repair／表面反应管流物种约束 | Cantera/cantera#1655 | 质量分数代数约束与物种排序；守恒及独立简单反应工况 | 已完成；[验收记录](../19-solver-repair/19.3-transport/surface-flow-constraint-repair/author/README.md) |
| 19.3.3 | two-temperature-state-repair／双温等离子体状态方程 | Cantera/cantera#1872 | 电子分压及固定密度／压力路径；混合理想气体状态关系 | 已完成；[验收记录](../19-solver-repair/19.3-transport/two-temperature-state-repair/author/README.md) |
| 19.3.4 | multisite-surface-concentration-repair／多占位表面浓度 | Cantera/cantera#1996 | 多位点占据、浓度与表面反应；位点平衡及独立反应核对，保留两项关联修复范围 | 已完成；[验收记录](../19-solver-repair/19.3-transport/multisite-surface-concentration-repair/author/README.md) |
| 19.3.5 | reconstructed-energy-repair／可压缩流能量重构 | su2code/SU2#2602 | 重构一致性与稳定性；状态恒等关系及收敛流场，十步回归不作物理参考 | 待实施 |
| 19.3.6 | deformed-tangential-boundary-repair／变形边界切向约束 | geodynamics/aspect#6818 | 当前几何法向与切向速度；解析几何／流场，公开限制AMG支持范围 | 待实施 |
| 19.4.1 | graded-electrode-inventory-repair／梯度电极锂库存 | pybamm-team/PyBaMM#5810 | 空间加权积分与电极库存观测；独立积分，区分观测和演化误差 | 已完成；[验收记录](../19-solver-repair/19.4-observations/graded-electrode-inventory-repair/author/README.md) |
| 19.4.2 | diffusion-element-heat-repair／扩散元件电压与耗散 | pybamm-team/PyBaMM#5859 | 扩散过电势和不可逆热；独立能量账本与电路极限 | 已完成；[验收记录](../19-solver-repair/19.4-observations/diffusion-element-heat-repair/author/README.md) |
| 19.4.3 | hysteresis-heat-repair／开路电势滞回热源 | pybamm-team/PyBaMM#3867 | 平衡与分支OCP的能量差；明确参数语义及独立循环功核对 | 已完成；[验收记录](../19-solver-repair/19.4-observations/hysteresis-heat-repair/author/README.md) |
| 19.4.4 | granular-pair-stress-repair／颗粒成对力应力统计 | lammps/lammps#4219 | 成对贡献与累计力的区别；独立virial及小颗粒系统 | 已完成；[验收记录](../19-solver-repair/19.4-observations/granular-pair-stress-repair/author/README.md) |
| 19.4.5 | wall-heat-flux-repair／近壁热流离散与观测 | su2code/SU2#2347 | 边界和后处理热流一致；解析温度梯度与能量平衡 | 待实施 |
| 19.4.6 | solid-fluid-energy-observation-repair／固流传热能量统计 | idaholab/moose#22074 | 固／流分区体积分与能量观测；独立积分与瞬态／稳态范围核对 | 待实施 |
| 19.5.1 | point-ownership-repair／域外点归属与外推 | FEniCS/dolfinx#4450 | 单元内外归属与可选外推；精确几何分类及多单元回归 | 待实施 |
| 19.5.2 | nearest-projection-repair／单元插值最近投影回退 | precice/precice#1304 | 边面顶点选择及插值；精确最近点与重心坐标 | 已完成；[验收记录](../19-solver-repair/19.5-geometry/nearest-projection-repair/author/README.md) |
| 19.6.1 | dft-decimation-repair／非线性场频谱采样 | NanoComp/meep#2408 | DFT抽样与混叠；已知频率信号及真实场求解回归 | 待实施 |
| 19.6.2 | cylindrical-field-pml-repair／柱坐标场与PML | NanoComp/meep#2338 | 正负方位模态点源和吸收层；对称性及收敛场／通量 | 待实施 |
| 19.6.3 | complex-helmholtz-fmm-repair／复波数Helmholtz快速算子 | bempp/bempp-cl#20 | 复数接口与衰减核；独立核函数及稠密／FMM对照 | 待实施 |
| 19.6.4 | parallel-pml-reduction-repair／并行吸收层归约 | SPECFEM/specfem2d#661 | 并行归约与PML稳定性；进程数对照及独立波传播参考 | 待实施 |

## 批次安排与边界

优先形成状态／几何／观测等参考可精确核对的首批，再推进材料与反应、多物理、波动和大型CFD环境。共享同一求解器的题复用固定构建环境，但每题基线、修复子集和数据验收独立绑定；不得将其他题的修复或无关上游改动混入本题基线／参考补丁。同题的多个必要修复点可以共同组成完整修复，但须分别有可检出的工况，解释其共同服务的能力。

除已明确标为完成且链接验收记录的题外，其余项仍属规划或制作，不能因为出现在此表中被计为已完成。修复题仅公开规定范围；不把上游完整应用、GPU、MPI或尚未验证的模型组合默认为支持。必要缩限须仍保留原问题的实质修复能力，并经设计审阅。

独立规划审阅见`runs/design-review/repair-22-plan/report.md`：已逐题检查22项，未发现必须合并／拆分的实质重复；21道新增题尚需逐题范围卡，不能将本轮审阅称作规划全部通过。范围卡按真实源码和可执行性核查逐题补充，当前新增卡见[逐题范围](repair-22-scopes.md)。
