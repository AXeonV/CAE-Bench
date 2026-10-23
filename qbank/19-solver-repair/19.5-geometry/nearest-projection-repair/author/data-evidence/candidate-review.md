# nearest-projection-repair 独立考生审阅

## 分阶段审阅与最终结论

先完成 statements，再按协调方明确新增的公开白名单升级 exam-materials。最终题面结论：本轮未发现未决问题。两种模式、候选几何集合、身份、完整节点权重轴、场量、唯一性、评分及资源可由公开三文件确定。

初始 statements 阶段未读取样例。最终样例状态：01、02 的全部公开 JSON/HDF5/Gmsh 输入、reference、grading 和 output 已检查，无必需资产缺失。

## 材料及版本

白名单仅下列三文件；通用协议已在本独立考生上下文全文阅读，本轮核对实际 SHA 相同。技能及 workflow 仅用于审阅方法，不补本题含义。

| 文件（仓库相对路径） | SHA256 |
|---|---|
| qbank/19-solver-repair/19.5-geometry/nearest-projection-repair/instruction.md | f4c6bbdd0d905b6d9d92c4c3141ff9942ec0dd1a4443e893230d7c8edbfe4fb4 |
| qbank/19-solver-repair/19.5-geometry/nearest-projection-repair/DATA.md | 6476144240b47326b27837e69f9d01539fc4979d521a3c85906dc7c0b169dede |
| docs/CONTRACT.md | 130d4416fd533812493780c8bc6afbc0a158de6800b59bbec14a852f3cf1c063 |

仅 instruction.md、DATA.md、CONTRACT.md 解释题意。初始 statements 阶段未读 source、driver、author、设计、隐藏 case、参考生产、data-manifest、ZIP 或任何样例；最终阶段仅扩大到下文明确列出的公开材料，仍未读求解源码、driver或作者材料。未改题、未写完整 solver、未运行付费 benchmark。此前审过其他题的上下文没有包含本题作者材料。

## 按考生消费顺序检查

| 项目 | 依据及结论 |
|---|---|
| 两种模式 | DATA:3、11–13 明确 mode=0/1；nearest 的集合随 D 定义，cell 优先闭三角形或四面体包含插值，再执行完全相同的 nearest。nearest 不把 D2 三角形内部或 D3 四面体内部算作候选。 |
| 几何完备性及边界 | DATA:7–9 明确低阶实体类型、D2 z=0、D3 嵌入面、显式边／面、孤立节点、无序集合不重复、非退化、范围与质量约束。全部源节点始终是顶点候选，不从未导出实体推断几何。 |
| 闭集合及非负权重 | DATA:11–13 排除无限仿射外推及负权重，闭实体包含端点／边界，缺高维实体时降为现有低维集合。 |
| 唯一性及多重表示 | DATA:9、34 比较嵌入完整节点轴的权重，避免同一位置由不同全局组合任意重建。共享边／顶点的零权重扩展可相同；cell 多闭单元包含时也要求相同权重，数据保证排除冲突。无须增加维度优先级或tag优先级。 |
| 身份与轴 | DATA:19、31、34 规定递增源节点tag、探针ID、source引用、points坐标、完整权重按node_ids顺序与node_TAG标签；身份不等于读取顺序。输出绑定probes，故只需按CONTRACT复制探针IDs和instant时间，不把node_ids误当输出位置。 |
| 场与采样 | DATA:21 定义3个独立无量纲components，不是D维空间向量；分片线性重建在选定闭单纯形中执行，外点先投影后内插。static时间轴和sampling不会额外定义演化或连续外推。 |
| 输出与单位 | DATA:25–34 完整声明shape、dtype、components、quantity、unit；projection、distance单位m，weights与mapped_values无量纲。位置和映射由同一完整权重重建，distance为查询点到返回位置的范数。 |
| 真实修复边界 | instruction:7–9 明确单Index.cpp、替换路径、接口保留、重编与重新链接、不允许替代输出/改驱动或算例硬编码。DATA:15 明确真实API、候选数n覆盖原语与driver仅重建观测，不要求猜测默认n截断。 |
| 评分与资源 | instruction:11 明确每例全部query/全部输出逐值通过、atol按量纲、rtol=1e-8、case等权及失败处理，4CPU/8GiB、编译180s/每例30s。领域与非目标范围清楚。 |

## 具体反例检查

以下是纸面几何反例，不是实际样例验证或完整求解器。

