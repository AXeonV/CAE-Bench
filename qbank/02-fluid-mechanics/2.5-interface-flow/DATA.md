# 2.5 公共数据说明

必须读取 [多相配置完整规范](../../../docs/FLUID-MULTIPHASE.md)、[通用输入输出契约](../../../docs/CONTRACT.md) 和 [共同要求](COMMON.md)。本节复用physics.model/parameters、fields、conditions和outputs，不使用cfd-2.1的四键声明。每题DATA只列本题选择，不能省略规范中必需参数。

唯一固定域location恰覆盖全部D维体单元，初态和显式acceleration共用它；边界location恰好分割全部外边界，不重叠。标量数值为带单位常数或场引用，向量只用场；场为float64实体average，标量[T,N,1]，向量[T,N,D]，不可广播或展平。输入数据采样须显式说明uniform/piecewise_constant、constant/linear及forbid，初态单帧恰为time_start，线性驱动覆盖整个时间区间。输出统一一轴，末时刻time_end。

全部压力为绝对静压，重力通过显式acceleration输入。alpha始终表示a相；各题a/b的物理对象不同，应按逐题及规范解释。分散题使用表观通量flux_a/flux_b，不能将其当作相内平均速度。所有输出物理定义、单位、允许集合、初态/边界完整参数表由上述规范拥有，不从题号或来源文件推断。

输出按outputs.array写HDF5 dataset，同时复制所需IDs和时间支持数组，禁止额外数组或属性。可以通过caeoj.sdk.load_problem/write_result完成结构读写，物理模型和数值求解由程序承担。辅助函数multiphase_parameters/multiphase_phase_mass见协议SDK节；通用校验成功不是物理验证。

examples、references、cases仅保留目录。此阶段没有正式输入、公开样例或参考答案；协议验证的临时fixture不作为题库数据或评测发布。
