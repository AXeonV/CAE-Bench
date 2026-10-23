# 独立设计审阅：19.3.5 可压缩流重构能量一致性

结论：**本轮未发现未决问题（规划设计范围）**。精确节点状态重构与指定CFD离散稳定回归的双层范围成立，当前材料没有将NASA曲线或粗wallfunction网格冒充高精度物理reference。本人未参与本题实现；本结论不认证正式输入、CFD全场物理精度、资源或判题后端。

阶段是范围规划，末尾“拟冻结的计分边界”是本次判断的当前目标；旧“构建尚未完成”段落作为历史状态理解，不用它否认末尾真实原型。最终instruction/DATA/完整case族尚未冻结，本轮不做考试自足性或全数据结论。

## 能力定位和真实区别

[PR2608](https://github.com/su2code/SU2/pull/2608)的实质是重构时保留既存rhoE/H与T关系中的偏差，避免wallfunction迭代能量被重新从平衡T覆盖。T/u/p梯度、EOS重算rho、增量更新H和真实守恒转换均属输运状态关系修复，放在19.3合理。UMUSCL表达式另一个改写代数等价，不独立包装为第二缺陷。

两个有区别的合法情境：平衡输入H=CpT+|v|²/2与非平衡迭代存储H=CpT+|v|²/2+δ。两者相同T/u/p但H差δ，正确重构保持δ并添加温度/动能增量；原件直接由更新T/u重算H只在前者偶然正确。另有MUSCL关闭、物理失败一阶回退、边限幅/点限幅和2D/3D输入，不能把补丁缩成给特定平板或δ=1000的硬编码。

非平衡状态不是要求考生认可一种不物理的最终理想气体模型，而是明确的求解器中间存储契约。公开DATA应给H、T、rho、p各自输入身份与允许关系；不能把作者内部“wall模型阶段”作为隐藏特例。当前范围卡已明确该区分。

## 两层评价与参考资格

直接状态层可用独立恒等式H_new-H_old=Cp(T_new-T_old)+(|v_new|²-|v_old|²)/2及rhoE=rhoH-p核对。读到的真实CConfig/CNSVariable driver只装填状态/梯度，调用实际reconstructPrimitives和compressibleConservatives，不在driver补焓。因此其可作为此方法要求的真实入口。

完整CFD层不是重复精确恒等测试：真实重构路径可能受到调用方式、存储更新或有限物理状态影响，必须保留原指定14k点可压缩SST壁函数流动，以及全场有限性、残差和延续稳定。某修复只对driver特殊输入成立却不能稳定真实程序时，应由此层检出；不能退成10步regression数字或只核一个Cf。

同一固定修复SU2给定离散的输出，可以在源码修复题中用作明确的软件回归判据。PHILOSOPHY允许题目指定方法，第19章也把真实源码/API约束列为目标；其合理前提是题面公开离散/设置及回归性质，不将该结果宣称普遍高精度物理解。当前粗网格Cf相对NASA低y+ SST-V差约20%，并非可忽略的参考精度，而是模型/网格不等价的外部限制。现行卡明确把NASA留作者作为背景，足以避免错误物理评分。

因此本轮不要求为了软件回归必须先把Cf校准到NASA，也不同意以自评分或残差低直接宣称物理准确。若最终改为高精度物理Cf评分，则现有依据不足，需重新审阅。

## 独立性与后续门槛

修改边界common.hpp且不混另一SU2基线补丁，有助区分本题和19.4.5壁面热流离散/报告。来源换成等价重构模块时，数学状态目标仍然存在；只有库路径/API属于明确方法要求，NASA工况来源没有变成隐藏物理定义。

已读重构family审计记录：baseline在4类活动重构偏差1000J/kg，fixed误差至5.82e-11；一阶/回退保持输入。这是作者原型证据，本轮不重新运行或以它替正式全数据审计。CFD可行性记录是少量真实流动，尚不能证明规划2–3个变体均稳定。参考壁节点T/rho/P不同步的约0.13%也必须按中间存储身份处理，不强套最终热平衡恒等。

正式冻结仍需把真实CFD残差/延续稳定观察和容差、适用节点/压力能量含义、固定离散输出范围、case权重公开；6直接族与2–3流动族按实际结果收束，不能用数量替覆盖。强制重编CNumericsSIMD.cpp、库和CFD并证明加载生效属于后端验收。本轮未发现要求改掉当前双层设计的阻断。

## 实际材料与版本

基线HEAD：`6da63a4203b144fc22fbbc0a598a59f33b960e46`。范围卡与work证据未由该提交绑定，以实际SHA为准；git status --short未给出这三张runs卡的跟踪条目（忽略的工作证据）。关键材料如下，其余逐文件SHA见同目录materials.json。

| 材料 | SHA256 |
|---|---|
| runs/authoring/repair-22/su2-2602-scope.md | c51eb2068ebe955d63d69899f773a56a63328d99e9edb711bf891578a5054cb1 |
| work/repair-22/su2-2602/pr.json | 56ce5efc12feff13cbf22216d2221ed61865d0baf77c096bc678304dc1b1aa9b |
| work/repair-22/su2-2602/reconstruction-driver.cpp | 5cf02e633cd7f4a25fd53067b50074533a4890ec18e71fdd280cf6f3d71cf937 |
| work/repair-22/su2-2602/SU2_CFD__include__numerics_simd__flow__convection__common.hpp.patch | 7679e8392e89a293691c755fe809c5157a8b8a16c986ec3425bf1a53967123e2 |
| work/repair-22/su2-2602/reconstruction-feasibility.json | f5b02453d968b893188a3693f0d84542af8a23ed6db7db6a0a71b463ddde4a21 |
| work/repair-22/su2-2602/reconstruction-family-audit.json | 9f5ed0abc1222c053700c1bea095062bef6eb61b2d7ad2fc6077d99bced84c23 |
| work/repair-22/su2-2602/reconstruction-family-cases.json | 89adf2f154156c82c652e8be57851a549eda8567056a045ebb921102c90227b1 |
| work/repair-22/su2-2602/flow-feasibility.json | e4d9ed063249deb924ef2992e30b93d6278f5e5f85f1fdc92496ae58cdded0bf |

已读取PHILOSOPHY、章规划、CONTRACT和架构职责。没有用已有父级批准替代判断；没有实施或修改题目，也没有新运行求解器/编译。对公开参数域、完整数据和资源均仅给阶段性边界，后续冻结变化需复核。
