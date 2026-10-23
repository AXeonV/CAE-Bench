# 19.4.4 LAMMPS颗粒成对维里：独立范围设计审阅

日期：2026-10-23。阶段：范围卡，辅助核对未冻结公开题面／DATA草稿与来源补丁。结论：**限定范围规划通过，本轮未发现未决设计问题。** 仅认可瞬时Hooke接触、真实Kokkos Serial成对维里及全局／逐粒子统计的能力与评价对应，不认证构建、原型数值、正式数据、资源或可信后端。

## 材料与隔离

按`caeoj-design-review`技能执行。未读取实现驱动、独立脚本、构建日志、原型输出或正式case，不执行求解器或Benchmark。主仓库HEAD `fafbd7bc2b10749f2dfd208e14ff0d7950b484be`；开始时本题等若干题目录与来源审查材料未跟踪，未由目录存在推断完成。路径均相对`D:/Code/CAE-Bench-OJ`，SHA256如下：

| 材料 | SHA256 |
|---|---|
| runs/authoring/repair-22/lammps-4219-scope.md | 5AD9DB983BD172770656AA34E51BE4084C846EEF80B7323454D8076D9C8C2345 |
| qbank/19-solver-repair/19.4-observations/granular-pair-stress-repair/instruction.md（未冻结草稿） | 226E6EF9B534DFDED2FF052BEE02EC1B7BAE2D0B815CA4BAAE3593548C7C23FC |
| qbank/19-solver-repair/19.4-observations/granular-pair-stress-repair/DATA.md（未冻结草稿） | 7CC7823C1C8CEE2D647C422D18485EAFE5B67AA1C2702AF61347E6B4CC04EA18 |
| work/solver-issue-research/lammps-lammps-4219-html.json | 1B2DB4B7F78337AF597E24FFAB8C381BAE4DE508984FBC4D5D29DE5DF0CB0EE3 |
| work/solver-issue-research/fc3ef61ec91e7ec2.json（PR4346 files，仅核对目标两文件） | 42FCB8F11A9DC418BE194292AA69D318F63B0AD24AFE37F5B9E2442BAECD4F98 |

来源定位还查看PR4346缓存的URL元数据，`389396f90b4e759f.json` SHA256 `0B7143631E111B7938842EF1F2CEDB5C74F92BAFCC821B3CF7A23A1A1396AB0F`；结论不依赖未读PR正文。哲学及章节定位沿用已读PHILOSOPHY SHA256 `1CAA7693D2734AF313AE2FCEFD45A836FB1CE9664A732D2604BD75556ED50409`、chapter-19 SHA256 `7C580259EAB5A7A0F9BFFE02E391E7DC40C2CE8D3CCA6C80EA665B5AFD38C34F`。不展开公开草稿中的源码包、运行器或CONTRACT链接，因此不是完整公开包或考生审阅。

## 来源实质与修改边界

来源#4219指出`gran/hooke/history/kk`统计函数传入累计粒子力而非当前接触对力，导致应力过累计；力本身可以仍正确。PR4346目标两文件差异确把tally输入改为成对fx/fy/fz，并重整global／peratom分支，使同时请求时两者均可累计。这两个点均是本题承诺，既不是仅输出格式调整，也没有把无关Brownian、deform或通信变更混入题目。

允许cpp和匹配h有实际模板实现依据；保留真实pair及Kokkos路径，并要求其真实依赖重编，符合源码修复方法目标。选CPU Serial、单进程、half邻居和newton on/off是公开执行边界，不声称GPU、MPI或其他邻居算法正确。CPU执行仍能检验累计力／成对力和统计分支错误，来源症状的物理核心未丢失；GPU上的原始应用是来源证据，不是必须复刻的唯一能力定义。

原issue含用户改写Hertz接触及FCC压缩应用。本题明确定义真实Hooke模型，且只修原Hooke Kokkos文件；共同错误位于统计使用的力，而非Hertz半径因子。改编成小颗粒瞬时输入可以精确识别同一统计错误，不应冒称完整原始压缩实验或Hertz应用重放，当前卡片未作这种声明。

