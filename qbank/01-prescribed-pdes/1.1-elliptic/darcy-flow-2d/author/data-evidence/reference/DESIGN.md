# 来源核对与题面设计

## 固定来源

- 数据集：[PDEBench / DaRUS V8](https://darus.uni-stuttgart.de/dataset.xhtml?persistentId=doi%3A10.18419%2FDARUS-2986&version=8.0)，DOI `10.18419/DARUS-2986`，数据许可 CC BY 4.0；检查日期 2026-10-13。数据许可不自动覆盖生成代码许可。
- 方程背景：[官方论文补充材料 D 节](https://proceedings.neurips.cc/paper_files/paper/2022/file/0a9747136d411fb83f0cf81820d44afb-Supplemental-Datasets_and_Benchmarks.pdf)。论文、配置、源码与发布数据分别作为证据，不假定四者完全一致。
- 审核使用的源码版本（不证明所有发布文件由该提交生成）：[`4ff3e3a4aa1561721b5571fa3a048a0a463e0568`](https://github.com/pdebench/PDEBench/commit/4ff3e3a4aa1561721b5571fa3a048a0a463e0568)。
- 下载 CSV：[固定版本发布入口清单](https://github.com/pdebench/PDEBench/blob/4ff3e3a4aa1561721b5571fa3a048a0a463e0568/pdebench/data_download/pdebench_data_urls.csv)。实际支持范围取本次 DaRUS V8 元数据清单；CSV 中的历史入口及未发布生成器配置不自动纳入。

题面设计阶段核对了文本配置、源码和发布元数据；随后由统一工具按需读取发布 HDF5 的选定样本和帧。实际选样、输入哈希与准备状态见运行后生成的 selection.json、../../preparation.json 和私有 certificate.json。读取和结构转换不构成轨迹误差验证；官方整文件 MD5 记录发布身份，远程子集的完整性范围另见工具说明。

## 核对过的源码

以下源码由官方 PDEBench 项目提供；NLE 生成器由 NEC Laboratories Europe GmbH 开发。本仓库仅记录数学契约与来源分析，不复制生成器代码。

| 源码/配置 | 本次读取文本 SHA-256 |
|---|---|
| [pdebench/data_gen/data_gen_NLE/ReactionDiffusionEq/reaction_diffusion_2D_multi_solution_Hydra.py](https://github.com/pdebench/PDEBench/blob/4ff3e3a4aa1561721b5571fa3a048a0a463e0568/pdebench/data_gen/data_gen_NLE/ReactionDiffusionEq/reaction_diffusion_2D_multi_solution_Hydra.py) | `36376e7e4f2bafa3bade18c7a7ceeca6fc78bd7897a9eb06e688cce880e86fe8` |
| [pdebench/data_gen/data_gen_NLE/ReactionDiffusionEq/config/multi/config_2D.yaml](https://github.com/pdebench/PDEBench/blob/4ff3e3a4aa1561721b5571fa3a048a0a463e0568/pdebench/data_gen/data_gen_NLE/ReactionDiffusionEq/config/multi/config_2D.yaml) | `903131b296f999bb8c85892c5140a7432fd24134c3e0bd6452076de013a63238` |
| [pdebench/data_gen/data_gen_NLE/utils.py](https://github.com/pdebench/PDEBench/blob/4ff3e3a4aa1561721b5571fa3a048a0a463e0568/pdebench/data_gen/data_gen_NLE/utils.py) | `fc3a848a12e79e89bb53898944fe96ccbc44236b22ce4b6a705eda00a8018d71` |

## 发布配置对应

| 发布文件 | DaRUS datafile ID | MD5（来源身份） |
|---|---:|---|
| `2D_DarcyFlow_beta0.01_Train.hdf5` | 133217 | `d05c287d4c0b7d3178b0097084238251` |
| `2D_DarcyFlow_beta0.1_Train.hdf5` | 133218 | `294f9a03a4aa16b0e386469ca8b471be` |
| `2D_DarcyFlow_beta1.0_Train.hdf5` | 133219 | `81694ed31306ff2e5f6b76349b0b4389` |
| `2D_DarcyFlow_beta10.0_Train.hdf5` | 133220 | `a7f23cf8011fc211b180828af39b7d1a` |
| `2D_DarcyFlow_beta100.0_Train.hdf5` | 133221 | `7c09f3b1bb097737d3fd52ffb0c6f1c8` |

模型标识为 `darcy_flow_2d`。参数与输入场对应关系以 [DATA.md](../DATA.md) 为准；文件标签不作为程序输入，不允许由文件名隐式改写参数。

## 当前参考政策（2026-10-20）

[本次核查](../direct-20261020/REPORT.md)将论文数学条件、源离散实现、数据格式与本题采样约定分开记录。题面恢复论文 D.4 的四边零 Dirichlet；源程序的零虚单元是离散闭合，不再提升为边界面值等于相邻单元平均的一半。

直接工具按实际 beta 属性、源标签、坐标、数组布局及系数值域检查后使用发布单帧 state。未认证稳态收敛作为来源局限保留，不再作为全族拦截；不独立求平衡态、不改变参考、不筛掉样本。题面的系数双线性重建与单元平均输出是显式采样约定，不等于声明发布数据精确求解该连续问题。精度、阈值和求解资源没有因此获得独立认证。

## 历史参考策略

2026-10-13 的旧流程曾独立求解算术面系数、零外部单元的离散平衡态，并记录发布快照与修正残差；这是旧参考生产历史，不能作为现行直接取用发布参考的实施说明，也不能将其结果标为原始 DaRUS 数据。此前“非局部边界”是将离散闭合解释成连续边界的设计，现已撤销。旧 selection、证据和修正产物保留历史身份，不能直接重新绑定到修订后的题面。

本次只核查五档各一个已缓存实际样本并验证转换链，没有制作或安装20个正式case，也没有进行模型评测。批次就绪以本题后续独立的选择、安装及验收记录为准。
