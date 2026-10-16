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
| [pdebench/data_gen/data_gen_NLE/AdvectionEq/advection_multi_solution_Hydra.py](https://github.com/pdebench/PDEBench/blob/4ff3e3a4aa1561721b5571fa3a048a0a463e0568/pdebench/data_gen/data_gen_NLE/AdvectionEq/advection_multi_solution_Hydra.py) | `cd66448573b7510500b2c9622617669a8789c2d7cb28d368c30e192c03502f46` |
| [pdebench/data_gen/data_gen_NLE/AdvectionEq/config/multi/config.yaml](https://github.com/pdebench/PDEBench/blob/4ff3e3a4aa1561721b5571fa3a048a0a463e0568/pdebench/data_gen/data_gen_NLE/AdvectionEq/config/multi/config.yaml) | `61948db1c7832c434ed84b12260eb1f6f33f5e349a61a399ddf8efaff2bbb8f0` |

## 发布配置对应

| 发布文件 | DaRUS datafile ID | MD5（来源身份） |
|---|---:|---|
| `1D_Advection_Sols_beta0.1.hdf5` | 255672 | `b4be2fc3383f737c76033073e6d2ccfb` |
| `1D_Advection_Sols_beta0.2.hdf5` | 255671 | `d47b52c1be4b6bcaa8748a8df2f5fbb8` |
| `1D_Advection_Sols_beta0.4.hdf5` | 255674 | `d595bbfd2c659df995a93cd40d6ea568` |
| `1D_Advection_Sols_beta0.7.hdf5` | 255666 | `f89030c240a1e90b55649776854a84c2` |
| `1D_Advection_Sols_beta1.0.hdf5` | 255675 | `1fe41923a4123db55bf4e89bea32e142` |
| `1D_Advection_Sols_beta2.0.hdf5` | 255677 | `0e9beff98693089c38e213a1f2b9ac43` |
| `1D_Advection_Sols_beta4.0.hdf5` | 255676 | `a87b03ff425496360e2732921805f47d` |
| `1D_Advection_Sols_beta7.0.hdf5` | 255664 | `72a286ad2fcba574bd20bc045ba82d58` |

模型标识为 `advection_1d`。参数与输入场对应关系以 [DATA.md](../DATA.md) 为准；文件标签不作为程序输入，不允许由文件名隐式改写参数。

## 当前参考政策

当前数学定义以 instruction.md 与 DATA.md 为准。来源身份、实际坐标、完整初值、时间轴和族相关一致性逐例核对。保留经结构与族相关一致性审核的官方数值轨迹作为数值参考，局限写入逐例证书。数值参考不等于精确连续真解；误差阈值、连续误差与执行资源尚未校准。

## 当前采样与源实现差异

题面直接给实际速度 c。当前源码采用 c=β；[2023 年缩放修正](https://github.com/pdebench/PDEBench/commit/ac1ed78bac6bf79f8d8dba863df7d292a1e1f1ed)以前存在 c=2β 的历史约定。当前选定轨迹逐例与本题分片常数初值的精确周期平移积分比较，差异保存在证书；不改动旧题 1D_Advection_Sols_beta0.4 的契约。

这是连续 PDE 求解题，提交程序自行选择数值方法。输入的重建规则与输出观测量是本题数学契约；源随机场、离散更新及连续重建不能自动视为同一对象。生成算法和参考策略只在作者材料中说明，不要求参赛程序复现。

## 参赛材料修订

公开题面直接声明实际传播速度 c，生成器缩放历史仅保留在本文。

## 后续评测阶段

统一获取、缓存、选样冻结和协议转换入口已在 src/utils/PDEBench/prepare.py 实现。参考收敛/误差审核、误差阈值和执行资源仍需补充。现有参考策略已固定；发布前仍须确认其对当前连续契约的精度，并决定是否需进一步独立重算。样例与测试分组见 SAMPLES.md、TEST-CASES.md；本地输入和参考准备状态以统一工具生成的 ../author/preparation.json 为准。官方原始对照保存在私有 official-candidate.h5；仅经源对齐审核或修正的参考写入 reference.h5；现有评分与资源配置用于试运行；正式参考精度和资源预算仍须校准，不能据此宣称正式评测已发布。
