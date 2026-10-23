# RC2 独立设计审阅

结论：**需修订评价结论与明确设计取舍**。全部82题的公开 instruction.md、DATA.md 已逐题核读；共同 CONTRACT 已完整核读且82份逐份核SHA相同。本轮有具体反例的评价偏置及设计哲学适用范围待决项，不存在依据本轮阅读即可宣布82题数学、数值或资源验收通过的结论。

本报告不改变编号、纳入范围、case阈值或实现。评分尺度的问题是已经公开定义的设计选择所产生的偏置，**不是已经证实的文档—实现冲突**；实际判题器、参考、样例及隐藏输入均未阅读。

## 独立性、材料与方法

本审阅从新的独立审阅上下文开始，未接收作者推导、既有审阅结论或实现。只读取协调方指定的 PHILOSOPHY、design/README、chapter-01-prescribed-pdes、chapter-02-fluid-mechanics、chapter-02-task-plan，以及 public-whitelist.json 中 role=statement/contract 的文件。白名单清单含样例路径，但没有打开任何样例、隐藏数据、作者报告、生成器、参考解、评分配置或求解器实现。仅以文件列表和git元数据确认工作区状态。

材料按批读取；对12题CFD2.1与部分能量题的重复模板，以已经全文阅读的基文加完整逐行差分复核目标文件全文，未省略新增或修改的内容。初次过大输出截断的段落另行补读，不将文件被工具读入等同于完成审阅。246份题内文件逐份从实际RC2解包路径计算SHA256，与白名单全部相符；164份题面/DATA均纳入逐题判断。82份CONTRACT的共同SHA256为 `130d4416fd533812493780c8bc6afbc0a158de6800b59bbec14a852f3cf1c063`，相同内容只需阅读一次。全部路径、SHA、行数及逐题结论见配套 design-review-summary.json。

审阅检查能力定位、相邻能力的实质差异、来源替换后语义是否保持、建模责任与共同观测是否一致。对可变问题族尝试不同几何、初态、驱动或材料响应下的合法问题；对固定专题区分观测变化和实际物理问题变化。资料不足不自动转换为数学缺陷，自主建模不自动等于欠定。

## 明确的设计问题与具体反例

### DR-01：压力容差随表示基准显著改变，不能等同于统一压差精度（P2）

位置：CFD2.1全部12题 instruction.md“评价”的 `atol+0.01×|参考值|`、pressure的0.1Pa绝对容差，与各DATA“分析声明”允许 absolute/gauge 的组合。另见 viscoelastic-steady / transient 的 DATA“连续模型与闭合”允许任意有限 reference_pressure，而 instruction 对pressure使用0.2Pa+2%绝对静压。

反例：同一不可压缩解，选参考绝对压100000Pa，某点绝对静压100010Pa、表压10Pa。两个合法表示下的压力容差分别为1000.2Pa与0.2Pa。候选在该点出现+10Pa误差时，absolute表示通过，gauge表示失败。若需保持平均压力规范，可在两个等体积区域分别加+10Pa和-10Pa；此误差不靠常数偏置消除，仍具有同一表示偏置。这里评估的是公开评价函数的数学性质，不声称实际case存在这样的候选或输入。

影响：同一物理压差误差因背景或表示而得到不同结果，不能将通过分数解释为共同的1%压力变化精度。Oldroyd-B封闭域把平均压力设成任意reference_pressure，同样可以在不改变速度/构象的情况下任意放大相对压力容差。

最小建议：在保持全部题号、物理范围、输出压力及规范约束的前提下，明确评价是“绝对静压相对精度”还是“流动压差精度”。若目标为后者，使用公开、物理等价的差压尺度制定容差，再核对实际参考与case；例如按公开基准计算压力扰动尺度，仍直接比较原压力误差，不允许候选私自去均值。不能只改文案而不核对判题配置，也不建议本轮盲调阈值。

分类：**明确评价偏置，发布精度声明待决；没有证据判定实现不符文档**。界面双流体题已经明确用 `|p_ref-pressure_reference|` 定相对尺度，说明库内存在与压差目标一致的处理，但不能直接照抄到没有同类公开基准的所有气体题。

