# 独立考生题面审阅：migration-soret-scaling-repair

- 模式：statements。
- 最终结论：**本轮未发现未决问题**。数学问题、源码修复边界及完整结果契约足以从公开三文件理解。初审发现一处输出 key 集合冲突，已按下述有界复核关闭。
- 样例状态：未纳入；本次白名单只有公开三文件，未读取样例或实际公开包。不能据此确认公开包可运行、可信适配器行为或参考数值正确。
- 独立性：本审阅上下文未读取 author、隐藏 cases/reference、源码实现、参考解、生成器或其他审阅报告；未实现修复，未运行模型或求解器。只在本审阅目录写报告。

## 版本绑定与允许材料

基线 HEAD：`6da63a4203b144fc22fbbc0a598a59f33b960e46`。审阅时 instruction.md、DATA.md 均为未跟踪文件；以下 SHA256 是实际工作树版本，不能以 HEAD 代替。

| 文件 | SHA256 |
|---|---|
| qbank/19-solver-repair/19.3-transport/migration-soret-scaling-repair/instruction.md | C273FF5C708EFD7578852A06C565061205B3B28FD10A0BCF4F489F271CF4F8F6 |
| qbank/19-solver-repair/19.3-transport/migration-soret-scaling-repair/DATA.md | 099E93D85614463E91DFC69BE52C68F9F2BD7ADA09BB7D7235963CDBD433B578 |
| docs/CONTRACT.md | 130D4416FD533812493780C8BC6AFBC0A158DE6800B59BBEC14A852F3CF1C063 |

流程材料：根 AGENTS.md、caeoj-candidate-review/SKILL.md 及其 references/workflow.md。对祖先和公开文件所在目录的精确 AGENTS.md 路径进行了存在性检查，未发现额外适用文件。没有扩大到题目目录读取其他材料。

## 发现与关闭历史

### F1 / P2 / 已关闭：输出 HDF5 的完整 key 集合自相矛盾

初审 DATA SHA256：`B228A7315B4DDEE8858F9BE281E75FC8225A92BC8D0446012223B7169DA8DC79`。位置：DATA.md:40；CONTRACT.md:310–316。以下保留原发现。

DATA 写“输出 HDF5 有且仅有下列三个 float64 数组”，表中仅 concentration、temperature、potential。CONTRACT 则要求结果同时保存输出位置 IDs 及时间轴数组，并明确所有额外或缺失 key 均不合法。这里 nodes 使用 node_ids，instant 使用 times，故 CONTRACT 要求五个 key：concentration、temperature、potential、node_ids、times。其中 times 本身也是 float64 数组。

最小反例：结果只保存三个 `(1,N,1)` 场数组，满足 DATA 的排他描述，但违反 CONTRACT；再复制 int64[N] node_ids 和 float64[1] times，满足 CONTRACT，却不再只有 DATA 所列的三个 float64 数组。即使考生只交源文件、由可信驱动写 HDF5，这仍使公开的观察和适配器责任无法一致解释。

影响：考生无法从三文件唯一判断合法结果文件；不同实现或本地验证可能据不同文档判定缺失/额外数组。

最小建议：将 DATA 改为“三个输出场数组”，随后引用 CONTRACT §9 的 IDs/时间复制规则，并明确本题完整结果 key 集合为上述五项，不复制四个仅边界位置使用的 IDs。

关闭复核：重新只读完整 DATA.md 并核验实际 SHA256 为 `099E93D85614463E91DFC69BE52C68F9F2BD7ADA09BB7D7235963CDBD433B578`。输出段现在称“三个结果 field”，显式另要求按 CONTRACT 保存 node_ids、times，故五个 key 的集合及身份/时间轴责任已一致。其余 DATA 内容与初审一致；instruction.md、CONTRACT.md 的 SHA256 均未变化。F1 关闭，当前无未决问题。没有读取作者材料、源码、隐藏数据或样例。

## 逐项覆盖与可做题判断

| 检查项 | 判断与公开依据 |
|---|---|
| 电迁移 | DATA:9 明确等温、DT=0、两端 Dirichlet、带符号整数 z、e/kB 数值及 J 与守恒方程；无须从源码补漂移正负号。 |
| Soret | DATA:11 明确 z=0、电势恒定、底端 Dirichlet、顶端零总通量、DT 正负号及弱式；顶端并非零浓度梯度，含义明确。 |
| Y/c/密度 | DATA:7 定义 Y、c=ρY、χ 两种模式，给 D、DT 单位和 DTabs=ρDTrel；两种 J 均为质量通量，绝对浓度模式无需另乘 ρ。 |
| 合法域与零值 | DATA:7、25–34 给定浓度物理范围、六参数范围、mode/units 枚举、z 整数范围、两模式约束、驱动力上限、Soret 平衡剖面范围；DT=0、z=0 与质量分数零均有公开依据。所有数值有限由 CONTRACT 统一保证。 |
| 非默认辅助变量名 | DATA:13 明确 ThermalField、ElectricField、Conc 和绑定关键词，Equation 中 Absolute Mass 设置及零系数关键词省略。考生保留真实模块读取这些绑定的能力属于已公开责任，不是隐藏要求。 |
| 离散 | DATA:13、17–19 固定给定均匀完整 QUAD4 网格、标准 Galerkin、无 bubbles/stabilization、UMFPACK；无网格重建自由。参考为有限元节点解由 instruction:11 明确。没有用连续解析曲线替代离散答案的依据。 |
| 边界与顺序 | DATA:3、9、11、34–36 明确三场侧边齐次自然边界、上下条件、四边物理组和位置、先温度电势后浓度。矩形角点的侧边自然条件不产生额外独立 Dirichlet 冲突。 |
| 节点与输出 | DATA:36、40–48 明确全部节点、node_ids 身份顺序、三个场、单位、shape 和有限性；CONTRACT:120、149 定义递增及对应索引。完整 key 集合经修订已与 CONTRACT 一致，F1 已关闭。 |
| 修改与 API 边界 | instruction:5、7 明确只交普通 AdvectionDiffusion.F90、真实替换路径、保留公开接口与模块求解、禁止其他文件和绕过求解；运行接口及可信驱动不作密度补偿明确。 |
| 构建、资源和评分 | instruction:9–13 给编译环境、配置命令、目标、构建路径、4 CPU/4 GiB、构建180秒/逐例20秒、各场绝对/相对容差、逐值接受条件、按文件通过比例及基础设施错误分类，未发现必须从私有评分配置补充的要求。 |

## 实际验证与限制

完成了三文件交叉阅读、维度/符号一致性检查、合法域和索引约定核对，并构造 F1 的最小反例。未检查真实输入、样例、公开包内文件、编译依赖安装情况、源码 API 实际实现、驱动输出和数值参考；也未验证构建或逐例时间能否达标。

已完成 F1 修订后的 DATA SHA256 重新绑定与输出段/CONTRACT 一致性复核，并核对其余二文件版本未变。其他材料如有变化，须核对版本后判断是否需要扩大复核。当前结论不外推为隐藏数据正确、实际可编译或资源达标。

