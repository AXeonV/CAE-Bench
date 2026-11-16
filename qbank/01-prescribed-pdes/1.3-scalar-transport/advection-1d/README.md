# 一维周期线性平流

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

正式数据选择见[data-manifest.json](data-manifest.json)；旧reference目录的来源选择保留历史身份。

当前评分及资源配置用于试运行，连续 PDE 参考误差和资源校准尚未完成。数值参考与精确连续真解应加以区分；来源与审核证据见 `author/data-evidence/reference/`，不能仅凭参考文件存在认定其精度。

## 数据获取

按[已发布PDEBench数据获取流程](../../../maintenance/PDEBENCH-DATA.md)装配本题数据，版本与发布状态以该指南引用的记录为准；本题data-manifest.json是正式选择的唯一入口。来源制作与历史安装证据在author/data-evidence中。
