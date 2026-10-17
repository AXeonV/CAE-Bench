# imposed-field-migration 数据契约

入口problem.json及data_file引用的扁平HDF5，路径相对清单；顶层采用CONTRACT通用结构。physics恰含model、parameters，model=`species-imposed-field-migration-v1`；task可省略，出现须为`imposed-field-migration`。禁止profile、contract_version、analysis、materials混用。不接受未列字段、位置、条件或参数组合。

## 物理与支持范围

一维静止稀溶液中的独立离子示踪组分；恒温T、外场E沿+x，通量J_i=−D_i∂x c_i+w_i c_i，w_i=D_i z_i F E/(RT)，∂t c_i=−∂x J_i。两端均给定浓度；正电荷在正E下向+x漂移。背景支持电解质维持外场，其库存与电荷不参与输出；无Poisson反馈、电中性浓度约束、电极反应、流动或焦耳热。中性组分退化为Fick扩散。

## 全局参数

parameters恰含下表全部项；每项只有value、unit，数值有限、布尔不是数值、integer必须JSON整数；全部参数无缺省。

| 参数 | 单位 | 含义及值域 |
|---|---|---|
| `species_count` | `1` | 组分数s，JSON整数1..8 |
| `length` | `m` | 区间长度L>0 |
| `temperature` | `K` | 给定恒温T>0 |
| `electric_field` | `V/m` | 沿+x的恒定外场E，可正可负或零 |
| `gas_constant` | `J/(mol.K)` | 气体常数R>0，由输入明确给定 |
| `faraday` | `C/mol` | 法拉第常数F>0，由输入明确给定 |

## 几何、位置和身份

spatial_dimension=1；meshes、geometries均为空。所有points坐标为float64[N,1]、单位m；这些点只描述初态、边界或观测，不指定内部离散。IDs按CONTRACT非负、严格递增，实体行与字段N轴对应，ID不能作数组下标。

| location | kind及数量 | 完整语义 |
|---|---|---|
| `system` | entities，1..1项 | 唯一材料／动力学参数对象，不是空间探针 |
| `knots` | points，2..257项 | 初态空间结点，x严格递增，首尾恰为0、L |
| `left` | points，1..1项 | 左端坐标x=0 |
| `right` | points，1..1项 | 右端坐标x=L |
| `probes` | points，1..256项 | 严格位于0<x<L的独立接收点；坐标可重复，身份独立 |

## 时间、数组与重建

time_axes恰为initial、boundary、observe。initial引用float64[1]=[0.0]；observe引用float64[T]，1≤T≤129，首项≥0、末项H>0；boundary引用float64[B]，2≤B≤129，首项0、末项H；中间严格递增。输出仅用observe；材料与初态用initial；两端条件用boundary。输出请求不约束求解器内部时间步，也不表示帧间跳跃。物理初态固定t=0，不是迭代初猜。

场均float64，形状[T,N,*component_shape]。scalar固定shape=[1]、components=["value"]；components类型按表中shape行优先展平为["c1",...,"cL"]，L为分量总数。s替换为species_count；所有组分按i=1..s，同一算例各表始终同序，标签不表示化学名称。逻辑字段名与HDF5 array key自由且区分；quantity等于data键名，键value例外等于该条件variable。引用只能同location、同规定时间轴，fields恰为被条件实际引用的字段，无未用字段。

所有data均必须采用{"field":"逻辑字段名"}，不接受内联数值、option或数组；表中每种operator恰一条，data键全集如下，无可选键／缺省参数或其他条件。每字段均point；sampling显式，extrapolation=forbid。材料与所有entities场space=uniform、time=constant，表示各对象固定属性／初态，不作对象间插值；uniform不要求不同实体行的值相同，各行独立给定。初态knots场space=piecewise_linear、time=constant，在相邻结点按x逐组分线性重建，含两端；端部场space=uniform、time=linear，在boundary相邻时刻逐组分线性插值，覆盖[0,H]不外推。初态浓度两端与各端t=0边界值必须相等（存储float64精确相等），无不相容角点。

## 条件全集

### `diffusivity`

role=`material`，variable=`diffusivity`，operator=`diffusivity`，location=`system`；时间轴`initial`，完整覆盖该位置。data恰含：

| 键 | 类型、单位、语义与限制 |
|---|---|
| `value` | components [s]，`m2/s`；各组分常量有效扩散系数D_i>0 |
### `initial`

role=`initial`，variable=`concentration`，operator=`initial`，location=`knots`；时间轴`initial`，完整覆盖该位置。data恰含：

| 键 | 类型、单位、语义与限制 |
|---|---|
| `value` | components [s]，`mol/m3`；t=0的移动相体积浓度c_i≥0 |
### `left`

role=`boundary`，variable=`concentration`，operator=`left`，location=`left`；时间轴`boundary`，完整覆盖该位置。data恰含：

| 键 | 类型、单位、语义与限制 |
|---|---|
| `value` | components [s]，`mol/m3`；该端移动相浓度Dirichlet历史，c_i≥0 |
### `right`

role=`boundary`，variable=`concentration`，operator=`right`，location=`right`；时间轴`boundary`，完整覆盖该位置。data恰含：

| 键 | 类型、单位、语义与限制 |
|---|---|
| `value` | components [s]，`mol/m3`；该端移动相浓度Dirichlet历史，c_i≥0 |
### `charge`

role=`material`，variable=`charge`，operator=`charge`，location=`system`；时间轴`initial`，完整覆盖该位置。data恰含：

| 键 | 类型、单位、语义与限制 |
|---|---|
| `value` | components [s]，`1`；整数电荷数z_i，−4..4，允许中性组分 |

## 输出

每个下列quantity至少一次，可重复请求；逻辑名及array key自由，不得修改quantity、单位、location或分量。输出均float64、point、引用observe，不含sampling。形状及components按上文规则；各输出是相应时刻与对象的瞬时状态，不是时间平均或积分。

| quantity | 类型、单位和含义 | 完整位置 |
|---|---|---|
| `concentration` | components [s]，`mol/m3`；移动相体积浓度c_i(x,t) | `probes` |

结果HDF5只含输出array及必需IDs／时间轴，严格复制输入身份和顺序；不导出输入场、坐标或额外数组。恰好t=0的探针输出按初态空间重建。

## 接收限制与组合



对象数量及参数范围见上表，输入与输出场各至多2000000数值分量。除显式声明检查外，正式数据还须独立核验材料模型适用、连续问题适定、所请求观测存在、非负物理解及预算内参考精度；排除任意病态尺度和无限刚性组合。声明校验不证明物理／数值准确性。无正式样例时不从目录名、来源软件或文件顺序推导任何额外条件。
