# 发布前全题审查与修订候选版

范围为RC2的全部82题：第0章2题、第1章13题、第2章43道流动能力题和24道CFDCodeBench；647正式case角色、96样例角色。第19章未纳入。设计、考生材料和实际数据审查均已完成，原始发现和修订复核分别保存；本记录不授予参考数值或正式Benchmark资格。

修订版：[RC3交付包](<D:/Code/CAE-Bench-OJ/runs/releases/caeoj-qbank-20261023-rc3.zip>)，4912036993 bytes，SHA256 `755fce2fd4fe2298ec6cb8055fac433e116342e610415d22113ae61b13238593`。对应[README](<D:/Code/CAE-Bench-OJ/runs/releases/caeoj-qbank-20261023-rc3/README.md>)及[catalog快照](catalog.json)。RC1、RC2原件保持；最终审阅的公开文本进入本RC3，不能用旧RC2替代修订版。

## 修复与对齐

- 78题原本只在作者选样元数据标记format，公开三文件未说明随机输出用途。独立审阅用负浓度、越界体积分数、非正定构象等反例定位误导；现在逐题明确编号、随机结构用途及非数值答案属性。数值样例保持原角色，不把坏物理解改称合格参考。
- 24道CFDCodeBench补齐solve.py、--input/--output、路径基准、退出与离线依赖要求；固定数学定义、数值阈值和资源未改。
- 将另一checkout的24题维护源码、冻结选样、来源证据及声明／归一化扩展纳入当前分支。格式样例装配、单题／多题发布和Harbor命令与现有源码修复能力合并，格式输出不再指向不存在的判分参考。来源身份与实际字节见[source-alignment.json](source-alignment.json)。
- 固定问题兼容专题明确独立计分及非问题族泛化边界；章导航、生成器、存储设计、维护流程和技能同步修订。

## 审查证据

- 独立设计：[原审](design-review.md)、[修订复核](design-recheck.md)，82题全覆盖。
- 独立考生材料：[43题原审](flow-candidate-review.md)、[复核](flow-candidate-recheck.md)；[另39题原审](other-candidate-review.md)、[复核](other-candidate-recheck.md)。625份公开材料最终摘要匹配，修订只涉及公开说明和入口，DATA及实际数值载荷不变。
- [实际数据](actual-data-review.md)：743份真实输入的全部数组及网格、4069项实值／变体到公开文档的映射；95份实际公开输出全读结构和复制轴检查，另一个smoke样例仅提供数值参考，符合声明。所检项目未确认新增文档／数据冲突。完整逐值证据以gzip保存，解压摘要见[索引](compressed-evidence.json)。
- [配置映射](scoring-map.json)：647份真实判题配置均枚举，逐值quantity容差表对照零不一致；特殊NRMSE／归一化规则保留原配置并由相关回归覆盖。
- 本轮相关回归72项通过：数据池21、格式样例6、CFD兼容6、公开发布9、Harbor30；[独立代码审阅](integration-review.md)关闭源码修复×format组合问题。
- [公开包刷新](refresh-report.json)：82题冻结运行闭包与当前闭包逐文件相同，每个旧成员先验证原manifest摘要；仅替换instruction/DATA，其他解压字节原样保留并更新公开清单。原发布器另完成前14题真实预检；其余采用文本刷新，不把未重复的大数组预检说成新执行。
- [最终消费](independent-consumption.json)：RC3完整verify；6类代表题从最终归档提取、独立安装、正确参考得1分、数值变异被拒；全部项目模块来自新安装路径，复用已有Python依赖，未宣称干净机器资源验收。[外层ZIP](delivery-verification.json)逐成员SHA／大小通过。

## 仍保留的发布限制

