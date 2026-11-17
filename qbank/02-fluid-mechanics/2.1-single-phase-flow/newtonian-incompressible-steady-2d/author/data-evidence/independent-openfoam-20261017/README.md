# 其余 19 例的 OpenFOAM 独立交叉验证

详细记录已外置到独立 HF 维护归档；本页提到的 JSON、CSV 和 runs/ 均相对于装配后的 `work/211-evidence/independent-openfoam-20261017/`。获取和重放命令见[维护入口](../../README.md)，固定归档版本与摘要见[archive-index.json](../archive-index.json)。Git 只保留本页、逐例结论、摘要和生产者信息。

验证对象是补充分支 `cases/2-1-1-supplement` 固定提交 `fbe115effe8131bd575c0cde1c9ca87a9d87fd3a` 中除 `010 / lid-square` 外的全部 19 例。原参考生产者是 Lethe；本次采用 OpenFOAM Foundation 的现成 `incompressibleFluid` 模块，通过 `foamRun` 实际求解。结果、逐例结论与局限见本目录 `report.md`；全部分量差异见 `pointwise-differences.csv`，详细指标及 case ID 见 `comparison.json`。

## 来源与独立性

OpenFOAM-dev 源码固定为 `5de9f113a9e3d0f76ae8f9df6ec02554c866851b`，已安装程序日志的 Build 与该提交一致，源码工作树干净。实际二进制及主要库的摘要、编译器、依赖版本和固定源码链接见 `producer.json`。