1. **D2内部不等于nearest零距离**：三角形顶点(0,0)、(2,0)、(0,2)，全部边显式存在，查询(.3,.4)。cell权重为(.65,.15,.2)，距离0；nearest应到x=0边上的(0,.4)，权重(.8,0,.2)，距离.3。DATA:11–13已明确区分，不能因有二维三角形而统一选择内部插值。
2. **低维更近应获选**：在上述集合加入独立节点(.3,.41)。nearest最近是该节点，距离.01，比边距离.3小；不能因边维度较高而胜出。相反cell仍在包含三角形内插，不能让更近孤立节点抢走内部cell语义。DATA:7、11、13同时消除两种误读。
3. **有限实体与外推**：仅有一条有限线段和两个端点、查询在线段延长线上且超过端点。无限直线投影会出现负权重，但公开要求最近闭线段／顶点和非负重心坐标，故应选端点，而不是距离0的仿射外推。
4. **节点读取顺序不决定权重轴**：若source文件先读tag42再读tag7而node_ids=[7,42]，权重仍按node_7、node_42输出；DATA:19、31、34与CONTRACT的身份规则一致。
5. **同位置不同权重不能替代**：包含三角形内点可用别的节点组合重建同一空间位置，但DATA:34要求来自实际包含单元的权重，且评分独立检查weights和三个场分量。只匹配位置或常数场不能通过全部输出。

未发现需修订、待核实或依赖外部领域知识补足的公开要求；不提出算法或空间搜索数据结构偏好。

## statements 阶段覆盖与限制（历史）

本轮只认证三文件题意可解释性。未核对任何实际source.msh、HDF5、JSON、公开output或reference，未验证全部范围与唯一性保证在实际输入中成立。未执行协议工具、真实库API、编译、资源实测、公开包独立可用性、数值参考认证或隐藏测试审计。后续升级exam-materials须先取得明确公开白名单和冻结ZIP版本，再按实际版本补充本报告。


## exam-materials 范围与版本

明确新增白名单后读取 data-manifest 的 samples 映射确认01/02身份；读取这两例 input/problem.json、input/input.h5、input/source.msh、reference/grading.json、reference/reference.h5、output/result.h5；ZIP仅读取README/MANIFEST、同样三文件/样例及中性SDK，未追踪pool或读取其他资产内容。README/MANIFEST确认public_samples=[01,02]。

公开ZIP SHA256：e14c27835494d87aaf42c3e334544f0bf17bc8b6f8e2a311e0e6f0c403bef029，与冻结值一致。三文件版本未变；三文件及两例全部已允许公开资产在ZIP内与工作树字节相同，SHA与MANIFEST相符。SDK字节SHA与本独立审阅上下文此前已读的中性SDK完全相同，未从其依赖或扩展实现补题意。

### 全部样例实际覆盖

- 01：D=2、mode=1、V=3、Q=5；网格有3点单元、3条边、1三角形。文件节点次序为[24,7,41]，权重轴node_ids为[7,24,41]，实际检验了身份重排。查询覆盖内部cell、边投影、顶点回退及外点。
- 02：D=3、mode=1、V=4、Q=5；有4点单元、6边、4面、1四面体。文件节点次序[41,58,24,7]，权重轴[7,24,41,58]。查询覆盖内部cell、闭边界cell、面投影和顶点回退。
- 已读完整两份source.msh全部节点和单元连接，非仅网格摘要；按MSH4.1ASCII块解析。所有源tag为正，坐标/D2零z、点数/实体数、允许类型、边面显式完备、无重复无序集合、节点距离/边长、任意顶点基矩阵奇异值比均满足公开约束。每例仅单一高维cell，其边面为一致边界，没有同维内部重叠。
- 已完整读取两例全部数组，无大数组截取。输入keys恰为node_ids、probe_ids、probe_coordinates、times、nodal_values，dtype、shape、严格递增身份、坐标范围、场范围、时间值全部符合DATA；输出恰为四场加probe_ids/times，轴和编号正确复制。
- 检查根级HDF5 dataset、无分组/属性/软外链/别名/外置/虚拟数据、允许压缩、有限值及全部元数据quantity/unit/components/sampling。输出weights轴与node_TAG标签匹配node_ids，mapped_values是三个无量纲components，未误作D维向量；projection才是D维m单位vector。
- 两份grading对全部四quantity的单位、逐点/逐时刻/逐分量规则、rtol及atol均与题面一致；公开output与reference文件逐字节一致。

### 独立几何与数值核对

仅对已批准样例，用NumPy仿射最小二乘求闭单纯形各子面的投影并限制非负重心坐标，比较有限原语最近点；cell先解包含单元重心坐标，再回退同一nearest集合。没有编写真实库修复、搜索树或完整solver。

逐点核对全部10个查询的包含/回退分支、完整节点权重、投影位置、欧氏距离、三个映射场值；检查非负/sum=1、权重重建坐标与场、距离重建。对于nearest分支，逐原语验证距离相同的表示具有同一完整权重，其他候选满足1e-6m距离间隔。cell若有多种闭单元表示则比较完整权重，两例实际只有单个cell。

