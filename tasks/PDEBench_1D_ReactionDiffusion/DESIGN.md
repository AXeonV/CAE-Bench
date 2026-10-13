# 来源核对与题面设计

## 固定来源

- 数据集：[PDEBench / DaRUS V8](https://darus.uni-stuttgart.de/dataset.xhtml?persistentId=doi%3A10.18419%2FDARUS-2986&version=8.0)，DOI `10.18419/DARUS-2986`，数据许可 CC BY 4.0；检查日期 2026-10-13。数据许可不自动覆盖生成代码许可。
- 方程背景：[官方论文补充材料 D 节](https://proceedings.neurips.cc/paper_files/paper/2022/file/0a9747136d411fb83f0cf81820d44afb-Supplemental-Datasets_and_Benchmarks.pdf)。论文、配置、源码与发布数据分别作为证据，不假定四者完全一致。
- 源码版本：[`4ff3e3a4aa1561721b5571fa3a048a0a463e0568`](https://github.com/pdebench/PDEBench/commit/4ff3e3a4aa1561721b5571fa3a048a0a463e0568)。
- 下载 CSV：[固定版本发布入口清单](https://github.com/pdebench/PDEBench/blob/4ff3e3a4aa1561721b5571fa3a048a0a463e0568/pdebench/data_download/pdebench_data_urls.csv)。实际支持范围取本次 DaRUS V8 元数据清单；CSV 中的历史入口及未发布生成器配置不自动纳入。

只检查文本配置、源码和发布元数据；除不可压缩流代表文件的有限头部读取外，未下载 HDF5 数据。因此这里不宣称已核验所有轨迹内容或误差。MD5 记录官方发布身份，后续提取样本还须另存实际数组哈希。

## 核对过的源码

以下源码由官方 PDEBench 项目提供；NLE 生成器由 NEC Laboratories Europe GmbH 开发。本仓库仅记录数学契约与来源分析，不复制生成器代码。

| 源码/配置 | 本次读取文本 SHA-256 |
|---|---|
| [pdebench/data_gen/data_gen_NLE/ReactionDiffusionEq/reaction_diffusion_multi_solution_Hydra.py](https://github.com/pdebench/PDEBench/blob/4ff3e3a4aa1561721b5571fa3a048a0a463e0568/pdebench/data_gen/data_gen_NLE/ReactionDiffusionEq/reaction_diffusion_multi_solution_Hydra.py) | `d0ed4a424d0355e585593ca34fccc7ecb1d4f04ac282c75e45064b5dc42cc9d2` |
| [pdebench/data_gen/data_gen_NLE/ReactionDiffusionEq/config/multi/config.yaml](https://github.com/pdebench/PDEBench/blob/4ff3e3a4aa1561721b5571fa3a048a0a463e0568/pdebench/data_gen/data_gen_NLE/ReactionDiffusionEq/config/multi/config.yaml) | `81dde6aa8a5f1bf4eed730e7ec37056cb4501b2e9b5c739d8a2fea96f7809875` |

## 发布配置对应

| 发布文件 | DaRUS datafile ID | MD5（来源身份） |
|---|---:|---|
| `ReacDiff_Nu0.5_Rho10.0.hdf5` | 133178 | `ff7c724b18e7ebe02e19c179852f48ee` |
| `ReacDiff_Nu0.5_Rho1.0.hdf5` | 133177 | `69a429239778d529cd419ed5888ea835` |
| `ReacDiff_Nu0.5_Rho2.0.hdf5` | 133179 | `ac907daa7e483d203a5c77567cdea561` |
| `ReacDiff_Nu0.5_Rho5.0.hdf5` | 133180 | `fb149e7540d8977af158bb8fec1048a3` |
| `ReacDiff_Nu1.0_Rho10.0.hdf5` | 133182 | `a94e65631881a27ddae3ef74caf53093` |
| `ReacDiff_Nu1.0_Rho1.0.hdf5` | 133181 | `bd73c2f3448d03e95e98c3831fc8fa70` |
| `ReacDiff_Nu1.0_Rho2.0.hdf5` | 133183 | `112c01a76447162bd67c8c1073f58ca2` |
| `ReacDiff_Nu1.0_Rho5.0.hdf5` | 133184 | `fa224c9d143de37ac6914d391e70f425` |
| `ReacDiff_Nu2.0_Rho10.0.hdf5` | 133186 | `a3e25a9fb8a99f010352ad3dd1afd596` |
| `ReacDiff_Nu2.0_Rho1.0.hdf5` | 133185 | `925a7e2c9b9e40ad2dd44b7002ec882b` |
| `ReacDiff_Nu2.0_Rho2.0.hdf5` | 133187 | `426353b241acfbc64067acb1bdc80ade` |
| `ReacDiff_Nu2.0_Rho5.0.hdf5` | 133188 | `f2890bdac5103a3b78fac5f80e57b760` |
| `ReacDiff_Nu5.0_Rho10.0.hdf5` | 133190 | `264c80af0e2a6cc1f70e87275e0f6ac4` |
| `ReacDiff_Nu5.0_Rho1.0.hdf5` | 133189 | `0ed75b55f61bec11c47d379e34959e54` |
| `ReacDiff_Nu5.0_Rho2.0.hdf5` | 133191 | `f927f5d85f2e9bd97dff31b4dab051ae` |
| `ReacDiff_Nu5.0_Rho5.0.hdf5` | 133192 | `c9c26e2b5f2d4bf5bcbbd4ba34fefd5e` |

模型标识为 `reaction_diffusion_1d`。参数与输入场对应关系以 [DATA.md](DATA.md) 为准；文件标签不作为程序输入，不允许由文件名隐式改写参数。

## 差异与本题选择

当前 V8 发布目录包含 16 个 Train 参数文件。源码 CSV 仍列有额外 react 测试文件及 ν=10，当前发布清单未包含这些文件，本题不把它们加入范围。源码采用分裂反应更新；本题求连续耦合方程，不要求复现分裂步骤。

这是连续 PDE 求解题，官方数值生成算法不是提交必须复现的算法。单元平均/点采样的连续初值定义是本题新增的明确契约，不宣称恢复源生成器原始随机场。物理参数没有证据时不从文件名推断；任何转换均须满足这里已选定的方程和采样含义。

## 后续评测阶段

统一获取、缓存、选样冻结和协议转换入口已在 src/utils/PDEBench/prepare.py 实现。参考收敛/误差审核、误差阈值和执行资源仍需补充。应先确认参考计算解的是同一数学问题，再决定是否采用官方轨迹或独立参考。样例与测试分组见 SAMPLES.md、TEST-CASES.md；本地输入和参考准备状态以统一工具生成的 author/preparation.json 为准。官方对照保存在私有 official-candidate.npz，未经审核不作为 reference.npz；尚未校准 judge-config 和高维运行资源，不能直接组装正式评测。
