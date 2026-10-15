# 2.5—2.7 题面与多相协议实施记录

日期：2026-10-15。作者实施范围为 2.5 六题、2.6 四题、2.7 五题，按冻结的 [逐题清单](../chapter-02-task-plan.md) 保留编号、slug、维度及方法边界。依照 caeoj-author-section 与 caeoj-extend-io 执行；本记录不属于考生材料。

## 初始盘点和决定

原章规划只有 2.5—2.7 的方向，新逐题清单已在题面前冻结。本批新增节目录此前不存在；未覆盖已有 2.1、2.2 文件。交付限定题面、必要协议实现与接口验证；用户明确将 examples/references/cases 数据留后，不生成正式样例、参考或评测。

| 节 | 逐题目录 | 规划/题面 | 协议 | 静态检查 | 独立考生审阅 |
|---|---|---|---|---|---|
| 2.5 | [6题](../../02-fluid-mechanics/2.5-interface-flow/README.md) | 六题映射完成 | 解析界面、气相忽略/双侧动量、毛细润湿可显式区分 | passed，6 topics | 由章级主Agent另行安排，未由作者冒称通过 |
| 2.6 | [4题](../../02-fluid-mechanics/2.6-dispersed-flow/README.md) | 四题映射完成 | 单向/双向/泡滴/浓相闭合，固定Euler观测 | passed，4 topics | 同上 |
| 2.7 | [5题](../../02-fluid-mechanics/2.7-phase-change-flow/README.md) | 五题映射完成 | 热质交换、解析蒸冷、混合沸腾/空化、熔凝 | passed，5 topics | 同上 |

新增有限首版选择及依据：

- 不新建移动粒子坐标：2.6 观测采用固定Euler含率与表观相通量，因此不以假探针填充轨迹数组；这是相平均输运任务，非逐粒接触力学。
- 不以task隐式固定物理：12个独立显式版本model规定真实物理方法；同一方法在2D/3D复用，各题DATA固定实际维度。界面模型、相平均模型与热交换模型不混用其压力/相分数含义。
- 新的闭合实际公开：颗粒响应时间线性阻力、浓相压强及增黏、双温交换、稀溶质相内浓度/分配系数、界面动力学、体积蒸冷动力学、等温压力线性空化及mushy焓法均给出精确定义，不能通过“建模自由”隐藏缺口。
- 不相变与熔凝首版使用静止封闭壁面，避免先承诺尚未定义的一般入口相状态；热壁面可加热/冷却。液汽相变必须有压力储槽，避免不等密度相变与封闭刚性不可压缩域的体积不相容。
- 界面初态由二值单元指示函数唯一确定，不给平均含率却暗示任意亚单元界面。界面面积不由alpha唯一确定，故首版通过体积/质量整体量评价，不冒称能从alpha唯一重建面积。
- 所有压力均为绝对静压；自由面/储槽固定外压，其余封闭域固定体积平均压力。分散通量与相内平均速度严格区分，缺相输出有明确延拓。
- 1800秒/8CPU/8GiB及3%相对目标是本节有限模型设计选择，**尚无真实数据校准证据**；不是沿用2.1已验证预算。逐题DATA/COMMON明确说明限制。

## 需求—声明—拥有层

| 需求 | 实际声明 | 拥有/实现 |
|---|---|---|
| 方法、维度和材料 | physics.model、spatial_dimension、闭合的parameters集合 | qbank/maintenance/protocols/FLUID-MULTIPHASE.md；fluid_multiphase.py |
| 物理初态/驱动 | initial/assign、显式acceleration/source，全域实体平均场 | 专用检查：变量集合、空间覆盖、值域、时间轴、sampling |
| 壁面/储槽 | flow/wall、pressure_reservoir，精确data参数和option | 专用检查：真实外面全覆盖、重叠、允许模型、单位与入流状态 |
| 多相观测 | alpha、velocity或flux_a/b，适用热/质/相变率 | 专用检查：恰好输出集合、位置/单位/shape/时间；通用输出器 |
| 相质量 | rho*sum(alpha*真实单元体积) | SDK两个helper；几何测度由调用方显式提供，不凭节点数猜测 |
| 兼容性 | 显式fluid-multiphase-…-v1 opt-in | 未启用完全返回；未知前缀model拒绝；禁止混用CFD四键 |

没有新增JSON字段，故Schema结构无需另造；领域允许集合及相容性由专用检查拥有。根Agent负责接线（包括仅新fluid前缀开启geometry=True）、SDK公开导出、发布工具依赖/隔离打包和整章回归。本作者仅修改三个节目录、领域规范、领域模块、本测试及本记录，未提交、未改共享基础设施。

## 验证证据

命令（仓库.venv环境）：

```sh
.venv/bin/python -m unittest discover -s tests -p 'test_fluid_multiphase.py'
.venv/bin/python .agents/skills/caeoj-author-section/scripts/check_statements.py --section qbank/02-fluid-mechanics/2.5-interface-flow --output runs/authoring/2.5-interface-flow/static.json
.venv/bin/python .agents/skills/caeoj-author-section/scripts/check_statements.py --section qbank/02-fluid-mechanics/2.6-dispersed-flow --output runs/authoring/2.6-dispersed-flow/static.json
.venv/bin/python .agents/skills/caeoj-author-section/scripts/check_statements.py --section qbank/02-fluid-mechanics/2.7-phase-change-flow --output runs/authoring/2.7-phase-change-flow/static.json
```

