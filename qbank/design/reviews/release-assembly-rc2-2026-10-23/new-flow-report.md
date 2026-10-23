# RC2 新覆盖流动题组装

2026-10-23，仅补取 Titan 三题已存在的 11 份候选，不重算、不调用模型、不改变远端任务。输入、数值参考、评分配置、design/execution/status 元数据保留于 `new-flow-payload/`。

|题号|task_id|正式 case|公开格式样例|
|---|---|---:|---:|
|2.2.9|caeoj-910229|4|1|
|2.2.11|caeoj-910211|3|1|
|2.4.4|caeoj-910244|4|1|

必要载荷预计 10,755,958 bytes；流式 SSH tar 只读传输。逐文件与此前 `new-payload-hashes.json` 的字节数及 SHA-256 比较全部一致，归档摘要记录在 `new-flow-transfer.json`。三项 task_id 在来源组合 checkout 的所有现有 data-manifest 中检查无冲突。

优先检查组合 checkout，确认这 11 份新结果未在本地后才补取。题面、DATA、judge-config 和 Harbor 配置从组合 checkout 复制，未修改题意、阈值或资源。使用该 checkout 匹配版本的 pack、assemble、strict verify、输入与参考格式验证、参考自判分及原 publisher 创建独立 stage；11 例均通过接口消费检查。v2 quantities 评分文件仅由既有 `direct_config` 转换为实际消费表示。

每题从首例输入创建一个公开随机格式样例，原始数值参考不进入公开样例。公开 ZIP 路径检查没有隐藏 cases、reference、author 或 data-manifest。真实数值参考仅存在维护 stage 和 pool。`new-flow-public-check.json` 记录检查；`new-flow-report.json` 包含逐例结果、来源映射和原文档摘要。

`new-flow-plan.json` 是可以并入总发行计划的三个记录。`profile=unvalidated-reference-rc`：本轮不授予数值正确性、来源许可或干净机器预算认证。项目 LICENSE 不代表所有求解器与数据的通用分发授权。状态中保留的原生停止、封闭质量/EOS转换与精度审查事项仍然有效。