- DR-01：14题公开的压力相对误差尺度对规范／基准表示敏感，是有反例的评价设计偏置，尚未发现文档与实现冲突。本轮未盲改阈值，待明确采用何种物理误差尺度并完成相应参考／容差核验。
- [17题分支缺口](open-coverage-gaps.json)：9道能量题缺source/acceleration/assign，6道CFD瞬态题缺previous／hold，2道黏弹性题缺入口／出口。不能由当前case成绩宣称覆盖整个公开问题族；未悄悄删范围或造新参考。
- 新增41道流动题仍为unvalidated-reference-rc；其他题既有profile和历史独立证据保持。全量数值资格、轨迹级物理保证、预算、许可范围和异机交付仍需相应证据，不由本次文档与输入审计认证。完整模型执行器与求解器镜像不在此材料包中。

本版适合团队材料审阅及有限结论下的试跑，`ready_for_formal_benchmark=false`。本轮未拉HF、未新增Titan载荷、未求解重算、未调用收费考生模型，case ID、选样及全部正式判据保持。

## 逐题账本

版本摘要、原参考profile与状态见[task-ledger.json](task-ledger.json)，具体缺口和反例由上述报告拥有。

|题目|正式角色|样例角色|考生审阅|数据契约|覆盖|设计待决|
|---|---:|---:|---|---|---|---|
|[简单测试](../../../../qbank/00-basic-tests/0.1-io/smoke-test/instruction.md)|11|1|完成并复核|已审|本轮未见分支缺口|—|
|[Case 判题链路测试](../../../../qbank/00-basic-tests/0.2-grading/case-grading-test/instruction.md)|6|2|完成并复核|已审|本轮未见分支缺口|—|
|[二维空间变系数 Darcy 型稳态问题](../../../../qbank/01-prescribed-pdes/1.1-elliptic/darcy-flow-2d/instruction.md)|20|2|完成并复核|已审|本轮未见分支缺口|—|
|[二维稳态热传导](../../../../qbank/01-prescribed-pdes/1.1-elliptic/heat-conduction-steady-2d/instruction.md)|32|2|完成并复核|已审|本轮未见分支缺口|—|
|[一维 Freundlich 迟滞扩散](../../../../qbank/01-prescribed-pdes/1.2-diffusion-reaction/diffusion-sorption-1d/instruction.md)|16|2|完成并复核|已审|本轮未见分支缺口|—|
|[二维瞬态热传导](../../../../qbank/01-prescribed-pdes/1.2-diffusion-reaction/heat-conduction-transient-2d/instruction.md)|24|2|完成并复核|已审|本轮未见分支缺口|—|
|[一维 logistic 反应扩散](../../../../qbank/01-prescribed-pdes/1.2-diffusion-reaction/reaction-diffusion-1d/instruction.md)|32|2|完成并复核|已审|本轮未见分支缺口|—|
|[二维 FitzHugh–Nagumo 反应扩散](../../../../qbank/01-prescribed-pdes/1.2-diffusion-reaction/reaction-diffusion-2d/instruction.md)|16|2|完成并复核|已审|本轮未见分支缺口|—|
|[一维周期线性平流](../../../../qbank/01-prescribed-pdes/1.3-scalar-transport/advection-1d/instruction.md)|24|2|完成并复核|已审|本轮未见分支缺口|—|
|[二维浅水方程](../../../../qbank/01-prescribed-pdes/1.4-hyperbolic/shallow-water-2d/instruction.md)|16|2|完成并复核|已审|本轮未见分支缺口|—|
|[一维周期黏性 Burgers 方程](../../../../qbank/01-prescribed-pdes/1.5-advection-diffusion/burgers-1d/instruction.md)|24|2|完成并复核|已审|本轮未见分支缺口|—|
|[二维非均匀强迫不可压缩流](../../../../qbank/01-prescribed-pdes/1.6-constrained-systems/incompressible-navier-stokes-2d/instruction.md)|16|2|完成并复核|已审|本轮未见分支缺口|—|
|[一维可压缩 Navier–Stokes](../../../../qbank/01-prescribed-pdes/1.7-coupled-systems/compressible-navier-stokes-1d/instruction.md)|16|2|完成并复核|已审|本轮未见分支缺口|—|
|[二维可压缩 Navier–Stokes](../../../../qbank/01-prescribed-pdes/1.7-coupled-systems/compressible-navier-stokes-2d/instruction.md)|24|2|完成并复核|已审|本轮未见分支缺口|—|
|[三维可压缩 Navier–Stokes](../../../../qbank/01-prescribed-pdes/1.7-coupled-systems/compressible-navier-stokes-3d/instruction.md)|6|2|完成并复核|已审|本轮未见分支缺口|—|
|[2.1.1 2D 常黏度牛顿流体不可压缩流动稳态分析](../../../../qbank/02-fluid-mechanics/2.1-single-phase-flow/newtonian-incompressible-steady-2d/instruction.md)|10|1|完成并复核|已审|本轮未见分支缺口|DR-01|
|[2.1.3 3D 常黏度牛顿流体不可压缩流动稳态分析](../../../../qbank/02-fluid-mechanics/2.1-single-phase-flow/newtonian-incompressible-steady-3d/instruction.md)|10|1|完成并复核|已审|本轮未见分支缺口|DR-01|
|[一维周期黏性 Burgers](../../../../qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-1d-burgers-equation/instruction.md)|1|1|完成并复核|已审|本轮未见分支缺口|—|
|[一维矩形初态扩散](../../../../qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-1d-diffusion/instruction.md)|1|1|完成并复核|已审|本轮未见分支缺口|—|
|[理想气体激波管](../../../../qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-1d-euler-shock-tube/instruction.md)|1|1|完成并复核|已审|本轮未见分支缺口|—|
|[一维周期对流扩散](../../../../qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-1d-linear-convection/instruction.md)|1|1|完成并复核|已审|本轮未见分支缺口|—|
|[一维非线性熵输运](../../../../qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-1d-nonlinear-convection/instruction.md)|1|1|完成并复核|已审|本轮未见分支缺口|—|
|[二维黏性 Burgers](../../../../qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-burgers-equation/instruction.md)|1|1|完成并复核|已审|本轮未见分支缺口|—|
|[二维对角熵输运（终时 0.32）](../../../../qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-convection/instruction.md)|1|1|完成并复核|已审|本轮未见分支缺口|—|
|[二维矩形初态扩散](../../../../qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-diffusion/instruction.md)|1|1|完成并复核|已审|本轮未见分支缺口|—|
|[二维对角熵输运（终时 0.40）](../../../../qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-inviscid-burgers/instruction.md)|1|1|完成并复核|已审|本轮未见分支缺口|—|
|[矩形混合边界 Laplace 势](../../../../qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-laplace-equation/instruction.md)|1|1|完成并复核|已审|本轮未见分支缺口|—|
|[二维线性脉冲平移](../../../../qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-linear-convection/instruction.md)|1|1|完成并复核|已审|本轮未见分支缺口|—|
|[不可压盖驱方腔（黏度 0.01）](../../../../qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-navier-stokes-cavity/instruction.md)|1|1|完成并复核|已审|本轮未见分支缺口|—|
|[周期通道启动流](../../../../qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-navier-stokes-channel/instruction.md)|1|1|完成并复核|已审|本轮未见分支缺口|—|
|[双 Gaussian 源 Poisson 势](../../../../qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-poisson-equation/instruction.md)|1|1|完成并复核|已审|本轮未见分支缺口|—|
|[四边恒温矩形稳态传热](../../../../qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-steady-heat-equation/instruction.md)|1|1|完成并复核|已审|本轮未见分支缺口|—|
|[Gaussian 初温与持续热源](../../../../qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-unsteady-heat-equation/instruction.md)|1|1|完成并复核|已审|本轮未见分支缺口|—|
|[Cess 闭合双壁湍流通道](../../../../qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-fully-developed-turbulent-channel-flow/instruction.md)|1|1|完成并复核|已审|本轮未见分支缺口|—|
|[不可压盖驱方腔（黏度 0.1）](../../../../qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-lid-driven-cavity/instruction.md)|1|1|完成并复核|已审|本轮未见分支缺口|—|
|[圆柱外圆环涡量流函数流动](../../../../qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-flow-past-circular-cylinder/instruction.md)|1|1|完成并复核|已审|本轮未见分支缺口|—|
|[周期 KdV–Burgers](../../../../qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-1d-kdv-burgers-equation/instruction.md)|1|1|完成并复核|已审|本轮未见分支缺口|—|
|[二维 Rayleigh–Bénard 对流](../../../../qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-rayleigh-benard-convection/instruction.md)|1|1|完成并复核|已审|本轮未见分支缺口|—|
|[周期剪切流与被动示踪剂](../../../../qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-2d-shear-flow-with-tracer/instruction.md)|1|1|完成并复核|已审|本轮未见分支缺口|—|
|[圆管扰动的最右增长率](../../../../qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-pipe-flow-disk-evp/instruction.md)|1|1|完成并复核|已审|本轮未见分支缺口|—|
|[Lane–Emden 正基态](../../../../qbank/02-fluid-mechanics/2.13-cfdcodebench/cc-lane-emden-equation/instruction.md)|1|1|完成并复核|已审|本轮未见分支缺口|—|
|[2.1.2 2D 常黏度牛顿流体不可压缩流动瞬态分析](../../../../qbank/02-fluid-mechanics/2.1-single-phase-flow/newtonian-incompressible-transient-2d/instruction.md)|10|1|完成并复核|已审|缺分支|DR-01|
|[2.1.4 3D 常黏度牛顿流体不可压缩流动瞬态分析](../../../../qbank/02-fluid-mechanics/2.1-single-phase-flow/newtonian-incompressible-transient-3d/instruction.md)|10|1|完成并复核|已审|缺分支|DR-01|
|[2.1.5 2D 非牛顿流体不可压缩流动稳态分析](../../../../qbank/02-fluid-mechanics/2.1-single-phase-flow/generalized-newtonian-incompressible-steady-2d/instruction.md)|8|1|完成并复核|已审|本轮未见分支缺口|DR-01|
|[2.1.6 2D 非牛顿流体不可压缩流动瞬态分析](../../../../qbank/02-fluid-mechanics/2.1-single-phase-flow/generalized-newtonian-incompressible-transient-2d/instruction.md)|8|1|完成并复核|已审|缺分支|DR-01|
|[2.1.7 3D 非牛顿流体不可压缩流动稳态分析](../../../../qbank/02-fluid-mechanics/2.1-single-phase-flow/generalized-newtonian-incompressible-steady-3d/instruction.md)|7|1|完成并复核|已审|本轮未见分支缺口|DR-01|
|[2.1.8 3D 非牛顿流体不可压缩流动瞬态分析](../../../../qbank/02-fluid-mechanics/2.1-single-phase-flow/generalized-newtonian-incompressible-transient-3d/instruction.md)|8|1|完成并复核|已审|缺分支|DR-01|
|[2.1.9 2D 常黏度牛顿流体等温可压缩流动稳态分析](../../../../qbank/02-fluid-mechanics/2.1-single-phase-flow/newtonian-isothermal-compressible-steady-2d/instruction.md)|3|1|完成并复核|已审|本轮未见分支缺口|DR-01|
|[2.1.10 2D 常黏度牛顿流体等温可压缩流动瞬态分析](../../../../qbank/02-fluid-mechanics/2.1-single-phase-flow/newtonian-isothermal-compressible-transient-2d/instruction.md)|5|1|完成并复核|已审|缺分支|DR-01|
|[2.1.11 3D 常黏度牛顿流体等温可压缩流动稳态分析](../../../../qbank/02-fluid-mechanics/2.1-single-phase-flow/newtonian-isothermal-compressible-steady-3d/instruction.md)|3|1|完成并复核|已审|本轮未见分支缺口|DR-01|
|[2.1.12 3D 常黏度牛顿流体等温可压缩流动瞬态分析](../../../../qbank/02-fluid-mechanics/2.1-single-phase-flow/newtonian-isothermal-compressible-transient-3d/instruction.md)|5|1|完成并复核|已审|缺分支|DR-01|
|[2.2.1 2D 牛顿流体低速流动与传热稳态分析](../../../../qbank/02-fluid-mechanics/2.2-single-phase-energy/newtonian-lowmach-steady-2d/instruction.md)|10|1|完成并复核|已审|本轮未见分支缺口|—|
|[2.2.2 2D 牛顿流体低速流动与传热瞬态分析](../../../../qbank/02-fluid-mechanics/2.2-single-phase-energy/newtonian-lowmach-transient-2d/instruction.md)|10|1|完成并复核|已审|本轮未见分支缺口|—|
|[2.2.3 3D 牛顿流体低速流动与传热稳态分析](../../../../qbank/02-fluid-mechanics/2.2-single-phase-energy/newtonian-lowmach-steady-3d/instruction.md)|10|1|完成并复核|已审|本轮未见分支缺口|—|
|[2.2.4 3D 牛顿流体低速流动与传热瞬态分析](../../../../qbank/02-fluid-mechanics/2.2-single-phase-energy/newtonian-lowmach-transient-3d/instruction.md)|10|1|完成并复核|已审|本轮未见分支缺口|—|
|[2.2.5 2D 无黏可压缩流动稳态分析](../../../../qbank/02-fluid-mechanics/2.2-single-phase-energy/inviscid-compressible-steady-2d/instruction.md)|10|1|完成并复核|已审|本轮未见分支缺口|—|
|[2.2.6 2D 无黏可压缩流动瞬态分析](../../../../qbank/02-fluid-mechanics/2.2-single-phase-energy/inviscid-compressible-transient-2d/instruction.md)|10|1|完成并复核|已审|缺分支|—|
|[2.2.7 3D 无黏可压缩流动稳态分析](../../../../qbank/02-fluid-mechanics/2.2-single-phase-energy/inviscid-compressible-steady-3d/instruction.md)|10|1|完成并复核|已审|本轮未见分支缺口|—|
|[2.2.8 3D 无黏可压缩流动瞬态分析](../../../../qbank/02-fluid-mechanics/2.2-single-phase-energy/inviscid-compressible-transient-3d/instruction.md)|10|1|完成并复核|已审|缺分支|—|
|[2.2.10 2D 牛顿流体可压缩流动与传热瞬态分析](../../../../qbank/02-fluid-mechanics/2.2-single-phase-energy/newtonian-compressible-transient-2d/instruction.md)|5|1|完成并复核|已审|缺分支|—|
|[2.2.12 3D 牛顿流体可压缩流动与传热瞬态分析](../../../../qbank/02-fluid-mechanics/2.2-single-phase-energy/newtonian-compressible-transient-3d/instruction.md)|5|1|完成并复核|已审|缺分支|—|
|[2.3.1 2D 不可压缩湍流定常平均分析](../../../../qbank/02-fluid-mechanics/2.3-turbulent-flow/rans-steady-2d/instruction.md)|8|1|完成并复核|已审|本轮未见分支缺口|—|
|[2.3.2 3D 不可压缩湍流定常平均分析](../../../../qbank/02-fluid-mechanics/2.3-turbulent-flow/rans-steady-3d/instruction.md)|7|1|完成并复核|已审|本轮未见分支缺口|—|
|[2.3.3 3D 不可压缩湍流非定常平均分析](../../../../qbank/02-fluid-mechanics/2.3-turbulent-flow/urans-transient-3d/instruction.md)|10|1|完成并复核|已审|本轮未见分支缺口|—|
|[2.3.4 3D 不可压缩湍流尺度解析统计分析](../../../../qbank/02-fluid-mechanics/2.3-turbulent-flow/resolved-statistics-3d/instruction.md)|10|1|完成并复核|已审|本轮未见分支缺口|—|
|[2.3.5 3D 等温可压缩湍流定常平均分析](../../../../qbank/02-fluid-mechanics/2.3-turbulent-flow/isothermal-rans-3d/instruction.md)|7|1|完成并复核|已审|本轮未见分支缺口|—|
|[2.4.1 3D 低速湍流传热定常平均分析](../../../../qbank/02-fluid-mechanics/2.4-turbulent-energy/thermal-rans-3d/instruction.md)|9|1|完成并复核|已审|缺分支|—|
|[2.4.2 3D 低速湍流传热非定常平均分析](../../../../qbank/02-fluid-mechanics/2.4-turbulent-energy/thermal-urans-3d/instruction.md)|4|1|完成并复核|已审|缺分支|—|
|[2.4.3 3D 低速湍流传热尺度解析统计分析](../../../../qbank/02-fluid-mechanics/2.4-turbulent-energy/thermal-statistics-3d/instruction.md)|10|1|完成并复核|已审|本轮未见分支缺口|—|
|[2.5.3 二维不混溶双流体界面瞬态流动](../../../../qbank/02-fluid-mechanics/2.5-interface-flow/immiscible-interface-2d/instruction.md)|10|1|完成并复核|已审|本轮未见分支缺口|—|
|[2.5.4 三维不混溶双流体界面瞬态流动](../../../../qbank/02-fluid-mechanics/2.5-interface-flow/immiscible-interface-3d/instruction.md)|10|1|完成并复核|已审|本轮未见分支缺口|—|
|[2.8.2 可压缩气膜润滑瞬态分析](../../../../qbank/02-fluid-mechanics/2.8-thin-film/gas-film/instruction.md)|10|1|完成并复核|已审|本轮未见分支缺口|—|
|[2.9.1 全湿浅水稳态分析](../../../../qbank/02-fluid-mechanics/2.9-shallow-water/fully-wet-steady/instruction.md)|3|1|完成并复核|已审|本轮未见分支缺口|—|
|[2.9.2 全湿浅水瞬态分析](../../../../qbank/02-fluid-mechanics/2.9-shallow-water/fully-wet-transient/instruction.md)|9|1|完成并复核|已审|本轮未见分支缺口|—|
|[2.9.3 干湿变化浅水瞬态分析](../../../../qbank/02-fluid-mechanics/2.9-shallow-water/wetting-drying/instruction.md)|7|1|完成并复核|已审|本轮未见分支缺口|—|
|[2.10.3 过渡区稀薄气体稳态分析](../../../../qbank/02-fluid-mechanics/2.10-rarefied-gas/transition-gas/instruction.md)|10|1|完成并复核|已审|本轮未见分支缺口|—|
|[2.10.4 自由分子气体稳态分析](../../../../qbank/02-fluid-mechanics/2.10-rarefied-gas/free-molecular/instruction.md)|10|1|完成并复核|已审|本轮未见分支缺口|—|
|[2.11.1 黏弹性流体稳态分析](../../../../qbank/02-fluid-mechanics/2.11-memory-fluids/viscoelastic-steady/instruction.md)|9|1|完成并复核|已审|缺分支|DR-01|
|[2.11.2 黏弹性流体瞬态分析](../../../../qbank/02-fluid-mechanics/2.11-memory-fluids/viscoelastic-transient/instruction.md)|9|1|完成并复核|已审|缺分支|DR-01|
|[2.2.9 2D 牛顿流体可压缩流动与传热稳态分析](../../../../qbank/02-fluid-mechanics/2.2-single-phase-energy/newtonian-compressible-steady-2d/instruction.md)|4|1|完成并复核|已审|缺分支|—|
|[2.2.11 3D 牛顿流体可压缩流动与传热稳态分析](../../../../qbank/02-fluid-mechanics/2.2-single-phase-energy/newtonian-compressible-steady-3d/instruction.md)|3|1|完成并复核|已审|缺分支|—|
|[2.4.4 3D 可压缩湍流传热定常平均分析](../../../../qbank/02-fluid-mechanics/2.4-turbulent-energy/compressible-thermal-rans-3d/instruction.md)|4|1|完成并复核|已审|缺分支|—|