## 问题族、真实差异与限制依据

四粒或更多非正交接触星簇与单对接触有实质能力差异：前者同一颗粒多个邻居使累计力与各对力不同，后者可能偶然无法区分。global-only、peratom-only与both则检验真实请求分支，不能以某一种模式正确替代全部。newton on/off和粒子排列变化可检验计数、ID及局部累计逻辑，仍属于同一成对维里能力。

无接触、零阻尼和单对是适当非触发回归；不同粒径／密度影响有效质量及转动力矩，不只是重复相同几何数值。非零切向／角速度可产生非中心力，检验全部六分量而非仅对角平均。颗粒状态不要求平衡是瞬时力求值的合理范围，无需加入时间积分或墙来使任意输入成为静态平衡。

零初始切向历史、run 0且不推进，使Hooke切向弹簧记忆为零，kt不影响此瞬间是已声明模型的结果；不能因此宣称历史演化已覆盖。法向排斥与切向低于Coulomb截断且留20%余量，是对接触分支有依据的限定，避免独立参考还需复现未承诺的截断／历史算法。该范围仍有弹簧、法向阻尼和转动切向阻尼的真实变化，不缩成纯法向单对。

## 公开物理与观测语义

辅助草稿已给出质量、有效质量、法向及切向速度、Hooke力公式，kn/kt与阻尼单位，接触半径、箱体积及作用反作用；不从软件默认推断物理。不存在Hertz半径缩放或隐藏动能压力。摩擦条件及非零距离由输入保证，不能由驱动更换模型来满足。

维里定义为位移外积成对作用力，六分量次序xx/yy/zz/xy/xz/yz明确。切向力使完整矩阵可不对称，不能把六分量默认当对称张量再旋转；范围卡要求先变换完整逐对外积后提取六分量，草稿也明确不作非对角对称平均。这避免错误的“看似物理”旋转回归。

逐粒子每对各分一半，不除粒子体积，单位N·m；它是`stress/atom NULL pair`的相反数。全局除立方箱体积为Pa，压缩为正、不含动能，与`compute pressure NULL pair`相对应。因此单粒子virial与全局压力不是同一单位的数组，也不应使用未经声明的颗粒体积求应力。力和力矩同时输出保持原有接触行为，tally修复不能通过改力来“配平”压力。

每种模式只要求声明输出，both必须同时满足两类统计；按全部观测通过才计case成绩，能发现一类统计掩盖另一类。粒子ID对应关系及逐粒子比较可检出仅总和正确。草稿已列资源／容差，但本轮不验证其校准或最终生效。

## 独立参考与证据层次

正式reference由真实修复LAMMPS运行生产，独立NumPy对输入逐对计算力、力矩、外积与半分摊，原则上避开原pair tally累积逻辑。非Kokkos同库路径可作为补充交叉核对，不应成为独立数学核查的替代。全局与逐粒子和一致只是必要恒等式；若两者共用同一错误力，它们可以共同错，卡片已明确仍需独立逐对结果。

源码补丁的成对力与双统计分支改变是静态证据。卡片报告原件／修复的四粒三接触数值及构建成功，本轮未读对应日志或执行，不认证这些事实，也不将一个原型外推至全部newton／tally模式。最终数据应分别触发过累计和both分支错误，并包含能使两者分离诊断的单模式回归；不需要限定固定case数量来冒充覆盖。

## 边界结论及后续验收

本题符合19.4观测与软件契约定位：修复真实统计量，不把它冒称时间积分或接触本构改进。与电化学热／库存题共享积分／累加的工程主题，但成对力、六分量外积、邻居与tally模式是独立领域能力，不构成机械重题。更换颗粒来源算例后任务含义仍然成立。

