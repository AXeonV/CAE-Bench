# 点归属输入与输出

通用JSON/HDF5/MSH及结果规则见[CONTRACT](../../../../docs/CONTRACT.md)。本题输入目录含`problem.json`、`input.h5`、`source.msh`。所有空间坐标、padding和距离使用m；唯一时间为0 s，不进行时间演化。

## 网格与几何语义

`task="point-ownership-repair"`，`spatial_dimension=D`为2或3；`geometries={}`、`conditions=[]`、`fields={}`。`meshes={"source":{"file":"source.msh"}}`。源网格为MSH4.1，D=2仅含线性三角形（Gmsh类型2），D=3仅含线性四面体（类型4）；可另含类型15的节点元素，不含其他单元。三维坐标写在MSH中，二维节点z严格为0。全部节点都至少用于一个顶维单元，1..16个顶维单元、D+1..48个节点。顶维单元的原MSH元素tag是输出单元标识，范围1..1,000,000。

节点坐标各分量绝对值不超过100 m，任意不同节点距离至少1e-3 m。每个单纯形以首节点为原点的边向量矩阵最小/最大奇异值之比不低于0.05；无重复单元或重叠内部。源文件中的节点/元素存储顺序不定义输出身份，须按声明标签处理。

查询数Q为1..24，坐标各分量绝对值不超过200 m，任意不同查询相距至少1e-4 m。闭单元包含其外表面、边和顶点；数据保证每个查询至多被一个闭单元包含，不采样多单元共享边界。任何不被包含的查询与全部闭单元的距离至少1e-5 m，避开浮点包含阈值的模糊区域。

候选集是逐轴闭包围盒各向外扩展padding后的命中单元。实际包含单元优先。允许外推且没有包含单元时，仅在候选集中选择与查询欧氏距离最小的闭单元；没有候选即未归属，不进行全局最近单元外推。数据保证非空候选集中最近单元唯一：存在其他候选时，最小与次小距离之差至少1e-6 m。几何唯一性及上述间隔由正式数据保证，不能从文件名或算例标识推断归属。

## 声明及输入数组

`physics.model="simplex-ownership-v1"`，`physics.parameters`仅有下列两个`{value,unit}`对象：

|参数|value及单位|含义|
|---|---|---|
|mode|JSON整数0、1或2，unit=`1`|0：第五参数false，严格实际包含；1：第五参数true，允许候选内外推；2：不传第五参数，默认语义应与1相同。不得用浮点0.0/1.0/2.0或布尔代替整数。|
|padding|有限数0..5，unit=`m`|逐轴包围盒的绝对扩展量；不改变实际包含定义。|

`locations.nodes={"kind":"mesh","mesh":"source","entity":"node","ids":"node_ids"}`；`locations.probes={"kind":"points","ids":"probe_ids","coordinates":"probe_coordinates"}`；`time_axes={"instant":"times"}`。输入HDF5包含：

|数组|dtype和形状|含义|
|---|---|---|
|node_ids|int64 `[N]`|源网格全部节点tag，严格递增。|
|probe_ids|int64 `[Q]`|正、唯一且严格递增的查询标识。|
|probe_coordinates|float64 `[Q,D]`|按probe_ids顺序给出的查询坐标。|
|times|float64 `[1]`|严格为`[0.0]`。|

## 输出与评分

输出为`result.h5`。除CONTRACT规定复制的输出位置身份`probe_ids`及时间轴`times`外，写下列三个float64数组，形状均为`[1,Q,1]`，按输入查询轴排列：

|数组|quantity；unit|每个查询的值|
|---|---|---|
|owned|point_owned；`1`|有归属为1，无归属为0。|
|cell_id|owning_cell_id；`1`|有归属时为选中单元的原MSH tag，无归属时为-1。|
|distance|cell_distance；`m`|有归属时为查询与选中闭单元的最短欧氏距离，无归属时为-1。实际包含点的数学距离为0。|

三项outputs声明均为`array=数组名`、`location="probes"`、`time_axis="instant"`、`dtype="float64"`、`kind="scalar"`、`component_shape=[1]`、`components=["value"]`、`value_kind="point"`；quantity和unit如表，不另含sampling。两个无量纲字段虽以float64保存，身份值必须精确一致。

owned与cell_id采用atol=rtol=0；distance采用atol=1e-8 m、rtol=1e-8。每例每个查询全部三个字段均通过才记通过。不存在可缺省的查询、输出或参考轴。公开样例与其对应计分case共享输入身份，仍按计分清单的每例一次计分。
