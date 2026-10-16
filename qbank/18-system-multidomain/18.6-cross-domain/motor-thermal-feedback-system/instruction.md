# 18.6.1 电机旋转热反馈系统

实现覆盖整个公开问题族的可复用求解器，冻结后处理多个未见算例。

每个systems对象是一套独立集总电机—惯性—热系统。反电动势K omega和电磁力矩K i使用同一正SI耦合常数K，保证功率转换一致。
R(T)=R0[1+a(T−Tref)]；L i_dot=U−R(T)i−K omega；J omega_dot=K i−B omega−tau；
Cth T_dot=R(T)i²+B omega²−H(T−Ta)。tau沿正转方向的阻力矩为正，可有符号。Ta是给定外界绝对温度，T为线圈与黏性耗散统一热节点的绝对温度，所有B omega²均进入该热节点；负载做功tau omega不进入该节点。
固定初态i=omega=0、T=Tref。不同systems之间无未声明耦合。

正式数据保证全程T>0、R(T)>0及固定电机／集总热模型适用。不考虑磁饱和、铁损或分布温度场。

模型和元件关系固定，考生负责按身份组装、求解、内部时间步及误差控制；语言与软件自由，解析／降阶方法覆盖全部公开契约同样有效，不要求某种参考算法。元件参数及外源时程由算例改变。输入输出只依赖[本题DATA](DATA.md)和[通用CONTRACT](../../../../docs/CONTRACT.md)。

## 运行与资源

入口`python solve.py --input /path/problem.json --output /path/result.h5`。每例Linux AMD64、240秒墙钟（含启动和I/O）、2CPU、4096MB、0GPU、无网络；正常0退出并完整写HDF5，无独立输出字节上限。生成求解器3600秒、构建1800秒。提前提供Python3、NumPy、SciPy、h5py、Gmsh、jsonschema及C++/OpenMP/OpenMPI/HDF5，不强制Python或Modelica。

规模：systems 1..32，load 2..256节点，response 1..256节点，static 1帧；输入场／输出场各至多2000000数值分量。资源与容差是待校准设计目标，正式数据必须独立核验精度、模型适用性与预算可达性，不能由结构合法参数推得全范围已验证。

## 评分

每有效例正常退出、结构合法，且全部请求quantity在所有时刻／对象／分量满足`|结果−参考|≤atol+rtol·|参考|`得1分，否则0；等号接受。无去均值、角度折返、按方向取绝对值、偏置拟合或超限豁免。

| quantity | atol | rtol | unit |
|---|---|---|---|
| `current` | 1e-08 | 0.002 | `A` |
| `angular_velocity` | 1e-07 | 0.002 | `rad/s` |
| `temperature` | 1e-05 | 0.002 | `K` |

成绩为通过有效例数／有效例数；输入、参考或配置错误归基础设施错误，不计考生失分，无有效例不产生成绩。仅声明检查与临时工具测试不证明物理或数值正确。
