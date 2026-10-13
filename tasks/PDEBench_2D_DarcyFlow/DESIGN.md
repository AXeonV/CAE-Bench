# 来源核对与题面设计

## 固定来源

- 数据集：[PDEBench / DaRUS V8](https://darus.uni-stuttgart.de/dataset.xhtml?persistentId=doi%3A10.18419%2FDARUS-2986&version=8.0)，DOI `10.18419/DARUS-2986`，数据许可 CC BY 4.0；检查日期 2026-10-13。数据许可不自动覆盖生成代码许可。
- 方程背景：[官方论文补充材料 D 节](https://proceedings.neurips.cc/paper_files/paper/2022/file/0a9747136d411fb83f0cf81820d44afb-Supplemental-Datasets_and_Benchmarks.pdf)。论文、配置、源码与发布数据分别作为证据，不假定四者完全一致。
- 审核使用的源码版本（不证明所有发布文件由该提交生成）：[`4ff3e3a4aa1561721b5571fa3a048a0a463e0568`](https://github.com/pdebench/PDEBench/commit/4ff3e3a4aa1561721b5571fa3a048a0a463e0568)。
- 下载 CSV：[固定版本发布入口清单](https://github.com/pdebench/PDEBench/blob/4ff3e3a4aa1561721b5571fa3a048a0a463e0568/pdebench/data_download/pdebench_data_urls.csv)。实际支持范围取本次 DaRUS V8 元数据清单；CSV 中的历史入口及未发布生成器配置不自动纳入。

题面设计阶段核对了文本配置、源码和发布元数据；随后由统一工具按需读取发布 HDF5 的选定样本和帧。实际选样、输入哈希与准备状态见运行后生成的 author/selection.json、author/preparation.json 和私有 certificate.json。读取和结构转换不构成轨迹误差验证；官方整文件 MD5 记录发布身份，远程子集的完整性范围另见工具说明。

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

模型标识为 `darcy_flow_2d`。参数与输入场对应关系以 [DATA.md](DATA.md) 为准；文件标签不作为程序输入，不允许由文件名隐式改写参数。

## 当前参考政策

用户已选择匹配官方生成器并审核官方数值轨迹。题面中与此冲突的早期解释以当前 instruction.md 和 DATA.md 为准。工具逐例核对来源、配置、实际坐标与时间、完整初值及模型一致性，保存审核指标和局限；参考不是精确连续真解，误差阈值及资源尚未校准。Darcy 额外求发布空间算子的稳态，避免使用尚未收敛的有限时间快照。

## 早期设计差异记录（已由下述源对齐修订取代）

对应源码中的二维变系数扩散加源项程序，不是 FitzHugh–Nagumo 生成器。a 由随机场阈值化为 0.1/1。`bc_2D(mode="Neumann")` 的实际分支把幽灵值设为零，不能据算子名称写成零通量；本题选定论文所述零 Dirichlet 边界。

官方通过有限时间演化获取“稳态”场；低残差或文件名均不能证明真正稳态。本题要求椭圆方程解，后续必须审核终态残差、边界定位及系数界面误差，不直接承诺发布终帧就是正确标答。

这是连续 PDE 求解题，官方数值生成算法不是提交必须复现的算法。单元平均/点采样的连续初值定义是本题新增的明确契约，不宣称恢复源生成器原始随机场。物理参数没有证据时不从文件名推断；任何转换均须满足这里已选定的方程和采样含义。

## 后续评测阶段

统一获取、缓存、选样冻结和协议转换入口已在 src/utils/PDEBench/prepare.py 实现。参考收敛/误差审核、误差阈值和执行资源仍需补充。应先确认参考计算解的是同一数学问题，再决定是否采用官方轨迹或独立参考。样例与测试分组见 SAMPLES.md、TEST-CASES.md；本地输入和参考准备状态以统一工具生成的 author/preparation.json 为准。官方原始对照保存在私有 official-candidate.npz；仅经源对齐审核或修正的参考写入 reference.npz；尚未校准 judge-config 和高维运行资源，不能直接组装正式评测。
