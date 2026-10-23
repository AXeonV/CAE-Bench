# 最近投影与单元插值数据

遵循[CONTRACT](../../../../docs/CONTRACT.md)。每例为`problem.json`、`input.h5`及`source.msh`。`task=nearest-projection-repair`，`spatial_dimension=D`为2或3，`physics.model=nearest-simplex-state-v1`。`physics.parameters`恰含`mode={"value":0或1,"unit":"1"}`，其中value必须是JSON整数（不使用浮点数1.0/0.0或布尔值），0表示nearest，1表示cell。`geometries={}`，`meshes={"source":{"file":"source.msh"}}`，`conditions=[]`。无时间演化。

## 几何与模式

Gmsh4.1 ASCII包含2..16个源节点，坐标单位m。只允许点(类型15)、两节点直线(1)、三节点平面三角形(2)和四节点直线四面体(4)。D=2时z=0且无四面体；D=3的三角形可嵌在任意平面。节点可孤立，几何可不连通；不由单元维度自动填充未导出的边或面。每个三角形的三条边、每个四面体的六条边和四个三角形面均须显式存在；连接关系由节点tag定义，顺序只决定该实体的重心坐标排列，不决定优先级。同一无序节点集合的原语不得重复。点单元只说明节点，全部源节点始终参与顶点候选。无高阶、退化或重叠内部的同维单元，不含坐标重合但tag不同的节点。

源坐标绝对值≤100 m，查询坐标绝对值≤200 m；不同节点间距及每条边长在[1e-3,100] m。三角形/四面体以任意顶点为原点的边向量矩阵，其最小与最大奇异值之比≥0.01。最多32条边、24个三角形和8个四面体。计分资料保证以下最近选择唯一：不同候选若有相同最近距离，嵌入完整节点轴后的权重相同；若权重不同，距离与最小距离相差至少1e-6 m。仅共享边/顶点导致的零权重表示视为相同。cell模式若含点位于多个闭单元上，它们的完整节点权重也须相同；不存在内部重叠或非一致的边界插值。

nearest模式：D=2的几何集合为全部导出边及全部节点；D=3另含全部导出三角形。求查询点到该闭集合的欧氏最近点，并以所选边/面/顶点的非负重心坐标形成节点权重；边/面之外的仿射投影不得以负权重当作插值。没有边/面时自然降到现有低维实体。nearest忽略三角形在D=2的内部及四面体在D=3的内部。

cell模式：先寻找包含查询点的闭三角形(D=2)或闭四面体(D=3)，在其中作线性重心插值，投影位置等于查询点，距离为0。没有包含单元时执行相同nearest规则。源网格缺少相应高维单元时，对全部点执行nearest；不延拓到无限直线/平面，不使用负权重外推。

可信driver调用真实`query::Index::findNearestProjection`或`findCellOrProjection`，候选数参数n取`max(1,导出边数,导出三角形数)`，使本题原语全部进入候选搜索。这里不要求默认n=4的近似截断行为；仍由真实Index实现完成选择。driver仅从返回权重重建位置及场，不另搜最近点或纠正权重。

## 数组与输入场

`locations.nodes={"kind":"mesh","mesh":"source","entity":"node","ids":"node_ids"}`，node_ids为全部源节点tag严格递增int64[V]。`locations.probes={"kind":"points","ids":"probe_ids","coordinates":"probe_coordinates"}`，probe_ids为非负严格递增int64[Q]，1≤Q≤32，probe_coordinates为float64[Q,D]。tag/探针编号是身份，不能按文件读取顺序或数值大小解释几何。`time_axes={"instant":"times"}`，times为float64 `[0.0]`，仅作静态观测标签。

唯一输入场`nodal_values`也使用同名HDF5 key，quantity=`nodal_value`、unit=`1`、location=`nodes`、time_axis=`instant`、kind=`components`、component_shape=`[3]`、components=`["a","b","c"]`、value_kind=`point`，数组为float64[1,V,3]，各值在[-1000,1000]。三分量是三个独立的无量纲节点量，不是空间向量。sampling恰为`{"space":"piecewise_linear","time":"constant","extrapolation":"forbid"}`：在选定闭单纯形内按其重心坐标作分片线性重建；查询原来在网格外时先按本题规则投影，再在投影点内插，不直接外推节点场。工具不隐式执行这一几何选择。

## 输出

所有输出位于probes、使用instant时间轴，float64，value_kind=point，复制公开的IDs和时间绑定；输出对象名与HDF5 key相同。

|对象/key|quantity|unit|kind / component_shape / components|shape与定义|
|---|---|---|---|---|
|projection|projection_position|m|vector / [D] / x,y及D=3时z|[1,Q,D]；返回的最近/内部插值位置p|
|distance|projection_distance|m|scalar / [1] / value|[1,Q,1]；非负欧氏距离‖query−p‖，cell内部为0|
|weights|barycentric_weights|1|components / [V] / 按node_ids顺序的node_TAG标签|[1,Q,V]；未使用节点为0，sum=1，非负重心权重|
|mapped_values|mapped_value|1|components / [3] / a,b,c|[1,Q,3]；每分量Σ_i weights_i*nodal_values_i|

例如node_ids=[7,42]时weights的components恰为["node_7","node_42"]。projection也等于Σ_i weights_i*x_i；内部cell插值权重来自包含单元而不是任意重建同一点的全局组合。计分同时检查完整权重、位置、距离和三个场分量，不能仅匹配常数场或总和。