### DR-02：24题兼容专题只检验固定解，须与统一“问题族泛化”定位明确协调（P2）

位置：全部2.13题 instruction 首段“固定连续问题”、DATA的空physics.parameters、固定全部初边值/参数/域及唯一终止时刻；对照 PHILOSOPHY第1—3节和design/README第0/1章职责。

反例：cc-pipe-flow-disk-evp固定Re=10000、m=5、kz=1，只输出一个最右增长率；任意合法ID与权重输入都对应同一个数。cc-1d-diffusion固定域、初态、边界、扩散系数和终时，两个合法输入仅在观测坐标/权重不同；同一个事先算好的连续解插值器足以覆盖全部公开契约。改变观测数量或坐标有I/O与重建意义，但没有产生第二个不同物理初边值问题。

影响：这24题可以有效承担固定基准兼容、求解/重建精度与移植回归测试；其通过数不能自动充当24个独立可复用问题族的泛化证据。其以来源专题组织、按几何或固定题单命名，与现行总哲学存在未显式声明的例外。数学定义大多已经自包含，替换数值来源并不必然破坏语义；因此这里不判定需要阅读来源软件。

最小建议：**保留全部24题号与纳入范围**，在设计规范中说明固定基准兼容专题的地位，成绩分层报告该专题与43个流动物理问题族、13个给定PDE问题族及2个基础测试。不要将82个题目数量写成82种互不重叠的泛化能力。若未来要扩展为物理问题族，另走授权设计流程，本轮不凭审阅擅增参数或改题。

分类：**明确的总定位与专题定位不一致，需要设计/发布表述决定；不是要求删除或迁移现有编号**。

## 待核实项

1. **多模型评价依据（9个湍流任务）**：RANS/URANS自选闭合、尺度解析允许DNS/LES且误差计入共同目标，公开定义本身不矛盾。URANS已给k、积分长度及各向同性初始应力，热URANS还明确初始热方差/协方差为零，故不应以缺少某来源软件的epsilon/omega为由要求补字段。待由维护验收核对各case参考不确定度、模型差异与已公开容差是否相容；本轮无权从隐藏参考推断公平性，也没有证据说5%容差必然不合理。
2. **连续数学目标与参考的对应**：Darcy/吸附扩散明确给非局部单元平均边界，可压缩PDE明确给密度加权定向黏性及守恒平均派生观测。它们是非标准但明确的数学问题，不能因为不像惯常软件配置就改回标准方程。本轮不能验证来源轨迹是否实现这些连续目标；应由参考/数据审计另核证据。
3. **预算与实际覆盖**：全库公开上限、物理适用性保证、稳定分支及有限迹声明是问题定义，不构成已经完成的计算证据。本轮没有运行任何求解器，不判定高维Boltzmann、湍流统计、瞬态可压缩或接口流在资源内必然可解/不可解，也不声称实际case覆盖题目全部条件变体。

## 可选优化与跨题边界

- cc-2d-convection与cc-2d-inviscid-burgers的PDE、域、初态、熵选择与边界相同，区别是终时0.32/0.40；后者公开说明保留不同来源身份。这应记录为同一能力的两个固定基准实例，保留逐题分数与编号，但不要将其当成两个新能力。两种黏度的盖驱方腔同理，改变雷诺数/终时有数值难度差异而不是新模型责任。
- cc-flow-past-circular-cylinder固定流函数基准20，但psi按未去背景NRMSE评价。psi的加常数不改变速度/涡量，而固定20进入分母；其psi通过精度不是流动扰动的10%精度。可选在评分意义中明确，或另行校准物理扰动尺度。omega仍独立受检，本轮不声称常数psi足以通过全题。
- gas-film及热可压缩/等温气体任务的绝对压相对容差对小压差不敏感，但绝对压同时决定气体密度，有合理的热力学目标，不能直接用DR-01的不可压缩规范平移论证宣判这些题错误。若要宣称小压差/载荷精度，须单独核对观测与尺度；gas-film的load已是独立观测但并非每例必选。
- inviscid-compressible-steady-2d/3d明确限于等熵静水平衡u=0。这个限定有助于避免未知环流分支，属于可自洽的变几何/体加速度/库存平衡问题族，但题名及能力统计应保留“本版仅静水平衡”的限制，不能宣称验证一般稳态Euler流动。

