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
| [pdebench/data_gen/src/sim_ns_incomp_2d.py](https://github.com/pdebench/PDEBench/blob/4ff3e3a4aa1561721b5571fa3a048a0a463e0568/pdebench/data_gen/src/sim_ns_incomp_2d.py) | `6916b9d4985ead2c612667b9d971a734d7ed27de51c4a3575fdbfa06cfcbe697` |
| [pdebench/data_gen/src/data_io.py](https://github.com/pdebench/PDEBench/blob/4ff3e3a4aa1561721b5571fa3a048a0a463e0568/pdebench/data_gen/src/data_io.py) | `74ef8cbf5c8d177294e584b062d2d836cd1823b21f3a8e0f8b65db2bc9ad6a99` |
| [pdebench/data_gen/configs/ns_incomp.yaml](https://github.com/pdebench/PDEBench/blob/4ff3e3a4aa1561721b5571fa3a048a0a463e0568/pdebench/data_gen/configs/ns_incomp.yaml) | `4b20f6706926a17295104978053dd7a3ddaa001b27f352c4599c705e22a836dd` |

## 发布配置对应

当前 V8 的 `2D/NS_incom` 下有 275 个 `ns_incom_inhom_2d_512-*.h5` 分片。分片不是不同方程或 275 个物理参数配置；种子和 batch 数由文件 config 决定。代表文件：datafile 133280，`ns_incom_inhom_2d_512-0.h5`，MD5 `54109d46f9c957317bd670ddb2068ac0`。

模型标识为 `inhomogeneous_incompressible_navier_stokes_2d`。参数与输入场对应关系以 [DATA.md](DATA.md) 为准；文件标签不作为程序输入，不允许由文件名隐式改写参数。

## 差异与本题选择

源码动量更新使用 particles×force；particles 还被速度输运。本题保留该耦合，不能写成静态 f 的普通受迫 NS。源码初始随机速度在保存首帧前没有执行不可压缩投影；本题以显式连续投影定义可解的初值，因此 t=0 输出一般不等于原始速度采样。

官方速度原为交错网格场，`data_io.to_centre_grid` 再采样至中心；本题采用独立点及分片双线性重建，不能声称这些中心值就是面通量。当前 V8 文件名均为 512；论文代表表中的 256 不用作本题网格数。

检查了官方文件 `ns_incom_inhom_2d_512-0.h5`（datafile 133280）头部中的 config：grid_size=512²、domain_size=1²、NU=0.01、DT=5×10⁻⁵、n_steps=100000、frame_int=100、n_batch=4。只读取 64 KiB 头部，未下载轨迹。当前源码用 grid_size 构造 bounds，而配置仍写 domain_size=1²；本题明确采用论文/配置的单位正方形，不默默把 512 长度域归一化而保留同一黏度。源码版本与发布坐标尺度的对应须在后续参考审核中解决。

中心采样重建、初始投影、耦合输运及域尺度都可能导致发布轨迹与本题连续解不同；未来标答必须独立审核或重算。

这是连续 PDE 求解题，官方数值生成算法不是提交必须复现的算法。单元平均/点采样的连续初值定义是本题新增的明确契约，不宣称恢复源生成器原始随机场。物理参数没有证据时不从文件名推断；任何转换均须满足这里已选定的方程和采样含义。

## 参赛材料修订

本轮仅消除字段位置歧义，保留连续 Helmholtz 初始投影和 χf 耦合输运。初始投影仍属于被测数学契约；若未来改为出题方预处理，必须同时重新定义初值表示和参考，不能只删除投影说明。

## 后续评测阶段

统一获取、缓存、选样冻结和协议转换入口已在 src/utils/PDEBench/prepare.py 实现。参考收敛/误差审核、误差阈值和执行资源仍需补充。应先确认参考计算解的是同一数学问题，再决定是否采用官方轨迹或独立参考。样例与测试分组见 SAMPLES.md、TEST-CASES.md；本地输入和参考准备状态以统一工具生成的 author/preparation.json 为准。官方对照保存在私有 official-candidate.npz，未经审核不作为 reference.npz；尚未校准 judge-config 和高维运行资源，不能直接组装正式评测。
