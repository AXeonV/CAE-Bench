# 19.6.4 最终公开设计有界复核

结论：**本轮未发现未决公开设计问题。** 原规划报告 V1 的模型/采样公开说明缺口已闭合；V2 的数值、参考、数据与资源事项仍由相应独立验收负责，本轮不认证其通过。

## 边界与版本

本轮由独立设计审阅 agent 按 caeoj-design-review 执行，只读白名单公开 instruction/DATA、纯范围与既有纯设计报告。未读其他 author 文件、数值记录、hidden、reference、源码或原型；未联网或调用考生。指定 qbank/design/repair22-specfem661-scope.md 不存在，按授权读取题内 author/scope.md，内容仅为范围。当前 HEAD `eb8911eae277ee62117c45ed57f3f23bee7f0fa7`；目标 DATA 存在 unstaged 修改，另有其他题 staged/unstaged 文件。实际复核绑定 raw SHA256。

| 材料 | raw SHA256 |
|---|---|
| qbank/PHILOSOPHY.md | 1caa7693d2734af313ae2fcefd45a836fb1ce9664a732d2604bd75556ed50409 |
| docs/CONTRACT.md | 130d4416fd533812493780c8bc6afbc0a158de6800b59bbec14a852f3cf1c063 |
| qbank/design/chapter-19-solver-repair.md | c0037530ce7a979b1f209d5f61c2cd40f6f4b60221db3013525397212890bb52 |
| qbank/19-solver-repair/19.6-waves/parallel-pml-reduction-repair/instruction.md | 459a6fa812bab350bb4e5b7bd4db4016d55879b7d5eb369b11be9bdf845c0bcc |
| qbank/19-solver-repair/19.6-waves/parallel-pml-reduction-repair/DATA.md | d71114151a266b8a108ac4adc86b35b784df25bc728ed3d2757533bf455479ce |
| qbank/19-solver-repair/19.6-waves/parallel-pml-reduction-repair/author/scope.md | aa9d3ddd5ee2f04518f43b843d79fc6e50dd251c2f5f96d0f1d43da3156e9e1c |
| runs/design-review/repair22-specfem661-clean/report.md | b17a51812251ae54ca5e1324e4d374a747ef86ff56705bd6bdb0961feb62c05e |
| runs/design-review/repair22-specfem661-clean/bounded-central-followup.md | 4a50ef79bd016f28dabc3dda83019ce8d1eec95ee2ab03c7a67383d539b5a0dc |

## V1 闭合与数学自洽

DATA 已明确物理 x,z 到协议二维槽位及 Gmsh 三列的编码关系；SH 是反平面标量位移，声学是位移势 chi，均非二维速度向量。SH 的 F 为 N/m，面积 delta 使右端与 rho u_tt 同量纲，源负号明确；声学 A 为 N，chi 为 kg/m，p=−chi_tt 为 Pa、grad(chi)/rho 为 m，源正号及禁用额外压力技巧明确。两支没有相互混淆量纲或输出变量。

初态与源已定义有限起点 −1.2/f、Ricker 中心零、零场及一阶时间导数、起点前不加载；明确起点源尾不严格零，不能以负无穷激励的状态代替。Nt、dt、首个零场样本、最后时刻、逐步记录、GLL接收插值及源分配约定均已公开。原生ASCII幅值先单精度量化再7位有效数字、最后存float64的观察要求明示，时间轴仍保留公开float64映射，避免把内部double精度误当输出精度保证。

无PML声学四壁的齐次Neumann，以及SH无PML自然零牵引已明确。开启声学C-PML时，上下各三行、L=3h、界面位置、仅z方向、K/d/alpha剖面、左右壁条件都已定义。新增外终端 z=0、800 的 chi=0，连同保存旧值、chi_t、chi_tt置零，关闭了先前外终端缺失；记忆变量初态零，时间离散固定真实库。有限C-PML及残余反射属于观察对象，未偷换为理想无反射场。是否真实源码与数据按此执行是后续验收，不能由文字证明。

## 能力、方法与评价

一个连通试件全部rank有接口，与两个独立试件中某rank独占一个试件、其他rank共享另一试件，是实质不同的合法通信参与输入。单元tag排序、原生分区算法、P=1/3/4和最后rank余数规则均明确，可复用实现必须处理真实参与结构；仅串行回退或按固定rank特判不满足方法要求。数据是否实际形成主/末端无接口仍需分区审计。

指定单文件真实MPI初始化修复与SH/声学传播、声学PML回归是一个共同软件能力，并不要求重做完整流固耦合或复现来源原始爆炸。当前题面与中央章节“并行波动接口”一致。原报告相邻题区别未因公开材料改变，本轮未扩大读取相邻数据或数值证据。

全部时刻与接收点均评分，允许残余返回波而不裁去后段；按分支分别给出正确单位的绝对容差和共同相对容差，合法性/运行失败与基础设施失败区分。真实固定离散回归目标和源码边界一致。容差是否数值充分、量化后是否恰当、完整吸收后段是否得到独立物理核查，本轮均不作通过判断。

未决公开设计项：无。原 V2 的真实分区、串行/MPI、传播/反射/吸收、参考独立性、全数据覆盖、可信实编、离线安装与资源预算仍需实际证据，不从作者数字或本报告继承任何就绪结论。