测试结果：15项通过（实际check_problem读取Gmsh/HDF5，不仅mock）；包含全部12个model及每个允许维度的合法输入、错误model/版本、单位/缺多参数/非正值、缺重初态、非二值界面含率、非法颗粒浓度、缺/重边界、非法算子/额外data、相变缺储槽、熔凝温度次序、时间覆盖/sampling、输出单位/时区间、负溶质浓度、接触角及堆积上界、未启用legacy不改义。质量helper使用独立手算：体积[2,6]、alpha=[.25,.75]、rho_a=1000给质量5000，rho_b=2给质量6；不是helper自生成预期。测试fixture只在TemporaryDirectory生成并自动清理。

三个节静态结果分别为6、4、5题，全部passed。该脚本只证明文件/链接/JSON片段等机械要求，不能证明物理定义或数值结果。

## 领域资料核查

以下官方资料用于核查“润湿需要接触角/滑移”“相变需显式潜热和相焓”“mushy阻力是物理模型而非仅算法参数”的边界，不将商业求解器配置当作本题隐含闭合：

- [COMSOL wetted-wall coupling](https://doc.comsol.com/6.3/doc/com.comsol.help.polymer/polymer_ug_fluidflow_multi.07.05.html)
- [Ansys evaporation-condensation model](https://ansyshelp.ansys.com/public/Views/Secured/corp/v261/en/flu_th/flu_th_sec_mp_evap_cond.html)
- [Ansys solidification/melting momentum](https://ansyshelp.ansys.com/public/Views/Secured/corp/v251/en/flu_th/flu_th_sec_melt_theory_momentum.html)

本题公式是本协议明确的有限模型，不声称与上述软件完整实现等价；未引用未公开的内部细节。

## 剩余限制和交接

独立只读考生审阅、意见修订及最终文件复核由章级主Agent继续；本记录当前不声称已通过。代码回归不证明真实多相物理准确性、连续模型适定、全程含率范围或离散解收敛。数据制作方仍须核查初态边界相容、无相轨迹交叉等相平均适用性、网格/时间误差、预算与相变/溶质参考证据。没有任何正式数据、数值/物理参考验证或评测发布。独立公开包导入/内容检查由根Agent统一实施。

## 独立审阅首轮修订（2026-10-15）

主Agent转交独立review_multiphase的五项实质意见，全部采纳并同步拥有定义的公共规范和受影响题面：

1. 尖锐蒸冷的单一Euler场明确是分片场、允许法向速度两侧迹不同；定义a→b法向、界面几何速度V、质量通量j和两侧运动学。补全切向速度连续、含反冲的 `[stress]n=j[u]`、相内牛顿梯度与三维Stokes去迹、温度连续和 `[k∂nT]=j[h]`。不同cp使用实际界面温度处焓差，热近似明确排除压力功/动能/黏性耗散；禁止将跳跃梯度放入全局黏性本构造成delta应力。
2. 尖锐蒸冷储槽alpha限定每面恒定纯相0或1；引用场必须time=constant。领域检查拒绝分数标签和0→1的线性切换。沸腾/空化保留混合分数范围，没有误伤均匀混合模型。增加真实check_problem回归，覆盖纯相常量、各面不同的纯相场、分数拒绝、纯端点线性切换拒绝及两种混合模型的分数合法性。
3. 沸腾/空化补全 `∂t(rho u)+div(rho u⊗u)=−grad p+div tau+rho g`，`tau=2mu[D−div(u)I/3]`、体黏度零；不暗中吸收迹项改变pressure定义。二维尖锐蒸冷相内部也采用三维平面嵌入同一约定。
4. 删除“单独均值精确复算乘积守恒量”的错误。可线性精确积分的是相体积、常相密度质量、已输出率及分散相rho_i*flux_i动量；变密度共速动量、相溶质和焓含均值相关性，现有观测只能重建近似，不能严格守恒判分。独立反例：等体积两个子区alpha=c=[0,1]，mean(alpha*c)=0.5，而mean(alpha)*mean(c)=0.25。未为掩盖此限制暗加输出。
5. 起始压力/派生相变率仅在具有制作方证明的有限唯一右迹时可请求；无证据则公共输出轴必须严格晚于time_start开始。没有新增伪装物理证明的布尔参数；检查器不求解右迹，明确这是数据制作责任。相变协议fixture改为正时间起请求，避免将未建立物理相容性的起始派生量冒充合法参考。

同步修正空化DATA的温度模板、非交换热题的双温措辞、沸腾率的每混合体积质量率表述。压力输出继续是绝对静压，设计评价明确以固定pressure_reference去背景后给相对误差：`abs(p_calc-p_ref)<=1 Pa+0.03*abs(p_ref-pressure_reference)`；不将背景绝对压力变成数千Pa误差容许，也不逐例平移对齐答案。预算/误差仍须后续真实数据校准。

本配置尚未正式发布且没有真实题库数据，以上修订仍使用v1，并同步全部15题及协议fixture；没有需要重写的旧真实数据。修订后17项协议测试通过，三节静态6+4+5题通过，diff whitespace检查通过；主Agent须继续对修订最终公开文件作独立复核。首轮意见已处理不等于作者自行宣布独立最终通过。
