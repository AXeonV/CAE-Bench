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

模型标识为 `burgers_1d`。参数与输入场对应关系以 [DATA.md](DATA.md) 为准；文件标签不作为程序输入，不允许由文件名隐式改写参数。

## 差异与本题选择

论文和源码把文件名中的 Nu/epsilon 除以 π 后用于扩散通量。本题输入已给出 κ，Nu 标签仅保存在来源记录中。官方单元中心初始化不自动等于解析初值的积分；本题将采样值定义为单元平均值及分片常数初值，相关参考偏差必须另行审核。

这是连续 PDE 求解题，官方数值生成算法不是提交必须复现的算法。单元平均/点采样的连续初值定义是本题新增的明确契约，不宣称恢复源生成器原始随机场。物理参数没有证据时不从文件名推断；任何转换均须满足这里已选定的方程和采样含义。

## 参赛材料修订

来源文件 Nu 标签对应 κ=Nu/π。公开题面仅给实际系数 κ 的支持集合，程序不读取 Nu 标签。

## 后续评测阶段

统一获取、缓存、选样冻结和协议转换入口已在 src/utils/PDEBench/prepare.py 实现。参考收敛/误差审核、误差阈值和执行资源仍需补充。应先确认参考计算解的是同一数学问题，再决定是否采用官方轨迹或独立参考。样例与测试分组见 SAMPLES.md、TEST-CASES.md；本地输入和参考准备状态以统一工具生成的 author/preparation.json 为准。官方对照保存在私有 official-candidate.npz，未经审核不作为 reference.npz；尚未校准 judge-config 和高维运行资源，不能直接组装正式评测。
