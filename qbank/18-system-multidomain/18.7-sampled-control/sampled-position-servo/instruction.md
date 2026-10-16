# 18.7.1 饱和与抗积分饱和的采样位置伺服

实现覆盖整个公开问题族的可复用求解器，冻结后处理多个未见算例。

每个systems对象为独立数字位置伺服。连续对象：theta_dot=omega，L i_dot=U−R0 i−K omega，J omega_dot=K i−B omega−tau。固定初态theta=omega=i=0。
数字控制时钟给定0=t0<t1<…<tN=t_end，所有系统共享时钟；每系统积分状态z0=0。在tk用连续状态theta(tk)和该节点参考r_k计算e_k=r_k−theta(tk)，w_k=Kp e_k+Ki z_k，U_k=min(Umax,max(−Umax,w_k))。
在[tk,t{k+1})严格保持U=U_k；若|w_k|≤Umax或w_k e_k<0，则z{k+1}=z_k+(t{k+1}−tk)e_k，否则z{k+1}=z_k。该递推只在时钟上执行，不能用连续PI或改成先更新积分再算U。
最后时刻tN仍用theta(tN)、r_N、z_N计算U_N并作为端点输出，不再更新z。等号按未饱和分支；U输出在时钟点取新值，右连续；连续状态跨时钟不重置。tau是沿正转方向的有符号外部阻力矩。

K、R0均固定，不含温度模型。control时钟与响应时刻独立，控制器不得在响应时刻额外更新。反向参考、饱和进入／退出和非均匀时钟均属于公开范围。

模型和元件关系固定，考生负责按身份组装、求解、内部时间步及误差控制；语言与软件自由，解析／降阶方法覆盖全部公开契约同样有效，不要求某种参考算法。元件参数、外源及参考时程由算例改变。输入输出只依赖[本题DATA](DATA.md)和[通用CONTRACT](../../../../docs/CONTRACT.md)。

## 运行与资源

入口`python solve.py --input /path/problem.json --output /path/result.h5`。每例Linux AMD64、300秒墙钟（含启动和I/O）、2CPU、4096MB、0GPU、无网络；正常0退出并完整写HDF5，无独立输出字节上限。生成求解器3600秒、构建1800秒。提前提供Python3、NumPy、SciPy、h5py、Gmsh、jsonschema及C++/OpenMP/OpenMPI/HDF5，不强制Python或Modelica。

规模：systems 1..32，load 2..256节点，response 1..256节点，static 1帧; control 2..256节点；输入场／输出场各至多2000000数值分量。资源与容差是待校准设计目标，正式数据必须独立核验精度、模型适用性与预算可达性，不能由结构合法参数推得全范围已验证。

## 评分

每有效例正常退出、结构合法，且全部请求quantity在所有时刻／对象／分量满足`|结果−参考|≤atol+rtol·|参考|`得1分，否则0；等号接受。无去均值、角度折返、按方向取绝对值、偏置拟合或超限豁免。

| quantity | atol | rtol | unit |
|---|---|---|---|
| `angle` | 1e-07 | 0.002 | `rad` |
| `angular_velocity` | 1e-07 | 0.002 | `rad/s` |
| `current` | 1e-08 | 0.002 | `A` |
| `control_voltage` | 1e-06 | 0.002 | `V` |

成绩为通过有效例数／有效例数；输入、参考或配置错误归基础设施错误，不计考生失分，无有效例不产生成绩。仅声明检查与临时工具测试不证明物理或数值正确。
