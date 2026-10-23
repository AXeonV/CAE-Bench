# 巨势材料系数的一致导数

修复真实 MOOSE `GrandPotentialSinteringMaterial`，使 [DATA.md](DATA.md) 定义的 PARABOLIC 材料值、一阶导数、完整二阶导数及对应有限元约束残量/Jacobian 一致。保留该范围内 strict 与 non-strict 两种调用，以及已定义的原有密度和巨势值。此题评价材料和离散算子实现，不评价完整烧结形貌或演化预测。通用格式见 [CONTRACT.md](../../../../docs/CONTRACT.md)。

提交目录恰含两个普通文件 `GrandPotentialSinteringMaterial.C`、`GrandPotentialSinteringMaterial.h`，分别替换源码树 `modules/phase_field/src/materials/` 和 `modules/phase_field/include/materials/` 中的同名文件。即使某个文件无需修改也须提交；每个文件不超过 1 MiB（1,048,576 字节）。不得提交目录、链接或额外文件。保留真实类和公共接口；不能修改驱动、框架其他源码或构建配置，不能以固定输出、算例识别或另一材料模型代替真实计算。

公开包提供固定基线的真实源码、许可证、输入输出适配器和构建入口。可信驱动使用真实 MOOSE `DerivativeParsedMaterial` 提供声明的平衡浓度多项式，调用目标材料，通过材料属性 API 读取观察量，并调用真实 `Reaction`、`MatReaction`、`MatBodyForce` 与 libMesh/PETSc 装配残量和解析 Jacobian。它只转换输入和原生输出，不补导数或修正材料值。运行接口为 `run_case.py --input problem.json --output result.h5`。

环境使用 GCC 12.2.1、CMake 3.26.5、原生 MOOSE make、libMesh 和 PETSc 3.23。必要框架与依赖已预编译；候选文件进入同一真实模块增量构建。公开 `CMakeLists.txt` 包装原生 make，目标为 `phasefield_repair`；源码和构建根为 `/opt/moose-source`，原生应用位于其 `modules/phase_field/phase_field-opt`。本地完整构建可使用官方开发环境 `idaholab/moose-dev@sha256:78d1470a041e789f0ecbfba507a890e03766c8983b09176da4f9eadaf4419149`，加载 `/environment` 后在源码 `modules/phase_field` 执行 `make -j2 METHOD=opt ENABLE_LIBTORCH=false`。一次性框架构建与候选增量构建分别计时。

按输入文件等权计分，该文件全部声明输出通过才得分。一般接受条件为 `|误差| ≤ atol + 1e-10·|参考值|`。单位为 `1` 的材料输出 atol=1e-10；数密度为 1e-6 m⁻³，巨势密度为 1e-5 J/m³；残量、对序参量及浓度的 Jacobian 为 1e-11 m；对化学势的 Jacobian 为 1e-8 m/J。

对逆能量系数 C、D 的值、梯度和 Hessian，分别使用本例输入给定的特征能量 `Ev=Va·kv`、`Es=Va·ks`（单位 J），判据为 `Ei·|误差| ≤ 1e-10 + 1e-10·Ei·|参考值|`。等价原单位绝对容差为 `1e-10/Ei` J⁻¹，相对容差仍为 1e-10；没有对答案作截断或归一化输出。该尺度用于区分逆能量单位的量级和近纯相切换函数的浮点舍入。公开样例参考与 grading 同样受检。

资源为 4 CPU、4 GiB 内存；每次候选增量构建限时 300 秒，每个输入运行限时 30 秒。构建、执行、格式或数值失败不得分；缺失工具或可信基线无法执行属于基础设施错误，单独报告。
