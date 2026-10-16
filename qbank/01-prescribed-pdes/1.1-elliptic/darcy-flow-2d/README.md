# 二维空间变系数 Darcy 型稳态问题

本题以方程、初边值条件、输入范围和观测量定义求解问题；算例可以由不同数据集、解析构造或独立生成器提供，但必须满足同一题目契约。

| 文件 | 用途 |
|---|---|
| [instruction.md](instruction.md) | 数学问题、支持范围与提交要求 |
| [DATA.md](DATA.md) | 字段、单位、采样含义与输入输出约定 |
| [grading.json](grading.json) | 当前评分规则 |
| [judge-config.json](judge-config.json) | 运行时限与输出大小限制 |
| [harbor/task.toml](harbor/task.toml) | 评测资源配置 |
| [author/data-evidence/reference/README.md](author/data-evidence/reference/README.md) | 当前算例来源、选样、参考方法与证据局限 |
| [author/README.md](author/README.md) | 数据准备工具与本地状态 |
| [通用数据协议](../../../../docs/CONTRACT.md) | 共享 JSON/Gmsh/HDF5 契约 |

本地不保留题目数据或仅含 `problem.json` 的骨架。PDEBench 的冻结来源选择保存在 `author/data-evidence/reference/selection.json`；尚未制备并上传 HF 的数据不可拉取使用。

当前评分及资源配置用于试运行，连续 PDE 参考误差和资源校准尚未完成。数值参考与精确连续真解应加以区分；来源与审核证据见 `author/data-evidence/reference/`，不能仅凭参考文件存在认定其精度。
