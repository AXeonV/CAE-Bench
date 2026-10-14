# 来源与证据边界

维护材料。来源为[PINNacle固定提交6f8d69c9c84c41d19644e4ceebdc64c4a11d3adf](https://github.com/i207M/PINNacle/tree/6f8d69c9c84c41d19644e4ceebdc64c4a11d3adf)。[Poisson2D_Classic源码](https://github.com/i207M/PINNacle/blob/6f8d69c9c84c41d19644e4ceebdc64c4a11d3adf/src/pde/poisson.py)支持scale=1方形四圆Laplace外1内0。[参考数据](https://github.com/i207M/PINNacle/blob/6f8d69c9c84c41d19644e4ceebdc64c4a11d3adf/ref/poisson1_cg_data.dat)头声明COMSOL6.0.0.354、2023-05-26、二维1246节点、列x,y,u。author保存哈希与转换证据。MIT仓库许可不自动证明第三方数据许可，正式发布须复核。

固定模型和真实点值由源支持。转换只取源行，不生成网格、不插值、不重算参考。JSON参数族、独立点、固定输出轴和冻结程序多输入是OJ新增定义。观测子集可继承对应行数值，物理参数变化不能继承。

源场未有本仓库独立收敛/残差/连续误差证书；新增范围无完整参考。本阶段只来源对齐和结构，不求解、不参赛评测、不校准容差资源、不报告数值通过。后续须许可与独立数值资源验收才可正式发布。

COMSOL原始文件头明确Length unit:m及u(1)，坐标与势单位直接沿用来源。