43道流动题内的2D/3D、稳态/瞬态、常黏度/剪切响应、等温压缩/热反馈、RANS/URANS/统计、界面/浅水/薄膜/动理学/记忆材料均有实际责任差异。共用solver不构成重复；也不要求按每种闭合模型拆题。第1章PDE与第2章物理题虽可描述同类现象，前者明确数学模型、后者明确材料和方法责任，不能只按velocity/pressure字段同名判重。第0章回传与判题链路测试无泛化物理承诺，符合基础设施职责。

来源独立性方面：除专题组织的DR-02外，本轮未发现公开求解定义要求读取某来源软件的隐藏配置。所有自定义连续采样、条件和固定响应均由本题两文件与CONTRACT显式定义。该结论仅说明公开设计，不说明参考数据已脱离来源误差。

## 逐题覆盖

下表“未发现”仅表示本轮公开设计阅读未发现其他未决矛盾；不等于数值、资源或隐藏judge公平性验收。每题均核读instruction与DATA，并核对共同CONTRACT版本。F项指上述明确设计问题；Q项指资料受限的待核实项。

| # | task | 设计判断与边界 | 两个合法输入的能力检查 |
|---|---|---|---|
| 1 | `smoke-test` | 协议回传；允许固定解法，职责合理 | 换空间维度/分量类型与多时间轴，核对数组身份。 |
| 2 | `case-grading-test` | 完整场回传与稀疏评价链路；区别于smoke-test | 改变三角形节点tag/观测分量或时刻，目标仍为完整输入场。 |
| 3 | `darcy-flow-2d` | 变系数椭圆＋公开非局部平均边界；不是物理渗透率题 | 常系数中心样本与棋盘正系数样本导致不同稳态。 |
| 4 | `heat-conduction-steady-2d` | 混合边界椭圆及纯Neumann规范 | Dirichlet驱动与混合法向通量/平均温度规范。 |
| 5 | `diffusion-sorption-1d` | 有限参数但c0可变的非线性迟滞扩散，非局部边界已明定 | c0=0与c0=0.2的入口启动响应不同。 |
| 6 | `heat-conduction-transient-2d` | 连续P1初态与扩散演化；输出时刻非内部步长 | 不同空间初态与Dirichlet/Robin边界组合。 |
| 7 | `reaction-diffusion-1d` | 标量logistic反应扩散，独立于二维反应系统 | 不同周期初态/反应速率组合。 |
| 8 | `reaction-diffusion-2d` | 双变量非线性反应扩散，完整初值和输出细单元子集已区分 | 两种不同完整激活/抑制初态，保持同一细单元观测子集。 |
| 9 | `advection-1d` | 周期线性平流，平均初态与平均输出相容 | 脉冲与多峰初态的平移；非仅改变时刻。 |
| 10 | `shallow-water-2d` | 平床径向溃坝的有限子族，不能外推一般地形浅水 | 由输入改变中心圆形高水区单元集合，水深前沿不同。 |
| 11 | `burgers-1d` | 标量黏性守恒律，不等于无黏熵输运 | 不同周期初态/黏度控制的波陡化与衰减。 |
| 12 | `incompressible-navier-stokes-2d` | 非均匀标量强迫耦合约束系统；预投影t0例外公开 | 改变初始tracer或静态矢量强迫，不能仅按NS无标量求解。 |
| 13 | `compressible-navier-stokes-1d` | 定向黏性PDE及守恒平均派生状态已明确，不改成标准NS | 周期随机初态与外推激波管；明确各配置参数范围。 |
| 14 | `compressible-navier-stokes-2d` | 二维方向耦合与定向黏性模型 | 二维密度/速度初态变化；守恒平均压力不同于平均压力。 |
| 15 | `compressible-navier-stokes-3d` | 三维方向耦合与守恒平均观测 | 三方向初始速度/密度变化；不能全化为二维。 |
| 16 | `newtonian-incompressible-steady-2d` | 二维稳态不可压牛顿；DR-01 | 不同孔洞几何/速度边界与体加速度驱动。 |
| 17 | `newtonian-incompressible-steady-3d` | 完整三维稳态不可压牛顿；DR-01 | 三维障碍物与不同牵引/运动壁驱动。 |
| 18 | `cc-1d-burgers-equation` | 固定周期黏性Burgers；DR-02 | 仅更换观测坐标/权重/ID（谱题仅ID/权重）不改变物理问题。 |
| 19 | `cc-1d-diffusion` | 固定矩形初态扩散；DR-02 | 仅更换观测坐标/权重/ID（谱题仅ID/权重）不改变物理问题。 |
| 20 | `cc-1d-euler-shock-tube` | 固定Sod熵解/反射壁；DR-02 | 仅更换观测坐标/权重/ID（谱题仅ID/权重）不改变物理问题。 |
| 21 | `cc-1d-linear-convection` | 固定周期对流扩散；DR-02 | 仅更换观测坐标/权重/ID（谱题仅ID/权重）不改变物理问题。 |
| 22 | `cc-1d-nonlinear-convection` | 固定周期Kruzkov熵解；DR-02 | 仅更换观测坐标/权重/ID（谱题仅ID/权重）不改变物理问题。 |
| 23 | `cc-2d-burgers-equation` | 固定二维黏性Burgers；DR-02 | 仅更换观测坐标/权重/ID（谱题仅ID/权重）不改变物理问题。 |
| 24 | `cc-2d-convection` | 固定二维对角熵输运t=0.32；DR-02 | 仅更换观测坐标/权重/ID（谱题仅ID/权重）不改变物理问题。 |
| 25 | `cc-2d-diffusion` | 固定二维初态扩散；DR-02 | 仅更换观测坐标/权重/ID（谱题仅ID/权重）不改变物理问题。 |
| 26 | `cc-2d-inviscid-burgers` | 同对角熵输运，仅终时0.40不同；DR-02 | 仅更换观测坐标/权重/ID（谱题仅ID/权重）不改变物理问题。 |
| 27 | `cc-2d-laplace-equation` | 固定混合边界Laplace势；DR-02 | 仅更换观测坐标/权重/ID（谱题仅ID/权重）不改变物理问题。 |
| 28 | `cc-2d-linear-convection` | 固定线性脉冲平移/间断点值；DR-02 | 仅更换观测坐标/权重/ID（谱题仅ID/权重）不改变物理问题。 |
| 29 | `cc-2d-navier-stokes-cavity` | 固定nu=0.01方腔/压力去均值；DR-02 | 仅更换观测坐标/权重/ID（谱题仅ID/权重）不改变物理问题。 |
| 30 | `cc-2d-navier-stokes-channel` | 固定周期通道启动流，只输出u；DR-02 | 仅更换观测坐标/权重/ID（谱题仅ID/权重）不改变物理问题。 |
| 31 | `cc-2d-poisson-equation` | 固定双Gaussian Poisson势；DR-02 | 仅更换观测坐标/权重/ID（谱题仅ID/权重）不改变物理问题。 |
| 32 | `cc-2d-steady-heat-equation` | 固定四边恒温传热/背景20评分；DR-02 | 仅更换观测坐标/权重/ID（谱题仅ID/权重）不改变物理问题。 |
| 33 | `cc-2d-unsteady-heat-equation` | 固定Gaussian热源扩散/背景1评分；DR-02 | 仅更换观测坐标/权重/ID（谱题仅ID/权重）不改变物理问题。 |
| 34 | `cc-fully-developed-turbulent-channel-flow` | 固定Cess闭合双壁通道，不允许换模型；DR-02 | 仅更换观测坐标/权重/ID（谱题仅ID/权重）不改变物理问题。 |
| 35 | `cc-lid-driven-cavity` | 固定nu=0.1方腔/压力去均值；DR-02 | 仅更换观测坐标/权重/ID（谱题仅ID/权重）不改变物理问题。 |
| 36 | `cc-flow-past-circular-cylinder` | 固定外圆环涡量流函数/基准20；DR-02 | 仅更换观测坐标/权重/ID（谱题仅ID/权重）不改变物理问题。 |
| 37 | `cc-1d-kdv-burgers-equation` | 固定KdV-Burgers周期演化；DR-02 | 仅更换观测坐标/权重/ID（谱题仅ID/权重）不改变物理问题。 |
| 38 | `cc-2d-rayleigh-benard-convection` | 固定RBC及确定性扰动/压力去均值；DR-02 | 仅更换观测坐标/权重/ID（谱题仅ID/权重）不改变物理问题。 |
| 39 | `cc-2d-shear-flow-with-tracer` | 固定投影剪切初态与示踪剂；DR-02 | 仅更换观测坐标/权重/ID（谱题仅ID/权重）不改变物理问题。 |
| 40 | `cc-pipe-flow-disk-evp` | 固定谱参数，只交同一个最右实增长率；DR-02 | 仅更换观测坐标/权重/ID（谱题仅ID/权重）不改变物理问题。 |
| 41 | `cc-lane-emden-equation` | 固定Lane-Emden正无节点基态；DR-02 | 仅更换观测坐标/权重/ID（谱题仅ID/权重）不改变物理问题。 |
| 42 | `newtonian-incompressible-transient-2d` | 二维瞬态不可压牛顿；DR-01 | 改变相容初速度及随时间变化的壁速。 |
| 43 | `newtonian-incompressible-transient-3d` | 三维瞬态不可压牛顿；DR-01 | 三维初速度与非均匀时变加速度。 |
| 44 | `generalized-newtonian-incompressible-steady-2d` | 二维无记忆剪切响应材料，区别于常黏度及黏弹性；DR-01 | 截断幂律与Cross材料响应输入。 |
| 45 | `generalized-newtonian-incompressible-transient-2d` | 二维瞬态剪切响应；DR-01 | 不同相容初速度与Carreau/幂律响应。 |
| 46 | `generalized-newtonian-incompressible-steady-3d` | 三维稳态剪切响应；DR-01 | 三维几何与Cross/Carreau-Yasuda材料。 |
| 47 | `generalized-newtonian-incompressible-transient-3d` | 三维瞬态剪切响应；DR-01 | 三维相容初态和不同剪切率依赖。 |
| 48 | `newtonian-isothermal-compressible-steady-2d` | 二维稳态等温压缩，不预测能量；DR-01 | 理想气体与线性barotropic响应，带库存/开口条件。 |
| 49 | `newtonian-isothermal-compressible-transient-2d` | 二维瞬态等温压缩；DR-01 | 不同初密度/速度，保持Ma约束。 |
| 50 | `newtonian-isothermal-compressible-steady-3d` | 三维稳态等温压缩；DR-01 | 三维几何/密度响应变化，不限定单一通道。 |
| 51 | `newtonian-isothermal-compressible-transient-3d` | 三维瞬态等温压缩；DR-01 | 三维初态与时变允许边界。 |
| 52 | `newtonian-lowmach-steady-2d` | 二维封闭域Boussinesq热反馈，固定响应自洽 | 改变重力/壁温分布与切向壁运动。 |
| 53 | `newtonian-lowmach-transient-2d` | 二维瞬态Boussinesq热流 | 改变相容初温/初速度与时变热条件。 |
| 54 | `newtonian-lowmach-steady-3d` | 三维封闭域热流，非简单二维扩展 | 三维热条件分区与体加速度。 |
| 55 | `newtonian-lowmach-transient-3d` | 三维瞬态热流，状态与时刻明确 | 改变三维初温/初速度与时间驱动。 |
| 56 | `inviscid-compressible-steady-2d` | 本版仅平滑等熵静水平衡u=0；保留能力限制 | 改变体加速度与库存/几何，压力温度分层变化。 |
| 57 | `inviscid-compressible-transient-2d` | 二维无黏热压缩瞬态，可有熵可容许间断 | 两种无真空正密度/正温度初态，产生不同压缩波。 |
| 58 | `inviscid-compressible-steady-3d` | 三维等熵静水平衡，不等于一般稳态Euler | 三维几何与保守体加速度/库存变化。 |
| 59 | `inviscid-compressible-transient-3d` | 三维无黏可压缩瞬态 | 三维初始速度/热状态变化，含完整动量能量。 |
| 60 | `newtonian-compressible-transient-2d` | 二维黏性导热可压缩瞬态；普通单元平均 | 不同初密度温度与壁面热条件。 |
| 61 | `newtonian-compressible-transient-3d` | 三维黏性导热可压缩瞬态 | 三维初态与温度相关物性变化。 |
| 62 | `rans-steady-2d` | 二维定常RANS平均场；具体闭合自由，Q1 | 改变封闭域驱动/几何；不固定来源模型变量。 |
| 63 | `rans-steady-3d` | 三维定常RANS；不等同二维RANS，Q1 | 三维几何/驱动改变平均流结构。 |
| 64 | `urans-transient-3d` | URANS标准化公共二阶初态明确；Q1 | 相同平均速度下不同公开k/积分尺度的建模初态。 |
| 65 | `resolved-statistics-3d` | 完整瞬时初态＋三维尺度解析离散统计；Q1 | 不同三维初速度与不同显式统计区间/采样。 |
| 66 | `isothermal-rans-3d` | 等温气体RANS，Favre速度/Reynolds密度压力；Q1 | 不同气体库存与壁面驱动。 |
| 67 | `thermal-rans-3d` | Boussinesq热RANS，共同物理观测；Q1 | 不同壁温/重力与机械驱动。 |
| 68 | `thermal-urans-3d` | 热URANS标准化热二阶初态为零；Q1 | 不同公开平均初温、k/长度及驱动。 |
| 69 | `thermal-statistics-3d` | 先空间平均后样本热统计，非RANS变量；Q1 | 完整瞬态热初态与离散统计区间改变。 |
| 70 | `immiscible-interface-2d` | 双侧不可压牛顿、无表面张力界面，初态精确0/1 | 不同相布局/密度比与体加速度。 |
| 71 | `immiscible-interface-3d` | 完整三维双流体界面，压力右迹条件明确 | 不同三维相块布局与三维体加速度。 |
| 72 | `gas-film` | 二维面内降维气膜，密度由绝对压、通量为体积通量 | 不同间隙场/时间轨迹与壁面切向速度。 |
| 73 | `fully-wet-steady` | 全湿稳态浅水，至少储槽及分支存在保证 | 不同床坡/储槽状态与底摩擦。 |
| 74 | `fully-wet-transient` | 全湿瞬态浅水，重力波/熵条件 | 不同初水深/水平速度及床面。 |
| 75 | `wetting-drying` | 干湿守恒熵解，干处u=0，不以数值阈值定义物理 | 不同干床布局与相容水深初态。 |
| 76 | `transition-gas` | 三维硬球Boltzmann碰撞与明确气壁混合反射 | 不同储槽与壁温/适应概率，非BGK替代。 |
| 77 | `free-molecular` | 无碰撞且可多次反射，孤立自由轨道已排除 | 不同三维几何/壁温/反射概率。 |
| 78 | `viscoelastic-steady` | 固定Oldroyd-B历史响应、入口构象与压力规范；DR-01 | 不同入口预伸长构象与通道几何/驱动。 |
| 79 | `viscoelastic-transient` | 完整相容速度/正定构象初态；DR-01 | 相同速度但不同初始预应力产生不同松弛过程。 |
| 80 | `newtonian-compressible-steady-2d` | 二维稳态黏性导热气体，库存固定压力水平 | 不同壁面热分区/驱动及气体库存。 |
| 81 | `newtonian-compressible-steady-3d` | 三维稳态黏性导热气体 | 三维几何/热条件及温度物性变化。 |
| 82 | `compressible-thermal-rans-3d` | 热可压缩RANS；Favre速度/温度与Reynolds压力/密度；Q1 | 不同气体库存、壁温与机械驱动。 |
