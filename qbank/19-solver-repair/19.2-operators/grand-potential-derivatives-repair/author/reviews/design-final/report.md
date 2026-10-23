# 19.2.2 独立规划设计审阅

审阅日期：2026-10-23。阶段：规划，尚无正式 instruction.md / DATA.md。结论：**资料不足；本轮未发现范围卡中的能力定位或完整 Hessian 目标有必须撤销的设计问题**。此结论不表示数值、资源、构建、判题或数据就绪。

## 独立性与基线

本审阅由独立上下文的设计审阅 agent 完成，仅使用协调方白名单及必要相邻题公开材料。未读取源码、补丁、作者原型、日志、隐藏数据、既有审阅或参考答案，未联网核实来源，因此范围卡中的上游版本与工程事实只视为作者声明。未运行付费考生。

仓库 HEAD：`bc426b951f2a462399af9a5f6d249fbe06c305c5`。审阅时 tracked diff 与 staged diff 均为空；存在其他题目录及来源记录的未跟踪文件。材料以文末 SHA256 而非 HEAD 单独绑定。报告是本轮唯一修改。

## 能力、范围与来源

题目要求在真实 GrandPotentialSinteringMaterial / DerivativeMaterialInterface 及 FE 装配链内实现材料系数的一致导数，属于可复用的材料及离散算子实现能力。指定类与源码边界是修复题的方法要求，数学目标仍由公开公式定义；更换算例来源不会改变目标。

两个有实质区别的合法输入可以分别是：单 η、常 ceq 的夹持端点与区间内部状态；多 η、含非对角二次项及一次项的区间内部状态。前者检验分段、材料值和 φ 导数，后者检验 η 梯度、η 间 Hessian 以及 φ–η 交叉项。固定单粒子算例或只修对角导数不能覆盖二者。参数区间虽待实际冻结，这种能力差异已经成立。

限制于 PARABOLIC strict 分支、同时保持同一非 strict 行为，具有能力依据；作者声明 strict+DILUTE/IDEAL 被构造器拒绝，不应将其扩成未验证承诺。数学关系是四个严格守恒系数的一致求值，并非完整烧结应用的物理适用性认证。材料试探状态不依赖历史轨迹；与 19.1.2 的提交/回滚序列能力不同。与已读 19.2.1 空间梁的坐标变换、刚度和节点力能力也无实质重复。

## 完整 Hessian 的判断

范围卡第 4、5 段规定 B=hs(φ)ceq(η)，故对任意非零 ceq 梯度与区间内 hs'，B 的 φ–η 混合导数一般非零；要求完整 Hessian 而把这项固定零会使数学目标自相矛盾。保留该项是同一材料能力的合理补全，并未任意拼接新的物理模型。

依据范围卡，上游只补部分导数，因此 exact upstream 不能直接充当完整 Hessian 的合格参考。现有三版重放计划正确地区分 baseline、exact upstream、upstream+作者扩展。正式验收必须逐项呈现此差别；不得把扩展版称为原样上游，不得由驱动或 SDK 填补默认零导数。独立符号/数值微分与独立 FE 形函数/求积路线原则上能避免把同一材料实现当唯一正确性依据，但本轮没有运行证据证明其完成。

## 输入输出与待落实事项

范围卡已定义 φ、η、w、T、Va、kv/ks 的数学和单位角色、ceq 二次多项式及夹持端点的一二阶导数。C、D 的单位为 eV^-1，其与 w 的乘积无量纲，四个系数对 w 的导数为零与定义一致。

以下属于规划阶段资料缺口，不能称已成题缺陷，也不能由本报告代为补定义：

- 正式 DATA 必须给出 ceq 多项式系数的存储顺序及非对角项是否含二倍约定、η 个数变化时梯度/Hessian 分量顺序、全部数组位置和单位。不能把数学变量的 Hessian 声明为笛卡尔空间 tensor；可复用 CONTRACT 的 components。
- 公开字段必须区分材料点状态与 FE 自由度/插值。CONTRACT 的节点场不自动赋予基函数语义，独立点也不能暗中充当积分点。需说明残量、Jacobian 行列身份、基函数、求积、边界/固定自由度及 c 的意义，并实际确认真实核符号后冻结。
- 材料值、一阶、完整二阶、非 strict 回归与 FE 残量/Jacobian 各自参与何种评分尚未落成；正式题面需完整列明，不以隐藏配置补定义。
- eV/nm³ 与协议整体 SI 习惯不同；正式公开材料必须固定准确单位代码、到真实 MOOSE 参数的转换和输出导数单位，转换不能修正材料导数。
- 数值合法域、η/φ 组合、状态数/网格规模、容差、真实构建和逐例资源尚待验证。全应用形貌与场演化即使成功运行，也不能据此自动获得独立物理准确性认证。

最小后续工作为按现有范围完成公开契约与真实三版重放，再针对最终契约复核；本轮没有要求缩减成只测上游已补的对角项。

## 材料与 SHA256

| 路径 | SHA256 |
|---|---|
| qbank/PHILOSOPHY.md | 1caa7693d2734af313ae2fcefd45a836fb1ce9664a732d2604bd75556ed50409 |
| qbank/design/chapter-19-solver-repair.md | 7c580259eab5a7a0f9bffe02e391e7dc40c2ce8d3cca6c80ea665b5afd38c34f |
| qbank/design/repair-22-checklist.md | 35cda7e9c586b5bc60d4c5394eed0a7ad2b0d409b35accac972df7c9025ef7fb |
| docs/CONTRACT.md | 130d4416fd533812493780c8bc6afbc0a158de6800b59bbec14a852f3cf1c063 |
| runs/authoring/repair-22/moose-30236-scope.md | 2d3455f961383084332b5be0516e222eb84566e906a706a19763bbe6dfbb1f79 |
| runs/authoring/repair-22/moose-22074-scope.md | 87c6a108457139985af05004be1780ec1ced5f6712a4e791380120d963cf9412 |
| qbank/19-solver-repair/19.2-operators/spatial-beam-transform-repair/instruction.md | 11bc5c792c1191dd02fb6170734b8dcfd5a95a76aaf20be087787535721cd637 |
| qbank/19-solver-repair/19.2-operators/spatial-beam-transform-repair/DATA.md | ea86ff1826a9038214f870e56262b96bc41c1b78a386fe85139f5cb0bd7d07c3 |

另已为跨题边界读取 19.4.1 和 19.4.5 的公开 instruction/DATA，其 SHA 见同轮 repair22-moose22074/report.md；它们没有用于本题数学结论。没有沿清单链接读取既有结论。

跨题复核补记：22074 范围卡随后修订并重新读取，SHA256 `6ea4b3e71755241f4a8346c1dc166e52caee1b523de4531391740ff1d8b7b946`，明确三维 Cartesian / 二维 RZ 的真实体积语义。该变化不影响本题导数或跨题无重复结论。具体初轮发现及关闭证据见同轮 22074 报告。
