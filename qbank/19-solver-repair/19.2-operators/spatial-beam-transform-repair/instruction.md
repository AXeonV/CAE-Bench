# 空间梁方向变换修复

修复给定 Kratos 源码中 `LinearTimoshenkoBeamElement3D2N` 的空间方向变换，使同一个实现正确处理 DATA 声明的均匀、线弹性、两节点 Timoshenko 梁。梁可取任意空间方向及截面参考轴，具有两个不同的弯曲惯性矩和有效剪切面积。物理量和完整数据定义见 [DATA.md](DATA.md)，通用存储规则见 [CONTRACT](../../../../docs/CONTRACT.md)。

每条输入记录是一根独立直梁。所有单元初始位移和转角为零。求值包括单元刚度及常量体加速度对应的一致节点外力，并将根端全部夹持、施加自由端集中力与力矩，求自由端的小变形线性静力响应。不含几何非线性、动力学、翘曲及初始应变。三个既有接口 `CalculateLocalSystem`、`CalculateLeftHandSide`、`CalculateRightHandSide` 均须正确，合并和分开调用的结果均被评价。

提交目录只包含替换文件 `timoshenko_beam_element_3D2N.cpp`。该文件替换公开源码包中 `applications/StructuralMechanicsApplication/custom_elements/beam_elements/timoshenko_beam_element_3D2N.cpp`。保持公开类及 API、线弹性单元积分及材料响应，修复应在该真实实现及其方向变换辅助方法内完成。不得读取算例身份、输出预置答案、执行外部程序、绕过指定单元或修改可信驱动。判题冻结源码后从不可变基线增量编译；开发环境中的二进制、其他源码或驱动改动均不进入提交。

公开包包含原始源码构建闭包及许可证、CMake 驱动和 JSON/HDF5 转换器。在开发镜像内可修改 `/opt/kratos-source/` 的上述源文件，执行 `cmake --build /opt/beam-build --target beam_repair -j2` 重建，然后运行 `python public/run_case.py --input samples/01/input/problem.json --output result.h5`。源码归档解压后可阅读实现；修改许可范围以本题声明为准。

每个算例同时检查两种调用路径的完整12×12刚度、完整12分量一致节点外力和6分量自由端响应。全部要求均通过才记该算例通过，最后按通过算例比例计分；公开样例也可能显式列为计分case，公开/隐藏身份以正式清单为准。每个数值按 `|computed-reference| <= atol + rtol*|reference|` 检查：归一化刚度 `atol=1e-4 N/m, rtol=1e-9`，归一化力 `atol=1e-8 N, rtol=1e-9`，归一化自由端位移 `atol=1e-11 m, rtol=1e-8`。

提交源码总量不超过1MiB。编译限时180秒；逐例执行限时15秒。开发/执行环境配置4个CPU、8GiB内存，Agent时间预算1800秒。编译失败、运行失败、超时或输出违反契约均使相应提交或算例不通过。

