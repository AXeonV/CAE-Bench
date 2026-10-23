# 19.2.2 最终公开设计有界复核

结论：**本轮未发现未决公开设计问题。** 初轮规划报告提出的公开说明事项已在本次实际读取的 instruction / DATA 中闭合。结论仅针对题目设计和契约，不认证源码、参考、容差的数值资格、数据覆盖、构建或资源达标。

## 边界与版本

本轮由独立设计审阅 agent 按 caeoj-design-review 复核，未读 author、hidden、reference、实现、原型或数值验收记录，未联网或调用考生。沿用初轮纯设计判断，不继承作者的数值通过结论。当前 HEAD `eb8911eae277ee62117c45ed57f3f23bee7f0fa7`；目标题目录为未跟踪，工作区还有其他题的 staged/unstaged 改动。报告仅绑定下列 raw 文件 SHA256，不以 HEAD 代替实际材料版本。

| 材料 | raw SHA256 |
|---|---|
| qbank/PHILOSOPHY.md | 1caa7693d2734af313ae2fcefd45a836fb1ce9664a732d2604bd75556ed50409 |
| docs/CONTRACT.md | 130d4416fd533812493780c8bc6afbc0a158de6800b59bbec14a852f3cf1c063 |
| qbank/design/chapter-19-solver-repair.md | c0037530ce7a979b1f209d5f61c2cd40f6f4b60221db3013525397212890bb52 |
| qbank/19-solver-repair/19.2-operators/grand-potential-derivatives-repair/instruction.md | 7f71e1c37b4008dd52c55526210f4b2e34e8a6e57077e013a2fffe09fad0e0db |
| qbank/19-solver-repair/19.2-operators/grand-potential-derivatives-repair/DATA.md | 433082b54edef569eb1605f512b5c213196007154d56c204419898813636c1c2 |
| runs/design-review/repair22-moose30236/report.md | fada5acb2f0413173f7dc5214085905482c32c34bfc2a872f67bac24b1ea1cf6 |

## 公开缺口闭合

DATA 的 ceq 定义已明确二次多项式的 1/2 双和、上三角系数、非对角项系数及 inactive η。梯度固定为五个无量纲变量，完整 Hessian 25 分量明确行优先顺序，使用 components 而非空间 tensor；跨 φ–η 及 η–η 两侧均在义务内。变量别名两组的逻辑映射明确，不能依赖固定变量字符串。strict/non-strict 的范围与原有四项密度/巨势回归值都已公开。

SI 定义可自洽：Va 为 m³，kv/ks 为 J/m³，因此 C、D 及其对无量纲变量的导数均为 J^-1；w 为 J，数密度为 m^-3，巨势密度为 J/m³。公开说明 PARABOLIC 不使用其他分支的 eV/K 常数、无隐藏换算，关闭了初轮单位/转换说明缺口。这是公开目标的量纲判断，不确认真实材料实现是否遵守。

FE 程序已定义为独立一维两节点线段，状态空间均匀，FIRST LAGRANGE、两点 Gauss、无边界约束及消去，不能暗加面积/厚度。残量为 ∫Ni[c−A−Bc−(C+D)w]dx，与初轮拟稿相反的符号现在已明确冻结；矩阵按独立节点自由度线性化，虽基态两端相同也不得当作一个共同变量。由此残量及对无量纲状态/浓度的 Jacobian 单位 m，对 w 的 Jacobian 为 m/J，与输出表及题面评分单位一致。原生残量/解析 Jacobian、INITIAL材料值、DOF 映射、未评分其他行与状态不更新的含义已说明。

公开范围与评分一致：全部声明的材料值/导数/FE 输出逐文件全通过才得分。逆能量系数采用输入 Ev=Va kv、Es=Va ks 乘误差比较，量纲无量纲；公开给出等价原单位 atol，并保留原单位返回值，未暗中改变输出。容差数值是否覆盖舍入或能检出错误，需要独立数据/数值审计，本轮不作证明。

## 可复用性及限制

单 active η、常 ceq、端点/越界夹持，与多 active η、非零交叉项、内部 φ、改变量名构成实质不同的合法输入；单一固定材料状态或只补对角导数不能覆盖公开族。指定真实类、两文件替换和真实 FE 装配是章级方法要求，不是任意解法偏好。局部材料/离散一致性与完整烧结演化的适用性清楚区分，未扩大为形貌预测认证，与初轮相邻题边界结论不冲突。

未决公开设计项：无。仍需其他验收承担：真实 baseline/exact-upstream/完整修复版区别、参考独立正确性、实际数据对公开组合的覆盖、真实构建/执行/后端及资源。这些不因公开契约闭合而获得通过。
