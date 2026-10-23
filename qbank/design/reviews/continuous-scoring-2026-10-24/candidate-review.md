# 连续评分独立考生审阅

范围：statements 模式。仅依据本轮白名单中的80题 instruction.md、DATA.md及共享 CONTRACT 快照；使用中性文本读取，重复条款去重核对，定向审阅评分与相关输出、压力和统计观测定义。没有读取作者代码、评分实现、实际case或隐藏reference。

结论：已逐题覆盖80题；最终快照无未关闭的评分发现。曾发现一处不改变分值的P3编辑不一致（CAND-001），现已复核关闭。此结论仅适用于本快照的评分定义与关联观测语义，不是全题逐行物理审计。

本轮未包含、未复查samples；不推断样例或隐藏参考数值正确，不证明资源可达或实现与文档一致。

共同规则已核对：各输出的每个标量分量、各请求时刻分别沿空间计算NRMSE，跨量/分量/时间取最大；所有请求初始帧、边界和零值参与；E≤0.05得1、0.05<E<0.10线性降分、E≥0.10得0，正式case算术平均。失败/非法输出零分与基础设施错误区分明确。逐题scale_floor及原文行号保存在JSON。

特例已核对：23道CFDCodeBench点观测题使用公开weights；4道不可压压力观测分别减去本时刻加权均值；2道温度题分别减固定背景20和1；多相两题仅压力参考RMS减pressure_reference，分子保留绝对压力误差。圆管特征值题固定N=1、等点权。统计题先空间平均后在含双端点的离散时间网格等权统计，完整张量按标量分量分别评价。

最终 CONTRACT 第457行已重读：CLI退出码0满分、1未满分（含部分分）、2基础设施错误；实际分值读取JSON.score。其SHA256为 
dbf943c664f1490c669c069fb59331ccd972f1adeeb76f2965ac01aa1f8b844f
.

CAND-001（P3，已关闭）：cc-pipe-flow-disk-evp 的DATA原权重用途描述与instruction等点权文字不一致；因N=1原本不改变分值。最终复读DATA.md:56，已明确等点权重且输入weights不影响本题分值，与instruction.md:31一致。最终DATA SHA256：0e57883e96510507ab7302fb5cbe6609c195f287376fc34ac92b4010a57869c3。