- [完整求解器源码](https://github.com/OpenFOAM/OpenFOAM-dev/tree/5de9f113a9e3d0f76ae8f9df6ec02554c866851b/applications/modules/incompressibleFluid)
- [同版本稳态 SIMPLE 教程配置](https://github.com/OpenFOAM/OpenFOAM-dev/blob/5de9f113a9e3d0f76ae8f9df6ec02554c866851b/tutorials/incompressibleFluid/pitzDailySteady/system/fvSolution)
- [官方 codedFvModel 源项接口](https://github.com/OpenFOAM/OpenFOAM-dev/blob/5de9f113a9e3d0f76ae8f9df6ec02554c866851b/src/fvModels/general/codedFvModel/codedFvModel.H)
- [实际点采样实现](https://github.com/OpenFOAM/OpenFOAM-dev/blob/5de9f113a9e3d0f76ae8f9df6ec02554c866851b/src/sampling/sampledSet/points/points.H)

本次是有限体积法与原 Lethe Q2/Q1 有限元法之间的交叉验证，使用不同代码、离散、网格和求解过程。未使用模型考生提交、LLM 或 benchmark。两者仍共享不可压缩牛顿流体连续方程及冻结工况；这不是实验真值或严格误差界。

`crosscheck_openfoam.py` 只读取冻结输入、转换格式并调用现成工具；不导入 Lethe 工况生成器或数值解。空间加速度通过 OpenFOAM 自带的 codedFvModel 接口装配，代码仅计算输入的仿射加速度和标准体积源项 `-V*a`，不实现或替换 PDE 求解器。

## 工况与数值映射

| 冻结输入 | OpenFOAM 表示及核对 |
|---|---|
| Gmsh 一阶三角形流体域，含台阶、凹槽及孔洞 | 从实际单元连接重建完整整数单位方块，逐块及总面积检查；blockMesh 生成同一多边形域，孔洞不填充；细分数按米定义 |
| DATA 全局 xy 平面 | 出平面挤出 0.1 m、单层单元，前后设 empty；所有速度出平面分量和梯度为零。挤出厚度不改变二维方程 |
| no_slip / moving_wall | 真实外边按其冻结 element IDs 归属分区；固定速度由原节点场沿原线段线性重建，在边界面中心求值。细网格与原分段节点对齐，保留两端斜坡 |
| 019 的 slip | 平面边界采用 slip；对应无穿透、零切向牵引，其余壁面仍无滑移 |
| source acceleration，m/s2，节点 P1 | 从实际节点及数组拟合全局仿射式，逐节点验证拟合误差 < 1e-14；本批源确实全部仿射，因而与所有原三角形 P1 场完全一致；没有额外重力 |
| 常数 rho 与动态 mu | 实际输入读取，设置 nu=mu/rho，laminar 牛顿流体；输出密度和动态黏度从材料回读，不能算作流场的独立数值证据 |
| 稳态 | steadyState，SIMPLE，中心有限体积通量、Gauss linear 梯度；真实迭代至规定残差，迭代编号不是物理时间 |
| gauge pressure、pin | OpenFOAM 解的是运动学压力，乘 rho 转为 Pa；用独立解在输入 pin 的采样值实施指定 0 Pa 点基准，未读取原参考来拟合压力偏移 |
| probes，point | 使用上游 sets/points、cellPoint 插值，逐点核对输出坐标与顺序；采样 U、p、gradU，按 DATA 的 sqrt(2 D:D) 计算剪切率；输出 clock 与 IDs 精确复制 |

逐档 `translation.json` 保存输入摘要、面积、网格数量、材料、源拟合误差、边界类型／长度／实际面数和观测点。原始配置与场已迁移至固定 HF 证据提交：完整原始结果为 `raw/openfoam-results.tar.gz`，实际 system、constant 字典和初始字段另存 `raw/openfoam-configurations.tar.gz`，早期诊断记录为 `raw/openfoam-diagnostics.tar.gz`。全部大小和摘要由轻量索引绑定；冻结的原始 JSON 仍保留实际执行时的位置，不将这些历史路径作为下载依赖。

## 比较与接口审计

比较全体实际请求的观测点、每个速度分量、压力、剪切率及两个材料输出；没有删去近壁点、零值或不利分量。报告绝对最大差、RMS、题面逐分量容差归一化差、最坏点 ID／坐标／分量，以及逐点完整差值。跨程序的归一化分母是 `atol + 0.01*abs(原 Lethe 参考)`，与正式判分一致；网格比较的分母使用较细档 OpenFOAM 值，单独记录，不能代替跨程序证据。

采用 caeoj-data-review，对照 instruction.md、DATA.md、CONTRACT.md 核对本批输入与转换输出；记录见 `interface-audit.json`。冻结池严格核验见 `frozen-pool-verification.json`。`production-grading.json` 是把独立计算的完整 HDF5 交给现有 SDK 和 `grade_case` 的真实执行结果，不是用本脚本的差异判断冒充判题链。

原输入、参考、grading、正式选样均不修改；HF main 和补充分支前后提交检查见 `hf-before.json` / `hf-after.json`。本次没有上传操作。

历史归档和清理状态保存在冻结的 `cleanup.json` 中。本次进一步将原始维护档案上传至独立 HF 分支，并通过固定提交重新获取；迁移验证记录见轻量索引同目录的 migration-validation.json。

## 复现

从原池固定提交装配后，按 `catalog.json` 的 name 映射准备 `source/cases/<name>` 和 `source/reference/<name>`，摘要必须与原目录 `supplement-20261017/catalog.json` 完全相同。在已构建的固定版本 OpenFOAM 环境中：

```sh
source /path/to/OpenFOAM-dev/etc/bashrc
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
python crosscheck_openfoam.py source runs --levels 16 --workers 19
python crosscheck_openfoam.py source runs --levels 24 --workers 19 --relaxation 0.95 --linear-relative 0.1
python crosscheck_openfoam.py source runs --levels 32 --workers 19 --relaxation 0.95 --linear-relative 0.1 --initial-level 24
python capture_openfoam_producer.py producer.json
python assess_openfoam.py source evidence --runs runs --catalog catalog.json
# 在安装本仓库 SDK 的环境执行实际消费链
python assess_openfoam.py source evidence --grade
```

实际执行 16、24、32 三档。16、24 从零初猜，32 由同工况已收敛的 OpenFOAM 24 档解经现成 mapFields/cellPointInterpolate 初始化，随后重新施加精确冻结边界，并真实迭代至相同外层残差要求。额外的 L 形腔 32 档零初猜计算用于核对初始化／线性相对停止设置对最终结果的影响，见 `initialization-consistency.json`。早期未完成的过严线性求解和未松弛 GAMG 试算不计入 57 次最终计算，保留诊断档案。上面的并行数服务于交叉验证计算，不证明 4 CPU／4 GiB 的考生资源达标。本次不改变已有资源验证结论或 benchmark 成绩。
