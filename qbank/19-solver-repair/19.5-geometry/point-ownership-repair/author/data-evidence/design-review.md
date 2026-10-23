# 独立设计审阅：19.5.1 域外点归属与可选外推

结论：**本轮未发现未决问题（规划设计范围）**。当前single-rank、线性triangle/tetrahedron、strict/closest/default三模式可以进入正式出题；此结论不是正式数据、公开包、预算或后端已验收。本人未参与本题实现，仅在设计审阅目录写报告。

阶段是范围规划。尚未以最终instruction/DATA冻结具体参数域、sentinel和评分，不能把范围卡当完整考试材料。scope首段“构建进行中、尚无数值验收”已落后于本次给出的真实prototype.json；本报告优先区分证据时间，不把旧状态当未完成构建的阻断，也不将新三点原型夸大为全部工况验收。建议owner后续维护同一进度事实，避免范围卡首尾矛盾。

## 能力和相邻边界

关闭外推是[来源PR4453](https://github.com/FEniCS/dolfinx/pull/4453)明确增加的核心能力，目标不是纠正所有域外归属。可复用修复要在真实determine_point_ownership内控制fallback，并保留默认开启时的原行为。两个有实质差别的合法查询是四面体(0,e1,e2,e3)内点(.1,.1,.1)，以及盒内但单元外的(.5,.5,.5)：前者所有模式有owner，后者strict无owner但closest/default有owner；盒外(1.1,1.1,1.1)在padding0即使closest也无owner。任何固定答案或仅看盒命中都无法覆盖这一族；旋转、多cell、padding候选改变、尺度和tri/tet分别增加真实几何差异。

与19.5.2 preCICE最近投影的区别成立：后者在给定离散几何上选择全局最近投影并返回重心权重/传递值；本题先由膨胀bbox产生候选，再作闭单元包含或候选内最近fallback，且输出归属身份。不连接场、不测插值不削弱本题几何语义，也不应声称已经认证MPI归属或非匹配场插值。

## 方法、API与可信驱动

读取原型和当前driver后，requires仅判断真实4/5参数API是否存在；原件缺新参数时直接调用旧API，候选有新参数时转交mode。它没有重判包含、距离比较或抹掉owner；因此原件strict模式产生错误是来源缺失能力的真实表现，兼容调度没有预先修好答案。

只提交utils.h、为determine_point_ownership增加可选find_closest_cell=true并使旧四参调用保持可用，足以实现所承诺C++入口，不必为完成此入口而允许改Python包装或fem调用。正式文档应精确列出要求兼容的入口；不能笼统声称上游整个Python/fem API均已扩展。距离由实际库shortest_vector对所选dest_cells计算，可作真实输出提取，不能由driver自选cell或另算包含后覆盖返回。新driver的query身份映射/重复点处理属于后续接口审阅事项，不可用坐标相等冒充普遍独立身份保证。

## 评价与数值依据

严格模式应只接受公开误差域内的实际包含。源码GJK用平方距离阈值10*epsilon；因此正式DATA必须限制尺度、退化程度以及明确域外点距边界的安全间隔，并把精确闭集合语义与数值判定误差校准讲清。范围卡已明确独立误差校准和远离歧义点，不以“增大包含容差”替代修复；无须在规划阶段凭空指定数值阈值。

包含单元/最近候选唯一性、排除共享界面多归属和平局，使比较原输入cell身份而非内部编号可定义。唯一外表面/边/顶点仍可测闭集合。独立重心坐标和单纯形投影可分别核对包含与距离；不能只用补丁结果作为唯一几何真值。

prototype.json中的实际结果为baseline两mode均[0,0,-1]，reference strict[0,-1,-1]、closest[0,0,-1]，与上述独立几何事实相容。456+183+128源码SHA记录及6依赖TU重编34.873s提供初步真实构建证据；本轮未重新编译，也未逐文件重新认证这些树。此原型还未认证triangle、多cell、padding变化、default四参回归、完整距离/身份输出或正式限时。

正式冻结前保留上述承诺覆盖、独立完整输出核对和全依赖重编生效证明；这属于数据/后端验收，不能因原型只有单tet把范围静默缩成三点特例。未发现需要改变当前能力定位的设计缺陷。

## 实际材料与版本

基线HEAD：`6da63a4203b144fc22fbbc0a598a59f33b960e46`。范围卡与work证据未由该提交绑定，以实际SHA为准；git status --short未给出这三张runs卡的跟踪条目（忽略的工作证据）。关键材料如下，其余逐文件SHA见同目录materials.json。

| 材料 | SHA256 |
|---|---|
| runs/authoring/repair-22/dolfinx-4450-scope.md | 82eb24fa37d21c0d59c9afaa8868547bcd319b36d7d2f6a875bea48311fe7ac9 |
| qbank/19-solver-repair/19.5-geometry/point-ownership-repair/author/data-evidence/prototype.json | 094d58ad79f0329ad081a234a71f20e31c36e49c9ce626d5c6462e418f7d7d31 |
| qbank/19-solver-repair/19.5-geometry/nearest-projection-repair/instruction.md | c005ef3119caaa49abcef59162b262aa85a6348bf133ef69b2bcee1987a2fdd5 |
| work/repair-22/dolfinx-4450/pull.json | 73e598821ece4e27f2d9309d3de92a2bb3f589e6bb736c5830ac8e25f489ed34 |
| work/repair-22/dolfinx-4450/files.json | c94e204c545f1c699b47813609c9b4748552519815c765ac5e9bdb236824a15e |
| work/repair-22/dolfinx-4450/ownership-prototype.cpp | 2f6646cdb35999eb04426b8f8a3429ae4d7d4111dae819f3b20132e7207a1ef0 |
| work/repair-22/dolfinx-4450/public/driver.cpp | 8c67a575c85f6920d9a566a33afa32ad1719787fdd5d3818e00c41f8e6ca819a |
| work/repair-22/dolfinx-4450/fixed-utils.h | 44cee2d91b2400ce193c6a93879884cdf6aaec06c343b3c36718590b6fb7b4eb |

已读取PHILOSOPHY、章规划、CONTRACT和架构职责。没有用已有父级批准替代判断；没有实施或修改题目，也没有新运行求解器/编译。对公开参数域、完整数据和资源均仅给阶段性边界，后续冻结变化需复核。