| 题目 | 空间权重 | 特例 | 结论 |
|---|---|---|---|
| darcy-flow-2d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| heat-conduction-steady-2d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| diffusion-sorption-1d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| heat-conduction-transient-2d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| reaction-diffusion-1d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| reaction-diffusion-2d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| advection-1d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| shallow-water-2d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| burgers-1d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| incompressible-navier-stokes-2d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| compressible-navier-stokes-1d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| compressible-navier-stokes-2d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| compressible-navier-stokes-3d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| newtonian-incompressible-steady-2d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| newtonian-incompressible-steady-3d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| cc-1d-burgers-equation | explicit_input_weights | direct | reviewed_no_scoring_blocker_found |
| cc-1d-diffusion | explicit_input_weights | direct | reviewed_no_scoring_blocker_found |
| cc-1d-euler-shock-tube | explicit_input_weights | direct | reviewed_no_scoring_blocker_found |
| cc-1d-linear-convection | explicit_input_weights | direct | reviewed_no_scoring_blocker_found |
| cc-1d-nonlinear-convection | explicit_input_weights | direct | reviewed_no_scoring_blocker_found |
| cc-2d-burgers-equation | explicit_input_weights | direct | reviewed_no_scoring_blocker_found |
| cc-2d-convection | explicit_input_weights | direct | reviewed_no_scoring_blocker_found |
| cc-2d-diffusion | explicit_input_weights | direct | reviewed_no_scoring_blocker_found |
| cc-2d-inviscid-burgers | explicit_input_weights | direct | reviewed_no_scoring_blocker_found |
| cc-2d-laplace-equation | explicit_input_weights | direct | reviewed_no_scoring_blocker_found |
| cc-2d-linear-convection | explicit_input_weights | direct | reviewed_no_scoring_blocker_found |
| cc-2d-navier-stokes-cavity | explicit_input_weights | pressure_weighted_demean_per_time | reviewed_no_scoring_blocker_found |
| cc-2d-navier-stokes-channel | explicit_input_weights | direct | reviewed_no_scoring_blocker_found |
| cc-2d-poisson-equation | explicit_input_weights | direct | reviewed_no_scoring_blocker_found |
| cc-2d-steady-heat-equation | explicit_input_weights | fixed_temperature_background_20 | reviewed_no_scoring_blocker_found |
| cc-2d-unsteady-heat-equation | explicit_input_weights | fixed_temperature_background_1 | reviewed_no_scoring_blocker_found |
| cc-fully-developed-turbulent-channel-flow | explicit_input_weights | direct | reviewed_no_scoring_blocker_found |
| cc-lid-driven-cavity | explicit_input_weights | pressure_weighted_demean_per_time | reviewed_no_scoring_blocker_found |
| cc-flow-past-circular-cylinder | explicit_input_weights | direct | reviewed_no_scoring_blocker_found |
| cc-1d-kdv-burgers-equation | explicit_input_weights | direct | reviewed_no_scoring_blocker_found |
| cc-2d-rayleigh-benard-convection | explicit_input_weights | pressure_weighted_demean_per_time | reviewed_no_scoring_blocker_found |
| cc-2d-shear-flow-with-tracer | explicit_input_weights | pressure_weighted_demean_per_time | reviewed_no_scoring_blocker_found |
| cc-pipe-flow-disk-evp | equal_positions | direct | reviewed_no_scoring_blocker_found |
| cc-lane-emden-equation | explicit_input_weights | direct | reviewed_no_scoring_blocker_found |
| newtonian-incompressible-transient-2d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| newtonian-incompressible-transient-3d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| generalized-newtonian-incompressible-steady-2d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| generalized-newtonian-incompressible-transient-2d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| generalized-newtonian-incompressible-steady-3d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| generalized-newtonian-incompressible-transient-3d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| newtonian-isothermal-compressible-steady-2d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| newtonian-isothermal-compressible-transient-2d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| newtonian-isothermal-compressible-steady-3d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| newtonian-isothermal-compressible-transient-3d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| newtonian-lowmach-steady-2d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| newtonian-lowmach-transient-2d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| newtonian-lowmach-steady-3d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| newtonian-lowmach-transient-3d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| inviscid-compressible-steady-2d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| inviscid-compressible-transient-2d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| inviscid-compressible-steady-3d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| inviscid-compressible-transient-3d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| newtonian-compressible-transient-2d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| newtonian-compressible-transient-3d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| rans-steady-2d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| rans-steady-3d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| urans-transient-3d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| resolved-statistics-3d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| isothermal-rans-3d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| thermal-rans-3d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| thermal-urans-3d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| thermal-statistics-3d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| immiscible-interface-2d | equal_positions | pressure_reference_offset_denominator_only | reviewed_no_scoring_blocker_found |
| immiscible-interface-3d | equal_positions | pressure_reference_offset_denominator_only | reviewed_no_scoring_blocker_found |
| gas-film | equal_positions | direct | reviewed_no_scoring_blocker_found |
| fully-wet-steady | equal_positions | direct | reviewed_no_scoring_blocker_found |
| fully-wet-transient | equal_positions | direct | reviewed_no_scoring_blocker_found |
| wetting-drying | equal_positions | direct | reviewed_no_scoring_blocker_found |
| transition-gas | equal_positions | direct | reviewed_no_scoring_blocker_found |
| free-molecular | equal_positions | direct | reviewed_no_scoring_blocker_found |
| viscoelastic-steady | equal_positions | direct | reviewed_no_scoring_blocker_found |
| viscoelastic-transient | equal_positions | direct | reviewed_no_scoring_blocker_found |
| newtonian-compressible-steady-2d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| newtonian-compressible-steady-3d | equal_positions | direct | reviewed_no_scoring_blocker_found |
| compressible-thermal-rans-3d | equal_positions | direct | reviewed_no_scoring_blocker_found |

全部实际文件SHA256、白名单匹配结果、逐题评分证据行与scale_floor见 candidate-review.json。共享CONTRACT在每题记录中保留，以便逐题追溯。

