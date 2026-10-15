# 2.10 公共数据说明

遵循[通用数据协议](../../../docs/CONTRACT.md)及[流体模型协议](../../../docs/FLUID-REDUCED.md)。输入problem.json引用一个真实MSH 4.1 ASCII网格及一个扁平HDF5；输出一个HDF5，IDs和时间轴精确复制。数组统一[T,N,*component_shape]，编号为身份而非行号。

本节model显式选择，既有通用physics.parameters与conditions装载所有物理信息，不添加未定义profile或隐藏JSON字典。不兼用cfd四键。参数集合、域条件、边界变量/算子/全部data键、常数与场表示、正值及组合限制逐model在规范列全。

域条件location=domain，节点覆盖全部域节点，输入分片线性；边界为真实外边界面，输入分片常量面平均，完整无重叠分区。每个输入字段都经条件解释。稳态仅[0]；瞬态显式起止、必需初态、输出时间与内部步长分开；输入时间插值linear或明确单帧constant，禁止外推。温度K，压力Pa，所有其他quantity单位、向外法向和积分定义见规范。

输出物理状态为网格节点点值，壁面交换为真实边界平均；整体观测只能用真实域单元aggregate，禁止假探针。具体必需与可选quantity由题目DATA和模型规范确定。输出校验只检查契约，数值比较见[共同要求](COMMON.md)。

本轮不提供可运行题库样例、参考或隐藏输入；protocol最小fixture在临时目录由tests/test_fluid_reduced.py生成，仅验证工具接口。不得把合法结构当作物理或数值验证。
