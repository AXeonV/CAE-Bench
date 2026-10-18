# FOAMBench 源题移植完整性审计

审计对象为 `qbank/02-fluid-mechanics/2.12-foambench`，源固定为 `e37e8b61fbb1f3532dcfd2f2e8ab67e7c91c3ee2`。本次只写审计记录；未运行仓库生成器、OpenFOAM 或任何 solver，未修改公开材料。检查目标是题面迁移完整性，不要求本阶段数据、参考、运行资源或正式评测就绪。

## 结论

题目身份覆盖完整：basic 110、advanced 16 共126；索引无缺题、无重复源映射。126条源 prompt 的UTF-8 SHA-256均与索引一致，126份author所存prompt亦逐字匹配原JSON。存在明确需要修复的SA壁距定义问题；另三道LES保留了流动场景，但其特定闭合任务被实质放宽，属于已部分披露的改编忠实性问题，不是软件无关化本身的问题。

## 发现

### [P1] SA-wall-distance：楔面SA方程的壁距指向不存在的无滑移壁

- sourcekey：`advanced:wedge_SA`；目标 `fb-advanced-wedge-sa/DATA.md:29`、`:33`、末尾额外状态段。
- 第29行全部固体边界为滑移楔面或对称边；第33行却定义 `d 为到最近无滑移壁的距离`。域内没有这样的壁。随后又要求楔面q=0，并特别说明其不等于无滑移。
- 反例：楔面上方任一内部点，按文字无法求有限d；取d=∞会消去SA破坏项，取几何楔面距离则保留破坏项，得到两个不同模型。并非缺参考或资源问题。
- 建议：明确d是否包含指定的滑移楔面。若选择几何壁距，写清其为本题SA模型壁，即使速度滑移也计入距离，并在author中披露；若选无壁极限，应明确d=∞及q=0边界为何保留。`counterFlowFlame2D_SA`已有明确无壁极限，可作为表述风格参考。

### [P2] LES-model-fidelity：三道LES的特定物理闭合被泛化为任意LES/直接解析

- sourcekey：`advanced:obliqueShock_LES`、`advanced:Cavity_LES`、`advanced:Cylinder_LES`。
- 目标对应DATA的“本题要求二维滤波尺度解析”段（obliqueshock为第31行）。
- 源obliqueShock prompt明确Smagorinsky，`constant/momentumTransport`亦给Smagorinsky、Cs=.17、cubeRootVol；cavity/cylinder明确dynamic kinetic energy equation model。目标三者却共用同一段，允许动态一方程闭合、“其他LES／直接解析方法”、模型与滤波核自选。
- 反例：源Smagorinsky题按目标允许dynamicKEqn甚至直接解析，无须遵守Smagorinsky的本构机制；两个不同滤波核作用于同一解析场仍会产生不同的“滤波速度”，当前没有统一输出滤波定义。这比移除软件、离散器、网格预算和固定dt更进一步，改变了所求模型。
- author已披露放开软件特定滤波或模型实现自由，故不判为隐瞒改编或机械误译。但“软件特定”措辞不足以表明Smagorinsky与dynamicKEqn属于不同闭合目标；obliqueShock目标甚至保留了无关dynamicKEqn措辞。
- 建议：保留模型名对应的闭合机制，给软件无关方程、常数与可解释滤波尺度定义，内部数值算法仍完全自由；或明确把它们标记为改变模型范围的派生题，避免称为完整保留源题建模要求。容差校准不能代替模型定义。

### [P3] 来源记录模板的无关内容

`fb-advanced-cavity-les/author/source.json`称采用prompt `q=3e-5、墙q=0`，但该题prompt只给k=.00375及k/nut壁函数。`fb-advanced-cylinder-sa/author/source.json`称“源LES”，`fb-advanced-wedge-sa/author/source.json`与`fb-advanced-obliqueshock-ke/author/source.json`也重复LES滤波解释。数值任务本体未因此丢失，但会误导后续维护者判断改编原因。建议按每题实际选择重写对应adaptation，而非共享跨模型模板。

## 变体与物理量核对

全部basic族均审阅基准prompt及其余9个prompt差异，逐题核对目标参数与条件。每题差异和实际哈希记录于 `coverage-source.json`，不是仅统计文件数。

