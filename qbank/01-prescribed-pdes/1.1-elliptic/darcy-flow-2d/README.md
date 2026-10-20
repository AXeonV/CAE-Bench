# 二维空间变系数 Darcy 型稳态问题

本题以方程、初边值条件、输入范围和观测量定义求解问题；算例可以由不同数据集、解析构造或独立生成器提供，但必须满足同一题目契约。

| 文件 | 用途 |
|---|---|
| [instruction.md](instruction.md) | 数学问题、支持范围与提交要求 |
| [DATA.md](DATA.md) | 字段、单位、采样含义与输入输出约定 |
| [作者评分模板](author/grading-template.json) | 制数模板；实际判题随case保存 |
| [judge-config.json](judge-config.json) | 运行时限与输出大小限制 |
| [harbor/task.toml](harbor/task.toml) | 评测资源配置 |
| [author/data-evidence/reference/README.md](author/data-evidence/reference/README.md) | 当前算例来源、选样、参考方法与证据局限 |
| [author/README.md](author/README.md) | 数据准备工具与本地状态 |
| [通用数据协议](../../../../docs/CONTRACT.md) | 共享 JSON/Gmsh/HDF5 契约 |

本地直接来源数据已安装；配方、冻结选择、原始参考政策与验收见[本批报告](author/data-evidence/install-20261020/REPORT.md)。数据Git忽略，重新制数按作者工具说明操作，无需先迁移HF。旧reference目录selection是历史规划。

当前评分及资源配置用于试运行，连续 PDE 参考误差和资源校准尚未完成。数值参考与精确连续真解应加以区分；当前来源与审核证据见[本批报告](author/data-evidence/install-20261020/REPORT.md)，不能仅凭参考文件存在认定其精度。
