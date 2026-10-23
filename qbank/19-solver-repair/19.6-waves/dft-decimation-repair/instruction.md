# 19.6.1 非线性场观测的DFT降采样修复

修复给定真实Meep的有限时间窗口傅里叶观测：非线性介质生成的源频带之外的谐波不能因自动降采样而混叠成伪响应，同时保留线性自动采样和显式采样设置。一个冻结提交处理[DATA.md](DATA.md)的全部合法输入；通用协议见[CONTRACT](../../../../docs/CONTRACT.md)。

提交目录恰含四个普通文件：`dft.cpp`、`fields.cpp`、`structure.cpp`、`meep.hpp`，每个不超过1 MiB（1,048,576字节），分别替换原始源码树`src/`下同名文件。保留原有公开API及真实FDTD推进与DFT累加器，不得修改可信driver、适配器、其他源码、构建规则，或以另写求解/输出程序、读取参考、按算例标识硬编码绕过修复。数值与方法要求分别核查。公开完整固定源码及许可证为`public/meep-source.tar.gz`，中性调用入口为`public/driver.cpp`。

本题输出归一化有限窗口复DTFT和真实采样元数据；DATA规定模型、居中空间取样、E/H半步错时、源包络、窗口及自动/显式stride。它不把有限脉冲的DFT当作无限时稳态相量或功率谱密度。仅有复谱接近还不够：实际线性自动stride及显式stride也必须符合声明，不能通过无条件关闭优化规避问题。

环境提供真实原件、GCC14.2、CMake、Autotools及离线SDK依赖。源码根目录`/opt/meep-upstream/meep-ccb3c372dc34ca75ce01f99c2b50e0e89ad0a203`，构建根目录`/opt/meep-repair-build`。修改四文件后，可执行`make -C /opt/meep-repair-build/upstream/src clean`，再执行`cmake --build /opt/meep-repair-build --target repair_sources --parallel 4`；运行样例用`python public/run_case.py --input samples/01/input/problem.json --output /tmp/result.h5`。正式后端从可信原件开始，先强制重编原件及健康检查，再冻结替换件，删除全部受头文件影响的真实中间件并重编/重链库和driver；提交中的二进制及缓存不参与判题。

每例全部请求的全部输出逐值通过才得1分，计分例等权，包括被公开为样例的计分例。接受条件为`abs(actual-reference) <= atol+rtol*abs(reference)`；observed_dft的atol=1e-9、rtol=1e-8，sampling_stride必须精确相等，time_step的atol=rtol=1e-12，window_end的atol=1e-10、rtol=1e-12。比较实部和虚部，不能只交模长或能量。参考对应规定的真实离散时间观测，不把连续傅里叶积分的离散误差计作修复误差。

环境4 CPU、4 GiB，候选编译300秒，每例运行30秒；程序、结构、非有限输出或候选编译失败均未通过。缺工具或可信原件不能构建/运行属于基础设施错误。范围为单进程一维电chi2/chi3模型及指定观测，不认证MPI、GPU、多能级材料、磁非线性或复杂几何。
