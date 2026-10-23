# 19.4.2 扩散元件的电压贡献与热功率

修复给定 PyBaMM 版本中的等效电路扩散元件和热子模型，使其在给定瞬时状态下返回正确的扩散过电势、不可逆热功率及总热功率，并保持关闭扩散时的行为。

系统以无量纲平均荷电状态（SoC）和扩散域 ξ∈[0,1] 内的线性 SoC 分布描述状态，表面为 ξ=1。OCV 是随题输入给定的单调递增三次多项式 U(s)，单位 V。正电流表示放电，扩散过电势定义为表面相对平均 SoC 对应的电压贡献：η=U(s_surface)−U(s_average)。这里 U(s_average) 不是 U(s) 的空间平均。关闭扩散时 η=0，表面 SoC 等于平均 SoC。

扩散贡献的热功率为 Qdot_diff=−Iη。不可逆热功率为各其他元件给定热功率之和加 Qdot_diff，总热功率另加给定的可逆热功率。所有热输出单位均为 W。输入是给定状态，并非从平衡态开始的时间积分；电流可在分布尚未翻转时反向，Qdot_diff 可为负，不得按电流方向猜测 η 或将热项强行裁剪为非负。

可信驱动调用真实库的 `DiffusionElement`／`NoDiffusion.get_coupled_variables()` 和 `ThermalSubModel.get_coupled_variables()`，采用给定 OCV、状态和元件热源。考察的是已有实现中的瞬时求值，不要求计算 SoC 的扩散轨迹或完整电池温度轨迹。完整字段、空间采样及输出规则见本题 DATA.md，通用文件规则见包内 CONTRACT.md。

## 修复与提交

基线源码来自固定提交 `371b41d7db6246bddcd9fba4d1c6a20deeabf8b6`，离线环境保留原 BSD 许可。源码安装于 `/opt/pybamm-build/source/packages/pybamm/src/pybamm`。最终仅提交以下两个普通 Python 源文件，各不超过 1 MiB：

- `/app/submission/diffusion_element.py`，替换 `models/submodels/equivalent_circuit_elements/diffusion_element.py`。
- `/app/submission/thermal.py`，替换同目录 `thermal.py`。

保持已有公开类、方法、变量名及其他未改变接口。可以重构文件内部实现；修复必须发生于现有子模型入口，不得另写输出程序替代，不得改动驱动、参数处理、空间离散或结果转换。开发环境中其他修改不进入判题，不提交 `solve.py`、二进制、补丁脚本或额外文件。

判题在独立固定环境中冻结两个提交文件，替换原件并完成可信语法构建检查，随后以不可修改的驱动调用子模型。构建产物与源文件对运行用户只读，按固定输入逐例求值。

试运行时先将修改件放入上述实际源码位置，执行 `cmake --build /opt/pybamm-build --target repair_sources`，再运行：

```text
python <本题目录>/public/run_case.py --input <样例目录>/input/problem.json --output result.h5
python -m caeoj grade --input <样例目录>/input/problem.json --output result.h5 --grading <样例目录>/reference/grading.json
```

## 资源与评价

- 开发求解上限 1800 秒，CPU 4 核，内存 8192 MB。
- 提交冻结后的构建上限 60 秒；每个 case 执行上限 30 秒，判题无网络。
- 每个状态的表面 SoC、扩散过电势、不可逆热功率及总热功率均需输出并通过比较。SoC 绝对容差 `1e-10`，电压绝对容差 `1e-9 V`，热功率绝对容差 `1e-8 W`；相对容差均为 `1e-8`，按 `abs(value-reference) <= atol + rtol*abs(reference)` 逐分量比较。
- 每例全部输出通过记1分，否则记0分，总成绩为通过例数除以总例数，各例等权。公开样例若计入分母，在测试清单中单列身份。
- 提交结构错误、候选语法构建失败、运行错误、超时或非法结果记相应例未通过；可信原件、数据或配置故障单列为基础设施错误。
