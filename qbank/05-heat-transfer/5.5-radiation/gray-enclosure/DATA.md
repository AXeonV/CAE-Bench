# gray-enclosure 数据契约

入口为problem.json及data_file引用的扁平HDF5，路径相对清单。`spatial_dimension=3`；physics恰含model与parameters，model=`thermal-gray-enclosure-v1`；task可省略，出现时必须为`gray-enclosure`。不允许contract_version、profile、analysis或materials混用。除自由对象名和数组key外，不接受本题未列的模型、字段或条件。

## 物理定义

封闭非参与介质腔体由p个内部等温的灰漫表面组成，几何效果完全由输入视角系数F给定，不要求从隐藏几何求射线。Fij≥0、ΣjFij=1、AiFij=AjFji，可有非零自视角；不把F转置或按另一表面面积定义。Gi=ΣjFij Jj，Ji=εiσTi⁴+(1−εi)Gi，σ=5.670374419e−8 W/(m2.K4)。每表面Ci dTi/dt=Pi−Ai(Ji−Gi)，Ci为总热容J/K，不再乘面积。表面净功率以向腔内离开为正，Pi为外界非辐射加热。0<εi≤1保证辐射度系统可解；不指定额外环境温度、对流或导热网络。F与面积接收检查的绝对容差为1e−10（互易性比较AiFij与AjFji时用1e−10 max(1 m2,Ai,Aj)）；不归一化或修复输入。

## 全局参数

parameters恰含下表全部项，每项恰为value和unit对象；值为有限实数，不含布尔值，整数项必须JSON整数。Tmin<Tmax，温区约束不是评分归一化基准。

| 参数 | 单位 | 含义与值域 |
|---|---|---|
| `start_time` | `s` | 初始时刻t0 |
| `end_time` | `s` | 终止时刻tf，严格大于t0 |
| `temperature_min` | `K` | 适用温区下界Tmin>0 |
| `temperature_max` | `K` | 适用温区上界Tmax>Tmin |
| `patch_count` | `1` | 表面数p，整数2..24 |

## 几何、位置和身份

meshes和geometries均为空对象。locations恰含enclosure：kind=entities，ids指向一个非负int64 ID；它代表一套腔体，表面顺序是components轴的顺序，不是假空间探针。p取patch_count；面积、容量、发射率、初温和功率的shape=[p]，F的shape=[p,p]，第i行第j列是Fij。components标签固定按行优先c1..cL（L为shape分量数）；不增加表面ID表，不按面积排序。

## 时间与输入场

time_axes必须含initial单帧[t0]、response非空严格递增请求时刻；全部轴至多101帧。response位于[t0,tf]。材料、初态以及标注static的记录字段只用initial单帧；其他加载字段可用任意已声明轴：单帧必须在t0，表示全程常量；多帧须首末恰为t0、tf，逐分量连续分段线性插值，不外推。除initial、response外，不允许未被加载字段使用的轴。输出时刻不等于内部时间步，不能跳过未请求的中间载荷。

所有fields必须被条件引用，条件引用fields逻辑名，field.array才是HDF5 key；名称均自由，不靠名字推断quantity。输入field的quantity必须等于条件表给出的data键，只有value的quantity按以下规则：initial_temperature.value为temperature；power.value为power。全部输入field显式sampling，extrapolation=forbid；sampling.space=uniform，表示每个表面的离散参数，不作空间插值；time为constant（static或单帧）或linear（加载多帧）。矩阵参数恒定，加载逐分量插值。components的分量标签见位置段。数组始终[T,N,*shape]；全部float64。本题全部data仅允许同location、同quantity／unit／kind的显式field引用，不允许内联数组或常量替代；禁止省略sampling。输入field的value_kind为point，表示每个离散表面的参数。

## 条件全集

### `enclosure`

role=`material`，variable=`radiation`，operator=`enclosure`，location=enclosure。必须出现；恰一条覆盖整个位置。参数只随实体变化，不随时间变化。data恰含下列全部键：

| data键 | 类型、单位及含义 |
|---|---|
| `area` | components ['p']，`m2`；各表面积Ai>0 |
| `capacity` | components ['p']，`J/K`；每个等温表面的总热容Ci>0 |
| `emissivity` | components ['p']，`1`；灰漫发射率0<εi≤1 |
| `view_factors` | components ['p', 'p']，`1`；Fij，行i射向列j的能量比例 |

### `initial_temperature`

role=`initial`，variable=`temperature`，operator=`initial_temperature`，location=enclosure。必须出现；恰一条覆盖整个位置。参数只随实体变化，不随时间变化。data恰含下列全部键：

| data键 | 类型、单位及含义 |
|---|---|
| `value` | components ['p']，`K`；各表面初温Ti(t0) |

### `power`

role=`source`，variable=`heat`，operator=`power`，location=enclosure。必须出现；恰一条覆盖整个位置。允许上述加载历史。data恰含下列全部键：

| data键 | 类型、单位及含义 |
|---|---|
| `value` | components ['p']，`W`；外界给每个表面的非辐射净加热功率Pi(t)，可正可负 |



## 输出及采样

outputs逻辑名称和array key自由，每个quantity至少一次；可重复请求。输出全部float64，轴为response，不含sampling；位置、单位、kind及分量按表，不允许其他quantity。

| quantity | 类型、单位与含义 | 位置及value_kind |
|---|---|---|
| `temperature` | components ['p']，`K`；各等温表面温度Ti | enclosure，point |
| `radiosity` | components ['p']，`W/m2`；总离面辐射度Ji，包含发射和反射 | enclosure，point |
| `net_radiation` | components ['p']，`W`；向腔内离开表面i的净辐射功率Ai(Ji−Gi) | enclosure，point |

输出point指每个离散表面自身状态；不表示固定空间探针或平均后的虚构温度，不对components轴排序、旋转或归一化。结果仅含输出array及其IDs、时间轴，严格沿用输入身份和行序；不复制坐标、输入字段或重新导出网格。

## 接收范围与验证边界

正式数据须确认给定F可代表本题灰漫表面系统、温度全程位于[Tmin,Tmax]、初态和加载相容，并用独立基准核验预算内可达设计精度。数值接受的F不被工具归一化，合法格式或线性系统可解不能替代参考和物理证据。
表面数2..24，一套enclosure。各轴至多101帧，输入与输出场分别至多3000000个数值分量。没有正式数据时，不把工具fixture当物理／数值验证。
