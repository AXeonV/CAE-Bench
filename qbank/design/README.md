# 题库总体设计

题库面向 CAE 各领域，统一按章、节、子节组织。第 0 章承担基础链路测试；第 1 章起要求 Agent 生产覆盖公开问题族的可复用求解器。给定 PDE 与通过物理描述定义分析任务，是题目描述与建模责任的区别，不作为两大类目录。

本文件确定章级规划，后续逐章展开节、子节及具体题目。规划独立于算例来源、数据就绪程度和实施顺序；列入目录不表示已完成题目或参考验证。设计原则见 [PHILOSOPHY.md](../PHILOSOPHY.md)。

执行流程见 [Agent 章节出题工作流](AUTHORING.md)，具体错误与修复经验见 [经验清单](AUTHORING-LESSONS.md)；可通过仓库技能 `caeoj-author-question` 完成指定章／节的题面，通过 `caeoj-design-data` 设计自包含 DATA；独立设计审阅使用 `caeoj-design-review`，检查问题族定位与划分；独立考生审阅使用 `caeoj-candidate-review`，可选允许缺样例或检查考试材料；需要评测配置或框架适配时使用 `caeoj-configure-judge`。

基础设施职责与依赖边界见[核心、题库扩展与维护工具](CORE-AND-EXTENSIONS.md)，实际配置见[运行装配维护说明](../maintenance/RUNTIME.md)，历史验证见[实施记录](reviews/runtime-refactor.md)。领域能力按物理组织，不绑定章节编号。

考生获得的材料、一次安装、统一命令和稳定 SDK，以及单题／多题装配的验收要求见[考生侧公开接口与材料装配](PUBLIC-INTERFACE.md)；内部拆分不应增加考生使用负担。

HF 题内数据池、稳定身份、选样清单及目录装配见[题库数据存储设计](DATA-STORAGE.md)。`caeoj-maint data` 制池、上传、选样、下载装配与核验操作见[数据池操作](../maintenance/DATA-SYNC.md)，实际迁移证据见[迁移记录](reviews/data-storage-migration.md)。

通用工具的历史实施见[数据池工具实施与验证](reviews/data-pool-tools.md)；当前自包含目录的迁移及验证见[case 布局收束](reviews/case-pool-simplification.md)。

## 章级目录

| 章 | 章名 | 覆盖范围 |
|---|---|---|
| 第 0 章 | [基础测试](../00-basic-tests/README.md) | 输入输出协议与判题链路测试，不涉及物理求解 |
| 第 1 章 | [给定 PDE 问题的求解](chapter-01-prescribed-pdes.md) | 按数学问题组织椭圆、扩散、输运、双曲、约束、耦合、高阶、谱、非局部、界面及随机 PDE；来源不决定目录 |
| 第 2 章 | [流体力学分析](chapter-02-fluid-mechanics.md) | 牛顿／非牛顿流体、不可压缩／可压缩流动、湍流、多相流、自由液面、薄膜流及稀薄气体流动 |
| 第 3 章 | [固体与结构力学分析](chapter-03-solid-mechanics.md) | 变形、应力、振动、稳定性、接触、塑性、黏弹性、损伤、断裂与疲劳 |
| 第 4 章 | [多体系统力学分析](chapter-04-multibody-mechanics.md) | 刚体与柔性体运动、连接约束、接触碰撞、摩擦及机构动力学 |
| 第 5 章 | [传热与热过程分析](chapter-05-heat-transfer.md) | 导热、对流换热、热辐射、相变传热及热物性变化 |
| 第 6 章 | [声学分析](chapter-06-acoustics.md) | 声传播、辐射、散射、吸收、热黏声学、气动声学及振声分析 |
| 第 7 章 | [电磁场与电路分析](chapter-07-electromagnetics.md) | 静电、导电、静磁、低频电磁、高频电磁、电路及场—路相互作用 |
| 第 8 章 | [光学与光子学分析](chapter-08-optics.md) | 几何光学、波动光学、干涉、衍射、偏振及光在介质中的传播 |
| 第 9 章 | [组分传输与化学反应分析](chapter-09-species-reactions.md) | 扩散、迁移、吸附、反应、反应流、燃烧及相关传质过程 |
| 第 10 章 | [电化学分析](chapter-10-electrochemistry.md) | 离子输运、电极反应、电化学界面及电化学能量转换过程 |
| 第 11 章 | [半导体与电子输运分析](chapter-11-semiconductor.md) | 载流子输运、产生与复合、电荷分布及相关器件物理 |
| 第 12 章 | [颗粒与散体力学分析](chapter-12-granular.md) | 颗粒运动、碰撞、摩擦、黏附、堆积及散体整体响应 |
| 第 13 章 | [多孔介质与渗流分析](chapter-13-porous-media.md) | 饱和／非饱和渗流、多相渗流、裂隙与双重介质、孔隙尺度流动及多孔介质中的输运 |
| 第 14 章 | [等离子体与带电粒子分析](chapter-14-plasma.md) | 放电、带电粒子输运、碰撞反应及电磁场作用 |
| 第 15 章 | 辐射输运与核工程物理分析 | 光子、中子等粒子的输运、散射、吸收、能量沉积及相关工程物理过程 |
| 第 16 章 | 材料组织与微观演化分析 | 相分离、晶粒长大、相变动力学及微结构演化 |
| 第 17 章 | [多物理场耦合分析](chapter-17-multiphysics.md) | 流固、热固、电热、压电、磁固、孔隙流固等跨领域相互作用，以及多场联合演化 |
| 第 18 章 | [系统级多领域分析](chapter-18-system-multidomain.md) | 集总参数与一维网络构成的机械、液压、气动、热、电等工程系统 |

