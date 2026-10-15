# 7.4.1 面外单频涡流

实现覆盖整个公开问题族的可复用求解器，冻结后处理多个未见算例。二维xy、z平移不变，e^(+iωt)相量，只求Az。B=(∂yAz,−∂xAz)，−div(ν∇Az)+iωσAz=Js，Jind,z=−iωσAz。明确固定纵向标势梯度为0，E_z=−iωAz；Js是独立给定的面外外加电流，不包含Jind。ν>0、σ≥0逐三角形常数，内部Az和ν∂nAz连续；Dirichlet固定绝对Az，其余ν∂nAz=0，至少一条Dirichlet。忽略位移电流、运动和磁滞；不能解释为任意三维导体电极连接模型。二维面积／边界积分按单位z长度解释；没有隐含厚度。

几何、材料、源及观测由算例变化。考生负责相容实现、内部离散／积分、线性代数与误差控制，语言和软件自由；覆盖整个契约的解析或降阶方法同样有效，不要求复制参考程序。仅需[本题DATA](DATA.md)及[通用CONTRACT](../../../../docs/CONTRACT.md)确定输入输出。

## 运行与资源

至多5000三角形、6000节点。唯一时间轴含1帧，输入／输出场各至多4000000分量。规模、预算及容差为待校准设计目标，正式数据须独立证明可达精度。

入口`python solve.py --input /path/problem.json --output /path/result.h5`。每例Linux AMD64、900秒墙钟（含启动和I/O）、4CPU、8192MB、0GPU，逐例无网络；程序0退出并完成HDF5写入，无独立字节上限。生成求解器3600秒、构建1800秒；提前提供Python3、NumPy、SciPy、h5py、Gmsh、jsonschema、C++/OpenMP/OpenMPI/HDF5，不强制Python。

## 评分

每有效例正常退出、结构合法且全部quantity的所有时刻／实体／分量满足`|结果−参考|≤atol(quantity)+rtol(quantity)|参考|`得1分，否则0分，等号接受。复量实虚分别比较，不调整全局相位、不用幅值或RMS替代。无去均值、拟合或超限豁免。

| quantity | atol | rtol | 单位 |
|---|---|---|---|
| `vector_potential` | 1e-09 | 0.005 | `Wb/m` |
| `magnetic_flux_density` | 1e-08 | 0.005 | `T` |
| `induced_current` | 1e-07 | 0.005 | `A/m2` |

成绩为通过有效例数／有效例数；输入、配置或参考错误为基础设施错误，不计考生失败；无有效例不产生成绩。结构和有限值遵守CONTRACT；容差与资源须正式评测前校准，工具测试不构成物理精度证据。
