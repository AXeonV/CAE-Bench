# 7.1.1 介质静电场

实现覆盖整个公开问题族的可复用求解器，冻结后处理多个未见算例。二维xy平面、z平移不变，材料逐三角形常数，各向同性线性。E=−∇V。D=εE，div D=ρf。内部界面V连续、D法向连续，无额外界面自由电荷。外法向n指向计算域外；Dirichlet固定V，normal_flux给D·n；其余外边界D·n=0。至少一条Dirichlet锚定绝对电势。二维面积／边界积分按单位z长度解释；没有隐含厚度。

几何、材料、源及观测由算例变化。考生负责相容实现、内部离散／积分、线性代数与误差控制，语言和软件自由；覆盖整个契约的解析或降阶方法同样有效，不要求复制参考程序。仅需[本题DATA](DATA.md)及[通用CONTRACT](../../../../docs/CONTRACT.md)确定输入输出。

## 运行与资源

至多5000三角形、6000节点。唯一时间轴含1帧，输入／输出场各至多4000000分量。规模、预算及容差为待校准设计目标，正式数据须独立证明可达精度。

入口`python solve.py --input /path/problem.json --output /path/result.h5`。每例Linux AMD64、600秒墙钟（含启动和I/O）、4CPU、8192MB、0GPU，逐例无网络；程序0退出并完成HDF5写入，无独立字节上限。生成求解器3600秒、构建1800秒；提前提供Python3、NumPy、SciPy、h5py、Gmsh、jsonschema、C++/OpenMP/OpenMPI/HDF5，不强制Python。

## 评分

每有效例正常退出、结构合法且全部quantity的所有时刻／实体／分量满足`|结果−参考|≤atol(quantity)+rtol(quantity)|参考|`得1分，否则0分，等号接受。无去均值、拟合或超限豁免。

| quantity | atol | rtol | 单位 |
|---|---|---|---|
| `potential` | 1e-06 | 0.005 | `V` |
| `electric_field` | 1e-07 | 0.005 | `V/m` |
| `electric_displacement` | 1e-10 | 0.005 | `C/m2` |

成绩为通过有效例数／有效例数；输入、配置或参考错误为基础设施错误，不计考生失败；无有效例不产生成绩。结构和有限值遵守CONTRACT；容差与资源须正式评测前校准，工具测试不构成物理精度证据。
