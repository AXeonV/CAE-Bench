# 二维空间变系数 Darcy 型稳态问题

已具备连续 PDE 题面、输入输出契约、样例及测试分组规划；问题定义与冻结选样清单纳入版本管理，数值数组、网格及绑定实际载荷的参考证书由统一准备工具在本地生成，当前状态见 author/preparation.json（运行后生成）。

| 文件 | 用途 |
|---|---|
| [instruction.md](instruction.md) | 方程、支持范围、初边值条件及提交要求 |
| [DATA.md](DATA.md) | 字段、单位、采样含义、条件记录及输出数组 |
| [DESIGN.md](DESIGN.md) | 固定官方来源、配置对应及实现差异 |
| [SAMPLES.md](SAMPLES.md) | 公开样例输入输出规划（作者材料） |
| [TEST-CASES.md](TEST-CASES.md) | 隐藏测试分组、目录与参考审核规划（作者材料） |
| [author/README.md](author/README.md) | 后续冻结清单与私有记录职责 |
| [通用数据协议](../../docs/CONTRACT.md) | 共享 JSON/Gmsh/HDF5 契约 |

样例与隐藏算例的来源和拆分已冻结，工具已支持生成真实输入与数值参考，具体本地状态见 author/preparation.json；误差阈值、执行资源及尚未完成的物理参考审核仍需补充。统一下载/缓存/协议转换入口已实现，见 [数据准备工具](../../src/utils/PDEBench/README.md)。只有完整公开样例、同契约参考及判分配置全部就绪后，才运行发布或 Harbor 组装。

公开样例的问题定义：[样例 01](samples/01/input/problem.json)、[样例 02](samples/02/input/problem.json)。隐藏定义保存在 cases/<ID>/problem.json，参考证书保存在 reference/<ID>/certificate.json；这些 JSON 随 Git 克隆保留，数组与网格需运行工具补齐。

本题覆盖当前官方已发布配置的数学问题，求解方法由提交程序选择。现有任务及其评测数据保持不变。

已提供宽松试运行配置：[judge-config.json](judge-config.json)、[Harbor 资源](harbor/task.toml)。实际运行入口会声明这些参数；正式参考误差和资源校准仍待完成，详见 [试运行说明](../../src/utils/PDEBench/EVALUATION.md)。本题不要求提供 baseline，可直接组装后运行 Agent。
