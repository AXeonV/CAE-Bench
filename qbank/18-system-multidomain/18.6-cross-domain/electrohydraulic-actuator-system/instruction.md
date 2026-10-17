# 18.6.2 电机泵与双腔液压执行系统

实现覆盖整个公开问题族的可复用求解器，冻结后处理多个未见算例。

每个systems对象为一套独立闭式电机泵—双腔液压缸—弹簧阻尼质量系统。变量i、omega、x、v、pA、pB；pA/B为相对共同参考绝对压力p0的表压。
L i_dot=U−R0 i−K omega；J omega_dot=K i−B omega−D(pA−pB)；
Q=D omega−Cl(pA−pB)，正流量从腔B泵往腔A；x_dot=v；M v_dot=A(pA−pB)−c v−k x−F；
VA=VA0+A x，VB=VB0−A x；pA_dot=Kf(Q−A v)/VA，pB_dot=Kf(−Q+A v)/VB。
D是泵每转角排量m3/rad，其SI数值使压差反力矩D(pA−pB)和流量D omega功率一致；Cl是A向B的内部泄漏导纳，Q已减去泄漏，不能再次从腔方程扣漏流。
固定初态i=omega=x=v=pA=pB=0。U有符号端电压，F为沿−x方向的有符号外部阻力；无行程止挡或速度重置。

正式数据保证全程VA>0、VB>0、p0+pA>0、p0+pB>0，且无空化／止挡和常物性失效；声明检查只核验初始参数正性，不证明轨迹限制。

模型和元件关系固定，考生负责按身份组装、求解、内部时间步及误差控制；语言与软件自由，解析／降阶方法覆盖全部公开契约同样有效，不要求某种参考算法。元件参数及外源时程由算例改变。输入输出只依赖[本题DATA](DATA.md)和[通用CONTRACT](../../../../docs/CONTRACT.md)。

## 运行与资源

入口`python solve.py --input /path/problem.json --output /path/result.h5`。每例Linux AMD64、480秒墙钟（含启动和I/O）、2CPU、4096MB、0GPU、无网络；正常0退出并完整写HDF5，无独立输出字节上限。生成求解器3600秒、构建1800秒。提前提供Python3、NumPy、SciPy、h5py、Gmsh、jsonschema及C++/OpenMP/OpenMPI/HDF5，不强制Python或Modelica。

规模：systems 1..32，load 2..256时间采样点，response 1..256时间采样点，static 1帧；输入场／输出场各至多2000000数值分量。资源与容差是待校准设计目标，正式数据必须独立核验精度、模型适用性与预算可达性，不能由结构合法参数推得全范围已验证。

## 评分

每有效例正常退出、结构合法，且全部请求quantity在所有时刻／对象／分量满足`|结果−参考|≤atol+rtol·|参考|`得1分，否则0；等号接受。无去均值、按方向取绝对值、偏置拟合或超限豁免。

| quantity | atol | rtol | unit |
|---|---|---|---|
| `current` | 1e-08 | 0.003 | `A` |
| `angular_velocity` | 1e-07 | 0.003 | `rad/s` |
| `displacement` | 1e-08 | 0.003 | `m` |
| `velocity` | 1e-07 | 0.003 | `m/s` |
| `chamber_pressure` | 0.01 | 0.003 | `Pa` |

成绩为通过有效例数／有效例数；输入、参考或配置错误归基础设施错误，不计考生失分，无有效例不产生成绩。仅声明检查与临时工具测试不证明物理或数值正确。
