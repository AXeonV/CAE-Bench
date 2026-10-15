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
| [pdebench/data_gen/data_gen_NLE/CompressibleFluid/CFD_multi_Hydra.py](https://github.com/pdebench/PDEBench/blob/4ff3e3a4aa1561721b5571fa3a048a0a463e0568/pdebench/data_gen/data_gen_NLE/CompressibleFluid/CFD_multi_Hydra.py) | `5d3fc091cf901b7d1b8a51f985fc8e197e90a591cbccd1d8e687d80ac8e0d697` |
| [pdebench/data_gen/data_gen_NLE/CompressibleFluid/CFD_Hydra.py](https://github.com/pdebench/PDEBench/blob/4ff3e3a4aa1561721b5571fa3a048a0a463e0568/pdebench/data_gen/data_gen_NLE/CompressibleFluid/CFD_Hydra.py) | `3544a117769650003149fcdd0b2d939a50d1ee9e5c5b65274a87b602b0308682` |
| [pdebench/data_gen/data_gen_NLE/utils.py](https://github.com/pdebench/PDEBench/blob/4ff3e3a4aa1561721b5571fa3a048a0a463e0568/pdebench/data_gen/data_gen_NLE/utils.py) | `fc3a848a12e79e89bb53898944fe96ccbc44236b22ce4b6a705eda00a8018d71` |
| [pdebench/data_gen/data_gen_NLE/CompressibleFluid/config/args/1D_Multi.yaml](https://github.com/pdebench/PDEBench/blob/4ff3e3a4aa1561721b5571fa3a048a0a463e0568/pdebench/data_gen/data_gen_NLE/CompressibleFluid/config/args/1D_Multi.yaml) | `a5cec61e2be6427bd61ca95f12d7cb6b2d104d010a50704f508304a56ab66720` |
| [pdebench/data_gen/data_gen_NLE/CompressibleFluid/config/args/1D_ShockTube6.yaml](https://github.com/pdebench/PDEBench/blob/4ff3e3a4aa1561721b5571fa3a048a0a463e0568/pdebench/data_gen/data_gen_NLE/CompressibleFluid/config/args/1D_ShockTube6.yaml) | `21e83d36c9047d3ff0496e55b282575c37a8cb071fa3b366fea13bf9bbcf5fe5` |

## 发布配置对应

| 发布文件 | DaRUS datafile ID | MD5（来源身份） |
|---|---:|---|
| `1D_CFD_Rand_Eta1.e-8_Zeta1.e-8_periodic_Train.hdf5` | 135485 | `ad22fe08b8abc721179dbb34f2cc8b2a` |
| `1D_CFD_Rand_Eta0.01_Zeta0.01_periodic_Train.hdf5` | 164672 | `2fdd00138f1d7abc794fb953021a9f43` |
| `1D_CFD_Rand_Eta0.1_Zeta0.1_periodic_Train.hdf5` | 164668 | `45655bd77d006ab539c52b7fbcf099b9` |
| `1D_CFD_Rand_Eta1.e-8_Zeta1.e-8_trans_Train.hdf5` | 133155 | `79857a11ad9a69d77b8cf249a1c72d06` |
| `1D_CFD_Shock_Eta1.e-8_Zeta1.e-8_trans_Train.hdf5` | 133156 | `08dffc3d84033c7574a70614703dd753` |
| `Sod6.hdf5` | 133150 | `adb2d95bf0d48e03bc0d8f4a2cbcd1c6` |

模型标识为 `compressible_navier_stokes_1d`。参数与输入场对应关系以 [DATA.md](../DATA.md) 为准；文件标签不作为程序输入，不允许由文件名隐式改写参数。

## 当前参考政策

当前数学定义以 instruction.md 与 DATA.md 为准。来源身份、实际坐标、完整初值、时间轴和族相关一致性逐例核对。保留经结构与族相关一致性审核的官方数值轨迹作为数值参考，局限写入逐例证书。数值参考不等于精确连续真解；误差阈值、连续误差与执行资源尚未校准。

## 当前采样与源实现差异

当前采用 Q_ij=ρ[η+(ζ+η/3)δ_ij]∂_jv_i 的密度加权定向黏性通量，η/ζ 单位 m²/s，能量黏性通量为 ∑_i v_iQ_ij。该定义取代早期常动力黏度、完整对称应力模型。初始 ρ、v、p 逐单元为常数；输出密度为平均密度，速度为平均动量/平均密度，压力从平均守恒量反算。源压力下限和分裂离散没有被加入连续方程，相关偏差须由参考误差审核处理，不能要求参赛程序隐式裁剪压力。

这是连续 PDE 求解题，提交程序自行选择数值方法。输入的重建规则与输出观测量是本题数学契约；源随机场、离散更新及连续重建不能自动视为同一对象。生成算法和参考策略只在作者材料中说明，不要求参赛程序复现。

## 参赛材料修订

来源 Train 文件的时间范围为 [0,1] s，Sod6 为 [0,2] s。公开数学契约统一按边界类型给出支持上界：周期到 1 s，外推到 2 s，不要求输入额外声明来源类别；这不增加来源文件或判例。

## 后续评测阶段

统一获取、缓存、选样冻结和协议转换入口已在 src/utils/PDEBench/prepare.py 实现。参考收敛/误差审核、误差阈值和执行资源仍需补充。现有参考策略已固定；发布前仍须确认其对当前连续契约的精度，并决定是否需进一步独立重算。样例与测试分组见 SAMPLES.md、TEST-CASES.md；本地输入和参考准备状态以统一工具生成的 ../author/preparation.json 为准。官方原始对照保存在私有 official-candidate.h5；仅经源对齐审核或修正的参考写入 reference.h5；尚未校准 judge-config 和高维运行资源，不能直接组装正式评测。
