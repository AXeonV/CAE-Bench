# 第二章 Titan 补充证据独立复核

复核方式：只读解析根代理保存的元数据与本地盘点，不再次SSH、不改原账本、不组装或执行。复核日期：2026-10-23T13:17:17.766595+00:00

结论：下列计数与集合关系复核通过；证据支持“有完整输入/reference候选可供审核”，不支持把118题称为release-ready。

## 复算结果

|项目|独立复算|结论|
|---|---:|---|
|远端设计ID总数/唯一数|630/630|630设计完整覆盖|
|unvalidated_candidate且5类必要文件存在且非空|356|356项具备实体；未做数值资格核验|
|与本地309来源ID交集|309|309全部仍在远端完整候选集合|
|新增来源ID|47|与hash文件47项集合一致：True|
|本地309未在远端完整候选集合|0|无遗漏|
|共同309参考摘要不符|0|仅比较status记录摘要与本地fixed_record，不是重新hash共同309实体|
|新增47必需hash/非空/参考status一致性失败|0|5文件元数据齐全；47reference实算摘要匹配status|
|core有实体候选题|43|含2.1.1/2.1.3；其余来自Titan完整候选|
|新覆盖题号|2.2.11, 2.2.9, 2.4.4|3题|
|core无实体题|22|22，列排除附录|
|FOAMBench有/无正式case题|51/75|51/75，与既有本地逐项盘点一致|
|CFDCodeBench有本地输入/reference题|24|24条既有记录对应路径现存|
|第二章有case审核主表题数|118|43+51+24=118|
|第二章无case排除附录题数|97|22+75=97|

118+97=215，是第二章65基础题+126 FOAMBench+24 CFDCodeBench的候选身份全覆盖，不是第0、1、2、19章整体发行题数。新增47不与原309重复；已有329地方性选样含309未验证+20既有参考，不与100/100/630候选池相加。

逐case实际状态统计：

|状态|数量|
|---|---:|
|unvalidated_candidate|356|
|native_iteration_limit|23|
|needs_attention|9|
|pending_producer_adapter|20|
|stopped_runtime_limit|2|
|held_unmatched_physics|220|

## 证据边界与标注要求

- `case-scan.json`逐case观测日期为`2026-10-23T13:10:49.631658+00:00`；indexed汇总仍为`2026-10-21T09:52:31.417115+00:00`，统计应使用observed_status，缺状态文件时明确回退indexed_status。220 held无产物不能因索引仍有设计而纳入。
- 新增47实算hash来自`new-payload-hashes.json`，时间`2026-10-23T13:14:40.509026+00:00`。这些hash证实观察时文件身份和完整性，不是数值准确性、物理等价或HDF5内部语义的验证。
- `reference-digest-comparison.json`及独立复算均只比较共同309的已记录reference摘要。不能改写为“共同309文件本轮实际hash验证通过”；它们此前本地产物与格式转换证据仍应单独保留。
- 47新增仍位于远端，本轮未搬运。审核页应标“远端完整候选/待回收及资格核验”，不能标成本地离线可执行包。
- 356全部状态是`unvalidated_candidate`。其中350条逐状态未显式写validation、6条写not_performed；全局index明确not_performed。缺validation字段不能默认通过。
- 2.1.1与2.1.3的历史通过证据支持参考资格的不同程度，仍需对应选用版本、题面一致性、执行预算和许可；其他题亦然。
- 因此118主表建议命名“已有case的审核候选”，不得称“可发布118题”“118题已验收”或“118题全部可离线跑”。97附录保留题号/来源及缺case原因，便于用户指认遗漏。
- FOAM51和CC24的存在性计数未因本次Titan新增改变；此审阅未替代其独立数值和许可审计。

## 复核依据

- `case-scan.json`：630条逐case状态与必要文件存在/大小。
- `new-payload-hashes.json`：47条新增实体流式hash记录。
- `reference-digest-comparison.json`：309共同reference记录摘要比对。
- `../ch02.json`：本地65题、126 FOAMBench身份、地方性选样及位置。
- `../cfdcodebench.json`：24项既有本地产物路径。
