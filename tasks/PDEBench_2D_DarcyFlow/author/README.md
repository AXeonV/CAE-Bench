# 出题计划与来源记录

本目录属于作者材料，不进入 Agent 公开包。具体源样本选择和输入生成状态以运行统一工具后产生的 selection.json、preparation.json 为准。

中央工具入口为 `src/utils/PDEBench/prepare.py`。`selection.json` 固定源文件身份、样本索引、公开/隐藏拆分、case ID 和格式变体，可纳入 Git；`preparation.json` 与 `prepared/` 记录本地完成状态及文件摘要，`sample-certificates/` 保存公开样例的私有参考、对照和证书，均由工具生成且不进入 Git。隐藏参考证书位于 reference/<ID>/certificate.json。证书记录实际时间、契约摘要、参考策略、检查指标及证据局限；状态文件本身不是科学验证。误差阈值和执行资源仍待校准。

分组、预算、目录及冻结规则见 [TEST-CASES.md](../TEST-CASES.md)，样例设计见 [SAMPLES.md](../SAMPLES.md)，物理契约与来源差异见 [DESIGN.md](../DESIGN.md)。源索引和数组指纹只保存在作者材料及私有证书中，不加入输入 problem.json。
