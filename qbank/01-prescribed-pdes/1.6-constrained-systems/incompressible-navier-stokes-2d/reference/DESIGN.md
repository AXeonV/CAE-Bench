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
| [pdebench/data_gen/src/sim_ns_incomp_2d.py](https://github.com/pdebench/PDEBench/blob/4ff3e3a4aa1561721b5571fa3a048a0a463e0568/pdebench/data_gen/src/sim_ns_incomp_2d.py) | `6916b9d4985ead2c612667b9d971a734d7ed27de51c4a3575fdbfa06cfcbe697` |
| [pdebench/data_gen/src/data_io.py](https://github.com/pdebench/PDEBench/blob/4ff3e3a4aa1561721b5571fa3a048a0a463e0568/pdebench/data_gen/src/data_io.py) | `74ef8cbf5c8d177294e584b062d2d836cd1823b21f3a8e0f8b65db2bc9ad6a99` |
| [pdebench/data_gen/configs/ns_incomp.yaml](https://github.com/pdebench/PDEBench/blob/4ff3e3a4aa1561721b5571fa3a048a0a463e0568/pdebench/data_gen/configs/ns_incomp.yaml) | `4b20f6706926a17295104978053dd7a3ddaa001b27f352c4599c705e22a836dd` |

## 发布配置对应

| 发布文件 | DaRUS datafile ID | MD5（来源身份） |
|---|---:|---|
| `ns_incom_inhom_2d_512-0.h5` | 133280 | `54109d46f9c957317bd670ddb2068ac0` |
| `ns_incom_inhom_2d_512-1.h5` | 136439 | `e280fd3208fccb8ad5c1ff46c4796864` |
| `ns_incom_inhom_2d_512-2.h5` | 133721 | `1d7a2aac41a410bea6c887f624273d20` |
| `ns_incom_inhom_2d_512-3.h5` | 136466 | `e9c92a19854e96c918d3a46d39994be4` |
| `ns_incom_inhom_2d_512-4.h5` | 166289 | `306a56ac14ea5686921cbb3f09c7dcb6` |
| `ns_incom_inhom_2d_512-5.h5` | 136471 | `6a939d7418593d70faf7f90a191f841d` |
| `ns_incom_inhom_2d_512-6.h5` | 136472 | `36156ac1f8cecb47d076a1ee0707dec5` |
| `ns_incom_inhom_2d_512-7.h5` | 136473 | `e1b06fd07d09227a0767baa260f361e2` |

当前发布族共 275 个分片，工具首批使用按种子排序的前 8 个；分片不是不同物理参数配置。

模型标识为 `inhomogeneous_incompressible_navier_stokes_2d`。参数与输入场对应关系以 [DATA.md](../DATA.md) 为准；文件标签不作为程序输入，不允许由文件名隐式改写参数。

## 当前参考政策

当前数学定义以 instruction.md 与 DATA.md 为准。来源身份、实际坐标、完整初值、时间轴和族相关一致性逐例核对。保留经结构与族相关一致性审核的官方数值轨迹作为数值参考，局限写入逐例证书。数值参考不等于精确连续真解；误差阈值、连续误差与执行资源尚未校准。

## 当前采样与源实现差异

动量由 χf 驱动，χ 同时随速度输运；不是静态 f 的普通受迫流。当前契约保留 t=0 未投影的原始记录，t>0 以连续 Helmholtz 投影为右初值，且采用零壁速。发布中心速度源于交错场再采样，输入按独立点双线性重建，不能把中心点值当作面通量。8 个实际使用分片的配置、真实时间和单位域尺度已核对，结果见下文及逐例证书；连续投影与离散投影、中心再采样和输运误差仍需独立校准。

这是连续 PDE 求解题，提交程序自行选择数值方法。输入的重建规则与输出观测量是本题数学契约；源随机场、离散更新及连续重建不能自动视为同一对象。生成算法和参考策略只在作者材料中说明，不要求参赛程序复现。

## 参赛材料修订

当前题面保留连续 Helmholtz 初始投影、χf 耦合输运及预投影首帧记录。初始投影仍属于被测数学契约；若未来改为出题方预处理，必须同时重新定义初值表示和参考，不能只删除投影说明。

## 后续评测阶段

统一获取、缓存、选样冻结和协议转换入口已在 src/utils/PDEBench/prepare.py 实现。参考收敛/误差审核、误差阈值和执行资源仍需补充。现有参考策略已固定；发布前仍须确认其对当前连续契约的精度，并决定是否需进一步独立重算。样例与测试分组见 SAMPLES.md、TEST-CASES.md；本地输入和参考准备状态以统一工具生成的 ../author/preparation.json 为准。官方原始对照保存在私有 official-candidate.h5；仅经源对齐审核或修正的参考写入 reference.h5；尚未校准 judge-config 和高维运行资源，不能直接组装正式评测。

## 发布域尺度的实测区分

发布配置 domain_size=1² 与当前源码的 grid_size Box 不一致。对 datafile 133280 第 0 条轨迹，使用 t=0.005、0.01 的发布速度作时间线性插值，按 100 个子步独立双线性输运发布标量，排除边缘 1/8 区域；单位域的相对变化残差为约 0.00120，512 长度域为约 0.998。按发布配置采用单位域，工具已对全部 8 个所用分片重复该尺度区分并保存证据：单位域残差为 0.001108–0.002146，512 长度域为 0.998030–0.998047。它不是全 NS 误差认证，也不证明发布时使用的归档源码提交；不能把当前源码 Box 当作归档数据的物理域。
