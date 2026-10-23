# 并行波动求解的接口归约修复

同一二维波动实验被划分到多个进程后，应保留串行计算的传播与观测。一个进程可以完全拥有某个独立试件，从而没有与其他进程相接的网格界面；其他试件仍可跨进程划分。所附真实 SPECFEM2D 在这类合法输入上可能终止或停滞。请修复其接口初始化，使声明的问题族正常完成，同时保留连通网格、单进程及声学吸收层计算。

阅读 [DATA.md](DATA.md) 获取模型、离散、单位、分区及完整输入输出；通用格式遵循 [CONTRACT](../../../../docs/CONTRACT.md)。本题评估固定真实求解器的源码修复。支持无PML的SH反平面弹性波，以及可选上下C-PML的声学位势波；各分支均可采用一个或两个互不接触的矩形试件。固定求解器、离散方式和指定进程数属于方法要求。

提交目录恰含一个普通文件 `get_MPI.F90`，不超过1 MiB（1,048,576字节）。不允许额外文件、子目录或符号链接。文件完整替换固定基线的 `src/specfem2D/get_MPI.F90`；其他源码、构建配置、输入转换和运行器固定。须保持现有接口、真实MPI分区及原生求解调用。不得切换串行计算、删减进程或试件、另写求解器，或在输出层校正结果。

判题先实际重编原件并运行非触发健康算例，再替换提交、删除相关对象及可执行文件、重新编译真实Fortran目标。原件编译或健康环境失败归为基础设施问题；非法提交、候选编译失败、超时、求解失败和输出错误分别记录。编译预算为原件120秒、候选120秒。每例提供4 CPU、4 GiB内存，无外网，执行限210秒，评分限30秒；输出文件不超过1 MiB。

输出为全部声明接收点、全部声明时刻的标量时程 `wave_response`。不得省略早期尾部、边界返回波或吸收后的后段。参考是相同固定离散及源/采样约定下的真实求解器响应。逐项按 `|value-reference| <= atol + rtol*|reference|` 比较：SH位移 atol=2e-9 m、rtol=2e-6；声学位势 atol=5e-6 kg/m、rtol=2e-6。所有输出和协议检查通过才记该例通过，成绩为通过例数比例。非有限值、缺失输出或运行失败均不能通过。

完整原始源码及许可证在 `public/specfem-source.tar.gz`。`public/Par_file.template`、`SOURCE.template` 和 `run_case.py` 是固定输入与输出工具，只做格式转换、调用真实mesher/solver及读回原始采样。公开工具不修复通信或补算物理解。

提供的离线环境已配置原始源码和构建。开发文件位于 `/opt/specfem-repair-build/upstream/src/specfem2D/get_MPI.F90`。改动后先删除 `/opt/specfem-repair-build/upstream/obj/get_MPI.spec.o` 和 `/opt/specfem-repair-build/upstream/bin/xspecfem2D`，再执行 `cmake --build /opt/specfem-repair-build --target repair_sources`。该目标调用上游真实构建；不能靠已有二进制或文件时间戳代替重编。

考试包根目录支持离线 `python -m pip install .`。安装后先执行 `cd qbank/19-solver-repair/19.6-waves/parallel-pml-reduction-repair/`，再运行 `python public/run_case.py --input samples/01/input/problem.json --output /tmp/result.h5`；然后以 `python -m caeoj grade --input samples/01/input/problem.json --output /tmp/result.h5 --grading samples/01/reference/grading.json` 检查公开样例。`public/CMakeLists.txt` 负责既有真实构建的重编入口；从源码重新配置时使用GNU Fortran、OpenMPI、Scotch及 `--with-mpi --enable-double-precision MPI_INC=/usr/lib/x86_64-linux-gnu/openmpi/include FC=gfortran MPIFC=mpif90 FCFLAGS="-O2 -fallow-argument-mismatch" FLAGS_CHECK="-O2 -fallow-argument-mismatch"`，再执行上游 `make`。保留所附许可证。
