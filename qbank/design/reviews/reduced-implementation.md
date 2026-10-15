# 2.8—2.11 题面与协议实现记录

2026-10-15。用户授权全部17题的题面与必要协议，不制作examples/references/cases数据，不发布评测。沿用冻结[逐题清单](../chapter-02-task-plan.md)的4+4+4+5编号、slug、维度和分析类型。目录分别为2.8-thin-film、2.9-shallow-water、2.10-rarefied-gas、2.11-memory-fluids；每题instruction/DATA及每节README/COMMON/DATA已落实，数据目录只有.gitkeep。

## 选择与需求映射

本实现选择明确、有限、给定材料与连续模型的首版。数值方法自由；没有把隐藏参考的闭合强加给考生。薄膜单独固定薄隙假设，液体首题包括质量守恒空化；气膜保留可压缩储存；热膜公开跨隙均温能量闭合；Carreau膜明确局部跨隙非线性BVP，避免用等效牛顿公式掩盖流变。浅水含全湿稳态/瞬态、干湿及稳定两层；两层限制光滑双曲解，单层熵弱解的节点观测避开无唯一迹位置。稀薄气体明确连续滑移及硬球Boltzmann/无碰撞两种动理学，气壁反射和半空间储槽完整定义。2.11保留Oldroyd-B构象记忆、结构演化和温度移位；热Oldroyd明确弹性储能、溶剂与松弛耗散。

| 物理需要 | 实际声明 | 拥有层 |
|---|---|---|
| 固定完整模型、材料和分析 | physics.model=fluid-reduced-{slug}-v1；精确带单位parameters | qbank/maintenance/protocols/FLUID-REDUCED.md + fluid_reduced.MODELS |
| 几何、间隙/床高与初态 | domain全节点location；material/geometry、initial/assign条件 | 既有CONTRACT场/条件结构 + 领域检查 |
| 实际边界与条件 | exterior simplex facet分区、精确variable/operator/data集 | 领域规范、boundary_rules及覆盖检查 |
| 连续采样 | 域节点分片线性、边界分片常量；时间linear/constant、forbid外推 | 复用既有sampling结构 |
| 热、记忆、气壁与储槽状态 | 显式温度/构象/结构场或scalar常数；分布用完整Maxwellian参数解析定义 | 无新隐式数组或假坐标 |
| 载荷/水体积 | 真域单元aggregate/sum；N和m³分别属于载荷与体积 | 既有通用aggregate结构 |
| 宏观状态与壁面交换 | 有限quantity白名单、单位/种类/位置；kinetic仅壁面交换 | 领域规范/检查 |
| SDK | reduced_parameters、reduced_viscosity、maxwellian | 本模块；root接入公共SDK |

声明只使用已有JSON结构，因此不另造通用Schema字段。所有新model显式opt-in，拒绝未知fluid-reduced前缀名称，不与cfd四键混用；旧模型不启用该检查，未迁移任何旧数据。root负责将模块接入validation/公开包和SDK导出；在本次测试时接线已生效，实际validate_input可以触发E_FLUID。

## 实际验证

命令：`.venv/bin/python -m unittest discover -s tests -p test_fluid_reduced.py`，9个测试方法通过。测试以临时目录构造真实MSH4.1/HDF5/problem.json，全部17个model均经公开validate_input，通过SDK输出roundtrip验证真实IDs、轴与数组结构。

非法覆盖包括未知版本、缺/多参数、错单位、非正密度、错维度、初态quantity或sampling不符、缺边界/重复边界、输出错单位、构象错误kind（不触发eigvalsh崩溃）、非SPD构象、结构超界、空化压力与占据率不相容、气壁非切向运动及动理学交换指向储槽。独立数值预期：n=1的Carreau恒黏极限与exp温度移位、触变线性混合、Maxwellian一热速度处exp(-1)比及中心归一化。未将helper输出当作自己的独立参考。

四节分别运行技能check_statements.py，输出runs/authoring/2.8、2.9、2.10、2.11/static.json：4、4、4、5题全部通过链接与JSON静态检查。

## 未完成证据与职责

这是实现方记录，**不能替代独立考生视角审阅**；root另安排仅基于公开材料的逐节审阅及最终复核，详见章级记录。本文不宣布独立审阅通过。共享协议发生修订时全部17题均需重新检查。

没有真实题库输入、参考、PDE求解或物理实验；未验证薄隙/连续滑移适用性、动理学求解精度、两层双曲稳定、干湿前沿误差、复杂材料高弹性稳态存在或热能量数值收敛。参考数据、精度及1200/900/2400/1800秒等分节预算均待基准校准。未发布评测，也未把临时协议fixture当作正式样例。隔离公开包与旧行为回归由root统一执行，不能由这9个方法代替。

范围查证参考：COMSOL官方[薄膜说明](https://doc.comsol.com/6.4/doc/com.comsol.help.cfd/cfd_ug_fluidflow_thinfilm.12.18.html)、[浅水说明](https://doc.comsol.com/6.4/doc/com.comsol.help.cfd/cfd_ug_fluidflow_shallowwater.13.15.html)、[Oldroyd-B示例说明](https://www.comsol.com/model/flow-of-viscoelastic-fluid-past-a-cylinder-4383)仅用于核查方向分类；本题精确数学模型由公开协议定义，不由这些页面推断未声明实现。


## 独立公开审阅后的修订（2026-10-15）

root转交review_reduced的五项意见，均采纳并落实。1）薄膜gap时间采样结点的∂t h明确为内部/起点右迹、末点左迹，恒定场导数0；相应瞬时压力/通量/载荷遵同一迹。增加reduced_time_derivative与独立两段斜率2/3测试。2）所有模型节点点值须有唯一连续迹，依赖导数的应力/通量还需唯一导数迹；明确2.11分片线性初速度不自动产生唯一节点应力、不得以单元平均替代；推广到气壁/储槽交角及奇异边界交换。3）气壁反射全部改为明确fw(w)=f(Uw+w)的壁面分布，α=0不定义nw。4）两层首版收窄为layer_inlet完整超临界入流、layer_outflow纯超临界出流和layer_wall；去掉欠定的有限幅亚临界储槽。公开精确法向矩阵与全部特征符号，代码检查入流采样的双曲性/符号与同步时间轴，出流全过程分支由数据保证。测试含合法/非法入流、出流声明、旧算子拒绝以及可手算特征根；这些接口fixture不证明动力学全过程。5）17题DATA逐一修正热分区：热film/slip的温度嵌在流动条件，仅2.11两个热模型有独立完整temperature_wall分区；本构段就地明确a(T)。

修订后11个测试方法通过，17个真实模型输入/输出往返继续通过，4/4/4/5题静态检查全部通过。最终公开文件交还同一独立审阅者复核，本记录不自行宣布通过。