| basic族 | 已核对差异与解释 |
|---|---|
| obliqueShock（10题） | 逐变体核对入口U、顶边U、入口T、顶边T；R=5/7替代舍入值已披露，内部初态统一2.9/1/1按配置。 |
| squareBend（10题） | 逐变体核对入口温度、mu、Pr；原dt变化被识别为稳态迭代控制；质量流量0.5保留，毫米转米与稳态选择已披露。 |
| damBreakWithObstacle（10题） | 逐变体核对air/water运动黏度组合；1/1000密度、0.1s与.02s输出保留。 |
| pitzDaily（10题） | 逐变体核对入口10/15/20/25与nu的1e-5/1e-4/1e-3组合；保留k=.375与epsilon=14.855。 |
| counterFlowFlame2D（10题） | 逐变体核对fuel/air速度组合；0.5s/.05s保留；五组分和全局单步、混合输运等显式补足已披露。 |
| forwardStep（10题） | 逐变体核对4与1.1至2.7入口速度；保留1K、4s/.1s；补全几何与归一化物性。 |
| BernardCells（10题） | 逐变体核对上下壁温度301/305/310/315与300/295/290；1000s/50s保留；标准不可压Boussinesq替代源实现已披露。 |
| wedge（10题） | 逐变体核对入口速度5/10/15/20、T=1/2/3、Pr=1/.71/1.5；mu=0下Pr差异不影响Euler物理，等价性已披露。 |
| shallowWaterWithSquareBump（10题） | 逐变体核对初水面.01至.1及q=.001h/H；源截断小数规范化已披露；出口.01并未随初态更改。 |
| Cavity（10题） | 逐变体核对盖速1/1.5/2/3与nu组合；.1m缩放、10s/.5s、k/epsilon保留。 |
| Cylinder（10题） | 逐变体核对入口1/1.5/2/3与nu0组合；Cross的nuInf=10,m=.4,n=3完整保留；constant/Cross冲突公开选择Cross。 |

advanced 16题逐题核对：双方形/方形/菱形障碍的几何、2e-6运动黏度、1m/s、5s/.5s及SA/SST分工保留；源blockMeshDict1冲突采用prompt且披露。两个腔体SA分别为.1/.2m，3e-5初态与q=0墙取prompt，尺寸区别保留。两个圆柱分别保留SA=.03与LES初k=0/入口2e-5、nu=.01、2s/.05s；新增无回流范围显式公开。楔面SA保留mu=.01、5m/s、1K/1Pa、.2s/.02s。oblique KE/LES保留mu=1.6646e-4、入口/顶边速度和温度、10s/1s。两道火焰保留入口.1/-.1、.5s/.05s及SA/KE区分；五组分、初态热氮气、无壁SA等补足有记录。喷嘴保留1.7856e-5 SA初态/入口、1e-5s/1e-6s，轴对称解释、840/20密度、相黏度与表面张力来自配置，源0值被prompt覆盖已披露。LES闭合泛化与楔面壁距见上述发现。

压力/密度审阅：不可压源运动压力采用rho=1转Pa，障碍101325明确保留为gauge Pa且有author说明，不能误当绝对大气压；可压归一化气体使用Cp/R闭合，basic R=5/7与advanced R=.7143两种公开选择均有披露；damBreak与nozzle区分运动/动力黏度并用rho*nu混合，无发现直接把nu当mu的单位错误。Bernard采用标准不可压Boussinesq替代源heRhoThermo+Boussinesq已明确披露，应作为模型规范化记录而非漏迁。

时间审阅：腔体100步×.005s=.5s正确；squareBend源rhoSimpleFoam为稳态，其500与dt的迭代解释已披露，未机械转换为500s物理瞬态；其他瞬态输出保留源物理间隔，新增t=0采样公开可见。仅dt或mu=0下Pr不同导致数学等价的源变体仍独立保留来源身份，不因此判缺题。

## 哈希与审计界限

- basic文件SHA-256：`5f1c35384c6c6d9051134e7db3bfbc7be43300fe0b28db8e6fee1e33e9411ac3`。
- advanced文件SHA-256：`2e97ce1bd1444909000c4c6337c187c2237b7cdd81c3e2ef9f0ab8c0ea10c22b`。
- `coverage-source.json`逐条记录126个sourcekey、目标task、prompt实际SHA-256、源entry规范化SHA-256、instruction/DATA/source.json实际文件SHA-256、改编文本与变体差异。已有entry哈希均匹配本地源JSON的已知规范化序列化方式。
- 这是一份静态移植审计，不证明初边值问题可解、所有输出物理正确或数值预算达标。未校准资源、缺少真实样例与参考不是本次缺陷。未审计网络下载源以外的外部许可证细节。
