# 当前几何切向边界数据

通用结构见 [CONTRACT](../../../../docs/CONTRACT.md)。每例包含 `problem.json` 和 `input.h5`。`task=deformed-tangential-boundary-repair`、`physics.model` 为下述三个字符串之一；`spatial_dimension` 为实际空间维数D，取2或3。几何由以下参数及真实库构造，不提供外部网格，`geometries={}`、`meshes={}`、`conditions=[]`、`fields={}`。

`locations.probes={"kind":"points","ids":"probe_ids","coordinates":"probe_coordinates"}`。`probe_ids` 为严格递增的非负int64[N]，1≤N≤128。`probe_coordinates` 为float64[N,D]，单位m、分量按x/y/z，表示全时域不移动的Eulerian物理位置。每点严格位于所有要求时刻域内；到边界的距离不小于最小几何长度的1e-4。不跟随网格移动，不存在参考坐标／当前位置替换或作者数值插值。

`time_axes.frames=times`；`times` 为float64[T]，单位s。盒工况为 `[0,dt,2dt,…,end_time]`，`end_time/dt` 为1至8的整数，T≤9；静态圆环为 `[0]`。t=0是矩形初始域中已经求解的Stokes状态。之后每步先推进规定网格运动，再在该时刻当前域求解。可信运行器使用ASPECT原生 `point values` 后处理器，以Cartesian `Evaluation points`、`Use natural coordinates=false` 在上述固定点取值；原生输出直接对应要求时轴，不做重采样。

所有参数写作 `physics.parameters.<名称>={"value":数值,"unit":"…"}`，只允许本族下列键。通用参数为：

|名称|单位|含义及范围|
|---|---|---|
|density|kg/m^3|常密度，0.1至10|
|viscosity|Pa*s|动力黏度，0.1至10|
|temperature|K|全域及全部边界固定温度，200至1000；不影响本题常黏度Stokes系数|
|refinement|1|整数全局细化层数；二维盒1至6、三维盒1至2、圆环1至4|
|time_step|s|dt，0.05至1|
|end_time|s|盒为0.1至2，且满足上述整数步数；圆环为0|

所有域中的材料速度与压力满足 `div(u)=0`、`−grad(p)+div(2μ ε(u))=0`，其中 `ε(u)=(grad(u)+grad(u)^T)/2`。规定速度边界给出完整全局Cartesian速度。在切向边界，材料速度零法向分量、切向黏性牵引为零。压力以当前“top”面的平均值为零；二维按边长平均，三维按面积平均。边角使用相邻条件共同给出的相容速度。所有速度输入／输出均为m/s，时间均为s。

## deformed-tangential-parallel-v1：平行平面边界

另有 `width`、`height`（m，分别0.2至2、0.5至1.2）、`rate_x`（1/s，−2至2）、`velocity_x`（m/s，−1至1）。D=3还必须有 `depth`（m，0.2至1）、`rate_y`（1/s，−2至2）、`velocity_y`（m/s，−1至1）；D=2禁止这些三维键。

初始二维域为 `[0,width]×[0,height]`；三维为 `[0,width]×[0,depth]×[0,height]`，最后坐标为竖直方向。上下边界分别为当前平面 `z=t(rate_x*x+rate_y*y)` 与 `z=height+t(rate_x*x+rate_y*y)`；二维删去y项并用y为竖直坐标。上下边界材料速度切向；侧边给定 `(velocity_x,velocity_y,t(rate_x*velocity_x+rate_y*velocity_y))`，二维相应为 `(velocity_x,t*rate_x*velocity_x)`。

上下边界的规定网格速度为 `(0,0,rate_x*x+rate_y*y)`，二维为 `(0,rate_x*x)`，以当前Cartesian位置求值。侧边网格仅允许沿侧面移动，其内部平滑由固定ASPECT实现完成；不要求网格内部仿射。参数满足 `end_time*(abs(rate_x)*width+abs(rate_y)*depth)≤0.8*height`（二维删去y项），且实际网格不反转。该条件不把材料网格等同起来。

## deformed-tangential-wedge-v1：仅上壁变形及非均匀底壁驱动

仅D=2。另有 `width`（m，0.5至2）、`height`（m，0.4至1）、`rate_x`（1/s，−0.2至0.2）、`peak_velocity`（m/s，−1至1）。初始域为矩形。下壁及其网格固定在y=0，材料速度为 `(peak_velocity*(1−(2*x/width−1)^2),0)`。顶壁为 `y=height+t*rate_x*(x−width/2)`，材料速度切向，规定网格速度为 `(0,rate_x*(x−width/2))`。左右壁材料速度切向；侧壁网格仅允许竖直移动。输入保证 `end_time*abs(rate_x)*width/2≤0.3*height`，无单元反转。底壁抛物线在两端为零，满足侧壁条件。

## deformed-tangential-annulus-v1：静态圆环

仅D=2。另有 `inner_radius`、`outer_radius`（m，0.5至2.5，且0.5≤外半径−内半径≤1.5）、`angular_speed`（1/s，−1至1）。域为 `inner_radius<sqrt(x²+y²)<outer_radius`。网格固定；内圆给定材料速度 `(-angular_speed*y,angular_speed*x)`，外圆材料速度切向。没有盒尺寸、坡率或盒驱动键。

## 输出

两项均为float64、`location=probes`、`time_axis=frames`、`value_kind=point`；每行按输入probe_ids身份、每帧按times顺序。输出支持数组按CONTRACT复制。

|输出|quantity／单位|kind／分量|shape|意义|
|---|---|---|---|---|
|velocity|velocity／m/s|vector，component_shape=[D]，components按x/y/z|[T,N,D]|在输入固定Cartesian点、要求时刻的材料速度|
|pressure|pressure／Pa|scalar，component_shape=[1]，components=["value"]|[T,N,1]|同一位置时刻、采用上述平均压力规范的压力|

可信运行器直接读取ASPECT原生PointValues输出。该文本使用六位有效数字，数组值保留其原生精度；不能将其解释为额外物理误差修正。无需提交结果程序或自行选择采样插值算法。
