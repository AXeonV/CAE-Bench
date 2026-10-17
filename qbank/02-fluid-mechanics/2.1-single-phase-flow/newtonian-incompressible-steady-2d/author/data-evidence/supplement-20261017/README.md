# 2.1.1：20 个新增算例，2026-10-17

后续验证：除标准方腔 010 外的 19 例已用另一套现成 OpenFOAM 求解器实际交叉验证，逐例差异、结论和局限见[独立验证报告](../independent-openfoam-20261017/report.md)。以下保留初次制池时的出处和验证记录；原 Lethe 参考未改动。

本批仅入 HF 独立分支，正式测试／样例选择为空；没有调用 LLM 考生，没有运行 Agent benchmark。最终提交、逐例 ID、描述摘要和后续选样命令见本目录的 `delivery.md`、`catalog.json` 和 `select-cases.ps1`。`hf-start.json` 记录起始 main 及分支重建过程，`hf-upload.json` 记录实际上传回执，`remote-transport.json` 记录固定提交重新获取后的完整验证。

## 出处与生产者

- **工况出处**：`lid-square` 是标准封闭方腔，L=4 m、壁速 0.1 m/s、密度 1 kg/m3、动力黏度 0.004 Pa.s，Re=100。几何和量纲变换与 [Ghia、Ghia、Shin，JCP 48(3), 387–411 (1982)](https://doi.org/10.1016/0021-9991(82)90058-4) 的单位方腔对应。其余 19 例是本次作者设计的合法多边形工况，完整坐标、拓扑、驱动和材料见 `prepare_supplement.py` 的 specifications 及逐例 definition.json；不将这些改编工况宣称为文献复现。
- **实际参考生产者**：[Lethe](https://github.com/chaos-polymtl/lethe/tree/9bf70a921d86ed2fd8ccf5e5d4642d11ab4f7cf0)，固定源码提交 `9bf70a921d86ed2fd8ccf5e5d4642d11ab4f7cf0` 的现成 `lethe-fluid`，未改动求解器源码。可执行文件 SHA-256 为 `9322424b5702c66a8435b24d432f1a1b8d135c472e58a13d16710611b9d6f2b1`。依赖为已安装的 deal.II 9.8.0、Trilinos 16.2.0、OpenMPI 4.1.2；日志、配置、原始网格及原始输出关联均保留。
- **求解器方法依据**：采用上游 [2D lid driven cavity](https://github.com/chaos-polymtl/lethe/blob/9bf70a921d86ed2fd8ccf5e5d4642d11ab4f7cf0/examples/incompressible-flow/2d-lid-driven-cavity/cavity.prm) 的稳态模型，使用 Q2/Q1 速度／压力、Newton 非线性迭代和 GMRES/AMG。体源接口依据同一固定版本的 `examples/incompressible-flow/2d-mms/mms_quad/mms_2d_steady.prm`。配置中的初猜不是物理初态，不采用任意瞬态末帧。
- **独立数值比对**：仅方腔速度中线使用 Ghia 表 I 的 Re=100 列；取得的是 Lethe 固定版本附带的 [17 行转录数据](https://github.com/chaos-polymtl/lethe/blob/9bf70a921d86ed2fd8ccf5e5d4642d11ab4f7cf0/examples/incompressible-flow/2d-lid-driven-cavity/ref-2d-ghia-u.txt)，不是本次自制数据。保留原文件及 SHA-256，未声称重新从出版 PDF 逐字校勘。压力、剪切率及其他工况没有独立文献数值，逐例网格加密仍是同一求解器的验证。

## 制作、转换和数值验收

`prepare_supplement.py` 仅制作网格和配置、调用现成可执行文件；没有自编 PDE 求解器。整数矩形并集／差集定义精确多边形，内孔不作圆形近似。作者设计运动壁面的端点在 0.5 m 范围内线性降至零，避免与相邻静止壁面产生跳跃。标准方腔保留文献恒速顶壁。每条边界只归一组，边的连接关系给出法向，全部域按公共边连通。

输入为同一多边形上的一阶三角形网格，每单位长度 4 段；求解器网格为同域四边形，每单位长度分别 4、8、16 段，方腔另算 32、64 段。不存在曲面重建或几何改变。正式输入最多 1,408 个三角形、783 个节点。材料密度均为 1 kg/m3，除标准方腔外动力黏度为 0.1 Pa.s。体加速度是明确提供的空间线性向量，输入节点分片线性表示与实际求解器表达式完全一致；不是把力密度误作加速度。

每例在覆盖整个流体域内部的 0.5 m 格点请求速度、压力、密度、动力黏度和剪切率，共 1,702 个观测点。点不在壁面、内孔或角点上。没有请求输入网格全场，也没有用稀疏文献伪造全场；本题允许每例显式声明输出位置。此布局不评估观测点之间、紧邻角点或边界的误差。

`convert_supplement.py` 解码真实 VTU 结果。观测点均恰在求解器输出节点上，速度和压力不进行空间插值；核对重复节点上的连续量一致。梯度取重复单元迹的算术平均后计算 `sqrt(2 D:D)`，记录这一后处理近似。VTU 的 float32 字段转换为契约要求的 float64，不能因此增加原始有效精度。压力为运动学压力乘密度，再按第一观测点平移，使公开声明的点压力基准为 0 Pa；本批密度为 1，数值乘法为恒等。所有 IDs、时间和分量顺序按输入复制。

62 个最终网格计算均成功退出，末次 Newton 残差小于 1e-10。每个实际请求的速度、压力和剪切率分量比较最后两档网格，要求差值小于该分量题面容差的 25%；20/20 通过，最坏为 0.213916 倍容差。前三档中间结果和差异全部见 `evidence/numerical-validation.json`，没有将粗网格结果冒作高精度参考。该判据是参考制作的经验误差控制，不是严格后验误差上界。

方腔中线比对用单元内 Q2 插值计算文献位置，速度按 0.1 m/s 归一化。最大差异为 0.0050233 倍壁速，即 0.000502331 m/s；全部 17 点在题面速度容差内。文献表的有限网格误差、转录和舍入误差未与本次离散误差分离。此结果仅支持该中线速度比对，不独立认证压力或其余流场。见 `evidence/ghia-independent.json`。

最终参考计算均用 `taskset` 限制至 4 个 CPU，线程环境上限为 4，以 `/usr/bin/time -v` 记录资源。最大墙钟约 139.49 秒，最大 RSS 1,582,392 KiB，低于 600 秒、4 GiB。记录的是参考计算，不是所有未知考生算法的资源证明；没有将格式通过等同于资源达标。见 `resource-summary.json` 和最终档 `resource.txt`。

## 全批接口审计与判分

已应用 caeoj-data-review：`inventory.json` 枚举本批全部 20 个真实输入，题面及 DATA 快照齐全，无资产缺口。对照文件是本题 instruction.md、DATA.md 及 docs/CONTRACT.md。`interface-audit.json`、本地及远端 transport 报告覆盖：

| 实际路径／数组 | 公开约定与核对内容 |
|---|---|
| task、profile、analysis、materials | DATA 清单、分析声明、材料响应：steady/incompressible/laminar、恒温、gauge + point 基准、正常密度及黏度 |
| meshes.fluid、domain_ids、node_ids | CONTRACT 网格与位置、DATA 单一完整域：MSH 4.1 ASCII、一阶三角形、正面积、唯一且完整的全维单元，公共边连通 |
| wall_*_ids、boundary conditions | DATA 边界：全部真实外边及孔边恰覆盖一次，无重叠遗漏；moving_wall 节点值切向、固定几何；实际出现 no_slip、moving_wall、slip |
| wall_*_node_ids、wall_*_velocity | DATA 采样：恰覆盖条件边界全部节点、point、float64 [1,N,2]、piecewise_linear/constant/forbid；与求解器的端点斜坡逐段一致 |
| acceleration、source | DATA 体加速度：m/s2、完整材料域、节点 piecewise_linear、无物理 initial；实际出现有源与无源两分支 |
| probe_ids、probe_xy、pin_ids、pin_xy | CONTRACT 独立点、DATA 基准：严格递增 int64、float64 [N,2]、点在流体内，pin 仅一个点；不是网格 tag 或行号冒充身份 |
| clock 与五项输出 | DATA 输出、CONTRACT 结果：时间仅 [0.0]；全部 IDs／时间精确复制，float64 [1,N,C]，全局 xy；无额外 datasets、属性或外链 |
| reference.h5、grading.json | 题面评价：全部输出同等必需；使用已有 direct_outputs 评价器，atol/rtol 完全来自原作者模板，无自定义执行代码 |

通过 SDK 读取全部输入和完整候选 HDF5；通过独立的网格边计数、连通性、正面积和壁面切向检查。完整参考本身作为正例，20/20 得 1；每例分别扰动速度 +0.1 m/s、压力 +10 Pa、剪切率 +1 /s，以及删除速度字段，80/80 反例得 0。上传后使用固定提交、新缓存和新的隔离装配目录，重复严格完整性、全部实际输入、完整输出及同样判分正反例检查。没有拿只含正式选样的目录代表新增批次。

结论：本批接口审计通过，数值参考在上述证据范围内通过。未覆盖 pressure_outlet、traction、velocity inlet、flow_rate、periodic、absolute 压力、积分观测、混合单元或高 Re 分支；20 例的几何、拓扑和驱动差异不代表本题全部条件分支已覆盖。未以方腔中线吻合为其余 19 例提供独立来源背书。

## 复现与保留

制作程序在本题 author/，逐例配置、原始生产者摘要、执行日志、输入及参考摘要在本目录。复现所需软件版本已固定；远端工作目录中的 `evidence/raw-solver-results.tar.gz` 保留所有 62 档最终原始网格、VTU、配置和日志，摘要见 `raw-solver-results.sha256`；它是维护证据，不上传 HF 消费树。再次计算按 `run_supplement.py` 运行 4/8/16 档，再对 square 单独运行 32/64 档，执行 `check_ghia.py`、`convert_supplement.py`、`audit_supplement.py`。转换脚本不下载或上传数据；上传／拉取／装配使用现有 caeoj_tools.data_pool。

HF 保存的参考是全部实际请求输出的完整 HDF5，不是稀疏文献表。HF 不带求解器、转换代码、作者报告或临时执行载荷。清理情况、保留的原始档案位置及任何未完成项在 delivery.md 中记录。
