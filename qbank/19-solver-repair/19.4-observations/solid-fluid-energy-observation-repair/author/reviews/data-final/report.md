# MOOSE 22074 全量数据终审

结论：通过。审阅对象为 `qbank/19-solver-repair/19.4-observations/solid-fluid-energy-observation-repair`，以本次最终 instruction.md、DATA.md、docs/CONTRACT.md 为唯一语义依据；未修改题目、作者生产实现、池或公开材料。审阅依 caeoj-data-review、caeoj-configure-judge 执行。没有付费模型、原生重新求解或大型构建。

## 覆盖与可复核证据

`audit.py`、`data-math.json` 保存全部 12 cases、全部参数、输入 HDF5 每一数组的 dtype/shape/完整数值、全部五输出每一时刻的独立参考及误差。另完整加载两公开 samples 的输入、输出和参考评分。最终执行使用已经普通安装的固定 `caeoj-moose22074-verifier:v1`，UID/GID 1000，仓库只读、仅本审阅输出目录可写，网络禁用；运行时 descriptor 也保存在 JSON。裸开发 core 的 generic-structure 不被当作题内声明验证，最终所有输入及35变体均在完整题内绑定下复核。

|公开定义|全量核查|
|---|---|
|声明、身份与时间|task/维度/10种 model；空 geometries、meshes、conditions；experiment_ids=int64[1]=[1]；initial_time=float64[1]=[0]；frames 的 times 与输出精确复制|
|全部标量参数|23个参数的键集合、精确单位、有限性、整数类型、范围、固定控制量和Re≤10交叉约束由已绑定题内检查全部消费；逐例全值保留于data-math.json|
|两组输入系数|float64[1,1,10]、float64[1,1,12]；components顺序、initial轴、uniform/constant/forbid、K和m/s；RZ禁用分量为零，耦合两数组全零|
|模型分支|8显式完整笛卡尔/RZ×普通/AD×标准/重命名；4耦合覆盖稳态/瞬态×速度Q1/Q2；温度/压力Q1及QUAD9几何与场阶次分别核查|
|全部输出|五个float64[nt,1,1]、experiments/frames、scalar/[value]、J/J/W/W/W；恰含五输出加experiment_ids/times共7数组，无initial_time或输入系数混入|
|实际时刻|8显式+2稳态各1帧；瞬态Q1共4帧、Q2共5帧，包括t=0，按整数序号乘dt；均逐帧核查|

公开单项式、坐标与积分定义足以重建显式答案；本审阅采用单项式代数求导、乘法和精确反导数，未调用作者 `independent.py`、生产driver或目标C++。Cartesian体积雅可比与RZ完整2πr权重分别处理，温度能量不减Tref，仅流体计算Qadv，显式Robin=0。

4个耦合例读取真实原生 PointValueSampler 的全部单元内部点CSV。按实际物理坐标构造最小二乘矩阵，温度强制Q1，速度按输入强制Q1/Q2，独立检验所有9点残差后，以4×4 Gauss体积规则重建Es/Ef/Qadv/Qsrc；外壁3点强制Q1重建并解析积分Robin。没有把QUAD9几何节点当成低阶变量DOF，没有使用旧NodalValueSampler重复值。全部点位置最大偏差6.67e−16，指定阶次场最大拟合误差6.95e−14。两相积分、源时依赖、初态及每步Euler储能全部独立计算。

|量|12例全部时刻最大绝对误差|
|---|---:|
|Es|9.32e−10 J|
|Ef|7.46e−8 J|
|Qadv|1.17e−8 W|
|Qsrc|6.11e−16 W|
|Qrobin|6.20e−14 W|

全部误差远低于公开 `1e−5 + 1e−9*abs(reference)` 判据。独立整体能量账最大残差2.71e−8 W；没有强制归零、裁剪小负Robin或用边界焓流替换体积分。这里证明给定真实求解场上的观测积分正确，并非独立重新求解整条NS/热方程轨迹。

## 独立变体

`variants.py`、`variants.json` 共35项：2合法边界组合；16非法输入，包含奇数nx、浮点整数、单位变化、漏/多参数、sampling缺失、RZ禁用温度/旋流、耦合非零系数、Re超限、零源、稳态非零dt、瞬态漏初态/近似时刻、initial_time错误和NaN；6非法结果，包含支持量缺失/多余、错误ID、NaN、float32和展平；五项分别在阈值0.999与1.001倍的10项数值变体；零参考Robin在精确atol等号1项。全部符合预期，等号通过，外侧失败。

12个实际grading均通过全部五项全部时刻且无额外判据；2样例均score1。完整输出错误始终先由契约拒绝。逐例评分是五项全通过才得1分，正式12例含公开样例等权，详见同批后端终审。

## 数据绑定及来源

`../..` 下同批后端审阅的 `artifacts.py/artifacts.json` 独立检查HF revision `cadbdde490008f7709698216c5980c17bc6bdca9` 的实际assembly receipt 58文件全部SHA/尺寸一致、strict valid，两公开样例仍绑定01与09。12个原始参考CSV全部五列逐值精确等于正式HDF5，原生raw归档210文件与backend raw49文件逐SHA完整。原基线12例是缺注册类型而不能执行该新观测能力；不是原有方程的数值错误。已有能力另有真实健康运行证据。

完整基线源码、上游PR两新增文件、运行镜像、公开ZIP与正式Oracle闭环见 `runs/configure-judge/repair22-moose22074/report.md`。未发现阻断问题；没有未加载输入、未核对输出或待定数值参考。
