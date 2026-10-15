# 来源核验与协议覆盖

## 官方完整样本

来源为 Takamoto 等的 [PDEBench 数据集](https://doi.org/10.18419/darus-2986)，CC BY 4.0；文件 `1D_Advection_Sols_beta0.4.hdf5`，使用[官方列出的下载入口](https://github.com/pdebench/PDEBench/blob/main/pdebench/data_download/README.md)：`https://darus.uni-stuttgart.de/api/access/datafile/133110`。

源 `tensor` 为 float32 `[10000,201,1024]`。按预先固定的索引 0～11 选择 12 个完整样本，不筛选误差、不修改初值、不裁剪空间或时间，也不重新生成参考轨迹。全体数据集有 10000 个样本，本题并非导入全体数据集。前两点同时公开为完整示例。

每个源样本的全部 201×1024 个值先记录 SHA-256，再按 Gmsh 单元中心映射到 IDs 的顺序，精确转为 float64。此转换不增加源数据精度。每点 certificate 保存原索引、哈希和源列映射，测试通过逆映射和 float32 回转验证原值逐项一致。

## 已核实的历史问题

1. **速度缩放**：源文件标签与属性为 beta=0.4。官方提交 [ac1ed78：fix scaling issue for 1D advection](https://github.com/pdebench/PDEBench/commit/ac1ed78bac6bf79f8d8dba863df7d292a1e1f1ed) 在 2023 年给通量补上缺失的 0.5。历史通量是标准通量的两倍；发布轨迹与实际速度 0.8 吻合。题面和输入明确用 c=0.8，保留源轨迹原值，不让考生猜测历史标签。该处理属于题目定义，不写入通用协议。
2. **时间坐标多一项**：源 t-coordinate 有 202 项，但 tensor 只有 201 帧。官方生成器把坐标分配为 `it_tot+1`，轨迹分配为 `it_tot`。使用前 201 项对应全部真实帧，末帧 t=2；最后 2.01 没有对应的解帧。原始选定 HDF5 仍完整保留 202 项坐标，转换器只接受这一经核实的形状，遇到未知不匹配直接报错。
3. **官方数值离散误差**：参考是历史有限体积结果，不能套用解析解的紧容差。基线从初始单元常数场独立计算连续平流的单元平均解，12 点最大逐值差异约 0.05950。测试前固定绝对阈值 0.08，覆盖此差异并留少量余量；不依据 Agent 输出调整阈值。这验证了对完整官方轨迹的适配，不等同于认证高精度求解能力。

不复制带独立许可限制的上游求解源代码；下载器、格式转换器与 baseline 为本项目实现。

## CONTRACT 覆盖

| 需求 | 已有表示 |
|---|---|
| 一维等距有限体积网格 | Gmsh 线单元，`spatial_dimension=1` |
| 单元常数初值与平均输出 | element location，scalar，`value_kind=average` |
| 全部 201 个时刻 | 独立初始／输出 time_axes，float64 精确保存源值 |
| 周期区域 | 现有 boundary 条件的任务定义算子 periodic；DATA 明确位置和 period 含义 |
| 传播速度 | physics 带单位标量参数 |
| HDF5 来源与历史修复 | 出题侧 provenance，不属于求解器输入格式 |

**无需修改 CONTRACT.md、Schema、SDK 或校验器。** 周期算子的这一维适用范围写在 DATA.md；尚未声称覆盖任意非共形周期面。容器资源属于共享运行层，这轮不固定 CPU、内存或库线程数。
