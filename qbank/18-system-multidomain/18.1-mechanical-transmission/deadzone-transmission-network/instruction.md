# 18.1.2 含弹性死区的传动网络

实现覆盖整个公开问题族的可复用求解器，冻结后处理多个未见算例。

每节点为相对惯性参考系的一自由度转子，角度theta、角速度omega，J_i omega_dot=F_i−d_i omega_i+支路力矩之和，theta_dot=omega。
每有向支路a→b具有指定有符号变比n，delta=theta_a−n theta_b，delta_dot=omega_a−n omega_b；t=k sign(delta) max(|delta|−g,0)+c delta_dot，其中sign(0)=0。弹性项在|delta|≤g恰为0，黏性项全程存在，含死区内。
支路作用于a的力矩为−t，作用于b为+n t，输出t是尾端传向该支路的力矩。变比为无惯性的功率变换定义，不能按普通等大反向力矩连接。所有转子惯量为正；无固定角度、额外地约束、刚性齿轮约束或碰撞冲量。初态来自给定theta0、omega0，不是静态预平衡。

角度不按2pi折返或重新对齐。死区题的折点按连续力ODE处理，不引入冲量、速度重置或接触历史。

模型和元件关系固定，考生负责按身份组装、求解、内部时间步及误差控制；语言与软件自由，解析／降阶方法覆盖全部公开契约同样有效，不要求某种参考算法。连通拓扑、并联支路、有向编号、元件参数、初态及外源时程由算例改变。输入输出只依赖[本题DATA](DATA.md)和[通用CONTRACT](../../../../docs/CONTRACT.md)。

## 运行与资源

入口`python solve.py --input /path/problem.json --output /path/result.h5`。每例Linux AMD64、300秒墙钟（含启动和I/O）、2CPU、4096MB、0GPU、无网络；正常0退出并完整写HDF5，无独立输出字节上限。生成求解器3600秒、构建1800秒。提前提供Python3、NumPy、SciPy、h5py、Gmsh、jsonschema及C++/OpenMP/OpenMPI/HDF5，不强制Python或Modelica。

规模：nodes 2..128、edges 1..256，load 2..256时间采样点，response 1..256时间采样点，static 1帧；输入场／输出场各至多2000000数值分量。资源与容差是待校准设计目标，正式数据必须独立核验精度、模型适用性与预算可达性，不能由结构合法参数推得全范围已验证。

## 评分

每有效例正常退出、结构合法，且全部请求quantity在所有时刻／对象／分量满足`|结果−参考|≤atol+rtol·|参考|`得1分，否则0；等号接受。无去均值、角度折返、按方向取绝对值、偏置拟合或超限豁免。

| quantity | atol | rtol | unit |
|---|---|---|---|
| `angle` | 1e-07 | 0.002 | `rad` |
| `angular_velocity` | 1e-07 | 0.002 | `rad/s` |
| `transmitted_torque` | 1e-06 | 0.002 | `N.m` |

成绩为通过有效例数／有效例数；输入、参考或配置错误归基础设施错误，不计考生失分，无有效例不产生成绩。仅声明检查与临时工具测试不证明物理或数值正确。
