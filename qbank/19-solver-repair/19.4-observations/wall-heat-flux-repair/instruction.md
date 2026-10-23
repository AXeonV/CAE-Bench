# 壁面能量离散与热流报告修复

提供的 SU2 源码在不可压缩流的壁面能量处理与热流报告中存在不一致。修复它，使非正交网格上的恒温壁条件、真实温度场及原生报告的壁面热流保持一致，同时保留规定热流边界和真实对流行为。

提交目录只包含 `geometry_toolbox.hpp`、`CFVMFlowSolverBase.inl` 和 `CIncNSSolver.cpp`，每份文件不超过 1 MiB，分别替换 `Common/include/toolboxes/`、`SU2_CFD/include/solvers/`、`SU2_CFD/src/solvers/` 下的同名文件。保留接口和其余受支持行为，不修改驱动、另写求解器或按输入编号返回答案。可信运行器强制重新构建真实依赖闭包及 SU2_CFD，再调用不可修改的 `public/run_case.py` 读取数据并写结果。全部输入输出定义见 [DATA.md](DATA.md)，通用协议见 [CONTRACT](../../../../docs/CONTRACT.md)。

支持二维定常、单相、常物性层流，使用实际 `INC_NAVIER_STOKES` 与能量方程。数据包括变形四边形网格上的静止流导热、非零均匀速度的对流扩散、两壁恒温和规定热流/恒温混合边界。不包含可压缩流、共轭传热、NEMO、湍流或随时间变化的网格。流动工况中两壁沿切向同速滑动，入口速度相同，几何保持不变。

公开完整源码为 `public/su2-source.tar.gz`，其固定 MEL 依赖为 `public/mel-source.tar.gz`。Linux 中使用原 Meson/Ninja 构建，关闭 MPI、OpenMP、AD、CGNS、TECIO；配置需附加 `-Dcpp_args=-I/SOURCE/SU2_CFD/src/interfaces`，`/SOURCE` 为源码绝对路径。可用 `python public/run_case.py --input CASE/problem.json --output result.h5 --executable BUILD/SU2_CFD/src/SU2_CFD` 运行单个输入。

例如在题目根目录，使用 C++17 编译器、Python 3、Meson 1.8.3 和 Ninja：

```sh
mkdir -p su2/externals/mel
tar -xzf public/su2-source.tar.gz -C su2 --strip-components=1
tar -xzf public/mel-source.tar.gz -C su2/externals/mel --strip-components=1
cd su2
python preconfigure.py --no-codi --no-medi --no-opdi --no-mpp --no-coolprop --no-mel --no-mlpcpp
meson setup build -Dcpp_args=-I"$PWD/SU2_CFD/src/interfaces" -Dwith-mpi=disabled -Dwith-omp=false -Denable-cgns=false -Denable-tecio=false -Denable-autodiff=false -Denable-directdiff=false
ninja -C build SU2_CFD/src/SU2_CFD -j4
```

逐点温度、速度、压力、壁面热流及两壁积分均参与评分。每个算例全部输出和收敛条件通过才得分，算例等权。点值比较 `atol=1e-5, rtol=1e-7`；热率积分采用相同容差；残差日志允许绝对差 `0.5`，并须实际达到 DATA 门槛。参考为固定离散设置的真实求解器输出；导热解析解、非零对流的完整对流扩散解析解、网格收敛和边界能量平衡用于核查参考的物理资格，不能用解析公式在驱动中替代计算结果。

运行资源为 4 CPU、8 GiB，候选构建限时 900 秒，每个算例运行限时 180 秒。样例分别提供一个非正交导热工况和一个非正交非零对流工况。
