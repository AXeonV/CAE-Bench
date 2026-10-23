# 19.3.3 双温等离子体状态关系修复

给定 Cantera 3.1.0 真实源码，诊断并修复 `PlasmaPhase` 的状态关系，使具有独立重粒子温度和电子温度的理想混合物正确报告总压、电子分压、密度和物种浓度。一个提交必须覆盖 [DATA.md](DATA.md) 的整个问题族。协议见 [CONTRACT](../../../../docs/CONTRACT.md)。

O2、O 和 E 的摩尔分数给定，重粒子共享温度 T，电子温度为 Te。总压是所有物种的分压之和；电子分压只计电子。本题固定理想气体假设，不进行化学反应、空间输运或时间积分。各输入行是独立状态，时间轴零只是瞬时标签。模式0在固定密度下设置状态并改变电子温度；模式1在指定压力下设置状态、改变电子温度，再重设同一总压。最终状态必须同时满足这些约束。温度及组分改变不能破坏常温等温和零电子极限。

只提交 `PlasmaPhase.h`，替换真实源码 `include/cantera/thermo/PlasmaPhase.h`。保留所有现有公开类、函数签名和原有功能；可在该类内增加或覆写必要方法。可信驱动和源码其他文件不可修改，不得另写替代程序、读取参考或按算例标识硬编码。数值判分与方法要求分别核查。完整源码及许可证在 `public/cantera-source.tar.gz`；`public/driver.cpp` 给出固定 API 调用顺序，`public/plasma.yaml` 给出完整物种定义。

环境提供 `/opt/cantera-source`、`/opt/cantera-source/build` 和编译依赖。开发时替换头文件，执行 `cmake --build /opt/cantera-source/build --target repair_sources`；以 `python public/run_case.py --input samples/01/input/problem.json --output /tmp/result.h5` 执行样例。最终判题只接收该头文件并从可信源码重新编译；提交中现有二进制、驱动和构建缓存不参与判题。

逐例比较全部状态的四项输出，点值误差满足 `abs(actual-reference) <= atol + 1e-10*abs(reference)`。总压与电子分压 atol 为1e-7 Pa，密度1e-12 kg/m³，摩尔浓度1e-14 kmol/m³；该例全部输出通过才记通过，所有计分例等权。非有限数、缺输出、运行失败或候选编译失败均未通过。单例执行30秒，候选重编译900秒，环境4 CPU、8 GiB内存。此范围不要求电子分布、化学势、平衡、热容或任意复合状态反演的正确性。