**19.4.4限定范围规划通过。** 后续需冻结公开三文件并让独立考生上下文审阅，核对正式数据中的所有合法分支、成对参考和原件／修复真实重放、源码依赖闭包及编译缓存失效、资源／容差、HF固定回取和可信判题。当前草稿中样例“可运行”、预算和容差数值不能只因写在文档就视作事实；本轮不为这些交付项背书。

本设计审阅者已接触作者机制与来源补丁，不适合承担后续无作者上下文的考生／exam审阅。本题设计审阅到此结束。

## 有界增量：固定newton pair off

2026-10-23。主仓库HEAD仍为`fafbd7bc2b10749f2dfd208e14ff0d7950b484be`。新增范围卡SHA256为`515CE3850CF27EF5376A2C0F1BC0E9B333891EE61A17C580B06FD541FA823609`；只复核newton限制的必要事实与能力影响，不认证协调方提供的12/12或2/12成绩、其余物理参考或构建结果。初审on/off范围及初审SHA作为历史保留，最终结论适用于下述off限定。

额外获准读取的材料均在本题`author/data-evidence/`内，SHA256：

| 文件 | SHA256 |
|---|---|
| newton-on-unsupported-stderr.log | C41A6647B6F65B2656EE3FFB6E68B02B529C3200ABB29D9B247863DAA145BFB5 |
| upstream-verlet.cpp | C61A7F36D6EA7EB4E979E1A697D1592B906A57286A73455BBB76F9EF69A34B9F |
| upstream-fix_neigh_history.cpp | B95543FE032EAC9CBF0FFAFA79457FE74F38AE5A7FCB950A7467154C22951F9D |
| upstream-fix_neigh_history_kokkos.cpp | 542A58235EA7D342DD7195166F835A8263D70CB2BA449D3AD5AF100917261033 |

原始日志显示half/newton on的真实run 0虽已打印压力行，随后仍报`Fix neigh/history/kk requires newton 'off' for exchange communication`并返回失败；运行器没有吞掉返回码。静态调用链与报错相符：`Verlet::cleanup()`调用post_run，`FixNeighHistory::post_run()`调用pre_exchange，Kokkos版本在newton_pair为真时直接error，不依赖MPI进程数。本轮据这些限定材料认可“单进程Serial仍不能完整执行该newton on路径”的事实依据，不认可截取报错前数值作为成功输出。

仅允许pair cpp+h，且来源PR目标子集没有修辅助history模块，因此固定off有公开支持边界依据。若要支持on就需额外修改不在本题边界的辅助模块；当前选择保留真实完整run 0，而非伪装输出，是合理收束。

固定off不消除成对力／累计力差异，也不消除global-only、peratom-only、both三请求分支。多邻居非正交接触、转动及切向力、独立外积参考、力矩保持等实质能力继续保留；来源#4219的原运行说明本身也使用newton off。因此这不是为迁就错误结果删除目标触发条件，而是移除未受目标修复覆盖、实际不支持的执行模式。

已针对公开instruction和DATA核对相关文字，二者现固定off，DATA不再列on/off输入选择。本轮未展开checker／driver代码；它们的同步及非法on拒绝、生效参数、全正式case身份属于数据／后端验收，不能仅凭协调方告知就视为本报告已检查。范围卡前部仍保留on/off历史文字、末节明确最终off；最终维护版本应将现行范围统一为off，并保留变更原因而非让历史段落充当当前定义。

本次公开版本SHA256：instruction.md `47E8FCE53843E29F3824ABD3B25AEB24EDC37E5785776168F92AA0636A1193FB`；DATA.md `B38E80D72AE2116F0050BE3C69F01592197CE356BAC713C9915DA53675427197`。

**增量结论：19.4.4在公开固定newton off后，限定范围设计继续通过。** 调整原因、来源事实、最终公开限制和保留能力均已明确，不属于悄悄缩限。初审对“同时支持on/off”的认可不再作为当前能力声明。全部正式数值、原件／修复成绩及真实后端仍须另行验收。
