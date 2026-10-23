# 复波数 Helmholtz 快速算子修复

有衰减的三维 Helmholtz 计算在使用复波数时，快速求和接口及边界算子会报错或给出不一致的结果。请修复所附真实 Bempp 源码，使点相互作用、目标梯度、曲面边界算子及外部势在 [DATA.md](DATA.md) 声明的问题族内一致工作，并保留正实波数行为。遵循 [CONTRACT](../../../../docs/CONTRACT.md)。

提交目录恰含 `exafmm.py`、`fmm_assembler.py`、`helpers.py` 三个普通文件，每个不超过1 MiB（1,048,576字节），不允许子目录、符号链接或额外文件。三文件完整替换原库 `bempp/api/fmm/` 下同名文件，其余源码、原生 ExaFMM、驱动和构建工具固定。可重构允许文件中的实现，但须保留真实接口和快速路径，不得用全局稠密求和替换FMM。局部相互作用接口本身按其定义处理给定点对。

可信驱动固定使用真实 ExaFMM、`dense_evaluation=False`、Numba近场扣除及库自身的P1强形式接口。驱动只读取输入、映射身份、调用库和写回结果；它不生成解析答案或纠正库输出。边界输出是固定离散算子的P1投影系数，不是弱积分行，也不承诺连续超奇异场的经典逐点值。

所有声明输出的实部、虚部和梯度分量分别逐项比较，允许误差为 `|a-reference| <= 1e-7 + 2e-6*|reference|`。每例全部输出通过才通过，得分为通过例数比例。缺失、非有限或契约错误的输出不能通过。只修复点接口、只给正确势而不给梯度，或留下近场与远场不一致均不满足要求。

环境提供4 CPU、4 GiB内存，无外网；源码字节编译限60秒，每例执行限600秒、评分限30秒。判题先检查原始源码可字节编译和运行环境可用，再强制删除三文件的字节码，以提交件重新编译并实际导入运行。原件和环境故障属于基础设施错误；非法提交、候选编译失败、运行失败和数值错误分别处理。

`public/bempp-source.tar.gz` 与 `public/exafmm-source.tar.gz` 保存完整原始来源和许可证；`public/driver.py`、`CMakeLists.txt`、`run_case.py` 是固定调用工具。考试包根目录支持普通离线 `python -m pip install .`。安装后可用 `python public/run_case.py --input samples/01/input/problem.json --output /tmp/result.h5` 调用当前库，再用 `python -m caeoj grade --input samples/01/input/problem.json --output /tmp/result.h5 --grading samples/01/reference/grading.json` 检查样例。

运行库使用 `/opt/bempp-env/bin/python`，与格式工具的Python环境隔离。固定源码根目录为 `/opt/upstream/bempp-cl-84345ee9ee314c85750f045c7ad38090f5ea5f26`，构建目录为 `/opt/bempp-repair-build`。本地改源后，删除该源码 `bempp/api/fmm/__pycache__/` 下三个同名 `*.cpython-311.pyc`，再执行 `cmake --build /opt/bempp-repair-build --target repair_sources`；不要仅依赖文件时间决定是否重编。正式判题自动完成规定的删除和重建。
