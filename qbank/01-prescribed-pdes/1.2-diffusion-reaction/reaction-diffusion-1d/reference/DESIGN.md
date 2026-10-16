# 来源核对与题面设计

## 固定来源

- 数据集：[PDEBench / DaRUS V8](https://darus.uni-stuttgart.de/dataset.xhtml?persistentId=doi%3A10.18419%2FDARUS-2986&version=8.0)，DOI `10.18419/DARUS-2986`，数据许可 CC BY 4.0；检查日期 2026-10-13。数据许可不自动覆盖生成代码许可。
- 方程背景：[官方论文补充材料 D 节](https://proceedings.neurips.cc/paper_files/paper/2022/file/0a9747136d411fb83f0cf81820d44afb-Supplemental-Datasets_and_Benchmarks.pdf)。论文、配置、源码与发布数据分别作为证据，不假定四者完全一致。
- 审核使用的源码版本（不证明所有发布文件由该提交生成）：[`4ff3e3a4aa1561721b5571fa3a048a0a463e0568`](https://github.com/pdebench/PDEBench/commit/4ff3e3a4aa1561721b5571fa3a048a0a463e0568)。
- 下载 CSV：[固定版本发布入口清单](https://github.com/pdebench/PDEBench/blob/4ff3e3a4aa1561721b5571fa3a048a0a463e0568/pdebench/data_download/pdebench_data_urls.csv)。实际支持范围取本次 DaRUS V8 元数据清单；CSV 中的历史入口及未发布生成器配置不自动纳入。

题面设计阶段核对了文本配置、源码和发布元数据；随后由统一工具按需读取发布 HDF5 的选定样本和帧。实际选样、输入哈希与准备状态见运行后生成的 selection.json、../author/preparation.json 和私有 certificate.json。读取和结构转换不构成轨迹误差验证；官方整文件 MD5 记录发布身份，远程子集的完整性范围另见工具说明。

## 核对过的源码

以下源码由官方 PDEBench 项目提供；NLE 生成器由 NEC Laboratories Europe GmbH 开发。本仓库仅记录数学契约与来源分析，不复制生成器代码。

| 源码/配置 | 本次读取文本 SHA-256 |
|---|---|
| [pdebench/data_gen/data_gen_NLE/ReactionDiffusionEq/reaction_diffusion_multi_solution_Hydra.py](https://github.com/pdebench/PDEBench/blob/4ff3e3a4aa1561721b5571fa3a048a0a463e0568/pdebench/data_gen/data_gen_NLE/ReactionDiffusionEq/reaction_diffusion_multi_solution_Hydra.py) | `d0ed4a424d0355e585593ca34fccc7ecb1d4f04ac282c75e45064b5dc42cc9d2` |
| [pdebench/data_gen/data_gen_NLE/ReactionDiffusionEq/config/multi/config.yaml](https://github.com/pdebench/PDEBench/blob/4ff3e3a4aa1561721b5571fa3a048a0a463e0568/pdebench/data_gen/data_gen_NLE/ReactionDiffusionEq/config/multi/config.yaml) | `81dde6aa8a5f1bf4eed730e7ec37056cb4501b2e9b5c739d8a2fea96f7809875` |

## 发布配置对应

| 发布文件 | DaRUS datafile ID | MD5（来源身份） |
|---|---:|---|
| `ReacDiff_Nu0.5_Rho1.0.hdf5` | 133177 | `69a429239778d529cd419ed5888ea835` |
| `ReacDiff_Nu0.5_Rho2.0.hdf5` | 133179 | `ac907daa7e483d203a5c77567cdea561` |
| `ReacDiff_Nu0.5_Rho5.0.hdf5` | 133180 | `fb149e7540d8977af158bb8fec1048a3` |
| `ReacDiff_Nu0.5_Rho10.0.hdf5` | 133178 | `ff7c724b18e7ebe02e19c179852f48ee` |
| `ReacDiff_Nu1.0_Rho1.0.hdf5` | 133181 | `bd73c2f3448d03e95e98c3831fc8fa70` |
| `ReacDiff_Nu1.0_Rho2.0.hdf5` | 133183 | `112c01a76447162bd67c8c1073f58ca2` |
| `ReacDiff_Nu1.0_Rho5.0.hdf5` | 133184 | `fa224c9d143de37ac6914d391e70f425` |
| `ReacDiff_Nu1.0_Rho10.0.hdf5` | 133182 | `a94e65631881a27ddae3ef74caf53093` |
| `ReacDiff_Nu2.0_Rho1.0.hdf5` | 133185 | `925a7e2c9b9e40ad2dd44b7002ec882b` |
| `ReacDiff_Nu2.0_Rho2.0.hdf5` | 133187 | `426353b241acfbc64067acb1bdc80ade` |
| `ReacDiff_Nu2.0_Rho5.0.hdf5` | 133188 | `f2890bdac5103a3b78fac5f80e57b760` |
| `ReacDiff_Nu2.0_Rho10.0.hdf5` | 133186 | `a3e25a9fb8a99f010352ad3dd1afd596` |
| `ReacDiff_Nu5.0_Rho1.0.hdf5` | 133189 | `0ed75b55f61bec11c47d379e34959e54` |
| `ReacDiff_Nu5.0_Rho2.0.hdf5` | 133191 | `f927f5d85f2e9bd97dff31b4dab051ae` |
| `ReacDiff_Nu5.0_Rho5.0.hdf5` | 133192 | `c9c26e2b5f2d4bf5bcbbd4ba34fefd5e` |
| `ReacDiff_Nu5.0_Rho10.0.hdf5` | 133190 | `264c80af0e2a6cc1f70e87275e0f6ac4` |

模型标识为 `reaction_diffusion_1d`。参数与输入场对应关系以 [DATA.md](../DATA.md) 为准；文件标签不作为程序输入，不允许由文件名隐式改写参数。

## 当前参考政策

当前数学定义以 instruction.md 与 DATA.md 为准。来源身份、实际坐标、完整初值、时间轴和族相关一致性逐例核对。用同一连续 PDE 的独立加密计算替换有停滞问题的官方轨迹，并保留官方对照。数值参考不等于精确连续真解；误差阈值、连续误差与执行资源尚未校准。

## 当前采样与源实现差异

当前发布目录包含 16 个 Train 参数文件；未发布的 ν=10 或额外 react 测试配置不纳入题面。题目要求连续耦合方程，不要求分裂算法。部分官方轨迹远离 logistic 平衡仍停止变化，现已保留为对照，并以同一 PDE 的独立空间、时间加密计算生成参考，详情见下文。

这是连续 PDE 求解题，提交程序自行选择数值方法。输入的重建规则与输出观测量是本题数学契约；源随机场、离散更新及连续重建不能自动视为同一对象。生成算法和参考策略只在作者材料中说明，不要求参赛程序复现。

## 后续评测阶段

统一获取、缓存、选样冻结和协议转换入口已在 src/utils/PDEBench/prepare.py 实现。参考收敛/误差审核、误差阈值和执行资源仍需补充。现有参考策略已固定；发布前仍须确认其对当前连续契约的精度，并决定是否需进一步独立重算。样例与测试分组见 SAMPLES.md、TEST-CASES.md；本地输入和参考准备状态以统一工具生成的 ../author/preparation.json 为准。官方原始对照保存在私有 official-candidate.h5；仅经源对齐审核或修正的参考写入 reference.h5；现有评分与资源配置用于试运行；正式参考精度和资源预算仍须校准，不能据此宣称正式评测已发布。

## 独立参考准备

工具针对分片常数初值独立求解：原单元平均重复到加密单元，周期保守有限体积扩散用半离散矩阵的指数推进，logistic 反应用精确局部解，采用 Strang 分裂。在原输出单元上聚合加密值，比较联合及单独的空间、时间加密。每份参考保存实际差异与加密历史；准备目标为绝对差异 2×10⁻⁶，不是参赛判分阈值，也不是严格连续误差界。参考计算验证包括常数初值的精确 logistic 解及分片常数初值的独立热核 Fourier 积分。官方轨迹仍只作私有对照，未来评测须结合这些证据校准阈值。

## 官方轨迹审核后的修正

选定官方轨迹在正反应速率下出现远离 u=1 的后期停滞。审核记录了末区间平均值变化、名义反应平均和独立轨迹差异；不能把该停滞视为方程平衡。工具保留官方原始候选，以同一 PDE 的保守扩散和精确 logistic 反应独立重算答案。初始扩散层采用小步并逐渐增长，空间与时间独立加密时分别保持另一套分辨率/时序不变；证书保存实际加密差异。浮点粒度是可能原因，归档生成器版本和根因未被确定，不将原因推断当作事实。
