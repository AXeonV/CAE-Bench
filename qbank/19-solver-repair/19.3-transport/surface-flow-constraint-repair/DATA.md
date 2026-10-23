# 表面反应管流物种约束数据

通用结构见 [CONTRACT](../../../../docs/CONTRACT.md)。每例是 `problem.json` 与 `input.h5`；`task=surface-flow-constraint-repair`、`physics={"model":"catalytic-flow-state-v1","parameters":{}}`、`spatial_dimension=1`。`geometries`、`meshes`为空对象，`conditions=[]`。每一行独立建立一条稳态管流轨迹并观测一个指定轴向距离，不与其他行连续积分；无物理时间推进。

`locations.states={"kind":"entities","ids":"state_ids"}`；`state_ids`为长度N、互异int64标签，1≤N≤32。`time_axes.instant=times`，`times`为float64 `[0.0]`，仅代表瞬时观测标签。各字段 `location=states,time_axis=instant,value_kind=point`。标量shape=[1,N,1]，`kind=scalar,component_shape=[1],components=["value"]`；向量shape=[1,N,C]，`kind=components,component_shape=[C]`，分量顺序见表。数据集键与字段名相同。输入另带 `sampling={"space":"uniform","time":"constant","extrapolation":"forbid"}`。除两个选择字段species_order和coverage_mode（若本题有）为int64外，其余为float64。

|输入字段|quantity|单位|分量|定义与范围|
|---|---|---|---|---|
|species_order|species_order|1|value|0..5，机制气相排序分别为ABI、AIB、BAI、BIA、IAB、IBA|
|temperature|temperature|K|value|500..1500，全部管流及表面恒定温度T|
|pressure|pressure|Pa|value|1e4..1e6，入口绝对压力P|
|inlet_speed|speed|m/s|value|0.01..1，入口流速u|
|surface_area_to_volume|area_volume_ratio|1/m|value|10..10000，单位管流体积的催化表面积a|
|site_density|surface_site_density|kmol/m^2|value|1e-9..1e-6，表面位点摩尔面密度n0|
|adsorption_rate|adsorption_rate_constant|m^3/(kmol*s)|value|0..1e8，吸附速率常数ka|
|desorption_rate|rate_constant|1/s|value|100..1e6，解吸常数kd|
|conversion_rate|rate_constant|1/s|value|0..1e6，转化常数kc|
|distance|distance|m|value|0..2，从入口沿流向的观测距离z|
|inlet_mole_fractions|mole_fraction|1|A,B,I|各非负，和1（绝对误差≤1e-12），I≥0.05；按名字输入，不随species_order重排|

固定几何截面积为1e-4 m²，质量流率由入口实际密度、入口速度及截面积设置。A、B、I均由一个O原子构成、摩尔质量15.999 kg/kmol；S含一个Pt，AS含1个Pt与一个O，Pt摩尔质量195.084 kg/kmol。所有物种采用公开机制的常数热容，反应速率常数不依赖温度，T影响气体浓度。通用气体常数8314.46261815324 J/(kmol K)。气相无均相反应，表面只有以下三个不可逆反应：

1. `A + S => AS`，进度率q1=ka*C_A*C_S^1。
2. `AS => A + S`，q2=kd*C_AS。
3. `AS => B + S`，q3=kc*C_AS。

C_A为气相真实摩尔浓度(kmol/m³)，C_S、C_AS为表面真实摩尔浓度(kmol/m²)，q均为kmol/(m²s)。位点覆盖θ_k表示该物种所占位点数占总位点数；物种占位数s_S=1、s_AS=1，归一化表面满足θ_S+θ_AS=1。表面真实摩尔浓度定义为C_k=n0*θ_k/s_k；气相总摩尔浓度为P/(R*T)，各物种浓度为其摩尔分数乘总摩尔浓度。表面质量面密度是各物种摩尔浓度与其摩尔质量的乘积之和。管流表面准稳态条件为q1=q2+q3；气相净物种面源分别为(-q1+q2,q3,0)，全部动力学使用真实浓度。覆盖率、摩尔分数、质量分数含义不得混用。

可信驱动按species_order构造真实Cantera相，以名字设置入口组分；设置T/P、n0及三反应的常数倍率，使用真实FlowReactor和ReactorNet沿z积分，能量关闭。入口表面先由真实覆盖积分到稳态，管流内覆盖为代数准稳态，入口覆盖猜值不定义额外物理自由度。固定入口表面求稳态相对容差1e-7、绝对容差1e-12，管流IDA相对1e-9、绝对1e-12，最多20000步。单占位题的覆盖初猜S/AS各0.5；多占位题如下定义直接观测及其后初猜。

|输出字段|quantity|单位|分量|含义|
|---|---|---|---|---|
|mass_fractions|mass_fraction|1|A,B,I|观测位置的气相质量分数，固定按名字顺序|
|coverages|site_coverage|1|S,AS|最终准稳态位点覆盖|
|pressure|pressure|Pa|value|最终绝对压力|
|density|density|kg/m^3|value|最终气相质量体密度|
|speed|speed|m/s|value|最终气相流速|

全部输出的time_axis/location身份与输入相同，由可信运行器用SDK write_result写result.h5，考生只替换规定源码。输入均有限且合法，不要求处理范围外输入。零吸附、零转化、入口已有产物、惰性组分及任意六种气相排序均属支持范围。等摩尔质量及零净气相质量源是本题固定事实，不扩张到不同物种摩尔质量、气相沉积或可变温度问题。