| 样例 | projection最大绝对误差 m | distance最大绝对误差 m | weights最大绝对误差 | mapped_values最大绝对误差 |
|---|---|---|---|---|
| 01 | 1.110223025e-16 | 1.1443917e-16 | 1.110223025e-16 | 4.440892099e-16 |
| 02 | 5.551115123e-17 | 0 | 1.110223025e-16 | 8.881784197e-16 |

所有误差均在公开容差内。01的内部点(.2,.3)预期权重按node_ids顺序为(.2,.5,.3)、距离0；公开reference的距离约1.14e-16m是浮点舍入，远小于1e-8m容差，不是题意矛盾。02查询(.2,.1,-.2)投影(.2,.1,0)，距离.2m，按[7,24,41,58]顺序权重(0,.1,.8,.1)，实际检验了外点face回退及字段传递。

### 实际新增材料 SHA256

路径相对仓库根；zip:表示包内条目。

| 文件 | SHA256 |
|---|---|
| qbank/19-solver-repair/19.5-geometry/nearest-projection-repair/data-manifest.json | 686a12d73bd054662e205de0eec52e2b6b1c9cf084b6e8603e7431fe08471c35 |
| zip:README.md | dd1d96e949e4c2831d9f0d8deb406ce62e271971f89e67c874e9fec594f69cf7 |
| zip:MANIFEST.json | 9c5cb900e72bef9a19e8c4f2205ee0f631579bf1290abbf4976e1851a3060832 |
| zip:src/caeoj/sdk.py | 3ddf8f5a1b516eca67abae35a05a26dc1b7a8381a168d7d148ea22f2ecab9cba |
| qbank/19-solver-repair/19.5-geometry/nearest-projection-repair/samples/01/input/problem.json | 00a88bc4a51165c7937ab49ca2c592ab205dca44c940c210714f7b10466f0b0f |
| qbank/19-solver-repair/19.5-geometry/nearest-projection-repair/samples/01/input/input.h5 | e0dd60420023942521babb0d039c325216a90fae4aa47d8e7454557ba4e5ac37 |
| qbank/19-solver-repair/19.5-geometry/nearest-projection-repair/samples/01/input/source.msh | 00a24a5dd75178b169321d46d1595c93ce60b29eeb33ec5ed545db5e9d8c105b |
| qbank/19-solver-repair/19.5-geometry/nearest-projection-repair/samples/01/reference/grading.json | 2b33bdacb8140ae453d7df9ebc7438edb5d2b3bc72ab694901a753e2296b51e1 |
| qbank/19-solver-repair/19.5-geometry/nearest-projection-repair/samples/01/reference/reference.h5 | 27b1a2595904d643579e572d61edff245393f198c902da9ccfe3aeb9fb33a553 |
| qbank/19-solver-repair/19.5-geometry/nearest-projection-repair/samples/01/output/result.h5 | 27b1a2595904d643579e572d61edff245393f198c902da9ccfe3aeb9fb33a553 |
| qbank/19-solver-repair/19.5-geometry/nearest-projection-repair/samples/02/input/problem.json | caabe52b62016534f77334ff025976ea68b5c050e1100d977a47a27325648edb |
| qbank/19-solver-repair/19.5-geometry/nearest-projection-repair/samples/02/input/input.h5 | b003f3c2b689027ded5797ca6e33281d386544293d17870b7c318c85f261ebdf |
| qbank/19-solver-repair/19.5-geometry/nearest-projection-repair/samples/02/input/source.msh | 602842632ebd13784ebb53bdfd868ed5eb412766545e1af5250ba164e8536a21 |
| qbank/19-solver-repair/19.5-geometry/nearest-projection-repair/samples/02/reference/grading.json | 2b33bdacb8140ae453d7df9ebc7438edb5d2b3bc72ab694901a753e2296b51e1 |
| qbank/19-solver-repair/19.5-geometry/nearest-projection-repair/samples/02/reference/reference.h5 | 96a8f7813c528a1e0031af52f4ec15ae7033c6939198325fbd84909143c4169e |
| qbank/19-solver-repair/19.5-geometry/nearest-projection-repair/samples/02/output/result.h5 | 96a8f7813c528a1e0031af52f4ec15ae7033c6939198325fbd84909143c4169e |

## 最终限制与结论

本次公开样例均mode=1；虽然外点覆盖相同nearest回退，未实际核对mode=0、无高维cell、仅节点、不连通/孤立节点、多cell一致边界或最大尺寸样例。这些范围的定义已按statements检查，不把两例数值通过外推为全部数据覆盖。

未执行公开包安装、preCICE构建/链接、真实Index或driver、资源实测、隐藏case/参考生产/来源或完整公开包运行认证；不从源码反推题意。独立几何核对只认证两例公开输入及其参考/输出与定义一致。

最终结论：statements与exam-materials均本轮未发现未决问题；01、02全部已检查，无必需公开资产缺失。
