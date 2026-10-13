# 一维 logistic 反应扩散

已具备连续 PDE 题面、输入输出契约、样例及测试分组规划；数据由统一准备工具在本地生成，当前状态见 author/preparation.json（运行后生成）。

| 文件 | 用途 |
|---|---|
| [instruction.md](instruction.md) | 方程、支持范围、初边值条件及提交要求 |
| [DATA.md](DATA.md) | 字段、单位、采样含义、条件记录及输出数组 |
| [DESIGN.md](DESIGN.md) | 固定官方来源、配置对应及实现差异 |
| [SAMPLES.md](SAMPLES.md) | 公开样例输入输出规划（作者材料） |
| [TEST-CASES.md](TEST-CASES.md) | 隐藏测试分组、目录与参考审核规划（作者材料） |
| [author/README.md](author/README.md) | 后续冻结清单与私有记录职责 |
| [通用数据协议](../../docs/CONTRACT.md) | 共享 JSON/Gmsh/NPZ 契约 |

判例与样例的结构和分组已规划；具体源样本由工具冻结，输入与参考准备状态分别报告；误差阈值、执行资源及尚未完成的物理参考审核仍需补充。统一下载/缓存/协议转换入口已实现，见 [数据准备工具](../../src/utils/PDEBench/README.md)。只有完整公开样例、同契约参考及判分配置全部就绪后，才运行发布或 Harbor 组装。

本题覆盖当前官方已发布配置的数学问题，求解方法由提交程序选择。现有任务及其评测数据保持不变。
