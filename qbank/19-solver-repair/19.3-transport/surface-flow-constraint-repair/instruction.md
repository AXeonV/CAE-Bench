# 19.3.2 表面反应管流物种约束修复

修复给定 Cantera 3.1.0 真实源码，使指定催化管流问题族满足质量守恒、物种排序不变性及真实浓度质量作用律。一个提交须处理 [DATA.md](DATA.md) 的全部合法状态；通用数据协议见 [CONTRACT](../../../../docs/CONTRACT.md)。

理想气体A、B、I具有相同摩尔质量15.999 kg/kmol和相同热性质，I不参与反应；A和B代表相同元素组成的不同化学物种。定截面、无摩擦恒温稳态管流与催化表面接触。表面空位S占1个位点，吸附物AS占1个位点。表面在每一轴向位置满足反应准稳态，不进行覆盖率的轴向输运。反应及全部参数由DATA固定。三步反应共同产生气相A到B的净转换，不存在净气相质量或摩尔源；不得以输出归一化替代求解器守恒修复。所有气相物种排序都应给出同一按物种名字报告的物理解。

只提交 `FlowReactor.cpp`，替换 `src/zeroD/FlowReactor.cpp`。保留原公开API及本题范围内既有行为，可在允许文件内重构实现。禁止改写可信driver、机制、其他源码或构建材料；禁止另写替代输出程序、读取参考或按算例标识硬编码。数值与方法要求分别核查。完整真实源码及许可证位于 `public/cantera-source.tar.gz`，固定API调用见 `public/driver.cpp`，机制见 `public/mechanism.yaml`。

环境已提供真实源码和依赖。修改源文件后执行 `cmake --build /opt/cantera1655-build --target repair_sources`；以 `python public/run_case.py --input samples/01/input/problem.json --output /tmp/result.h5` 运行样例。可信运行器负责HDF5写回，考生仅提交规定源码。最终判题冻结源码，从可信基线强制重新编译实现与driver，提交中的二进制和驱动不参与判题。

每例比较全部状态的全部输出，点值误差满足 `abs(actual-reference) <= atol + rtol*abs(reference)`，所有输出通过才记该例通过，计分例等权。质量分数和覆盖率(atol,rtol)=(3e-7,1e-6)，压力(0.02 Pa,1e-8)，密度(1e-8 kg/m³,1e-7)，速度(1e-8 m/s,1e-7)。非有限数、缺少输出、运行失败或候选编译失败均未通过。每例执行60秒，候选重编译300秒，环境4 CPU、8 GiB内存。本题只评价公开指定的理想气体与表面机制，不承诺完整工业催化机理、非等摩尔质量气体、摩擦、能量演化或多相沉积预测。

每个提交文件不超过1 MiB（1,048,576字节）。
