# 出题计划与来源记录

本目录属于作者材料，不进入 Agent 公开包。具体源样本选择和输入生成状态以运行统一工具后产生的 selection.json、preparation.json 为准。

中央工具入口已在 `src/utils/PDEBench/prepare.py` 实现。本目录保存每题冻结的选样清单（`selection.json`）和物理参考审核清单（拟为 `reference-policy.json`），其中记录源文件身份、样本索引、公开/隐藏拆分、case ID、时间选取及参考计算策略。selection.json 由工具冻结；reference-policy.json 仍需在后续参考审核时定义。工具状态文件不会被当作科学审核证据。

分组、预算、目录及冻结规则见 [TEST-CASES.md](../TEST-CASES.md)，样例设计见 [SAMPLES.md](../SAMPLES.md)，物理契约与来源差异见 [DESIGN.md](../DESIGN.md)。源索引和数组指纹只保存在作者材料及私有证书中，不加入输入 problem.json。
