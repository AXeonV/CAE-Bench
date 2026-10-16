# 第二章协议需求、实现与相容性记录

2026-10-15；维护材料，不随题面交给考生。依据 caeoj-extend-io 工作流实施。当前交付是声明及接口基础设施；无真实流动求解或物理验证。

| 需求 | 输入／观测拥有位置 | 层与实际实现 |
|---|---|---|
| 2.1 封闭可压缩稳态质量库存 | analysis.mean_density，kg/m3，域总质量/体积（2D为单位厚度面积） | 唯一新增物理结构字段；problem.schema、cfd检查、CFD-2.1规范、两题及公共DATA、临时生成器、26项CFD测试同步 |
| 2.2 能量、状态依赖物性及初热状态 | physics.model=fluid-energy-*；parameters常量；conditions/fields | FLUID-ENERGY、fluid_energy、真实临时fixture，通用表示无需重造 |
| 2.3—2.4 RANS/URANS/尺度解析、统计窗口 | 显式模型选择方法；statistics_start/end/step；给定k与长度的标准化初始化 | 不以隐藏闭合变量评分；离散统计中央矩与独立预期测试；文档明确初始化近似及未来参考误差责任 |
| 2.5—2.7 相标识、固定位置界面/分散观测、热质交换/相变 | physics.model=fluid-multiphase-*；带单位参数及条件 | FLUID-MULTIPHASE、fluid_multiphase；单元平均与表观通量显式区分；尖锐蒸冷两侧运动学、反冲和热跳跃公开 |
| 2.8—2.9 平面降维、薄膜和深度平均 | physics.model=fluid-reduced-*，gap/bed等域条件；aggregate真实域积分 | FLUID-REDUCED、fluid_reduced；不造汇总点；薄膜时间导数单侧迹与两层超临界边界实际检查/助手 |
| 2.10 单原子气体与气壁 | 同上；分子质量/直径/储槽Maxwellian/壁面适应率 | 连续滑移与动理学碰撞问题分开；分布内部离散自由，公开实验室/壁面参考系，SDK Maxwellian有独立手算 |
| 2.11 历史与热移位材料 | 同上；构象/结构初态和入口条件；完整张量输出 | 材料响应、SPD、历史初态、温度移位、聚合物储能/耗散与唯一导数观测迹明确；SDK及真实fixture |
| 相同实体与时间的比较 | 通用固定IDs/时间/shape/dtype，输出语义依显式模型 | 通用校验先行，领域诊断E_FLUID；不转换单位、不投影初态、不修复答案 |
| 小压差叠加大绝对基准 | 公开评分配置的固定reference_offset | 仅改变相对容差尺度，不改变输入/输出压力表示或差值；实现证据见进度记录最终验证项 |

## 拥有层及版本决定

既有 CONTRACT 已有带单位参数、typed condition data、fields、time_axes、sampling和aggregate，足以表示新配置的有限首版。故2.2—2.11不新增通用顶层或自由表达式，不机械复制CFD四键。physics.model含显式-v1，各完整枚举及其参数/条件精确集合由领域规范与模块共同拥有，未知领域版本拒绝，task不决定物理。Schema新增领域physics与CFD四键互斥；通用field、location、storage结构及sampling枚举不变。

旧无新前缀的physics及完整CFD输入维持旧语义。新领域几何连接按前缀按需读取，旧大网格不因此加载额外连接。新领域不能混用analysis/materials四键或重复表达物理。

CFD库存是已发现的欠定声明修复：旧有状态锚定的输入不变；此前缺库存的封闭稳态现在拒绝。题库2.1实际数据为0，无数据迁移；不得擅自给未知旧输入补库存。通用SDK load_problem/read_constant精确保留新标量，未新增冗余SDK库存结构。临时解析静止示例显式写库存，只用于接口检查。

评分reference_offset采用评分配置层，不把评分尺度写入problem.json物理输入。旧配置省略该项等于0，保持绝对参考逐值比较。正式数据阶段须将每例pressure_reference作为固定公开评分常量，不允许读取答案后拟合偏移。

## 实现和公开工具

规范：CONTRACT、CFD-2.1、FLUID-ENERGY、FLUID-MULTIPHASE、FLUID-REDUCED及GRADING。

实现：problem.schema、validation领域分派、cfd、fluid_energy、fluid_multiphase、fluid_reduced、sdk、grading.schema/metrics/policy；publish_dist显式允许列表含全部新模块和规范。pyproject已以caeoj包交付模块，包数据既有Schema清单不缺新独立文件。

SDK保留通用读写，新增显式物性、条件采样、中央矩、相质量、流变及Maxwellian辅助；不选择闭合，不重建未声明的物理，也不代求流动。

公开工具隔离测试使用发布器真实TOOL_FILES允许列表复制到临时目录，在独立进程核对caeoj及三个新模块的实际路径，并验证三组临时MSH/HDF5输入与输出回传。没有制作正式题目包或调用题库发布；现有tasks的打包回归仅为工具兼容性测试，不构成第二章发布。

## 证据与限制

测试覆盖所有新模型及允许维度的最小真实输入、非法声明/引用/单位/位置/时间/组合、输出回传、独立材料/质量/统计/特征根/时间导数预期，以及旧通用/CFD和公开工具隔离。具体命令与最终测试总数见[章级进度](chapter-02-progress.md)，各组实现记录保留更细清单。

独立考生审阅发现后实际修订：质量库存；三维应力约定；URANS初始化；尖锐蒸冷跳跃与纯相储槽；平均乘积不可精确复算守恒量；派生初值迹；薄膜时间迹；双层边界；移动气壁参考系；导数点值及热边界分区。公共协议变动后对受影响全部节复核，文件清单散列随最终版本记录。

这些接口测试不证明薄隙比、Kn、相变模型真实性、界面解适定性、全程材料/体积分数范围、湍流统计可靠性、参考收敛或预算可达。资源与容差仍待实际数据校准；模型物理范围以各节有限首版为准，不声称已覆盖全部物性/边界/方法组合。examples/references/cases仅占位，数据与参考审核、真实数值/物理验证及正式评测均未进行。
