# 暂缓处理的三道题

2026-10-19，按用户决定记录以下问题，暂不修题、补算、重跑或解除工具门禁。后续工作聚焦其余八道 PDEBench 来源题目。本记录不把局部来源疑点解释为整个数据族已证不适用。

## 一维反应扩散：reaction-diffusion-1d（2026-10-20恢复直接制数）

用户已明确：忠实使用PDEBench发布数据，不补算或替上游认证数值精度。现有方程、周期边界及时间范围与补充材料D.2基本定义对应；历史停滞记录不再作为全族门禁。工具允许生成原始reference及引用example，新的20条试验验收见本题author/data-evidence/direct-20261020/。来源参数、网格、时间与转换完整性仍须核验；当前不改题面或评分、不启动模型。Darcy和二维不可压缩流继续暂缓。

## Darcy：darcy-flow-2d

- 官方补充材料 D.4 描述稳态问题和零 Dirichlet 边界；当前题面包含“边界值等于相邻原单元平均值一半”及系数双线性重建，属于额外的数学/采样解释。
- 既往作者记录还指出部分发布快照可能未达到稳态；当前工具不再独立求稳态修正参考。
- 尚缺：区分论文数学定义、对应发布数据的离散边界实现、我们新增的连续解释，以及具体轨迹的稳态适用性。不能认定直接恢复零边界即可解决全部来源问题。
- 暂不改变题面、自动修正参考或以离散残差替代连续精度证明。
- 依据：[题面](../../../01-prescribed-pdes/1.1-elliptic/darcy-flow-2d/instruction.md)、[既往来源记录](../../../01-prescribed-pdes/1.1-elliptic/darcy-flow-2d/author/data-evidence/reference/DESIGN.md)。

## 二维不可压缩流：incompressible-navier-stokes-2d（2026-10-20恢复直接制数）

用户授权先核对实际分片的黏度、壁面、强迫耦合、坐标/分量及首帧约定，对应成立后沿用发布速度轨迹。不重算投影、不修正参考，不要求连续解与离散参考完全一致。

已读取分片133280的实际配置和布局：NU=.01、domain_size=[1,1]、grid_size=[512,512]、velocity_extrapolation=ZERO、particle_extrapolation=BOUNDARY、force_extrapolation=ZERO；速度4×1000×512×512×2，标量及force布局一致，实际初帧时刻为0。固定源码说明χf耦合、交错场中心采样与预推进首帧保存；与题面数据映射相应，精确历史生成commit仍不由配置证明。历史单位域尺度证据保留，不把其余数值差异作为精度认证门槛。

工具逐分片严格核验配置与布局，解除全题拦截；输入保留原速度首帧、标量首帧、静态force，参考保留选中速度帧，不执行投影或参考修正。新20条/2example记录见本题author/data-evidence/direct-20261020/；是否安装就绪以该报告为准。Darcy继续暂缓。

## 当前工具状态与后续边界

以下是2026-10-19历史状态；一维反应扩散已按上节恢复，二维不可压缩流也已按上节恢复，Darcy仍使用全题门禁。原三题当时使用保守的全题门禁：可以取得 input 和私有 candidate.h5，不生成可判分 reference、example 或评测包。这个实现状态不等于三族全部数据已被逐例否决；解除门禁需要后续独立处理本记录，不属于此次剩余八题工作。

其余八题为：平流、Burgers、一维/二维/三维可压缩流、吸附扩散、二维反应扩散、浅水。当前真实 DaRUS 制数及容器判题验收只覆盖前三者中的平流、Burgers、一维可压缩流的固定小批周期配置；另五题仅有离线格式覆盖，见[验收记录](REPORT.md)。

官方对照：[PDEBench 补充材料 D.2/D.4/D.6](https://proceedings.neurips.cc/paper_files/paper/2022/file/0a9747136d411fb83f0cf81820d44afb-Supplemental-Datasets_and_Benchmarks.pdf)、[固定版本不可压缩流生成器](https://github.com/pdebench/PDEBench/blob/4ff3e3a4aa1561721b5571fa3a048a0a463e0568/pdebench/data_gen/src/sim_ns_incomp_2d.py)。当前操作见[工具 README](../../../../src/utils/PDEBench/README.md)。
