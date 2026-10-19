# PDEBench 归档 case 池

这三个数据池直接保留 PDEBench 轨迹，题目身份由各自 data-manifest.json 拥有，迁移范围见[执行规划](../../design/pdebench-hf-migration.md)。它们不沿用旧题的初态重解释或替代参考。

- [平流](pdebench-advection-1d/instruction.md)
- [Burgers](pdebench-burgers-1d/instruction.md)
- [可压缩流](pdebench-compressible-1d/instruction.md)

每例可按标准工具装配和读取。当前为数据迁移池，正式评测的完整物理题意、容差、资源和选样另行确定；归档身份验收不等于独立数值认证。正式清单保持为空，试验选择绑定在云端批次记录。
