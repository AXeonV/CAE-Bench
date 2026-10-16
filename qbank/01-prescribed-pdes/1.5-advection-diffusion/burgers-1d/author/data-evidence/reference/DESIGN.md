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
| [pdebench/data_gen/data_gen_NLE/BurgersEq/burgers_multi_solution_Hydra.py](https://github.com/pdebench/PDEBench/blob/4ff3e3a4aa1561721b5571fa3a048a0a463e0568/pdebench/data_gen/data_gen_NLE/BurgersEq/burgers_multi_solution_Hydra.py) | `905f01f0c60749665f9b55e0a58e4894df0c3fad62eea1b9a6ffbeae60ca6c50` |

## 发布配置对应

| 发布文件 | DaRUS datafile ID | MD5（来源身份） |
|---|---:|---|
| `1D_Burgers_Sols_Nu0.001.hdf5` | 268190 | `44cb784d5a07aa2b1c864cabdcf625f9` |
| `1D_Burgers_Sols_Nu0.002.hdf5` | 268193 | `edf1cd13622d151dfde3e4e5af7a95b4` |
| `1D_Burgers_Sols_Nu0.004.hdf5` | 268191 | `435e1fecb8a64a0b4563bb8d09f81c33` |
| `1D_Burgers_Sols_Nu0.01.hdf5` | 281363 | `e6d9a4f62baf9a29121a816b919e2770` |
| `1D_Burgers_Sols_Nu0.02.hdf5` | 268189 | `7c8c717a3a7818145877baa57106b090` |
| `1D_Burgers_Sols_Nu0.04.hdf5` | 281362 | `16f4c7afaf8c16238be157e54c9297c7` |
| `1D_Burgers_Sols_Nu0.1.hdf5` | 268185 | `660ba1008d3843bf4e28d2895eb607ce` |
| `1D_Burgers_Sols_Nu0.2.hdf5` | 268187 | `01d9333254dff2f3cad090b61f5cf695` |
| `1D_Burgers_Sols_Nu0.4.hdf5` | 268192 | `58327a6107e8f9defb5075677cc42533` |
| `1D_Burgers_Sols_Nu1.0.hdf5` | 281365 | `9021eba35332d127306f11ef84c1a60f` |
| `1D_Burgers_Sols_Nu2.0.hdf5` | 281364 | `70fe0c24d9313e70f6059e5212bdb3d7` |
| `1D_Burgers_Sols_Nu4.0.hdf5` | 268188 | `8af7f70166c00ffad377c80fa477d81f` |

模型标识为 `burgers_1d`。参数与输入场对应关系以 [DATA.md](../DATA.md) 为准；文件标签不作为程序输入，不允许由文件名隐式改写参数。

## 当前参考政策

当前数学定义以 instruction.md 与 DATA.md 为准。来源身份、实际坐标、完整初值、时间轴和族相关一致性逐例核对。保留经结构与族相关一致性审核的官方数值轨迹作为数值参考，局限写入逐例证书。数值参考不等于精确连续真解；误差阈值、连续误差与执行资源尚未校准。

## 当前采样与源实现差异

进入方程的扩散系数 κ=文件 Nu 标签/π；输入已经给实际 κ，不要求程序解析标签。初值是原单元内常数。工具逐例与独立 Cole–Hopf 积分比较并记录差异；该比较不自动成为判分阈值。

这是连续 PDE 求解题，提交程序自行选择数值方法。输入的重建规则与输出观测量是本题数学契约；源随机场、离散更新及连续重建不能自动视为同一对象。生成算法和参考策略只在作者材料中说明，不要求参赛程序复现。

## 参赛材料修订

来源文件 Nu 标签对应 κ=Nu/π。公开题面仅给实际系数 κ 的支持集合，程序不读取 Nu 标签。

## 后续评测阶段

统一获取、缓存、选样冻结和协议转换入口已在 src/utils/PDEBench/prepare.py 实现。参考收敛/误差审核、误差阈值和执行资源仍需补充。现有参考策略已固定；发布前仍须确认其对当前连续契约的精度，并决定是否需进一步独立重算。样例与测试分组见 SAMPLES.md、TEST-CASES.md；本地输入和参考准备状态以统一工具生成的 ../../preparation.json 为准。官方原始对照保存在私有 official-candidate.h5；仅经源对齐审核或修正的参考写入 reference.h5；现有评分与资源配置用于试运行；正式参考精度和资源预算仍须校准，不能据此宣称正式评测已发布。

## 独立参考准备

工具通过 Cole–Hopf 变换独立计算本题分片常数初值的连续解。先减去初始均值并作 Galilean 平移，初始势函数在各单元内为指数函数；与周期热核卷积可用高斯区间积分求值。单元平均由势函数对数在左右端点的差给出，保留非零均值。证书记录周期镜像尾界、扩大镜像和的一致性、质量与最大值原理检查；尾界不涵盖全部浮点误差。离线测试另与独立自适应积分比较，未使用官方正时间轨迹。
