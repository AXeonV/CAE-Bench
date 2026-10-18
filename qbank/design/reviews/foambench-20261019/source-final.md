# FOAMBench 源移植审计复核

复核对象为 `qbank/02-fluid-mechanics/2.12-foambench` 当前拟冻结公开材料及逐题author/source.json；固定源仍为 `e37e8b61fbb1f3532dcfd2f2e8ab67e7c91c3ee2`。原始 `source-audit.md` 和 `coverage-source.json` 保留不动，本文记录修复后的判断。仅写报告与最终coverage，未修改公开文件，未运行生成器或solver。

## 结论

前轮P1、P2、P3均已修复；本轮对指定修复与新增改编记录未发现新的来源完整性阻断项。新增物理初态与滤波定义是显式的作者规范化，不宜声称逐格复现源OpenFOAM算例；现有记录已经作出这种区分。

重新核验仍为basic 110、advanced 16，共126个唯一源映射，无缺题、无重复。126条prompt的UTF-8实际SHA-256均与source-index一致，所有author存储的原prompt逐字匹配固定源。共有34题的至少一份审计目标文件较前次快照改变；当前全部instruction.md、DATA.md、author/source.json的SHA-256、修改文件列表、适用复核意见记录在 `final-coverage-source.json`。

## 前轮发现闭环

| 前轮问题 | 复核证据 | 判断 |
|---|---|---|
| P1 wedge_SA壁距指向不存在的无滑移壁 | `fb-advanced-wedge-sa/DATA.md`现定义d到最近固体壁，明确包括本题滑移楔面，排除入口/出口/对称边；source解释此选择 | 关闭。楔面q=0和滑移速度相容于该明确的移植模型定义 |
| P2 Cavity_LES、Cylinder_LES任意LES/DNS及可选滤波 | 两份DATA固定二维动态一方程闭合，给Ck/Ce、k输运及应力，给共同域内归一高斯测试滤波，Δ分别固定.005m和.25m，禁止修改模型/滤波/Δ | 关闭。保留源dynamic kinetic energy equation的建模类别；固定物理Δ与连续测试滤波仍是显式改编 |
| P2 obliqueShock_LES丢失Smagorinsky | DATA恢复代数Smagorinsky，Cs=.17、Δ=.05m，定义应力、Favre速度、无独立亚格子能量，去掉无关k输运责任 | 关闭。源Cs=.17保留；固定Δ替代cubeRootVol被source明确披露 |
| P3 author跨模型模板记录 | cavityLES只解释k=.00375；cavitySA解释q=3e-5；cylinderSA不再称LES；wedgeSA/obliqueKE不再包含LES滤波模板；障碍SA/SST分别记录实际模型 | 关闭。所抽查全部原受影响条目已按题型修订 |

固定滤波与高斯定义使当前模型成为确定的软件无关问题，内部数值网格仍由考生选择。该修复消除了原报告指出的“任意模型/核对应不同输出目标”，并不证明新连续动态闭合在全部状态下数值可解或与源离散闭合等价；本次无需数值验证，亦无这类等价宣称。

## 新增改编披露复核

**BernardCells全部10题。** DATA将原均匀横流改为ψ=1e-4 sin²(πx/9) sin²(πy) m²/s，u=(∂yψ,−∂xψ)。由混合偏导相消可知无散；四边上两个速度分量均为零。DATA明确连续解析初态优先于其单元平均存储，不把平均重建误当另一初态。全部source记录明确“将不相容均匀横流改为公开流函数生成的无散且无滑移相容扰动”，没有把这个新扰动归称为源原值。上下壁温度族差异、1000s/50s时间要求未被此次修订抹去。此为诚实披露的物理初态变化。

**advanced五道障碍题。** `Double_Square_SA`、`Diamond_Obstacle_SA`、`Diamond_Obstacle_KOMEGASST`、`Rectangular_Obstacle_SA`、`Rectangular_Obstacle_KOMEGASST`均给原始v=(1,0)及u0=v−∇φ，Δφ=0，入口∂nφ=0、固壁∂nφ=v·n、出口φ=0。条件明确其只保留入口法向初态、固壁无穿透；无滑移切向启动在t>0施加。DATA同时说明initial数组存原始v而非最终u0，故读者无需猜测何时投影。source均明确写入原均匀速度穿障碍法向和公开Helmholtz投影，不再冒称原均匀速度就是物理初态。初压改为约束结果也已披露。此为诚实披露的物理初态规范化。

**出口规则。** 当前pressure_open明确回流仅采用给定场的切向分量，法向由压力与连续性求解；障碍题主条件段同样说明，消除了零回流向量被误作全速度强制为零的歧义。该表述给出了原pressureInletOutletVelocity的所选物理解释，不构成新增源速度数值改写。

## 边界

本次确认源身份、任务类别、改编披露和修复闭环。未运行求解器，未生成数据，未审阅数值参考与资源达标；不将缺少这些本阶段成果作为缺陷。最终coverage记录的是本轮读到的文件字节快照，公开文件若再修改需重新计算相关哈希。

## 最终局部文案刷新

全量rebuild冻结后重算126题文件哈希：相较前轮最终快照，恰有44份DATA.md改变，instruction.md与author/source.json均未改变。42道basic补显式task，两个advanced Cylinder将“入口切向启动”改为“入口瞬时启动”；前者明确索引身份，后者纠正启动描述，均不改变映射、模型或物理结论。126映射与全部源prompt哈希重新验证一致。`final-coverage-source.json`已刷新为此冻结快照。

## EOF格式刷新

随后40份basic DATA.md统一为单个结尾换行。逐份证明此前记录的SHA-256精确等于当前文件字节追加一个同格式换行后的SHA-256，因此变化仅删除一个多余EOF空行；全部instruction.md与author/source.json哈希仍一致。最终coverage已刷新，源映射及物理结论不变，未重做或扩大源审计。
