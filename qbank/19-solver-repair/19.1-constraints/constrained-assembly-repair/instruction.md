# 19.1.1 双边距离约束系统的加速度与反力求值

修复随题提供的 Project Chrono 核心源码，使 `ChSystem::DoAssembly()` 能在指定状态下正确求出双边距离约束系统的瞬时线加速度与约束反力，并保持位置、速度装配功能。

系统由三维刚体构成，距离约束连接两个刚体的质心。固定体的位置不变；活动体具有给定正质量，承受重力及质心外力。无接触、摩擦、驱动、可变长度或柔性。所有转动初态为零，质心连接及无外转矩使转动与本题观测解耦。系统可以具有多条相互耦合的约束，也可以包含无约束活动体。

加速度任务提供位置及速度相容的状态。你需要恢复该状态的线加速度及各约束施加在第二端点物体上的全局力向量。另有位置及速度装配的兼容性测试；这些测试的初猜可不相容，要求见 DATA.md。任务不涉及时间轨迹积分。

## 修复与提交

Linux x86_64 环境离线提供基线源码、配置完毕的构建目录、编译器和可信数据驱动。源码原件位于 `/opt/chrono-source`，构建目录为 `/opt/chrono-build`。可在开发环境中修改和试编译；基线源码压缩包也位于本题 `public/chrono-source.tar.gz`。该版本为 `c6acd4e5a199f56052ba74b8e9d735a2157ba613` 的构建源码，保留原 BSD 许可；包内省略运行时不依赖的几何资产及发布记录。

最终只提交 `/app/submission/ChAssemblyAnalysis.cpp`，它替换基线中的 `src/chrono/timestepper/ChAssemblyAnalysis.cpp`。提交文件不得超过 1 MiB。无需提交 `solve.py`、二进制或其他文件。允许重构该文件的内部实现，保持现有公开 API、类定义和其他层级装配的语义。修复必须发生在已有装配实现中；不得另写求解程序替代该入口，不得篡改驱动、输入读取或结果转换。

判题在独立环境从固定基线复制此文件，以既定配置重新编译，然后通过不可修改的驱动构建系统并调用 `DoAssembly()`。开发环境中的其他修改不会传入判题。只使用这个替换文件，不应用补丁命令、不运行考生脚本。

可用公开驱动检查样例：

```text
cmake --build /opt/chrono-build --target Chrono_core -j4
python <本题目录>/public/run_case.py --input <样例目录>/input/problem.json --output result.h5
python -m caeoj grade --input <样例目录>/input/problem.json --output result.h5 --grading <样例目录>/reference/grading.json
```

驱动只转换数据并调用真实 Chrono API，不修正物理结果。先把你修改的文件放到 `/opt/chrono-source/src/chrono/timestepper/ChAssemblyAnalysis.cpp` 再执行构建，最终仍须将其复制到提交路径。数据、单位、状态保证、输出及轴的完整定义见本题 DATA.md，通用文件规则见包内 `docs/CONTRACT.md`。

## 资源与评分

- 开发及修复时间上限 1800 秒；CPU 4 核，内存 8192 MB。
- 提交冻结后的增量编译上限 300 秒；单例执行上限 10 秒。判题无网络。
- 编译失败、提交结构错误、运行失败、超时或输出不合法记对应 case 未通过。可信数据、配置或判题基础设施故障单列，不算考生数值错误。
- 加速度及反力按各全局分量逐点比较：加速度绝对容差 `0.01 m/s^2`，约束力绝对容差 `0.05 N`，两者相对容差均为 `0.0005`；判据为 `abs(value-reference) <= atol + rtol*abs(reference)`。
- 位置/速度回归按输出各分量逐点比较，绝对容差分别为 `1e-8 m`、`1e-8 m/s`，相对容差 `1e-8`。每例全部必需输出通过才计 1 分，总成绩为通过例数除以总例数，各例等权。公开样例属于公开测试，若纳入计分会在运行清单中单列。
