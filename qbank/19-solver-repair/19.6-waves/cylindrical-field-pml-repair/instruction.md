# 柱坐标波场与吸收层修复

一个三维圆柱对称分解的电磁计算，在采用负角向模式和轴向吸收层时，包围面的频域通量出现错误。请修复所附真实 Meep 源码的场推进，使声明范围内的柱坐标波传播、吸收层及观测保持一致。

阅读 [DATA.md](DATA.md) 获取完整模型、源、时间/空间采样和输入输出定义，并遵循 [CONTRACT](../../../../docs/CONTRACT.md)。提交对固定离散计算的修复，保留真实求解器及其接口。输入网格只描述观测面的母线；内部电磁离散与吸收层由 DATA 指定的真实库构造。

提交目录恰含一个普通文件 `step_db.cpp`，不超过1 MiB（1,048,576字节），不允许符号链接、子目录或额外文件。该文件完整替换原件 `src/step_db.cpp`；其他源、头文件、构建工具及驱动固定。判题会先验证原始库实际可编译运行，再以提交文件实际重新编译相应翻译单元、真实库及驱动。原件或运行环境故障不计为提交错误；非法提交、候选编译失败、运行失败和数值错误分别处理。

每例输出 `spectral_flux`、`observed_dft`、`time_step` 和 `window_end`。谱通量是三个观测面的**独立绝对积分**，复场的实部与虚部分别比较。仅使正负模式具有相同总量，或只给出归一化分配，不能满足要求。字段、实体、分量、静态标签及数据类型须与输入声明一致。

所有数值按 `|a-reference| <= atol + rtol*|reference|` 逐项比较：谱通量atol=1e-9、rtol=1e-8；复场atol=1e-10、rtol=1e-8；步长atol=rtol=1e-12；终止时间atol=1e-10、rtol=1e-12。每例须全部满足才通过，得分为通过例数比例。缺失/非有限输出或契约错误不能通过。

环境提供4 CPU、4 GiB内存，无外网；候选编译限300秒，每例原生执行限1800秒、评分限30秒。完整原始源存档为 `public/meep-source.tar.gz`；`public/driver.cpp`、`CMakeLists.txt` 和 `run_case.py` 是固定调用/格式工具。驱动执行真实库，适配器只读取声明、传递输入及写回实际观测；它们不替你修复场更新。

在已装运行环境中，可使用 `python public/run_case.py --input samples/01/input/problem.json --output /tmp/result.h5` 调用当前编译的库，再用 `python -m caeoj grade --input samples/01/input/problem.json --output /tmp/result.h5 --grading samples/01/reference/grading.json` 检查公开样例。考试包根目录支持普通离线 `python -m pip install .`，无需联网或editable安装。

本地改源后须真实重编。固定源位于 `/opt/meep-upstream/meep-85e107771808a4b89e4b4514007512f48c1c121b/src/step_db.cpp`，CMake目录 `/opt/meep-repair-cmake`、构建目录 `/opt/meep-repair-build`。清除 `step_db.lo`、`step_db.o`、`.libs/step_db.o`、`libmeep.la`、`.libs/libmeep.so.30.0.0` 以及 `CMakeFiles/cylindrical_driver.dir/opt/meep-driver/driver.cpp.o`、`bin/cylindrical-driver` 后执行 `cmake --build /opt/meep-repair-build --target repair_sources --parallel 4`。这些路径前五项相对 `/opt/meep-repair-build/upstream/src`，后两项相对构建目录；不要仅靠复制文件时间判断是否已重编。正式判题自动执行规定的删除与重建。
