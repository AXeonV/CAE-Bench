# 17.7.1 热孔隙弹性联合演化

实现覆盖整个公开问题族的可复用求解器，冻结后处理多个未见算例。

均匀饱和小应变柱0≤x≤L，theta=T−T0，beta=E alpha；
sigma=E u_x−ab p−beta theta，sigma_x=0；
zeta=ab u_x+S p−gamma theta，zeta_t=m p_xx；
c theta_t+T0 beta u_xt+T0 gamma p_t=k theta_xx。
这是本题固定的线性互易三场模型，包含热致流体含量和压力／应变率热反馈，忽略对流及二阶耗散热。不能将温度只作为指定外场，或用独立热扩散替代第三式。

初态u=p=theta=0。0<ab≤1；gamma≥0；T0>0。接收条件T0 gamma²<S c，数据保证|theta|/T0≤0.01与|u_x|≤0.01。正定性仅为本线性模型接收条件，不声称通用热孔隙材料判据。

模型、初边值和参数解释已固定；考生负责数值离散、耦合算法与误差控制，语言／软件自由，解析或降阶方法覆盖完整契约同样有效。区间长度、材料系数、载荷时程和真实采样坐标随算例变化，不要求复现参考算法。输入输出见[本题DATA](DATA.md)及[通用CONTRACT](../../../../docs/CONTRACT.md)。

## 运行与资源

入口`python solve.py --input /path/problem.json --output /path/result.h5`。每例Linux AMD64、480秒墙钟（含启动与I/O）、2CPU、4096MB、0GPU、无网络；0退出并完整写出HDF5，无独立输出字节上限。生成求解器3600秒、构建1800秒；环境提前提供Python3、NumPy、SciPy、h5py、Gmsh、jsonschema及C++/OpenMP/OpenMPI/HDF5，不强制Python。采样点2..2048，瞬态载荷轴2..256节点、响应轴1..256节点；稳态／谐波1帧。输入场与输出场各至多2000000数值分量。内部网格、时间步和迭代不由采样点／输出时刻指定。

资源与容差为待正式数据校准的设计目标，不声称任意参数都已证明可在预算内求准。

## 评分

每有效例正常退出、结构合法且全部请求quantity的全部时间、位置、分量满足`|结果−参考|≤atol+rtol·|参考|`得1，否则0，等号接受。无去均值、归一化重排或固定偏置。

| quantity | atol | rtol | 单位 |
|---|---|---|---|
| `displacement` | 1e-09 | 0.003 | `m` |
| `pore_pressure` | 0.001 | 0.003 | `Pa` |
| `temperature_rise` | 1e-05 | 0.003 | `K` |

成绩为通过有效例数／有效例数，无有效例不产生成绩。输入、参考或配置错误属于基础设施错误，不计考生失败。工具校验和临时fixture测试不证明耦合物理、参考精度或预算校准。
