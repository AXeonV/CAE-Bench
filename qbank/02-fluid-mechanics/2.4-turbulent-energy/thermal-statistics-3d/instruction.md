# 2.4.3 3D 低速湍流传热尺度解析统计分析

实现一个可复用求解器，处理3维完整空间固定封闭域的单相流动。热膨胀牛顿液体，Boussinesq密度反馈；黏度和导热率按温度幂律变化。

从给定完整瞬时初态发展三维湍流，在指定离散统计网格上求均值、方差与适用协方差；输出时刻是统计终点标记。 必须使用DNS或适当LES的尺度解析统计，不以RANS模型变量替代。

几何、材料参数、壁面运动、适用的热条件、体加速度及观测由输入明确给出。本题以流动为主要目标；热反馈属于任务，不包含固体传热或反应。全部请求输出为：`velocity`, `pressure`, `temperature`, `velocity_covariance`, `temperature_variance`, `turbulent_heat_flux`。

完整任务由[共同要求](../COMMON.md)、[本题数据说明](DATA.md)和[公共数据说明](../DATA.md)组成；公共说明引用可随解题包交付的规范。入口为 `python solve.py --input problem.json --output result.h5`。每例1800秒、4 CPU、8 GiB、无GPU；所有输出通过共同要求中的结构及数值规则，本例得1分。资源及容差尚待真实数据校准。
