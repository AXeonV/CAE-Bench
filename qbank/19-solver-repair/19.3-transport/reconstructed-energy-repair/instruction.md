# 重构状态的能量一致性修复

提供的 SU2 源码在可压缩流 MUSCL 状态重构中存在能量一致性缺陷。修复 `common.hpp`，使其正确处理非线性迭代阶段已存储的总焓、重构后的状态及保守量，并保持限幅、一阶和非物理重构回退行为。修复还须使给定壁函数平板算例实际完成稳定的 CFD 计算。

提交目录只包含修改后的 `common.hpp`，文件不超过 1 MiB，替换 `SU2_CFD/include/numerics_simd/flow/convection/common.hpp`。保留接口及未受缺陷影响的功能。可信运行器重新构建真实 SU2 和模板调用程序，调用公开的 `public/run_case.py`，并负责写 HDF5；不得修改驱动、另外实现求解器、按算例编号返回答案或读取参考文件。输入输出完整定义见 [DATA.md](DATA.md)，通用格式见 [CONTRACT](../../../../docs/CONTRACT.md)。

两类算例分别检查直接状态重构和完整求解器回归。直接重构支持二维、三维、无限幅、边限幅、点限幅以及一阶/回退；阶段总焓允许与当前温度和速度的平衡公式存在已存储的偏差。完整 CFD 使用提供的固定网格、不可修改的离散配置和 SST 标准壁函数。该部分比较给定离散设置的收敛软件结果，考察真实求解器稳定性，不要求校准湍流模型或匹配高精度实验壁面摩擦曲线。

`public/su2-source.tar.gz` 为原版完整源码，`public/mel-source.tar.gz` 为该版本指定的 MEL。Linux 构建使用 Meson/Ninja，关闭 MPI、OpenMP、AD、CGNS 和 TECIO；Meson 配置另需 `-Dcpp_args=-I/SOURCE/SU2_CFD/src/interfaces`，其中 `/SOURCE` 替换为解压后的绝对路径。`public/reconstruction-driver.cpp` 使用真实 SU2 存储和模板接口，可与生成的 `libSU2core.a`、`libSU2Common.a` 链接。完整平板输入为 `public/flatplate.cfg` 和 `public/flatplate.su2`；运行器仅调整 DATA 声明的控制参数和输出格式。

例如使用 Python 3、Meson 1.8.3、Ninja 和 C++17 编译器，在题目根目录执行：

```sh
mkdir -p su2/externals/mel
tar -xzf public/su2-source.tar.gz -C su2 --strip-components=1
tar -xzf public/mel-source.tar.gz -C su2/externals/mel --strip-components=1
cd su2
python preconfigure.py --no-codi --no-medi --no-opdi --no-mpp --no-coolprop --no-mel --no-mlpcpp --no-fado
meson setup build -Dcpp_args=-I"$PWD/SU2_CFD/src/interfaces" -Dwith-mpi=disabled -Dwith-omp=false -Denable-cgns=false -Denable-tecio=false -Denable-autodiff=false -Denable-directdiff=false
ninja -C build SU2_CFD/src/SU2_CFD -j4
c++ -std=c++17 -O3 -DNDEBUG -I. -Iexternals/mel -Ibuild/Common/src -ICommon/src ../public/reconstruction-driver.cpp -Wl,--start-group build/SU2_CFD/src/libSU2core.a build/Common/src/libSU2Common.a -Wl,--end-group -o build/reconstruction-driver
cd ..
python public/run_case.py --input CASE/problem.json --output result.h5 --driver "$PWD/su2/build/reconstruction-driver" --executable "$PWD/su2/build/SU2_CFD/src/SU2_CFD"
```

每个算例声明的全部输出及运行条件均满足才得分，算例等权。直接重构逐点逐分量容差为 `atol=1e-7, rtol=1e-10`；完整 CFD 的密度、动量、能量和壁面摩擦系数容差分别为 `atol=1e-5, 1e-3, 1, 1e-7`，均配 `rtol=2e-5`。残差日志比较允许绝对差 `0.5`，并须达到 DATA 的收敛门槛，不能用小残差代替流场比较。资源为 4 CPU、8 GiB，候选构建限时 300 秒，每个算例运行限时 900 秒。