## 细化与归属规则

1. **按领域设章，逐级细化能力范围。** 维度、稳态／瞬态、材料类型、能量与湍流等物理范围，以及方法要求，在节、子节和具体题目层展开。给定 PDE 章按数学问题组织。
2. **几何和工况属于算例。** 腔体、弯管、台阶、障碍物等不单独成为物理问题族；题目应声明支持的几何与条件范围。
3. **行业应用作为标签。** 汽车、航空航天、土木、岩土、生物医学、制造加工等应用可以涉及多章，不据此重复建立相同能力的题目。
4. **每题有主要归属，允许交叉标签。** 依据主要分析目标和能力要求确定归属。以换热为目标的分析主要归传热章，以流动为目标且包含热效应的分析主要归流体章；以跨场反馈和联合响应为核心的题目归耦合章。
5. **跨题覆盖与物理耦合分别评测。** 同一求解器分别完成流体题和结构题属于跨题能力；计算流体与结构相互作用属于耦合分析能力。生产任务可以组合不同章节的题目，无须为每种组合新建题目。
6. **题目规划与算例建设分开。** 算例来源、覆盖、制作、参考验证及完成状态另行管理。PDEBench、FOAMBench 等只承担算例来源的角色；没有现成来源不改变题目定义。

## 逐章实施入口

逐题清单列出范围与拆分，章级目录定位实际题目，进度和审阅记录保存完成情况及验证限制。题面／配置完成与正式数据、参考、预算校准和评测发布分别记录，不在此重复维护验收结论。

| 章 | 题目目录 | 逐题清单 | 进度与审阅 |
|---|---|---|---|
| 第 2 章 | [题目](../02-fluid-mechanics/README.md) | [清单](chapter-02-task-plan.md) | [进度](reviews/chapter-02-progress.md) |
| 第 3 章 | [题目](../03-solid-mechanics/README.md) | [清单](chapter-03-task-plan.md) | [进度](reviews/chapter-03-progress.md) · [实施与审阅](reviews/chapter-03-implementation.md) |
| 第 4 章 | [题目](../04-multibody-mechanics/README.md) | [清单](chapter-04-task-plan.md) | [进度](reviews/chapter-04-progress.md) · [实施与审阅](reviews/chapter-04-implementation.md) |
| 第 5 章 | [题目](../05-heat-transfer/README.md) | [清单](chapter-05-task-plan.md) | [进度](reviews/chapter-05-progress.md) · [实施与审阅](reviews/chapter-05-implementation.md) |
| 第 6 章 | [题目](../06-acoustics/README.md) | [清单](chapter-06-task-plan.md) | [进度](reviews/chapter-06-progress.md) · [实施与审阅](reviews/chapter-06-implementation.md) |
| 第 7 章 | [题目](../07-electromagnetics/README.md) | [清单](chapter-07-task-plan.md) | [进度](reviews/chapter-07-progress.md) · [实施与审阅](reviews/chapter-07-implementation.md) |
| 第 8 章 | [题目](../08-optics/README.md) | [清单](chapter-08-task-plan.md) | [进度](reviews/chapter-08-progress.md) · [实施与审阅](reviews/chapter-08-implementation.md) |
| 第 9 章 | [题目](../09-species-reactions/README.md) | [清单](chapter-09-task-plan.md) | [进度](reviews/chapter-09-progress.md) · [实施与审阅](reviews/chapter-09-implementation.md) |
| 第 10 章 | [题目](../10-electrochemistry/README.md) | [清单](chapter-10-task-plan.md) | [进度](reviews/chapter-10-progress.md) · [实施与审阅](reviews/chapter-10-implementation.md) |
| 第 11 章 | [题目](../11-semiconductor/README.md) | [清单](chapter-11-task-plan.md) | [进度](reviews/chapter-11-progress.md) · [实施与审阅](reviews/chapter-11-implementation.md) |
| 第 12 章 | [题目](../12-granular/README.md) | [清单](chapter-12-task-plan.md) | [进度](reviews/chapter-12-progress.md) · [实施与审阅](reviews/chapter-12-implementation.md) |
| 第 13 章 | [题目](../13-porous-media/README.md) | [清单](chapter-13-task-plan.md) | [进度](reviews/chapter-13-progress.md) · [实施与审阅](reviews/chapter-13-implementation.md) |
| 第 14 章 | [题目](../14-plasma/README.md) | [清单](chapter-14-task-plan.md) | [进度](reviews/chapter-14-progress.md) |
| 第 17 章 | [题目](../17-multiphysics/README.md) | [清单](chapter-17-task-plan.md) | [进度](reviews/chapter-17-progress.md) · [实施与审阅](reviews/chapter-17-implementation.md) |
| 第 18 章 | [题目](../18-system-multidomain/README.md) | [清单](chapter-18-task-plan.md) | [进度](reviews/chapter-18-progress.md) · [实施与审阅](reviews/chapter-18-implementation.md) |
