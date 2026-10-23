# preCICE 19.5.2 最终公开变更有界复核

本报告只复核已完成独立考生审阅后的公开变更，不冒称重新完成全部材料的独立考生审阅。历史报告保持原样：`runs/candidate-review/repair22-precice/report.md`。本审阅者另按后端审阅授权读过源码和维护材料，因此不能冒充此前未接触解法的考生审阅者。

最终公开ZIP：`08223e23aeb1ab6cd9c01b53fd60fbb53dc4d4eacc29f04a6ba88d7d7e895a5c`，43条。实际证据见[bounded-public-change-evidence.json](bounded-public-change-evidence.json)。

1. 从已有探针镜像内`/tmp/agent.zip`读取中间版本，核对整包SHA为`b0caa6437806ba5f7c92c1a41e4fd070481b9124e19dadf12985cbcb31ee797f`。逐项比较43条，最终版仅instruction及MANIFEST改变，其余41条完全相同。新增instruction短语明确Index.cpp不超过1 MiB（1,048,576字节）；与既有max_source_bytes完全相同，未改变执行配置。删除该短语后逐字节SHA精确恢复历史考生报告的`f4c6bbdd0d905b6d9d92c4c3141ff9942ec0dd1a4443e893230d7c8edbfe4fb4`。
2. DATA新增mode.value必须为JSON整数0/1，明确排除1.0/0.0及布尔。它补明既有真实校验规则，不增加几何或算法义务；原两样例参数均为整数。删除这一短语并恢复原CRLF后，SHA精确恢复历史考生报告的`6476144240b47326b27837e69f9d01539fc4979d521a3c85906dc7c0b169dede`。换行差异不影响题意。最终DATA与中间b0caa版本完全相同。
3. 原考生报告列出的CONTRACT、data-manifest及两例全部12个JSON/HDF5/MSH/reference/output资产均实际计算SHA，与原审阅一致；公开SDK、扩展、driver、归档、README在b0caa至最终之间也逐条相同。

结论：两处澄清与已冻结实际消费者一致，无新的未决题意缺口；原独立考生报告可结合本有界复核覆盖最终版本。旧`e14c278...`ZIP原件未保留，本轮没有对其整包所有条目完成二进制差分；不将历史报告未列摘要的旧资产重新认证为亲自比对。前一独立数据审阅的`final-version-review.json`另外记录e14c至b0caa变化与19个SDK文件同一性。几何参考、库编译和资源不由本有界文本复核重新认证。
