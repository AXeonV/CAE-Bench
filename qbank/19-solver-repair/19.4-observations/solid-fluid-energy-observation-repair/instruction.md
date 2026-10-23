# 固流传热能量观测接口修复

为给定版本 MOOSE 补全缺失的能量对流体积分接口，使普通材料与自动微分（AD）材料都能通过原生后处理器得到流体的对流功率，同时保留固体、流体的储能、体热源和外壁散热观测。交付的接口须覆盖 [DATA](DATA.md) 的问题族：给定有限元温度／速度场的直接观测，以及真实固流耦合传热的稳态与瞬态观测。

目标版本尚未包含 `INSElementIntegralEnergyAdvection.C` 和 `INSElementIntegralEnergyAdvection.h`。提交目录恰含这两个完整文件，分别新增到固定源码的 `modules/navier_stokes/src/postprocessors/` 和 `modules/navier_stokes/include/postprocessors/`。真实 MOOSE 构建必须发现、编译并注册普通类型 `INSElementIntegralEnergyAdvection` 及 AD 类型 `INSADElementIntegralEnergyAdvection`。两类型接受温度变量 `temperature`、向量速度变量 `velocity`、比热材料属性名 `cp`、密度材料属性名 `rho` 和原生 `block` 选择，计算所选流体区域的体积分。

修复职责是可复用的库观测能力。保持既有求解方程、材料、有限元场、注册接口与其他后处理行为；不得修改可信转换／运行器、热流或动量内核，不得另写入口生产答案、把流体积分扩展到固体、改写输出抵消错误或用边界焓流替代要求的体积分。完整基线源码及许可证位于离线环境 `/opt/moose-source-2022`。`public/run_case.py` 调用真实求解器并转换原生输出；耦合分支的固定原生配置随公开工具提供。

公开包根目录可普通安装：

```sh
python -m pip install .
cd qbank/19-solver-repair/19.4-observations/solid-fluid-energy-observation-repair
python public/run_case.py --input samples/01/input/problem.json --output /tmp/result.h5
```

安装 SDK 不会补全目标库接口。编译并注册新增类型后，运行器按同一输入流程调用它。开发构建产物不作为提交；可信判题从原始基线重建、检查原生运行环境，再安装替换件并强制重建受影响的库和应用。

环境提供4个 CPU、4GiB内存。每文件不超过1MiB；原件及候选各有300秒编译预算，每例求解60秒。输出须符合 [CONTRACT](../../../../docs/CONTRACT.md)。每例的五项观测、全部规定时刻均须满足 `|提交值−参考值|≤atol+1e−9×|参考值|`：能量两项 atol 为 `1e−5 J`，功率三项为 `1e−5 W`。非有限值失败；所有计分例等权，公开样例也计入总分母。源码方法要求单独核查，不以文本相似性评分。
