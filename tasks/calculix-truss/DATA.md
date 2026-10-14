# 输入与输出契约

采用[CONTRACT.md](../../docs/CONTRACT.md)。task=calculix-truss，spatial_dimension=3，physics.model=linear_axial_truss；mesh main通过meshes.main.file引用MSH4.1 ASCII文件，路径相对入口目录。几何与连接以网格为准；一阶两节点线单元表示直杆。没有隐式数组下标连接。

physics.parameters必含young_modulus带unit=Pa、cross_section_area带unit=m2，以及poisson_ratio带unit=1，均为value/unit标量对象。E和A在所有杆上均匀；poisson_ratio是源材料记录，轴杆模型方程不使用它，允许[0,.49]。

## 位置与数组

各locations为kind=mesh、mesh=main。nodes为entity=node、ids=node_ids，含所有节点；bars为entity=element、dimension=1、ids=bar_ids，含全部杆；supports为node、ids=support_ids；roller为node、ids=roller_ids；loaded为node、ids=load_ids。各子集均非空，IDs为严格递增唯一int64，按tag引用，不是行号。supports与roller不重叠；载荷可与约束节点重叠，约束反力不输出。

|NPZ key|dtype|shape|含义|
|---|---|---|---|
|node_ids|int64|[N]|全节点tag|
|bar_ids|int64|[B]|全杆单元tag|
|support_ids|int64|[S]|全固定节点tag|
|roller_ids|int64|[R]|仅y固定节点tag|
|load_ids|int64|[K]|有集中力记录节点tag|
|times|float64|[1]|[1.0]静态荷载步标记|
|applied_force|float64|[1,K,3]|全局x,y,z集中力，N|

time_axes={steady:times}；时间1不是动态演化或积分步长。fields.applied_force的array同名、quantity=force、location=loaded、time_axis=steady、dtype=float64、kind=vector、component_shape=[3]、components=[x,y,z]、unit=N、value_kind=point。未在loaded中的节点无外加集中力；输入没有体力或分布载荷。源原节点1/3属supports，2属roller与loaded，applied_force=[[[1,0,0]]]。重编号实例保持物理连接并按新tags关联。

## 条件

conditions无序，恰好含以下三种记录，每种一条。每种data内字段均必有，不采用额外隐式缺省；variable=displacement。

1. role=boundary、location=supports、operator=all_components_dirichlet，data.value={value:0.0,unit:m}，表示各节点u_x=u_y=u_z=0。
2. role=boundary、location=roller、operator=y_dirichlet，data.value={value:0.0,unit:m}，只约束u_y=0，其余分量自由。
3. role=source、location=loaded、operator=nodal_force，data.force={field:applied_force}，引用fields.applied_force再由array访问NPZ。表示平衡方程右端的节点外力，不是牵引、体力或每长度载荷。

上述零位移是明确标量对象定义多分量约束，不是广播矢量输入；集中力始终用显式矢量场。节点可出现多个入射杆，平衡累加全部杆内力。

## 输出

outputs.axial_stress：array=axial_stress、quantity=axial_stress、location=bars、time_axis=steady、dtype=float64、kind=scalar、component_shape=[1]、components=[value]、unit=Pa、value_kind=average。轴杆σ沿杆常量，因此其单元平均就是该常量。结果NPZ恰好bar_ids、times、axial_stress；轴精确复制，不提交位移、反力、张量或诊断。结构校验只检验文件数组，不验证刚度正定、物理平衡或数值精度。

以下为三条完整条件记录的JSON列表片段；其余顶层元数据仍必需：

```json
[
  {"role":"boundary","variable":"displacement","location":"supports","operator":"all_components_dirichlet","data":{"value":{"value":0.0,"unit":"m"}}},
  {"role":"boundary","variable":"displacement","location":"roller","operator":"y_dirichlet","data":{"value":{"value":0.0,"unit":"m"}}},
  {"role":"source","variable":"displacement","location":"loaded","operator":"nodal_force","data":{"force":{"field":"applied_force"}}}
]
```

本题不使用Physical Group选择作用区域，位置均由对应IDs显式定义。geometries={}；不要求重新划分网格。
