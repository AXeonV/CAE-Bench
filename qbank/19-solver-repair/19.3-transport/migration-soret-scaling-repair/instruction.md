# 漂移与热扩散的浓度单位一致性

修复真实 Elmer `AdvectionDiffusion` 模块中电迁移及 Soret 热扩散对浓度单位和密度的处理，使其在 [DATA.md](DATA.md) 的稳态条带范围内正确工作，并保留已正常的单位模式及零驱动力行为。通用格式见 [CONTRACT.md](../../../../docs/CONTRACT.md)。

提交目录只能包含一个普通文件 `AdvectionDiffusion.F90`，文件不超过1 MiB（1,048,576字节），替换真实源码树的 `fem/src/modules/AdvectionDiffusion.F90`。不得提交目录、链接、额外文件或构建产物。保留公开接口与真实模块求解；不得修改可信驱动、其他源文件或构建配置，不得用固定答案、算例识别或替代求解器绕过该模块。

公开包包含必要真实源码及许可证、输入输出适配器和运行工具。可信驱动转换所给网格与声明，依次调用真实 `HeatSolve`、`StatCurrentSolve`、`AdvectionDiffusion`，输出它们的全部节点场；不对浓度、热扩散系数或电荷作密度补偿。`run_case.py --input problem.json --output result.h5` 是运行接口。

可信环境为 GCC/GFortran 14.2.0、CMake、Ninja、BLAS/LAPACK，串行 Elmer，Release Fortran 编译参数 `-O1 -DNDEBUG`。源码根目录为 `/opt/elmer-source`，构建目录为 `/opt/elmer-build`。本地可解包公开源码，在相同依赖环境使用 `cmake -S SOURCE -B BUILD -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_Fortran_FLAGS_RELEASE="-O1 -DNDEBUG" -DWITH_MPI=FALSE -DWITH_ELMERGUI=FALSE -DWITH_ElmerIce=FALSE -DWITH_ELMERPOST=FALSE -DBUILD_TESTING=OFF "-DINCLUDE_ELMER_MODULES=AdvectionDiffusion;StatCurrentSolve;HeatSolve"` 配置，再构建 `Solver_TGT ElmerGrid AdvectionDiffusion StatCurrentSolve HeatSolve`。本地适配器中的路径可对应修改；提交时仍只交指定源文件。

按输入文件计分，浓度、温度、电势全部输出满足容差才通过。相对容差统一为 `1e-8`（浓度）、`1e-9`（温度和电势）；绝对容差为质量分数 `1e-9`、质量浓度 `1e-7 kg/m³`、温度 `1e-6 K`、电势 `1e-10 V`。接受条件为绝对误差不大于绝对容差加相对容差乘参考值绝对值。参考是规定有限元离散的节点解，不能将连续解析解的离散误差视为修复误差。样例同样参与检验，最终得分为通过文件比例。

资源为 4 CPU、4 GiB 内存；候选模块构建限时 180 秒，每个输入运行限时 20 秒。构建或运行失败不得分；缺失工具或可信基线无法执行属于基础设施错误，单独报告。
