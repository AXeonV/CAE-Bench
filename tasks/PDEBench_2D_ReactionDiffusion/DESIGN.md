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
| [pdebench/data_gen/src/sim_diff_react.py](https://github.com/pdebench/PDEBench/blob/4ff3e3a4aa1561721b5571fa3a048a0a463e0568/pdebench/data_gen/src/sim_diff_react.py) | `1fb5e45e1302b8bd1bd3c0ad7e8ed4b7900eb9c0ef3a15d62051cd5f5bc2a2f8` |
| [pdebench/data_gen/configs/diff-react.yaml](https://github.com/pdebench/PDEBench/blob/4ff3e3a4aa1561721b5571fa3a048a0a463e0568/pdebench/data_gen/configs/diff-react.yaml) | `ac880dcd73e99b27c9df86eeb2ea69f5ac71378a78063a9cc349b080388ed942` |

## 发布配置对应

当前 V8 的 `2D/NS_incom` 下有 275 个 `ns_incom_inhom_2d_512-*.h5` 分片。分片不是不同方程或 275 个物理参数配置；种子和 batch 数由文件 config 决定。代表文件：datafile 133280，`ns_incom_inhom_2d_512-0.h5`，MD5 `54109d46f9c957317bd670ddb2068ac0`。

模型标识为 `reaction_diffusion_2d`。参数与输入场对应关系以 [DATA.md](DATA.md) 为准；文件标签不作为程序输入，不允许由文件名隐式改写参数。

## 差异与本题选择

源码状态位于单元中心，采用有限体积扩散；u 与 v 分别随机生成，必须同时提供初值。本题显式写出两个反应函数及单位尺度，不把此系统与一维 logistic 方程混用。发布轨迹与分片常数连续初值的误差须后续审核。

这是连续 PDE 求解题，官方数值生成算法不是提交必须复现的算法。单元平均/点采样的连续初值定义是本题新增的明确契约，不宣称恢复源生成器原始随机场。物理参数没有证据时不从文件名推断；任何转换均须满足这里已选定的方程和采样含义。

## 后续评测阶段

统一获取、缓存、选样冻结和协议转换入口已在 src/utils/PDEBench/prepare.py 实现。参考收敛/误差审核、误差阈值和执行资源仍需补充。应先确认参考计算解的是同一数学问题，再决定是否采用官方轨迹或独立参考。样例与测试分组见 SAMPLES.md、TEST-CASES.md；本地输入和参考准备状态以统一工具生成的 author/preparation.json 为准。官方对照保存在私有 official-candidate.npz，未经审核不作为 reference.npz；尚未校准 judge-config 和高维运行资源，不能直接组装正式评测。
