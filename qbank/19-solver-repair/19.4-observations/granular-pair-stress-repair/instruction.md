# 瞬时颗粒应力修复

提供的 LAMMPS 源码在 `gran/hooke/history/kk` 的应力统计中存在缺陷。修复它，使同一球形颗粒接触状态在请求全局压力、逐粒子维里量或同时请求两者时均正确，并保持接触力和力矩。

本题运行固定版本的真实 LAMMPS，使用单进程 Kokkos CPU Serial、half 邻居表以及 `newton pair off`。观察为 `run 0` 的初始瞬间，切向接触历史为零。接触模型包含法向弹簧、法向速度阻尼、切向速度阻尼及转动贡献；合法输入保持法向排斥且切向力低于摩擦截断。无时间积分、周期边界、墙、冻结颗粒或其它外力。输入和输出的全部定义见 [DATA.md](DATA.md)，通用格式见 [CONTRACT](../../../../docs/CONTRACT.md)。

提交目录只包含修改后的 `pair_gran_hooke_history_kokkos.cpp` 和 `pair_gran_hooke_history_kokkos.h`，不得增加其它文件。它们分别替换源码 `src/KOKKOS/` 下的同名文件。保留公开接口和已有允许工况的物理行为；不得读取题目编号、样例答案或绕过该 pair 实现计算输出。可信运行器负责构建真实共享库和可执行文件，并使用不可修改的 `public/run_case.py` 读取输入、运行求解器和写结果。

`public/lammps-source.tar.gz` 提供原版构建所需的源码、内置 Kokkos、CMake 和许可证。解压后可在 Linux 中构建：

```sh
cmake -S cmake -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_MPI=OFF -DBUILD_SHARED_LIBS=ON -DPKG_GRANULAR=ON -DPKG_KOKKOS=ON -DKokkos_ENABLE_SERIAL=ON -DKokkos_ENABLE_OPENMP=OFF -DCMAKE_CXX_STANDARD=17
cmake --build build --target lmp --parallel 4
python public/run_case.py --input CASE/problem.json --output result.h5 --executable build/lmp
```

运行器路径以运行器文件所在目录为准。提供两个公开样例，分别覆盖多接触和单接触。正式输入还覆盖三维接触方向、不同粒径与密度、粒子排列、阻尼与转动、无接触、三种统计请求。

每个算例对其声明的全部输出逐点逐分量比较；全部通过该算例才得分。算例等权。输出容差为力及力矩 `atol=1e-7, rtol=1e-8`，逐粒子维里量 `atol=1e-7, rtol=1e-8`，压力张量 `atol=1e-9, rtol=1e-8`。不得用整体平均替代逐粒子比较。运行资源为 4 CPU、8 GiB，构建限时 300 秒，每个输入运行限时 60 秒。

每个提交文件不超过1 MiB（1,048,576字节）。
