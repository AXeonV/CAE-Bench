# 第二章发行筛选检查稿：Titan更新

只读观察时间：2026-10-23 21:10:49 香港时间。逐例读取630个设计对应状态与文件存在性，未启动／停止任务，未下载数值载荷、装配、重算或改正式选样。

**发行版只保留有可用case并通过验收的题。无case不保留空题。** 本稿把“有完整输入／参考、值得后续核验”与“已经可以发行”分开；下表不是118题发行通过声明。开发目录和历史记录继续保留，未删除源码题目。

## 最新范围

|第二章范围|有完整case资产，进入后续核验|无完整可评分case，不纳入本次发行范围|
|---|---:|---:|
|能力题|43题|22题|
|FOAMBench历史题|51题|75题|
|CFDCodeBench历史题|24题|0题|
|合计|118题|97题|

能力题当前有528项完整逻辑候选：2.1.1本地100、2.1.3本地72、Titan当前356（其中309已在本地、47仅远端新定位）。原组合checkout的329项选择是其中子集／表示，不另相加。28项3D历史失败候选和本批274项未完成设计不进入完整候选集合。

**已确认的发行选样：2.1.1与2.1.3均使用既有10例版，各10例、合计20例。** 100例与72例仅为维护池，不能据完整候选数将它们全部纳入发行。两份现有manifest、原选择证据及20例输入／参考均在本地，本轮未改选样或重装配。逐例身份见文末“已确认的10例选样”。

## Titan变化与证据边界

- 当前逐例状态：356 unvalidated_candidate、23 native_iteration_limit、9 needs_attention、20 pending_producer_adapter、2 stopped_runtime_limit、220 held_unmatched_physics。逐例扫描与automation汇总计数一致。
- 356项候选的problem.json、input.h5、reference.h5、grading.json均存在且非空。相对本地309项，用design ID比对得到47项远端新增，分布15题；已有309项的reference记录摘要与本地固定选择证据一致。
- 对新增47项实际流式计算文件SHA256，47份reference摘要均与状态记录一致；这只是完整性证据，没有数值验收。
- 新增覆盖题：2.2.9、2.2.11、2.4.4。其余新增为已有题扩充case。
- 根目录execution-summary仍停在10月21日09:52 UTC（295项候选），automation汇总为10月22日17:42 UTC（356项）。本次结论使用10月23日的逐case观察，不把读取旧索引的时间当索引生成时间。
- 176份含PID的控制器标记本次均未发现对应活跃/proc身份；不据旧running字样重启，也不据此声明整个Titan无其他任务。
- FOAMBench仍保留10月20日停止标记；读取的compact和advanced汇总均早于停止，未发现后续新生产证明。原生结果与51个本地正式评分case分开，不能把剩余75题的原生目录直接算可评分case。

## 有完整case的43道能力题

“本地／远端新增”是位置计数；除2.1.1、2.1.3有既有资格证据外，其余来自本批未验证候选。全部仍需对齐发行题面、参考资格及执行预算。

|题号与题名|完整候选|本地已有|远端新增|旧组合选样|
|---|---:|---:|---:|---:|
|2.1.1 2D 常黏度牛顿流体不可压缩流动稳态分析|100|100|0|10|
|2.1.2 2D 常黏度牛顿流体不可压缩流动瞬态分析|10|10|0|10|
|2.1.3 3D 常黏度牛顿流体不可压缩流动稳态分析|72|72|0|10|
|2.1.4 3D 常黏度牛顿流体不可压缩流动瞬态分析|10|10|0|10|
|2.1.5 2D 非牛顿流体不可压缩流动稳态分析|10|8|2|8|
|2.1.6 2D 非牛顿流体不可压缩流动瞬态分析|10|8|2|8|
|2.1.7 3D 非牛顿流体不可压缩流动稳态分析|9|7|2|7|
|2.1.8 3D 非牛顿流体不可压缩流动瞬态分析|10|8|2|8|
|2.1.9 2D 常黏度牛顿流体等温可压缩流动稳态分析|7|3|4|3|
|2.1.10 2D 常黏度牛顿流体等温可压缩流动瞬态分析|9|5|4|5|
|2.1.11 3D 常黏度牛顿流体等温可压缩流动稳态分析|7|3|4|3|
|2.1.12 3D 常黏度牛顿流体等温可压缩流动瞬态分析|9|5|4|5|
|2.2.1 2D 牛顿流体低速流动与传热稳态分析|10|10|0|10|
|2.2.2 2D 牛顿流体低速流动与传热瞬态分析|10|10|0|10|
|2.2.3 3D 牛顿流体低速流动与传热稳态分析|10|10|0|10|
|2.2.4 3D 牛顿流体低速流动与传热瞬态分析|10|10|0|10|
|2.2.5 2D 无黏可压缩流动稳态分析|10|10|0|10|
|2.2.6 2D 无黏可压缩流动瞬态分析|10|10|0|10|
|2.2.7 3D 无黏可压缩流动稳态分析|10|10|0|10|
|2.2.8 3D 无黏可压缩流动瞬态分析|10|10|0|10|
|2.2.9 2D 牛顿流体可压缩流动与传热稳态分析|4|0|4|0|
|2.2.10 2D 牛顿流体可压缩流动与传热瞬态分析|9|5|4|5|
|2.2.11 3D 牛顿流体可压缩流动与传热稳态分析|3|0|3|0|
|2.2.12 3D 牛顿流体可压缩流动与传热瞬态分析|10|5|5|5|
|2.3.1 2D 不可压缩湍流定常平均分析|8|8|0|8|
|2.3.2 3D 不可压缩湍流定常平均分析|7|7|0|7|
|2.3.3 3D 不可压缩湍流非定常平均分析|10|10|0|10|
|2.3.4 3D 不可压缩湍流尺度解析统计分析|10|10|0|10|
|2.3.5 3D 等温可压缩湍流定常平均分析|7|7|0|7|
|2.4.1 3D 低速湍流传热定常平均分析|9|9|0|9|
|2.4.2 3D 低速湍流传热非定常平均分析|4|4|0|4|
|2.4.3 3D 低速湍流传热尺度解析统计分析|10|10|0|10|
|2.4.4 3D 可压缩湍流传热定常平均分析|4|0|4|0|
|2.5.3 二维不混溶双流体界面瞬态流动|10|10|0|10|
|2.5.4 三维不混溶双流体界面瞬态流动|10|10|0|10|
|2.8.2 可压缩气膜润滑瞬态分析|10|10|0|10|
|2.9.1 全湿浅水稳态分析|3|3|0|3|
|2.9.2 全湿浅水瞬态分析|9|9|0|9|
|2.9.3 干湿变化浅水瞬态分析|9|7|2|7|
|2.10.3 过渡区稀薄气体稳态分析|10|10|0|10|
|2.10.4 自由分子气体稳态分析|10|10|0|10|
|2.11.1 黏弹性流体稳态分析|9|9|0|9|
|2.11.2 黏弹性流体瞬态分析|10|9|1|9|

## 无完整case的22道能力题：不纳入本次发行

|题号与题名|原因|
|---|---|
|2.5.1 二维自由液面瞬态流动|本批10项均held_unmatched_physics；未定位完整可评分case|
|2.5.2 三维自由液面瞬态流动|本批10项均held_unmatched_physics；未定位完整可评分case|
|2.5.5 二维毛细与润湿瞬态流动|本批10项均held_unmatched_physics；未定位完整可评分case|
|2.5.6 三维毛细与润湿瞬态流动|本批10项均held_unmatched_physics；未定位完整可评分case|
|2.6.1 三维稀疏颗粒单向输运|本批10项均held_unmatched_physics；未定位完整可评分case|
|2.6.2 三维颗粒双向动量反馈|本批10项均held_unmatched_physics；未定位完整可评分case|
|2.6.3 三维气泡与液滴分散输运|本批10项均held_unmatched_physics；未定位完整可评分case|
|2.6.4 三维高浓度分散相流动|本批10项均held_unmatched_physics；未定位完整可评分case|
|2.7.1 三维不相变相间热质交换|本批10项均held_unmatched_physics；未定位完整可评分case|
|2.7.2 二维蒸发冷凝界面流动|本批10项均held_unmatched_physics；未定位完整可评分case|
|2.7.3 三维均匀混合沸腾流动|本批10项均held_unmatched_physics；未定位完整可评分case|
|2.7.4 三维等温空化流动|本批10项均held_unmatched_physics；未定位完整可评分case|
|2.7.5 二维熔化凝固伴随流动|本批10项均held_unmatched_physics；未定位完整可评分case|
|2.8.1 等温液体薄膜润滑稳态分析|本批10项均held_unmatched_physics；未定位完整可评分case|
|2.8.3 非等温液体薄膜瞬态分析|本批10项均held_unmatched_physics；未定位完整可评分case|
|2.8.4 广义牛顿液体薄膜稳态分析|本批10项均held_unmatched_physics；未定位完整可评分case|
|2.9.4 两层深度平均流动瞬态分析|本批10项均held_unmatched_physics；未定位完整可评分case|
|2.10.1 等温滑移气体稳态分析|本批10项均held_unmatched_physics；未定位完整可评分case|
|2.10.2 非等温滑移气体稳态分析|本批10项均held_unmatched_physics；未定位完整可评分case|
|2.11.3 触变结构演化瞬态分析|本批10项均held_unmatched_physics；未定位完整可评分case|
|2.11.4 非等温广义牛顿流体瞬态分析|本批10项均held_unmatched_physics；未定位完整可评分case|
|2.11.5 非等温黏弹性流体瞬态分析|本批10项均held_unmatched_physics；未定位完整可评分case|

## 新定位47项case

|题号|设计ID|工况|
|---|---|---|
|2.1.5|`ch02-2-1-5-01-power_law_channel`|入口发展通道；剪切变稀截断幂律、速度入口及完整储槽牵引出口；幂律有效剪切区和开边界|
|2.1.5|`ch02-2-1-5-06-power_law_traction`|直通道；截断幂律、两端完整矢量牵引；低高剪切截断及牵引条件|
|2.1.6|`ch02-2-1-6-01-power_law_channel`|入口发展通道；剪切变稀截断幂律、速度入口及完整储槽牵引出口；幂律有效剪切区和开边界|
|2.1.6|`ch02-2-1-6-06-power_law_traction`|直通道；截断幂律、两端完整矢量牵引；低高剪切截断及牵引条件|
|2.1.7|`ch02-2-1-7-01-power_law_channel`|入口发展通道；剪切变稀截断幂律、速度入口及完整储槽牵引出口；幂律有效剪切区和开边界|
|2.1.7|`ch02-2-1-7-06-power_law_traction`|直通道；截断幂律、两端完整矢量牵引；低高剪切截断及牵引条件|
|2.1.8|`ch02-2-1-8-01-power_law_channel`|入口发展通道；剪切变稀截断幂律、速度入口及完整储槽牵引出口；幂律有效剪切区和开边界|
|2.1.8|`ch02-2-1-8-06-power_law_traction`|直通道；截断幂律、两端完整矢量牵引；低高剪切截断及牵引条件|
|2.1.9|`ch02-2-1-9-05-ideal_obstacle_flux`|偏心方柱通道；理想气体、流量入口加给定密度、完整储槽牵引出口；内边界、流率归一化和入口密度|
|2.1.9|`ch02-2-1-9-08-ideal_symmetry_channel`|对称半通道；理想气体、速度与密度入口、对称面及完整储槽牵引出口；对称边界、压力与入口密度共同约束|
|2.1.9|`ch02-2-1-9-09-ideal_density_initial_or_inlet`|矩形通道；理想气体、非零体黏度、空间非均匀入口密度和完整储槽牵引出口；密度输入、体黏度与压缩性调整|
|2.1.9|`ch02-2-1-9-10-barotropic_network`|带双障碍物的多入口通道；线性正压、不同密度的两个速度入口、储槽牵引出口；多入口质量供给、状态关系与回流排除|
|2.1.10|`ch02-2-1-10-04-barotropic_periodic`|周期通道；线性正压、无压跳周期端面、体加速度驱动、非零体黏度；可压缩周期与体力驱动|
|2.1.10|`ch02-2-1-10-05-ideal_obstacle_flux`|偏心方柱通道；理想气体、流量入口加给定密度、完整储槽牵引出口；内边界、流率归一化和入口密度|
|2.1.10|`ch02-2-1-10-08-ideal_symmetry_channel`|对称半通道；理想气体、速度与密度入口、对称面及完整储槽牵引出口；对称边界、压力与入口密度共同约束|
|2.1.10|`ch02-2-1-10-10-barotropic_network`|带双障碍物的多入口通道；线性正压、不同密度的两个速度入口、储槽牵引出口；多入口质量供给、状态关系与回流排除|
|2.1.11|`ch02-2-1-11-05-ideal_obstacle_flux`|偏心方柱通道；理想气体、流量入口加给定密度、完整储槽牵引出口；内边界、流率归一化和入口密度|
|2.1.11|`ch02-2-1-11-08-ideal_symmetry_channel`|对称半通道；理想气体、速度与密度入口、对称面及完整储槽牵引出口；对称边界、压力与入口密度共同约束|
|2.1.11|`ch02-2-1-11-09-ideal_density_initial_or_inlet`|矩形通道；理想气体、非零体黏度、空间非均匀入口密度和完整储槽牵引出口；密度输入、体黏度与压缩性调整|
|2.1.11|`ch02-2-1-11-10-barotropic_network`|带双障碍物的多入口通道；线性正压、不同密度的两个速度入口、储槽牵引出口；多入口质量供给、状态关系与回流排除|
|2.1.12|`ch02-2-1-12-04-barotropic_periodic`|周期通道；线性正压、无压跳周期端面、体加速度驱动、非零体黏度；可压缩周期与体力驱动|
|2.1.12|`ch02-2-1-12-05-ideal_obstacle_flux`|偏心方柱通道；理想气体、流量入口加给定密度、完整储槽牵引出口；内边界、流率归一化和入口密度|
|2.1.12|`ch02-2-1-12-09-ideal_density_initial_or_inlet`|矩形通道；理想气体、非零体黏度、相容非均匀初密度与速度/密度入口、完整储槽牵引出口；密度输入、体黏度与压缩性调整|
|2.1.12|`ch02-2-1-12-10-barotropic_network`|带双障碍物的多入口通道；线性正压、不同密度的两个速度入口、储槽牵引出口；多入口质量供给、状态关系与回流排除|
|2.2.9|`ch02-2-2-9-01-thermal_cavity`|方盒；静壁、左右温差；封闭气体质量与非均匀密度|
|2.2.9|`ch02-2-2-9-06-heated_obstacle`|偏心方柱盒；内柱热壁、外壁冷却；内孔热交换|
|2.2.9|`ch02-2-2-9-07-nonuniform_source`|矩形盒；局部体热源、冷却壁；源项空间分布|
|2.2.9|`ch02-2-2-9-09-bulk_viscosity`|矩形盒；独立非零体黏度、壁面驱动及冷热壁；独立体黏度|
|2.2.10|`ch02-2-2-10-02-heated_lid`|方盒；运动顶壁和温差；可压缩热黏性耦合|
|2.2.10|`ch02-2-2-10-04-shear_heating`|矩形盒；上下反向壁、壁面定温；黏性耗散|
|2.2.10|`ch02-2-2-10-05-thermal_flux`|宽盒；底壁热流、顶壁定温；导热通量边界|
|2.2.10|`ch02-2-2-10-09-bulk_viscosity`|矩形盒；独立非零体黏度、相容低幅声学初态和热壁；独立体黏度|
|2.2.11|`ch02-2-2-11-06-heated_obstacle`|偏心方柱盒；内柱热壁、外壁冷却；内孔热交换|
|2.2.11|`ch02-2-2-11-07-nonuniform_source`|矩形盒；局部体热源、冷却壁；源项空间分布|
|2.2.11|`ch02-2-2-11-09-bulk_viscosity`|矩形盒；独立非零体黏度、壁面驱动及冷热壁；独立体黏度|
|2.2.12|`ch02-2-2-12-02-heated_lid`|方盒；运动顶壁和温差；可压缩热黏性耦合|
|2.2.12|`ch02-2-2-12-04-shear_heating`|矩形盒；上下反向壁、壁面定温；黏性耗散|
|2.2.12|`ch02-2-2-12-05-thermal_flux`|宽盒；底壁热流、顶壁定温；导热通量边界|
|2.2.12|`ch02-2-2-12-06-heated_obstacle`|偏心方柱盒；内柱热壁、外壁冷却；内孔热交换|
|2.2.12|`ch02-2-2-12-09-bulk_viscosity`|矩形盒；独立非零体黏度、相容低幅声学初态和热壁；独立体黏度|
|2.4.4|`ch02-2-4-4-01-thermal_cavity`|方盒；静壁、左右温差；封闭气体质量与非均匀密度|
|2.4.4|`ch02-2-4-4-06-heated_obstacle`|偏心方柱盒；内柱热壁、外壁冷却；内孔热交换|
|2.4.4|`ch02-2-4-4-07-nonuniform_source`|矩形盒；局部体热源、冷却壁；源项空间分布|
|2.4.4|`ch02-2-4-4-09-bulk_viscosity`|矩形盒；独立非零体黏度、壁面驱动及冷热壁；独立体黏度|
|2.9.3|`ch02-2-9-3-05-island`|有岛干床池；坝溃来流；绕岛分叉|
|2.9.3|`ch02-2-9-3-10-compound_topography`|分叉水道；床台阶与坝溃；地形控制的分区干湿|
|2.11.2|`ch02-2-11-2-07-inlet_memory`|直通道；速度入口给定SPD构象、完整牵引出口和自然记忆流出；入口构象不能省略；无回流、不添加应力扩散|

## 43题逐例候选：供用户核对

以下列出完整候选，不自动把全部候选写入正式选样。新增仅远端项没有重复下载；逐项位置与证据见同目录JSON。

### 2.1.1 2D 常黏度牛顿流体不可压缩流动稳态分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`case-026d4fd42eeba2d5268e1be8` 001|force-island-chamber|本地已有；历史通过，发行待验收|
|`case-e8f85c3a1f5574b5b7210265` 002|force-split-recess|本地已有；历史通过，发行待验收|
|`case-4c8211e10cfe6755bdc61e0e` 003|force-three-ribs|本地已有；历史通过，发行待验收|
|`case-0e6015c13e8f493dbf620799` 004|four-wall-circulation|本地已有；历史通过，发行待验收|
|`case-dbefd5f506818454526b5154` 005|lid-central-pedestal|本地已有；历史通过，发行待验收|
|`case-3fe4488e94450f59afd66166` 006|lid-cross-chamber|本地已有；历史通过，发行待验收|
|`case-fda4785a3d9d80b6a0822fb6` 007|lid-L-chamber|本地已有；历史通过，发行待验收|
|`case-68c02a8d2b43c88ee8b57f70` 008|lid-offset-baffle|本地已有；历史通过，发行待验收|
|`case-9b46104936e50028823b2557` 009|lid-serpentine-chamber|本地已有；历史通过，发行待验收|
|`case-546a59784b18a631bf12dd6a` 010|lid-square|本地已有；历史通过，发行待验收|
|`case-3332523b90c9f1044dc4b9af` 011|lid-square-obstacle|本地已有；历史通过，发行待验收|
|`case-a738752d73231f6a64c0f942` 012|lid-staggered-islands|本地已有；历史通过，发行待验收|
|`case-4585e0421691b3f39b24058f` 013|lid-step-floor|本地已有；历史通过，发行待验收|
|`case-f9894cc19c74db756546b5a9` 014|lid-T-chamber|本地已有；历史通过，发行待验收|
|`case-cfc58477001d526050bc651f` 015|lid-two-obstacles|本地已有；历史通过，发行待验收|
|`case-8f50767a53296e3d12436c21` 016|opposed-lids|本地已有；历史通过，发行待验收|
|`case-154ee75bd3aeb1ff6008c91b` 017|opposed-side-walls|本地已有；历史通过，发行待验收|
|`case-5b87a66b28e481e82ab5cf2b` 018|rotational-force-square|本地已有；历史通过，发行待验收|
|`case-a50104253013998d8905d65e` 019|shear-force-slip-channel|本地已有；历史通过，发行待验收|
|`case-f5d5b32cc81a01f07530987b` 020|side-driven|本地已有；历史通过，发行待验收|
|`case-fc5ed9b550c0418c10b5d161` 021|x80-bottom-comb-competing|本地已有；历史通过，发行待验收|
|`case-23fd82edbbe47d2325bff5ed` 022|x80-bottom-comb-wall|本地已有；历史通过，发行待验收|
|`case-6647aeed6a564bda504a7345` 023|x80-central-well-competing|本地已有；历史通过，发行待验收|
|`case-a69c2cec27ba9da8143edf4f` 024|x80-central-well-wall|本地已有；历史通过，发行待验收|
|`case-17757fb82885e45077f80fee` 025|x80-corner-cut-island-competing|本地已有；历史通过，发行待验收|
|`case-803a3e0972f9b329f35639fb` 026|x80-corner-cut-island-wall|本地已有；历史通过，发行待验收|
|`case-b980d6a66334bead6def4590` 027|x80-deep-left-pocket-competing|本地已有；历史通过，发行待验收|
|`case-56b6457f16a1af6cd8f02989` 028|x80-deep-left-pocket-wall|本地已有；历史通过，发行待验收|
|`case-110df023e481bc17775eff31` 029|x80-diagonal-gaps-competing|本地已有；历史通过，发行待验收|
|`case-509d7d871cfff5c2da20529d` 030|x80-diagonal-gaps-wall|本地已有；历史通过，发行待验收|
|`case-a1f7fdd0dfe309d65127fc9f` 031|x80-double-shelf-competing|本地已有；历史通过，发行待验收|
|`case-223669060037f94830404f7f` 032|x80-double-shelf-wall|本地已有；历史通过，发行待验收|
|`case-6577cfd3bc8083c0b41627ca` 033|x80-downward-staircase-competing|本地已有；历史通过，发行待验收|
|`case-686db303486eb02d63433dba` 034|x80-downward-staircase-wall|本地已有；历史通过，发行待验收|
|`case-c4e3a9e178e378fb34f387b9` 035|x80-eccentric-ring-competing|本地已有；历史通过，发行待验收|
|`case-6b627ffc83019a65984f8547` 036|x80-eccentric-ring-wall|本地已有；历史通过，发行待验收|
|`case-d5816f16c18ddb5c2cf50913` 037|x80-exact-adverse-couette-poiseuille|本地已有；历史通过，发行待验收|
|`case-6628b5477d34975cb5731b7f` 038|x80-exact-aiding-couette-poiseuille|本地已有；历史通过，发行待验收|
|`case-3f554b05894113d100a49db1` 039|x80-exact-co-moving-plates|本地已有；历史通过，发行待验收|
|`case-608f00ddf8c82077f0f1f19a` 040|x80-exact-couette-inlet-traction|本地已有；历史通过，发行待验收|
|`case-17e0b918ec49aafee4f374df` 041|x80-exact-couette-periodic|本地已有；历史通过，发行待验收|
|`case-3d624f9d364a926df88ce6bd` 042|x80-exact-counter-couette|本地已有；历史通过，发行待验收|
|`case-f3722c772c68eac103c06afe` 043|x80-exact-half-channel-slip|本地已有；历史通过，发行待验收|
|`case-38351d24077b5a3c28b49210` 044|x80-exact-half-channel-symmetry|本地已有；历史通过，发行待验收|
|`case-a5773a7fb830de76abafd83a` 045|x80-exact-hydrostatic-concave|本地已有；历史通过，发行待验收|
|`case-afbf4209dff6115ee3c9f591` 046|x80-exact-hydrostatic-island|本地已有；历史通过，发行待验收|
|`case-8dffd16586459938e9c4f076` 047|x80-exact-hydrostatic-reservoir|本地已有；历史通过，发行待验收|
|`case-6d638485fa905df3fb2e0439` 048|x80-exact-plug-flow-rate|本地已有；历史通过，发行待验收|
|`case-a7035697332f240644234729` 049|x80-exact-plug-pressure-outlet|本地已有；历史通过，发行待验收|
|`case-8419ad4dbae71014b508de13` 050|x80-exact-split-flow-rate|本地已有；历史通过，发行待验收|
|`case-731c251b36c11ca8ede9fa39` 051|x80-exact-traction-poiseuille|本地已有；历史通过，发行待验收|
|`case-2cbdc42d6ed8d1be7fe1280c` 052|x80-exact-vertical-poiseuille|本地已有；历史通过，发行待验收|
|`case-7ca4b8b904a1abe7cbe5f8d7` 053|x80-hanging-comb-competing|本地已有；历史通过，发行待验收|
|`case-03a49bce40c650662366147c` 054|x80-hanging-comb-wall|本地已有；历史通过，发行待验收|
|`case-3a14d5b16c7cb17af36cf3ef` 055|x80-horizontal-neck-competing|本地已有；历史通过，发行待验收|
|`case-651fefa00c8fe8c9e0ddbf3f` 056|x80-horizontal-neck-wall|本地已有；历史通过，发行待验收|
|`case-3335010496540e7d274991ee` 057|x80-hourglass-competing|本地已有；历史通过，发行待验收|
|`case-5470a6a07368d0d96d632b40` 058|x80-hourglass-wall|本地已有；历史通过，发行待验收|
|`case-344712a9e42e7905fd2d80a9` 059|x80-inlet-shaped-channel|本地已有；历史通过，发行待验收|
|`case-d69473fe7a7a4402f2295983` 060|x80-interdigitated-competing|本地已有；历史通过，发行待验收|
|`case-d327652d04194c229f139174` 061|x80-interdigitated-wall|本地已有；历史通过，发行待验收|
|`case-3bffa25c48a0c2a4e8a08f80` 062|x80-lower-arch-competing|本地已有；历史通过，发行待验收|
|`case-50a08167d289e354f3081335` 063|x80-lower-arch-wall|本地已有；历史通过，发行待验收|
|`case-402fe059be03339829c3725a` 064|x80-periodic-central-island|本地已有；历史通过，发行待验收|
|`case-d6f78769504bde4e0ba3b2df` 065|x80-periodic-counter-wall|本地已有；历史通过，发行待验收|
|`case-89cbff12aa587b6f1b3d2a49` 066|x80-periodic-floor-rib|本地已有；历史通过，发行待验收|
|`case-1b1efe546c3b870adfbc370d` 067|x80-periodic-slip-ceiling|本地已有；历史通过，发行待验收|
|`case-bf9684bdbfa174716ffecea6` 068|x80-periodic-staggered-ribs|本地已有；历史通过，发行待验收|
|`case-0cb2338cf9a194d60e7db587` 069|x80-periodic-straight|本地已有；历史通过，发行待验收|
|`case-3631a3d44fc61fd1a91466f0` 070|x80-plus-offset-competing|本地已有；历史通过，发行待验收|
|`case-82748be4a746b95e0f8b1f26` 071|x80-plus-offset-wall|本地已有；历史通过，发行待验收|
|`case-c6e09f60d73603abd63bccf5` 072|x80-square-ring-competing|本地已有；历史通过，发行待验收|
|`case-1e6d8f2c06b3ce7ce20f8aab` 073|x80-square-ring-wall|本地已有；历史通过，发行待验收|
|`case-2e375f460b651ceda6acbd29` 074|x80-staircase-competing|本地已有；历史通过，发行待验收|
|`case-c5b8be2128502cf2df845403` 075|x80-staircase-wall|本地已有；历史通过，发行待验收|
|`case-e98910680d81afb80559e136` 076|x80-stepped-island-competing|本地已有；历史通过，发行待验收|
|`case-effc11006e129cf3ec747b3f` 077|x80-stepped-island-wall|本地已有；历史通过，发行待验收|
|`case-0c946d6bc3267aedabe2bc79` 078|x80-tall-narrow-competing|本地已有；历史通过，发行待验收|
|`case-a32bd96d9f0fa177fdb9a38a` 079|x80-tall-narrow-wall|本地已有；历史通过，发行待验收|
|`case-676be6851d7a954885f6233c` 080|x80-thin-horizontal-island-competing|本地已有；历史通过，发行待验收|
|`case-eb539a9c32a0fe9f2fe20cf6` 081|x80-thin-horizontal-island-wall|本地已有；历史通过，发行待验收|
|`case-3cf72243c209b9d2ab24b3ef` 082|x80-thin-vertical-island-competing|本地已有；历史通过，发行待验收|
|`case-3e9ba2526d10b6a96145a96a` 083|x80-thin-vertical-island-wall|本地已有；历史通过，发行待验收|
|`case-4901543106f398d4d543057e` 084|x80-three-chambers-competing|本地已有；历史通过，发行待验收|
|`case-f8dc780bc4ca4467d75e37a1` 085|x80-three-chambers-wall|本地已有；历史通过，发行待验收|
|`case-5e6dd08e82b5ff5d2613b557` 086|x80-three-islands-competing|本地已有；历史通过，发行待验收|
|`case-f1e06a271c8a51cd99834dd3` 087|x80-three-islands-wall|本地已有；历史通过，发行待验收|
|`case-aed170fafb71f353ffed76d1` 088|x80-three-lobes-competing|本地已有；历史通过，发行待验收|
|`case-0cb432663d477af7dc68ec8c` 089|x80-three-lobes-wall|本地已有；历史通过，发行待验收|
|`case-09de4f96e14d87df43effaab` 090|x80-twin-wells-competing|本地已有；历史通过，发行待验收|
|`case-085a11cea1b7bdc51bfaec36` 091|x80-twin-wells-wall|本地已有；历史通过，发行待验收|
|`case-a21714c71efaedb35e8967a9` 092|x80-two-window-competing|本地已有；历史通过，发行待验收|
|`case-e6d3e759fad0daa1ff685eb3` 093|x80-two-window-wall|本地已有；历史通过，发行待验收|
|`case-aab4aed7b29cacfc32905900` 094|x80-unequal-twin-islands-competing|本地已有；历史通过，发行待验收|
|`case-6669d922717886c3221baef8` 095|x80-unequal-twin-islands-wall|本地已有；历史通过，发行待验收|
|`case-b0f4e65de66124c6c696ef7a` 096|x80-upper-arch-competing|本地已有；历史通过，发行待验收|
|`case-d020c56f473ffd528ccac933` 097|x80-upper-arch-wall|本地已有；历史通过，发行待验收|
|`case-e1a4245e9c00a68ffe4b7e7b` 098|x80-upper-shelf-competing|本地已有；历史通过，发行待验收|
|`case-f677d893f2ea9b9185d6a8f0` 099|x80-upper-shelf-wall|本地已有；历史通过，发行待验收|
|`case-5bd099d8aa922c7830cdc653` 100|x80-wide-shallow-competing|本地已有；历史通过，发行待验收|

### 2.1.2 2D 常黏度牛顿流体不可压缩流动瞬态分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-1-2-01-lid_start` |方腔；顶壁从静止线性加速；黏性启动与主涡形成|本地已有；本批未验证|
|`ch02-2-1-2-02-velocity_reservoir` |带偏心方柱直通道；速度入口线性启动、完整储槽牵引出口、无滑移侧壁；开边界及压力出口的完整牵引语义|本地已有；本批未验证|
|`ch02-2-1-2-03-traction_channel` |直通道；两端显式总牵引的分段线性压差驱动；完整矢量牵引、无额外压力规范|本地已有；本批未验证|
|`ch02-2-1-2-04-periodic_acceleration` |周期直通道；周期端面、无滑移壁、时变全域加速度；周期无压力跳跃，体力驱动及均值压力规范|本地已有；本批未验证|
|`ch02-2-1-2-05-symmetry_channel` |通道对称半域；速度入口、牵引出口、一个平面对称边界；对称重建与无回流保证|本地已有；本批未验证|
|`ch02-2-1-2-06-slip_vortex` |全滑移方盒；满足无穿透及零切向牵引的非零涡初态；滑移和物理初态，不用零初态覆盖全部瞬态|本地已有；本批未验证|
|`ch02-2-1-2-07-spatial_force` |非对称封闭域；空间非均匀非保守体加速度，时间按previous分段保持；静壁、点压力规范；分布源项、非线性时间采样和点规范；给定体力不补造其他源|本地已有；本批未验证|
|`ch02-2-1-2-08-obstacle_flux` |直通道；严格正流量和后续非均匀shape；滑移侧壁；相容穿流初速度；流量全边界归一化、内孔、真实面平均与整体流率/载荷|本地已有；本批未验证|
|`ch02-2-1-2-09-pulse` |方腔；顶壁加速、保持、减速至静止；驱动撤去后的涡衰减；稳态题改为分段顶壁驱动|本地已有；本批未验证|
|`ch02-2-1-2-10-reversal` |方腔；顶壁正向启动后反向；流向反转的记忆；稳态题改为不等速反向双壁|本地已有；本批未验证|

### 2.1.3 3D 常黏度牛顿流体不可压缩流动稳态分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`case-e215683cc2c314b54af53642` 001-hydrostatic-01|hydrostatic；box；tet；pressure=absolute；gauge=mean|本地已有；历史通过，发行待验收|
|`case-4cf23c0b75352df29edd6bb9` 002-hydrostatic-02|hydrostatic；box；tet；pressure=gauge；gauge=point|本地已有；历史通过，发行待验收|
|`case-6287a7bc3c2d414a084f27e9` 003-hydrostatic-03|hydrostatic；box；tet；pressure=gauge；gauge=mean|本地已有；历史通过，发行待验收|
|`case-e45467460b31147a0cc41f06` 004-hydrostatic-04|hydrostatic；box；tet；pressure=gauge；gauge=point|本地已有；历史通过，发行待验收|
|`case-0c4687297f0a1e1a801c9880` 005-hydrostatic-05|hydrostatic；box；tet；pressure=gauge；gauge=mean|本地已有；历史通过，发行待验收|
|`case-c3e81be86316515284b89014` 006-hydrostatic-06|hydrostatic；box；tet；pressure=absolute；gauge=point|本地已有；历史通过，发行待验收|
|`case-9392126e5caad6bbc5a9f0ea` 007-hydrostatic-07|hydrostatic；box；tet；pressure=gauge；gauge=mean|本地已有；历史通过，发行待验收|
|`case-36afa3491e509a571b67bce3` 008-hydrostatic-08|hydrostatic；box；tet；pressure=gauge；gauge=point|本地已有；历史通过，发行待验收|
|`case-e587edcbe1c11f1f6e28ccd8` 009-hydrostatic-09|hydrostatic；box；tet；pressure=gauge；gauge=mean|本地已有；历史通过，发行待验收|
|`case-3545a453e1b103065922d243` 010-hydrostatic-10|hydrostatic；box；tet；pressure=gauge；gauge=point|本地已有；历史通过，发行待验收|
|`case-9cb786d811ef214efaf8ef2f` 011-hydrostatic-11|hydrostatic；box；tet；pressure=absolute；gauge=mean|本地已有；历史通过，发行待验收|
|`case-96e28f928b8594aeb312fe48` 012-hydrostatic-12|hydrostatic；box；tet；pressure=gauge；gauge=point|本地已有；历史通过，发行待验收|
|`case-cb22136ba96b6bf7e6b4c638` 013-hydrostatic-13|hydrostatic；box；tet；pressure=gauge；gauge=mean|本地已有；历史通过，发行待验收|
|`case-797502d7d9f2ab18e632aea6` 014-hydrostatic-14|hydrostatic；box；tet；pressure=gauge；gauge=point|本地已有；历史通过，发行待验收|
|`case-85f7cdc19198b823e3cca6af` 015-hydrostatic-15|hydrostatic；box；tet；pressure=gauge；gauge=mean|本地已有；历史通过，发行待验收|
|`case-20fd0bd9dc7aa67d30d5bac3` 016-hydrostatic-16|hydrostatic；box；tet；pressure=absolute；gauge=point|本地已有；历史通过，发行待验收|
|`case-ccf8ffd3f6cc87a87f35ae24` 017-hydrostatic-17|hydrostatic；box；tet；pressure=gauge；gauge=mean|本地已有；历史通过，发行待验收|
|`case-7929e5931fb708f8e70982ab` 018-hydrostatic-18|hydrostatic；box；tet；pressure=gauge；gauge=point|本地已有；历史通过，发行待验收|
|`case-87f11108f4a541d74fa90196` 019-couette-01|couette；box；tet；pressure=absolute；gauge=mean|本地已有；历史通过，发行待验收|
|`case-8e008ec86963316e2c79d864` 020-couette-02|couette；box；hex；pressure=gauge；gauge=point|本地已有；历史通过，发行待验收|
|`case-7268913aaa147c90a547f4b3` 021-couette-03|couette；box；prism；pressure=gauge；gauge=mean|本地已有；历史通过，发行待验收|
|`case-c1120600e56502bb4c476355` 022-couette-04|couette；box；pyramid；pressure=gauge；gauge=point|本地已有；历史通过，发行待验收|
|`case-86ee50313dc2a0b4fa9fcb46` 023-couette-05|couette；box；mixed；pressure=gauge；gauge=mean|本地已有；历史通过，发行待验收|
|`case-1eeb1aa3bd56da718c44afdb` 024-couette-06|couette；box；tet；pressure=absolute；gauge=point|本地已有；历史通过，发行待验收|
|`case-ac13853772b0dbe4a4048360` 025-couette-07|couette；box；hex；pressure=gauge；gauge=mean|本地已有；历史通过，发行待验收|
|`case-9c67f2391da9f79a2027e884` 026-couette-08|couette；box；prism；pressure=gauge；gauge=point|本地已有；历史通过，发行待验收|
|`case-ae2dfdaa2f67a3dca27b7690` 027-couette-09|couette；box；pyramid；pressure=gauge；gauge=mean|本地已有；历史通过，发行待验收|
|`case-0bbf51d4fd563de513a6cd6c` 028-couette-10|couette；box；mixed；pressure=gauge；gauge=point|本地已有；历史通过，发行待验收|
|`case-d3c6ffd92f8c2adc46713614` 029-couette-11|couette；box；tet；pressure=absolute；gauge=mean|本地已有；历史通过，发行待验收|
|`case-e99f37a0e69054be6b5d77d1` 030-couette-12|couette；box；hex；pressure=gauge；gauge=point|本地已有；历史通过，发行待验收|
|`case-628cb96a66692e3af0377909` 031-couette-13|couette；box；prism；pressure=gauge；gauge=mean|本地已有；历史通过，发行待验收|
|`case-b492b197eeb7c5b642d6590e` 032-couette-14|couette；box；pyramid；pressure=gauge；gauge=point|本地已有；历史通过，发行待验收|
|`case-79b044a49812b3c3d80dc7a9` 033-couette-15|couette；box；tet；pressure=gauge；gauge=mean|本地已有；历史通过，发行待验收|
|`case-1ce0d16bfc31d876d5b1d318` 034-couette-16|couette；box；tet；pressure=absolute；gauge=point|本地已有；历史通过，发行待验收|
|`case-b24e9a4fe7f7eec77272c25e` 035-couette-17|couette；box；tet；pressure=gauge；gauge=mean|本地已有；历史通过，发行待验收|
|`case-44d99efd5ffa3250b83dc972` 036-couette-18|couette；box；tet；pressure=gauge；gauge=point|本地已有；历史通过，发行待验收|
|`case-e5e7eb066b237fd30a2d2b5c` 037-couette-19|couette；box；tet；pressure=gauge；gauge=mean|本地已有；历史通过，发行待验收|
|`case-8545b22af3538923f203c59c` 038-couette-20|couette；box；tet；pressure=gauge；gauge=point|本地已有；历史通过，发行待验收|
|`case-7a11ab77ce9cb54ba25a06d8` 039-periodic-duct-01|periodic-duct；box；tet；pressure=absolute；gauge=mean|本地已有；历史通过，发行待验收|
|`case-bd7f7aabeffc09aca3312536` 040-periodic-duct-02|periodic-duct；box；hex；pressure=gauge；gauge=point|本地已有；历史通过，发行待验收|
|`case-342bf13fa398c5baecb3bd42` 041-periodic-duct-03|periodic-duct；box；prism；pressure=gauge；gauge=mean|本地已有；历史通过，发行待验收|
|`case-432a2679f0b5a330c1160dd8` 042-periodic-duct-04|periodic-duct；box；pyramid；pressure=gauge；gauge=point|本地已有；历史通过，发行待验收|
|`case-9c4f48cfb074b831f9e5af55` 043-periodic-duct-05|periodic-duct；box；mixed；pressure=gauge；gauge=mean|本地已有；历史通过，发行待验收|
|`case-128fd80cf2d00f22c0375bd1` 044-periodic-duct-06|periodic-duct；box；tet；pressure=absolute；gauge=point|本地已有；历史通过，发行待验收|
|`case-38773f4e231f030e0b973bea` 045-periodic-duct-07|periodic-duct；box；hex；pressure=gauge；gauge=mean|本地已有；历史通过，发行待验收|
|`case-6e6934e22a01c544ca958d81` 046-periodic-duct-08|periodic-duct；box；prism；pressure=gauge；gauge=point|本地已有；历史通过，发行待验收|
|`case-b59b4cfc7a10bc23c170ec8b` 047-periodic-duct-09|periodic-duct；box；pyramid；pressure=gauge；gauge=mean|本地已有；历史通过，发行待验收|
|`case-4da7a5b23fd6113cba412fb5` 048-periodic-duct-10|periodic-duct；box；mixed；pressure=gauge；gauge=point|本地已有；历史通过，发行待验收|
|`case-346db4baabaaa684cdd44688` 049-periodic-duct-11|periodic-duct；box；tet；pressure=absolute；gauge=mean|本地已有；历史通过，发行待验收|
|`case-ea9f220baef008a2eea870b2` 050-periodic-duct-12|periodic-duct；box；hex；pressure=gauge；gauge=point|本地已有；历史通过，发行待验收|
|`case-b72d1c5aa4e81c3b59032258` 059-cavity-01|cavity；box；tet；pressure=absolute；gauge=mean|本地已有；历史通过，发行待验收|
|`case-bfe13e8f4e227f3d8f19891c` 060-cavity-02|cavity；box；tet；pressure=gauge；gauge=point|本地已有；历史通过，发行待验收|
|`case-61f5824c31d2f72af25b5535` 063-cavity-05|cavity；box；tet；pressure=gauge；gauge=mean|本地已有；历史通过，发行待验收|
|`case-da121ec73505dea5c73c8469` 064-cavity-06|cavity；box；tet；pressure=absolute；gauge=point|本地已有；历史通过，发行待验收|
|`case-d5249aa45670eb36bfc815c7` 065-cavity-07|cavity；box；tet；pressure=gauge；gauge=mean|本地已有；历史通过，发行待验收|
|`case-9c65c732e1d848594cc9a9a6` 068-cavity-10|cavity；box；tet；pressure=gauge；gauge=point|本地已有；历史通过，发行待验收|
|`case-eafeb2172a7d5e4888d59edc` 071-cavity-13|cavity；box；tet；pressure=gauge；gauge=mean|本地已有；历史通过，发行待验收|
|`case-e4a9a3f78ca2602fca78d920` 072-cavity-14|cavity；box；tet；pressure=gauge；gauge=point|本地已有；历史通过，发行待验收|
|`case-b098c03a1e9c6a6ed4bcce0e` 075-cavity-17|cavity；obstacle；tet；pressure=gauge；gauge=mean|本地已有；历史通过，发行待验收|
|`case-41dde335a20a54def6988689` 079-cavity-21|cavity；obstacle；tet；pressure=absolute；gauge=mean|本地已有；历史通过，发行待验收|
|`case-2f6e0ee2802c7e41ba0dadf1` 083-plug-01|plug；box；tet；pressure=absolute；gauge=mean|本地已有；历史通过，发行待验收|
|`case-9f21bdd96efd2e6fcc59f801` 085-plug-03|plug；box；prism；pressure=gauge；gauge=mean|本地已有；历史通过，发行待验收|
|`case-449ea88b437e84552cfc36c6` 086-plug-04|plug；box；pyramid；pressure=gauge；gauge=point|本地已有；历史通过，发行待验收|
|`case-e0206150a584aa1a40f0923c` 088-plug-06|plug；box；tet；pressure=absolute；gauge=point|本地已有；历史通过，发行待验收|
|`case-affdcd32d37a0501ea23070f` 089-plug-07|plug；box；hex；pressure=gauge；gauge=mean|本地已有；历史通过，发行待验收|
|`case-111820673fb7615988888c64` 091-plug-09|plug；box；pyramid；pressure=gauge；gauge=mean|本地已有；历史通过，发行待验收|
|`case-4193a6c3607bdeb91e588fea` 092-plug-10|plug；box；mixed；pressure=gauge；gauge=point|本地已有；历史通过，发行待验收|
|`case-b26cf91c2847b4e18aec1525` 094-plug-12|plug；box；hex；pressure=gauge；gauge=point|本地已有；历史通过，发行待验收|
|`case-cf78f6dd1048dd908a8d69be` 095-plug-13|plug；box；prism；pressure=gauge；gauge=mean|本地已有；历史通过，发行待验收|
|`case-447d9c0ade66820c76b29c7a` 097-plug-15|plug；box；mixed；pressure=gauge；gauge=mean|本地已有；历史通过，发行待验收|
|`case-efa180962537a915b01677ec` 098-plug-16|plug；box；tet；pressure=absolute；gauge=point|本地已有；历史通过，发行待验收|
|`case-72f17662567296336d22707a` 100-plug-18|plug；box；prism；pressure=gauge；gauge=point|本地已有；历史通过，发行待验收|

### 2.1.4 3D 常黏度牛顿流体不可压缩流动瞬态分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-1-4-01-lid_start` |方腔；顶壁从静止线性加速；黏性启动与主涡形成|本地已有；本批未验证|
|`ch02-2-1-4-02-velocity_reservoir` |带偏心方柱直通道；速度入口线性启动、完整储槽牵引出口、无滑移侧壁；开边界及压力出口的完整牵引语义|本地已有；本批未验证|
|`ch02-2-1-4-03-traction_channel` |直通道；两端显式总牵引的分段线性压差驱动；完整矢量牵引、无额外压力规范|本地已有；本批未验证|
|`ch02-2-1-4-04-periodic_acceleration` |周期直通道；周期端面、无滑移壁、时变全域加速度；周期无压力跳跃，体力驱动及均值压力规范|本地已有；本批未验证|
|`ch02-2-1-4-05-symmetry_channel` |通道对称半域；速度入口、牵引出口、一个平面对称边界；对称重建与无回流保证|本地已有；本批未验证|
|`ch02-2-1-4-06-slip_vortex` |全滑移方盒；满足无穿透及零切向牵引的非零涡初态；滑移和物理初态，不用零初态覆盖全部瞬态|本地已有；本批未验证|
|`ch02-2-1-4-07-spatial_force` |非对称封闭域；空间非均匀非保守体加速度，时间按previous分段保持；静壁、点压力规范；分布源项、非线性时间采样和点规范；给定体力不补造其他源|本地已有；本批未验证|
|`ch02-2-1-4-08-obstacle_flux` |直通道；严格正流量和后续非均匀shape；滑移侧壁；相容穿流初速度；流量全边界归一化、内孔、真实面平均与整体流率/载荷|本地已有；本批未验证|
|`ch02-2-1-4-09-pulse` |方腔；顶壁加速、保持、减速至静止；驱动撤去后的涡衰减；稳态题改为分段顶壁驱动|本地已有；本批未验证|
|`ch02-2-1-4-10-reversal` |方腔；顶壁正向启动后反向；流向反转的记忆；稳态题改为不等速反向双壁|本地已有；本批未验证|

### 2.1.5 2D 非牛顿流体不可压缩流动稳态分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-1-5-01-power_law_channel` |入口发展通道；剪切变稀截断幂律、速度入口及完整储槽牵引出口；幂律有效剪切区和开边界|仅远端新定位；本批未验证|
|`ch02-2-1-5-02-power_law_thickening` |周期通道；剪切增稠截断幂律、体力驱动；增稠、周期无压差及体源|本地已有；本批未验证|
|`ch02-2-1-5-03-cross_obstacle_flux` |带偏心方柱通道；Cross、带shape的流量入口及储槽牵引出口；平台过渡、流率归一化与内孔|本地已有；本批未验证|
|`ch02-2-1-5-04-carreau_cavity` |带偏心方柱的Carreau双壁腔；Carreau、上下壁反向驱动；不同剪切层的黏度反馈|本地已有；本批未验证|
|`ch02-2-1-5-05-yasuda_symmetry` |通道对称半域；Carreau–Yasuda、对称面和无滑移壁、速度入口；独立Yasuda指数及对称边界|本地已有；本批未验证|
|`ch02-2-1-5-06-power_law_traction` |直通道；截断幂律、两端完整矢量牵引；低高剪切截断及牵引条件|仅远端新定位；本批未验证|
|`ch02-2-1-5-07-cross_spatial_force` |封闭非对称腔；Cross、空间非均匀非保守体加速度、点压力规范；源项、停滞区和点压力规范|本地已有；本批未验证|
|`ch02-2-1-5-08-carreau_pulse` |方腔；Carreau、相向分段壁速；低高剪切平台或瞬态黏度调整|本地已有；本批未验证|
|`ch02-2-1-5-09-yasuda_slip` |带滑移边界的通道；Carreau–Yasuda、速度入口及储槽牵引出口；滑移条件及非线性流率|本地已有；本批未验证|
|`ch02-2-1-5-10-mixed_initial_or_drive` |非对称多壁腔；截断幂律、稳态不等速多壁驱动；不同初态与驱动、混合网格及导数观测|本地已有；本批未验证|

### 2.1.6 2D 非牛顿流体不可压缩流动瞬态分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-1-6-01-power_law_channel` |入口发展通道；剪切变稀截断幂律、速度入口及完整储槽牵引出口；幂律有效剪切区和开边界|仅远端新定位；本批未验证|
|`ch02-2-1-6-02-power_law_thickening` |周期通道；剪切增稠截断幂律、体力驱动；增稠、周期无压差及体源|本地已有；本批未验证|
|`ch02-2-1-6-03-cross_obstacle_flux` |Cross直通道；严格正流量和后续非均匀shape；滑移侧壁；相容穿流初速度；平台过渡、流率归一化与内孔|本地已有；本批未验证|
|`ch02-2-1-6-04-carreau_cavity` |带偏心方柱的Carreau双壁腔；Carreau、上下壁反向驱动；不同剪切层的黏度反馈|本地已有；本批未验证|
|`ch02-2-1-6-05-yasuda_symmetry` |通道对称半域；Carreau–Yasuda、对称面和无滑移壁、速度入口；独立Yasuda指数及对称边界|本地已有；本批未验证|
|`ch02-2-1-6-06-power_law_traction` |直通道；截断幂律、两端完整矢量牵引；低高剪切截断及牵引条件|仅远端新定位；本批未验证|
|`ch02-2-1-6-07-cross_spatial_force` |封闭非对称腔；Cross、空间非均匀非保守体加速度、点压力规范；源项、停滞区和点压力规范|本地已有；本批未验证|
|`ch02-2-1-6-08-carreau_pulse` |方腔；Carreau、分段线性壁速脉冲和相容物理初速度；低高剪切平台或瞬态黏度调整|本地已有；本批未验证|
|`ch02-2-1-6-09-yasuda_slip` |带滑移边界的通道；Carreau–Yasuda、速度入口及储槽牵引出口；滑移条件及非线性流率|本地已有；本批未验证|
|`ch02-2-1-6-10-mixed_initial_or_drive` |非对称多壁腔；截断幂律、非零相容物理初速度和多壁驱动；不同初态与驱动、混合网格及导数观测|本地已有；本批未验证|

### 2.1.7 3D 非牛顿流体不可压缩流动稳态分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-1-7-01-power_law_channel` |入口发展通道；剪切变稀截断幂律、速度入口及完整储槽牵引出口；幂律有效剪切区和开边界|仅远端新定位；本批未验证|
|`ch02-2-1-7-03-cross_obstacle_flux` |带偏心方柱通道；Cross、带shape的流量入口及储槽牵引出口；平台过渡、流率归一化与内孔|本地已有；本批未验证|
|`ch02-2-1-7-04-carreau_cavity` |带偏心方柱的Carreau双壁腔；Carreau、上下壁反向驱动；不同剪切层的黏度反馈|本地已有；本批未验证|
|`ch02-2-1-7-05-yasuda_symmetry` |通道对称半域；Carreau–Yasuda、对称面和无滑移壁、速度入口；独立Yasuda指数及对称边界|本地已有；本批未验证|
|`ch02-2-1-7-06-power_law_traction` |直通道；截断幂律、两端完整矢量牵引；低高剪切截断及牵引条件|仅远端新定位；本批未验证|
|`ch02-2-1-7-07-cross_spatial_force` |封闭非对称腔；Cross、空间非均匀非保守体加速度、点压力规范；源项、停滞区和点压力规范|本地已有；本批未验证|
|`ch02-2-1-7-08-carreau_pulse` |方腔；Carreau、相向分段壁速；低高剪切平台或瞬态黏度调整|本地已有；本批未验证|
|`ch02-2-1-7-09-yasuda_slip` |带滑移边界的通道；Carreau–Yasuda、速度入口及储槽牵引出口；滑移条件及非线性流率|本地已有；本批未验证|
|`ch02-2-1-7-10-mixed_initial_or_drive` |非对称多壁腔；截断幂律、稳态不等速多壁驱动；不同初态与驱动、混合网格及导数观测|本地已有；本批未验证|

### 2.1.8 3D 非牛顿流体不可压缩流动瞬态分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-1-8-01-power_law_channel` |入口发展通道；剪切变稀截断幂律、速度入口及完整储槽牵引出口；幂律有效剪切区和开边界|仅远端新定位；本批未验证|
|`ch02-2-1-8-02-power_law_thickening` |周期通道；剪切增稠截断幂律、体力驱动；增稠、周期无压差及体源|本地已有；本批未验证|
|`ch02-2-1-8-03-cross_obstacle_flux` |Cross直通道；严格正流量和后续非均匀shape；滑移侧壁；相容穿流初速度；平台过渡、流率归一化与内孔|本地已有；本批未验证|
|`ch02-2-1-8-04-carreau_cavity` |带偏心方柱的Carreau双壁腔；Carreau、上下壁反向驱动；不同剪切层的黏度反馈|本地已有；本批未验证|
|`ch02-2-1-8-05-yasuda_symmetry` |通道对称半域；Carreau–Yasuda、对称面和无滑移壁、速度入口；独立Yasuda指数及对称边界|本地已有；本批未验证|
|`ch02-2-1-8-06-power_law_traction` |直通道；截断幂律、两端完整矢量牵引；低高剪切截断及牵引条件|仅远端新定位；本批未验证|
|`ch02-2-1-8-07-cross_spatial_force` |封闭非对称腔；Cross、空间非均匀非保守体加速度、点压力规范；源项、停滞区和点压力规范|本地已有；本批未验证|
|`ch02-2-1-8-08-carreau_pulse` |方腔；Carreau、分段线性壁速脉冲和相容物理初速度；低高剪切平台或瞬态黏度调整|本地已有；本批未验证|
|`ch02-2-1-8-09-yasuda_slip` |带滑移边界的通道；Carreau–Yasuda、速度入口及储槽牵引出口；滑移条件及非线性流率|本地已有；本批未验证|
|`ch02-2-1-8-10-mixed_initial_or_drive` |非对称多壁腔；截断幂律、非零相容物理初速度和多壁驱动；不同初态与驱动、混合网格及导数观测|本地已有；本批未验证|

### 2.1.9 2D 常黏度牛顿流体等温可压缩流动稳态分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-1-9-01-ideal_lid` |方腔；理想气体、顶壁驱动；密度与绝对静压耦合|本地已有；本批未验证|
|`ch02-2-1-9-02-barotropic_lid` |方腔；线性正压、顶壁驱动；不同于理想气体的状态关系|本地已有；本批未验证|
|`ch02-2-1-9-03-ideal_deep` |深腔；理想气体、侧壁驱动；受限回流中的密度分布|本地已有；本批未验证|
|`ch02-2-1-9-05-ideal_obstacle_flux` |偏心方柱通道；理想气体、流量入口加给定密度、完整储槽牵引出口；内边界、流率归一化和入口密度|仅远端新定位；本批未验证|
|`ch02-2-1-9-08-ideal_symmetry_channel` |对称半通道；理想气体、速度与密度入口、对称面及完整储槽牵引出口；对称边界、压力与入口密度共同约束|仅远端新定位；本批未验证|
|`ch02-2-1-9-09-ideal_density_initial_or_inlet` |矩形通道；理想气体、非零体黏度、空间非均匀入口密度和完整储槽牵引出口；密度输入、体黏度与压缩性调整|仅远端新定位；本批未验证|
|`ch02-2-1-9-10-barotropic_network` |带双障碍物的多入口通道；线性正压、不同密度的两个速度入口、储槽牵引出口；多入口质量供给、状态关系与回流排除|仅远端新定位；本批未验证|

### 2.1.10 2D 常黏度牛顿流体等温可压缩流动瞬态分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-1-10-01-ideal_lid` |方腔；理想气体、顶壁驱动；密度与绝对静压耦合|本地已有；本批未验证|
|`ch02-2-1-10-02-barotropic_lid` |方腔；线性正压、顶壁驱动；不同于理想气体的状态关系|本地已有；本批未验证|
|`ch02-2-1-10-03-ideal_deep` |深腔；理想气体、侧壁驱动；受限回流中的密度分布|本地已有；本批未验证|
|`ch02-2-1-10-04-barotropic_periodic` |周期通道；线性正压、无压跳周期端面、体加速度驱动、非零体黏度；可压缩周期与体力驱动|仅远端新定位；本批未验证|
|`ch02-2-1-10-05-ideal_obstacle_flux` |偏心方柱通道；理想气体、流量入口加给定密度、完整储槽牵引出口；内边界、流率归一化和入口密度|仅远端新定位；本批未验证|
|`ch02-2-1-10-06-ideal_stratified_slip` |高腔；理想气体、均匀竖直体加速度、滑移壁；封闭质量库存、分层和滑移|本地已有；本批未验证|
|`ch02-2-1-10-07-barotropic_stratified` |矩形腔；线性正压、斜向体加速度；非竖直压力和密度梯度|本地已有；本批未验证|
|`ch02-2-1-10-08-ideal_symmetry_channel` |对称半通道；理想气体、速度与密度入口、对称面及完整储槽牵引出口；对称边界、压力与入口密度共同约束|仅远端新定位；本批未验证|
|`ch02-2-1-10-10-barotropic_network` |带双障碍物的多入口通道；线性正压、不同密度的两个速度入口、储槽牵引出口；多入口质量供给、状态关系与回流排除|仅远端新定位；本批未验证|

### 2.1.11 3D 常黏度牛顿流体等温可压缩流动稳态分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-1-11-01-ideal_lid` |方腔；理想气体、顶壁驱动；密度与绝对静压耦合|本地已有；本批未验证|
|`ch02-2-1-11-02-barotropic_lid` |方腔；线性正压、顶壁驱动；不同于理想气体的状态关系|本地已有；本批未验证|
|`ch02-2-1-11-03-ideal_deep` |深腔；理想气体、侧壁驱动；受限回流中的密度分布|本地已有；本批未验证|
|`ch02-2-1-11-05-ideal_obstacle_flux` |偏心方柱通道；理想气体、流量入口加给定密度、完整储槽牵引出口；内边界、流率归一化和入口密度|仅远端新定位；本批未验证|
|`ch02-2-1-11-08-ideal_symmetry_channel` |对称半通道；理想气体、速度与密度入口、对称面及完整储槽牵引出口；对称边界、压力与入口密度共同约束|仅远端新定位；本批未验证|
|`ch02-2-1-11-09-ideal_density_initial_or_inlet` |矩形通道；理想气体、非零体黏度、空间非均匀入口密度和完整储槽牵引出口；密度输入、体黏度与压缩性调整|仅远端新定位；本批未验证|
|`ch02-2-1-11-10-barotropic_network` |带双障碍物的多入口通道；线性正压、不同密度的两个速度入口、储槽牵引出口；多入口质量供给、状态关系与回流排除|仅远端新定位；本批未验证|

### 2.1.12 3D 常黏度牛顿流体等温可压缩流动瞬态分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-1-12-01-ideal_lid` |方腔；理想气体、顶壁驱动；密度与绝对静压耦合|本地已有；本批未验证|
|`ch02-2-1-12-02-barotropic_lid` |方腔；线性正压、顶壁驱动；不同于理想气体的状态关系|本地已有；本批未验证|
|`ch02-2-1-12-03-ideal_deep` |深腔；理想气体、侧壁驱动；受限回流中的密度分布|本地已有；本批未验证|
|`ch02-2-1-12-04-barotropic_periodic` |周期通道；线性正压、无压跳周期端面、体加速度驱动、非零体黏度；可压缩周期与体力驱动|仅远端新定位；本批未验证|
|`ch02-2-1-12-05-ideal_obstacle_flux` |偏心方柱通道；理想气体、流量入口加给定密度、完整储槽牵引出口；内边界、流率归一化和入口密度|仅远端新定位；本批未验证|
|`ch02-2-1-12-06-ideal_stratified_slip` |高腔；理想气体、均匀竖直体加速度、滑移壁；封闭质量库存、分层和滑移|本地已有；本批未验证|
|`ch02-2-1-12-07-barotropic_stratified` |矩形腔；线性正压、斜向体加速度；非竖直压力和密度梯度|本地已有；本批未验证|
|`ch02-2-1-12-09-ideal_density_initial_or_inlet` |矩形通道；理想气体、非零体黏度、相容非均匀初密度与速度/密度入口、完整储槽牵引出口；密度输入、体黏度与压缩性调整|仅远端新定位；本批未验证|
|`ch02-2-1-12-10-barotropic_network` |带双障碍物的多入口通道；线性正压、不同密度的两个速度入口、储槽牵引出口；多入口质量供给、状态关系与回流排除|仅远端新定位；本批未验证|

### 2.2.1 2D 牛顿流体低速流动与传热稳态分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-2-1-01-horizontal_conduction` |方腔；左右温差、静壁、无浮力；导热基线与绝对温度|本地已有；本批未验证|
|`ch02-2-2-1-02-natural_convection` |方腔；左右温差和竖直重力；Boussinesq自然对流|本地已有；本批未验证|
|`ch02-2-2-1-03-heated_lid` |方腔/有限深度盒；顶壁运动且壁面温差；3D另用侧壁沿z驱动；强制热输运、黏性耗散和真实三维流动|本地已有；本批未验证|
|`ch02-2-2-1-04-mixed_aiding` |深腔；侧壁运动与浮力协同；混合对流协同|本地已有；本批未验证|
|`ch02-2-2-1-05-mixed_opposing` |深腔；侧壁运动与浮力相反；竞争驱动|本地已有；本批未验证|
|`ch02-2-2-1-06-heat_source` |矩形腔；局部体热源、一片定温壁；源项与总能量流出|本地已有；本批未验证|
|`ch02-2-2-1-07-heat_flux` |宽腔；底壁热通量、顶壁定温；非Dirichlet热条件|本地已有；本批未验证|
|`ch02-2-2-1-08-variable_viscosity` |方腔；顶壁驱动、温度幂律黏度；温黏反馈|本地已有；本批未验证|
|`ch02-2-2-1-09-variable_conductivity` |带偏心方柱的腔；冷热外壁、温度幂律导热；非线性导热和内孔边界|本地已有；本批未验证|
|`ch02-2-2-1-10-thermal_pulse_or_split` |矩形腔；多分区冷热壁和机械驱动，无物理初态；非均匀或非定常热驱动|本地已有；本批未验证|

### 2.2.2 2D 牛顿流体低速流动与传热瞬态分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-2-2-01-horizontal_conduction` |方腔；左右温差、静壁、无浮力；导热基线与绝对温度|本地已有；本批未验证|
|`ch02-2-2-2-02-natural_convection` |方腔；左右温差和竖直重力；Boussinesq自然对流|本地已有；本批未验证|
|`ch02-2-2-2-03-heated_lid` |方腔/有限深度盒；顶壁运动且壁面温差；3D另用侧壁沿z驱动；强制热输运、黏性耗散和真实三维流动|本地已有；本批未验证|
|`ch02-2-2-2-04-mixed_aiding` |深腔；侧壁运动与浮力协同；混合对流协同|本地已有；本批未验证|
|`ch02-2-2-2-05-mixed_opposing` |深腔；侧壁运动与浮力相反；竞争驱动|本地已有；本批未验证|
|`ch02-2-2-2-06-heat_source` |矩形腔；局部体热源、一片定温壁；源项与总能量流出|本地已有；本批未验证|
|`ch02-2-2-2-07-heat_flux` |宽腔；底壁热通量、顶壁定温；非Dirichlet热条件|本地已有；本批未验证|
|`ch02-2-2-2-08-variable_viscosity` |方腔；顶壁驱动、温度幂律黏度；温黏反馈|本地已有；本批未验证|
|`ch02-2-2-2-09-variable_conductivity` |带偏心方柱的腔；冷热外壁、温度幂律导热；非线性导热和内孔边界|本地已有；本批未验证|
|`ch02-2-2-2-10-thermal_pulse_or_split` |矩形腔；分段线性壁温脉冲、相容物理初态和机械驱动；非均匀或非定常热驱动|本地已有；本批未验证|

### 2.2.3 3D 牛顿流体低速流动与传热稳态分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-2-3-01-horizontal_conduction` |方腔；左右温差、静壁、无浮力；导热基线与绝对温度|本地已有；本批未验证|
|`ch02-2-2-3-02-natural_convection` |方腔；左右温差和竖直重力；Boussinesq自然对流|本地已有；本批未验证|
|`ch02-2-2-3-03-heated_lid` |方腔/有限深度盒；顶壁运动且壁面温差；3D另用侧壁沿z驱动；强制热输运、黏性耗散和真实三维流动|本地已有；本批未验证|
|`ch02-2-2-3-04-mixed_aiding` |深腔；侧壁运动与浮力协同；混合对流协同|本地已有；本批未验证|
|`ch02-2-2-3-05-mixed_opposing` |深腔；侧壁运动与浮力相反；竞争驱动|本地已有；本批未验证|
|`ch02-2-2-3-06-heat_source` |矩形腔；局部体热源、一片定温壁；源项与总能量流出|本地已有；本批未验证|
|`ch02-2-2-3-07-heat_flux` |宽腔；底壁热通量、顶壁定温；非Dirichlet热条件|本地已有；本批未验证|
|`ch02-2-2-3-08-variable_viscosity` |方腔；顶壁驱动、温度幂律黏度；温黏反馈|本地已有；本批未验证|
|`ch02-2-2-3-09-variable_conductivity` |带偏心方柱的腔；冷热外壁、温度幂律导热；非线性导热和内孔边界|本地已有；本批未验证|
|`ch02-2-2-3-10-thermal_pulse_or_split` |矩形腔；多分区冷热壁和机械驱动，无物理初态；非均匀或非定常热驱动|本地已有；本批未验证|

### 2.2.4 3D 牛顿流体低速流动与传热瞬态分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-2-4-01-horizontal_conduction` |方腔；左右温差、静壁、无浮力；导热基线与绝对温度|本地已有；本批未验证|
|`ch02-2-2-4-02-natural_convection` |方腔；左右温差和竖直重力；Boussinesq自然对流|本地已有；本批未验证|
|`ch02-2-2-4-03-heated_lid` |方腔/有限深度盒；顶壁运动且壁面温差；3D另用侧壁沿z驱动；强制热输运、黏性耗散和真实三维流动|本地已有；本批未验证|
|`ch02-2-2-4-04-mixed_aiding` |深腔；侧壁运动与浮力协同；混合对流协同|本地已有；本批未验证|
|`ch02-2-2-4-05-mixed_opposing` |深腔；侧壁运动与浮力相反；竞争驱动|本地已有；本批未验证|
|`ch02-2-2-4-06-heat_source` |矩形腔；局部体热源、一片定温壁；源项与总能量流出|本地已有；本批未验证|
|`ch02-2-2-4-07-heat_flux` |宽腔；底壁热通量、顶壁定温；非Dirichlet热条件|本地已有；本批未验证|
|`ch02-2-2-4-08-variable_viscosity` |方腔；顶壁驱动、温度幂律黏度；温黏反馈|本地已有；本批未验证|
|`ch02-2-2-4-09-variable_conductivity` |带偏心方柱的腔；冷热外壁、温度幂律导热；非线性导热和内孔边界|本地已有；本批未验证|
|`ch02-2-2-4-10-thermal_pulse_or_split` |矩形腔；分段线性壁温脉冲、相容物理初态和机械驱动；非均匀或非定常热驱动|本地已有；本批未验证|

### 2.2.5 2D 无黏可压缩流动稳态分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-2-5-01-vertical_gravity` |方盒；均匀竖直保守加速度；等熵静水与总体质量|本地已有；本批未验证|
|`ch02-2-2-5-02-horizontal_gravity` |宽盒；均匀水平保守加速度；不同几何质量归一化；不是旋转复制|本地已有；本批未验证|
|`ch02-2-2-5-03-oblique_gravity` |非正方矩形盒；斜向保守加速度；双向温度及密度梯度|本地已有；本批未验证|
|`ch02-2-2-5-04-deep_column` |深柱盒；竖直保守加速度；可观分层和温度范围限制|本地已有；本批未验证|
|`ch02-2-2-5-05-quadratic_potential` |方盒；二次势的线性回复加速度；非均匀保守体力|本地已有；本批未验证|
|`ch02-2-2-5-06-anisotropic_potential` |矩形盒；不同方向刚度的二次势；各向异性势能与质量约束|本地已有；本批未验证|
|`ch02-2-2-5-07-offcentre_well` |带偏心方孔的盒；偏心二次势；内孔域上的质量积分|本地已有；本批未验证|
|`ch02-2-2-5-08-piecewise_potential` |长盒；连续分片线性势；契约分片输入的静水重建|本地已有；本批未验证|
|`ch02-2-2-5-09-double_well` |宽盒；双阱光滑保守势的采样；多个密度峰而非自由环流|本地已有；本批未验证|
|`ch02-2-2-5-10-multiaxis_well` |非对称盒；含交叉项的正定二次势；耦合多方向静水平衡|本地已有；本批未验证|

### 2.2.6 2D 无黏可压缩流动瞬态分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-2-6-01-acoustic_mode` |封闭矩形盒；小幅平面声学压力扰动；线性极限|本地已有；本批未验证|
|`ch02-2-2-6-02-compression_pulse` |长封闭盒；有限幅平滑压缩脉冲；非线性压缩|本地已有；本批未验证|
|`ch02-2-2-6-03-rarefaction` |长封闭盒；无真空稀疏波初态；膨胀与熵可容许性|本地已有；本批未验证|
|`ch02-2-2-6-04-sod` |封闭长盒；Sod型分片初态，早于端壁反射取样；激波、接触与稀疏波|本地已有；本批未验证|
|`ch02-2-2-6-05-contact` |封闭长盒；等压静止密度接触面；接触间断保持|本地已有；本批未验证|
|`ch02-2-2-6-06-cross_acoustic` |方盒；相交的低幅声学扰动；多方向波传播|本地已有；本批未验证|
|`ch02-2-2-6-07-radial_blast` |方盒；中心高压区、静止初速度；圆柱/球面膨胀|本地已有；本批未验证|
|`ch02-2-2-6-08-offcentre_blast` |长宽不等的盒；偏心高压区；非对称壁面反射|本地已有；本批未验证|
|`ch02-2-2-6-09-gravity_adjustment` |高盒；均匀初态与分段线性加速度脉冲；时变体力调整中的能量转换|本地已有；本批未验证|
|`ch02-2-2-6-10-obstacle_reflection` |带方形障碍物的盒；低幅压力脉冲；绕射和封闭内边界|本地已有；本批未验证|

### 2.2.7 3D 无黏可压缩流动稳态分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-2-7-01-vertical_gravity` |方盒；均匀竖直保守加速度；等熵静水与总体质量|本地已有；本批未验证|
|`ch02-2-2-7-02-horizontal_gravity` |宽盒；均匀水平保守加速度；不同几何质量归一化；不是旋转复制|本地已有；本批未验证|
|`ch02-2-2-7-03-oblique_gravity` |非正方矩形盒；斜向保守加速度；双向温度及密度梯度|本地已有；本批未验证|
|`ch02-2-2-7-04-deep_column` |深柱盒；竖直保守加速度；可观分层和温度范围限制|本地已有；本批未验证|
|`ch02-2-2-7-05-quadratic_potential` |方盒；二次势的线性回复加速度；非均匀保守体力|本地已有；本批未验证|
|`ch02-2-2-7-06-anisotropic_potential` |矩形盒；不同方向刚度的二次势；各向异性势能与质量约束|本地已有；本批未验证|
|`ch02-2-2-7-07-offcentre_well` |带偏心方孔的盒；偏心二次势；内孔域上的质量积分|本地已有；本批未验证|
|`ch02-2-2-7-08-piecewise_potential` |长盒；连续分片线性势；契约分片输入的静水重建|本地已有；本批未验证|
|`ch02-2-2-7-09-double_well` |宽盒；双阱光滑保守势的采样；多个密度峰而非自由环流|本地已有；本批未验证|
|`ch02-2-2-7-10-multiaxis_well` |非对称盒；含交叉项的正定二次势；耦合多方向静水平衡|本地已有；本批未验证|

### 2.2.8 3D 无黏可压缩流动瞬态分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-2-8-01-acoustic_mode` |封闭矩形盒；小幅平面声学压力扰动；线性极限|本地已有；本批未验证|
|`ch02-2-2-8-02-compression_pulse` |长封闭盒；有限幅平滑压缩脉冲；非线性压缩|本地已有；本批未验证|
|`ch02-2-2-8-03-rarefaction` |长封闭盒；无真空稀疏波初态；膨胀与熵可容许性|本地已有；本批未验证|
|`ch02-2-2-8-04-sod` |封闭长盒；Sod型分片初态，早于端壁反射取样；激波、接触与稀疏波|本地已有；本批未验证|
|`ch02-2-2-8-05-contact` |封闭长盒；等压静止密度接触面；接触间断保持|本地已有；本批未验证|
|`ch02-2-2-8-06-cross_acoustic` |方盒；相交的低幅声学扰动；多方向波传播|本地已有；本批未验证|
|`ch02-2-2-8-07-radial_blast` |方盒；中心高压区、静止初速度；圆柱/球面膨胀|本地已有；本批未验证|
|`ch02-2-2-8-08-offcentre_blast` |长宽不等的盒；偏心高压区；非对称壁面反射|本地已有；本批未验证|
|`ch02-2-2-8-09-gravity_adjustment` |高盒；均匀初态与分段线性加速度脉冲；时变体力调整中的能量转换|本地已有；本批未验证|
|`ch02-2-2-8-10-obstacle_reflection` |带方形障碍物的盒；低幅压力脉冲；绕射和封闭内边界|本地已有；本批未验证|

### 2.2.9 2D 牛顿流体可压缩流动与传热稳态分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-2-9-01-thermal_cavity` |方盒；静壁、左右温差；封闭气体质量与非均匀密度|仅远端新定位；本批未验证|
|`ch02-2-2-9-06-heated_obstacle` |偏心方柱盒；内柱热壁、外壁冷却；内孔热交换|仅远端新定位；本批未验证|
|`ch02-2-2-9-07-nonuniform_source` |矩形盒；局部体热源、冷却壁；源项空间分布|仅远端新定位；本批未验证|
|`ch02-2-2-9-09-bulk_viscosity` |矩形盒；独立非零体黏度、壁面驱动及冷热壁；独立体黏度|仅远端新定位；本批未验证|

### 2.2.10 2D 牛顿流体可压缩流动与传热瞬态分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-2-10-01-thermal_cavity` |方盒；静壁、左右温差；封闭气体质量与非均匀密度|本地已有；本批未验证|
|`ch02-2-2-10-02-heated_lid` |方盒；运动顶壁和温差；可压缩热黏性耦合|仅远端新定位；本批未验证|
|`ch02-2-2-10-03-deep_thermal` |深盒；竖直温差与重力；气体分层|本地已有；本批未验证|
|`ch02-2-2-10-04-shear_heating` |矩形盒；上下反向壁、壁面定温；黏性耗散|仅远端新定位；本批未验证|
|`ch02-2-2-10-05-thermal_flux` |宽盒；底壁热流、顶壁定温；导热通量边界|仅远端新定位；本批未验证|
|`ch02-2-2-10-07-nonuniform_source` |矩形盒；局部体热源、冷却壁；源项空间分布|本地已有；本批未验证|
|`ch02-2-2-10-08-power_transport` |方盒；温度幂律黏度和导热、顶壁驱动；非恒定输运性质|本地已有；本批未验证|
|`ch02-2-2-10-09-bulk_viscosity` |矩形盒；独立非零体黏度、相容低幅声学初态和热壁；独立体黏度|仅远端新定位；本批未验证|
|`ch02-2-2-10-10-wall_pulse_or_partition` |非对称盒；分段线性壁温脉冲、相容物理初态和机械驱动；壁温历史或壁温分区|本地已有；本批未验证|

### 2.2.11 3D 牛顿流体可压缩流动与传热稳态分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-2-11-06-heated_obstacle` |偏心方柱盒；内柱热壁、外壁冷却；内孔热交换|仅远端新定位；本批未验证|
|`ch02-2-2-11-07-nonuniform_source` |矩形盒；局部体热源、冷却壁；源项空间分布|仅远端新定位；本批未验证|
|`ch02-2-2-11-09-bulk_viscosity` |矩形盒；独立非零体黏度、壁面驱动及冷热壁；独立体黏度|仅远端新定位；本批未验证|

### 2.2.12 3D 牛顿流体可压缩流动与传热瞬态分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-2-12-01-thermal_cavity` |方盒；静壁、左右温差；封闭气体质量与非均匀密度|本地已有；本批未验证|
|`ch02-2-2-12-02-heated_lid` |方盒；运动顶壁和温差；可压缩热黏性耦合|仅远端新定位；本批未验证|
|`ch02-2-2-12-03-deep_thermal` |深盒；竖直温差与重力；气体分层|本地已有；本批未验证|
|`ch02-2-2-12-04-shear_heating` |矩形盒；上下反向壁、壁面定温；黏性耗散|仅远端新定位；本批未验证|
|`ch02-2-2-12-05-thermal_flux` |宽盒；底壁热流、顶壁定温；导热通量边界|仅远端新定位；本批未验证|
|`ch02-2-2-12-06-heated_obstacle` |偏心方柱盒；内柱热壁、外壁冷却；内孔热交换|仅远端新定位；本批未验证|
|`ch02-2-2-12-07-nonuniform_source` |矩形盒；局部体热源、冷却壁；源项空间分布|本地已有；本批未验证|
|`ch02-2-2-12-08-power_transport` |方盒；温度幂律黏度和导热、顶壁驱动；非恒定输运性质|本地已有；本批未验证|
|`ch02-2-2-12-09-bulk_viscosity` |矩形盒；独立非零体黏度、相容低幅声学初态和热壁；独立体黏度|仅远端新定位；本批未验证|
|`ch02-2-2-12-10-wall_pulse_or_partition` |非对称盒；分段线性壁温脉冲、相容物理初态和机械驱动；壁温历史或壁温分区|本地已有；本批未验证|

### 2.3.1 2D 不可压缩湍流定常平均分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-3-1-01-lid_cavity` |方盒；顶壁驱动；平均主涡|本地已有；本批未验证|
|`ch02-2-3-1-03-wide_cavity` |宽盒；顶壁驱动；长回流与多涡|本地已有；本批未验证|
|`ch02-2-3-1-04-opposed_walls` |矩形盒；反向双壁；双剪切层|本地已有；本批未验证|
|`ch02-2-3-1-05-codirectional_walls` |矩形盒；同向双壁；不同剪切拓扑|本地已有；本批未验证|
|`ch02-2-3-1-06-orthogonal_walls` |立方盒/二维方腔；相邻壁切向运动；三维横向二次流；二维邻壁耦合|本地已有；本批未验证|
|`ch02-2-3-1-07-obstacle` |偏心方柱盒；外顶壁运动；障碍物尾流与间隙射流|本地已有；本批未验证|
|`ch02-2-3-1-09-unequal_walls` |深盒；不等速反向壁；非对称动量输入|本地已有；本批未验证|
|`ch02-2-3-1-10-pulsed_or_partitioned` |非对称盒；多分区非均匀壁速，无物理初态；平均响应或离散统计窗口；不得用末帧代替统计|本地已有；本批未验证|

### 2.3.2 3D 不可压缩湍流定常平均分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-3-2-01-lid_cavity` |方盒；顶壁驱动；平均主涡|本地已有；本批未验证|
|`ch02-2-3-2-03-wide_cavity` |宽盒；顶壁驱动；长回流与多涡|本地已有；本批未验证|
|`ch02-2-3-2-06-orthogonal_walls` |立方盒/二维方腔；相邻壁切向运动；三维横向二次流；二维邻壁耦合|本地已有；本批未验证|
|`ch02-2-3-2-07-obstacle` |偏心方柱盒；外顶壁运动；障碍物尾流与间隙射流|本地已有；本批未验证|
|`ch02-2-3-2-08-spatial_acceleration` |宽盒；空间非均匀、非保守体加速度与静壁；分布驱动和压力重建，不局限壁面驱动|本地已有；本批未验证|
|`ch02-2-3-2-09-unequal_walls` |深盒；不等速反向壁；非对称动量输入|本地已有；本批未验证|
|`ch02-2-3-2-10-pulsed_or_partitioned` |非对称盒；多分区非均匀壁速，无物理初态；平均响应或离散统计窗口；不得用末帧代替统计|本地已有；本批未验证|

### 2.3.3 3D 不可压缩湍流非定常平均分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-3-3-01-lid_cavity` |方盒；顶壁驱动；平均主涡|本地已有；本批未验证|
|`ch02-2-3-3-02-deep_cavity` |深盒；顶壁驱动；深部回流|本地已有；本批未验证|
|`ch02-2-3-3-03-wide_cavity` |宽盒；顶壁驱动；长回流与多涡|本地已有；本批未验证|
|`ch02-2-3-3-04-opposed_walls` |矩形盒；反向双壁；双剪切层|本地已有；本批未验证|
|`ch02-2-3-3-05-codirectional_walls` |矩形盒；同向双壁；不同剪切拓扑|本地已有；本批未验证|
|`ch02-2-3-3-06-orthogonal_walls` |立方盒/二维方腔；相邻壁切向运动；三维横向二次流；二维邻壁耦合|本地已有；本批未验证|
|`ch02-2-3-3-07-obstacle` |偏心方柱盒；外顶壁运动；障碍物尾流与间隙射流|本地已有；本批未验证|
|`ch02-2-3-3-08-spatial_acceleration` |宽盒；空间非均匀、非保守体加速度与静壁；分布驱动和压力重建，不局限壁面驱动|本地已有；本批未验证|
|`ch02-2-3-3-09-unequal_walls` |深盒；不等速反向壁；非对称动量输入|本地已有；本批未验证|
|`ch02-2-3-3-10-pulsed_or_partitioned` |非对称盒；脉冲壁速、公开平均初速度及不同正k/积分长度尺度的空间初态；平均响应或离散统计窗口；不得用末帧代替统计|本地已有；本批未验证|

### 2.3.4 3D 不可压缩湍流尺度解析统计分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-3-4-01-lid_cavity` |方盒；顶壁驱动；平均主涡|本地已有；本批未验证|
|`ch02-2-3-4-02-deep_cavity` |深盒；顶壁驱动；深部回流|本地已有；本批未验证|
|`ch02-2-3-4-03-wide_cavity` |宽盒；顶壁驱动；长回流与多涡|本地已有；本批未验证|
|`ch02-2-3-4-04-opposed_walls` |矩形盒；反向双壁；双剪切层|本地已有；本批未验证|
|`ch02-2-3-4-05-codirectional_walls` |矩形盒；同向双壁；不同剪切拓扑|本地已有；本批未验证|
|`ch02-2-3-4-06-orthogonal_walls` |立方盒/二维方腔；相邻壁切向运动；三维横向二次流；二维邻壁耦合|本地已有；本批未验证|
|`ch02-2-3-4-07-obstacle` |偏心方柱盒；外顶壁运动；障碍物尾流与间隙射流|本地已有；本批未验证|
|`ch02-2-3-4-08-spatial_acceleration` |宽盒；空间非均匀、非保守体加速度与静壁；分布驱动和压力重建，不局限壁面驱动|本地已有；本批未验证|
|`ch02-2-3-4-09-unequal_walls` |深盒；不等速反向壁；非对称动量输入|本地已有；本批未验证|
|`ch02-2-3-4-10-pulsed_or_partitioned` |非对称盒；完整非零散度零瞬时初速度和分段线性壁速；按DATA明确等权样本窗口；平均响应或离散统计窗口；不得用末帧代替统计|本地已有；本批未验证|

### 2.3.5 3D 等温可压缩湍流定常平均分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-3-5-01-lid_cavity` |方盒；顶壁驱动；平均主涡|本地已有；本批未验证|
|`ch02-2-3-5-03-wide_cavity` |宽盒；顶壁驱动；长回流与多涡|本地已有；本批未验证|
|`ch02-2-3-5-06-orthogonal_walls` |立方盒/二维方腔；相邻壁切向运动；三维横向二次流；二维邻壁耦合|本地已有；本批未验证|
|`ch02-2-3-5-07-obstacle` |偏心方柱盒；外顶壁运动；障碍物尾流与间隙射流|本地已有；本批未验证|
|`ch02-2-3-5-08-spatial_acceleration` |宽盒；空间非均匀、非保守体加速度与静壁；分布驱动和压力重建，不局限壁面驱动|本地已有；本批未验证|
|`ch02-2-3-5-09-unequal_walls` |深盒；不等速反向壁；非对称动量输入|本地已有；本批未验证|
|`ch02-2-3-5-10-pulsed_or_partitioned` |非对称盒；多分区非均匀壁速，无物理初态；平均响应或离散统计窗口；不得用末帧代替统计|本地已有；本批未验证|

### 2.4.1 3D 低速湍流传热定常平均分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-4-1-01-horizontal_conduction` |方腔；左右温差、静壁、无浮力；导热基线与绝对温度|本地已有；本批未验证|
|`ch02-2-4-1-02-natural_convection` |方腔；左右温差和竖直重力；Boussinesq自然对流|本地已有；本批未验证|
|`ch02-2-4-1-03-heated_lid` |方腔/有限深度盒；顶壁运动且壁面温差；3D另用侧壁沿z驱动；强制热输运、黏性耗散和真实三维流动|本地已有；本批未验证|
|`ch02-2-4-1-04-mixed_aiding` |深腔；侧壁运动与浮力协同；混合对流协同|本地已有；本批未验证|
|`ch02-2-4-1-05-mixed_opposing` |深腔；侧壁运动与浮力相反；竞争驱动|本地已有；本批未验证|
|`ch02-2-4-1-07-heat_flux` |宽腔；底壁热通量、顶壁定温；非Dirichlet热条件|本地已有；本批未验证|
|`ch02-2-4-1-08-variable_viscosity` |方腔；顶壁驱动、温度幂律黏度；温黏反馈|本地已有；本批未验证|
|`ch02-2-4-1-09-variable_conductivity` |带偏心方柱的腔；冷热外壁、温度幂律导热；非线性导热和内孔边界|本地已有；本批未验证|
|`ch02-2-4-1-10-thermal_pulse_or_split` |矩形腔；多分区冷热壁和机械驱动，无物理初态；非均匀或非定常热驱动|本地已有；本批未验证|

### 2.4.2 3D 低速湍流传热非定常平均分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-4-2-07-heat_flux` |宽腔；底壁热通量、顶壁定温；非Dirichlet热条件|本地已有；本批未验证|
|`ch02-2-4-2-08-variable_viscosity` |方腔；顶壁驱动、温度幂律黏度；温黏反馈|本地已有；本批未验证|
|`ch02-2-4-2-09-variable_conductivity` |带偏心方柱的腔；冷热外壁、温度幂律导热；非线性导热和内孔边界|本地已有；本批未验证|
|`ch02-2-4-2-10-thermal_pulse_or_split` |矩形腔；分段线性壁温脉冲、相容物理初态和机械驱动；非均匀或非定常热驱动|本地已有；本批未验证|

### 2.4.3 3D 低速湍流传热尺度解析统计分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-4-3-01-horizontal_conduction` |方腔；左右温差、静壁、无浮力；导热基线与绝对温度|本地已有；本批未验证|
|`ch02-2-4-3-02-natural_convection` |方腔；左右温差和竖直重力；Boussinesq自然对流|本地已有；本批未验证|
|`ch02-2-4-3-03-heated_lid` |方腔/有限深度盒；顶壁运动且壁面温差；3D另用侧壁沿z驱动；强制热输运、黏性耗散和真实三维流动|本地已有；本批未验证|
|`ch02-2-4-3-04-mixed_aiding` |深腔；侧壁运动与浮力协同；混合对流协同|本地已有；本批未验证|
|`ch02-2-4-3-05-mixed_opposing` |深腔；侧壁运动与浮力相反；竞争驱动|本地已有；本批未验证|
|`ch02-2-4-3-06-heat_source` |矩形腔；局部体热源、一片定温壁；源项与总能量流出|本地已有；本批未验证|
|`ch02-2-4-3-07-heat_flux` |宽腔；底壁热通量、顶壁定温；非Dirichlet热条件|本地已有；本批未验证|
|`ch02-2-4-3-08-variable_viscosity` |方腔；顶壁驱动、温度幂律黏度；温黏反馈|本地已有；本批未验证|
|`ch02-2-4-3-09-variable_conductivity` |带偏心方柱的腔；冷热外壁、温度幂律导热；非线性导热和内孔边界|本地已有；本批未验证|
|`ch02-2-4-3-10-thermal_pulse_or_split` |矩形腔；分段线性壁温脉冲、相容物理初态和机械驱动；非均匀或非定常热驱动|本地已有；本批未验证|

### 2.4.4 3D 可压缩湍流传热定常平均分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-4-4-01-thermal_cavity` |方盒；静壁、左右温差；封闭气体质量与非均匀密度|仅远端新定位；本批未验证|
|`ch02-2-4-4-06-heated_obstacle` |偏心方柱盒；内柱热壁、外壁冷却；内孔热交换|仅远端新定位；本批未验证|
|`ch02-2-4-4-07-nonuniform_source` |矩形盒；局部体热源、冷却壁；源项空间分布|仅远端新定位；本批未验证|
|`ch02-2-4-4-09-bulk_viscosity` |矩形盒；独立非零体黏度、壁面驱动及冷热壁；独立体黏度|仅远端新定位；本批未验证|

### 2.5.3 二维不混溶双流体界面瞬态流动

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-5-3-01-stable_layers` |方盒；稳定重力分层、零初速度；分层基线|本地已有；本批未验证|
|`ch02-2-5-3-02-lock_exchange` |长盒；水平相分离；密度流交换|本地已有；本批未验证|
|`ch02-2-5-3-03-rt_wave` |方盒；上重下轻、界面低幅扰动；Rayleigh–Taylor发展|本地已有；本批未验证|
|`ch02-2-5-3-04-rising_blob` |高盒；轻相团块位于重相内部；无表面张力浮升|本地已有；本批未验证|
|`ch02-2-5-3-05-sinking_blob` |高盒；重相团块位于轻相内部；沉降和变形|本地已有；本批未验证|
|`ch02-2-5-3-06-two_blobs` |方盒；两种尺寸的轻相团块；团块相互作用|本地已有；本批未验证|
|`ch02-2-5-3-07-inclined_interface` |长盒；斜界面、稳定密度序；界面调整|本地已有；本批未验证|
|`ch02-2-5-3-08-obstacle_exchange` |带固定方柱盒；侧向分层释放；不同相绕障|本地已有；本批未验证|
|`ch02-2-5-3-09-viscosity_contrast` |矩形盒；近等密度、黏度对比及相容涡初态；黏性对比而非仅密度对比|本地已有；本批未验证|
|`ch02-2-5-3-10-double_lock` |三段长盒；两端重相、中间轻相；双向密度前缘相互作用|本地已有；本批未验证|

### 2.5.4 三维不混溶双流体界面瞬态流动

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-5-4-01-stable_layers` |方盒；稳定重力分层、零初速度；分层基线|本地已有；本批未验证|
|`ch02-2-5-4-02-lock_exchange` |长盒；水平相分离；密度流交换|本地已有；本批未验证|
|`ch02-2-5-4-03-rt_wave` |方盒；上重下轻、界面低幅扰动；Rayleigh–Taylor发展|本地已有；本批未验证|
|`ch02-2-5-4-04-rising_blob` |高盒；轻相团块位于重相内部；无表面张力浮升|本地已有；本批未验证|
|`ch02-2-5-4-05-sinking_blob` |高盒；重相团块位于轻相内部；沉降和变形|本地已有；本批未验证|
|`ch02-2-5-4-06-two_blobs` |方盒；两种尺寸的轻相团块；团块相互作用|本地已有；本批未验证|
|`ch02-2-5-4-07-inclined_interface` |长盒；斜界面、稳定密度序；界面调整|本地已有；本批未验证|
|`ch02-2-5-4-08-obstacle_exchange` |带固定方柱盒；侧向分层释放；不同相绕障|本地已有；本批未验证|
|`ch02-2-5-4-09-viscosity_contrast` |矩形盒；近等密度、黏度对比及相容涡初态；黏性对比而非仅密度对比|本地已有；本批未验证|
|`ch02-2-5-4-10-double_lock` |三段长盒；两端重相、中间轻相；双向密度前缘相互作用|本地已有；本批未验证|

### 2.8.2 可压缩气膜润滑瞬态分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-8-2-01-squeeze` |矩形面积；均匀间隙线性减小；可压缩挤压|本地已有；本批未验证|
|`ch02-2-8-2-02-separation` |矩形面积；均匀间隙线性增大；气膜稀释|本地已有；本批未验证|
|`ch02-2-8-2-03-wedge_start` |收敛楔形面积；壁速从零启动；剪切泵送瞬态|本地已有；本批未验证|
|`ch02-2-8-2-04-pressure_pulse` |矩形面积；侧边压力脉冲、恒定间隙；压力扩散|本地已有；本批未验证|
|`ch02-2-8-2-05-tilt_squeeze` |矩形面积；倾斜间隙并挤压；空间与时间间隙变化|本地已有；本批未验证|
|`ch02-2-8-2-06-local_dimple` |带局部凹坑的面积；滑动壁和可压缩初压；二维纹理气膜|本地已有；本批未验证|
|`ch02-2-8-2-07-oblique_slide` |非正方面积；双向间隙梯度和斜向壁速；二维气体通量|本地已有；本批未验证|
|`ch02-2-8-2-08-two_wall_drive` |矩形面积；上下壁不同速度历史；时变剪切泵送|本地已有；本批未验证|
|`ch02-2-8-2-09-inner_feed` |带内孔的面积；内孔供气、四周环境压；多连通供气|本地已有；本批未验证|
|`ch02-2-8-2-10-squeeze_release` |矩形面积；先挤压再分离；压缩/恢复历史|本地已有；本批未验证|

### 2.9.1 全湿浅水稳态分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-9-1-01-flat_subcritical` |长矩形水道；平床、储槽亚临界来流；特征储槽边界|本地已有；本批未验证|
|`ch02-2-9-1-04-oblique_bed` |矩形水道；横向床坡；双向深度梯度|本地已有；本批未验证|
|`ch02-2-9-1-10-compound_bed` |非对称水道；双床丘与储槽状态；多床形相互作用|本地已有；本批未验证|

### 2.9.2 全湿浅水瞬态分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-9-2-01-gaussian_hump` |封闭方池；低幅水深隆起；全湿重力波|本地已有；本批未验证|
|`ch02-2-9-2-02-wet_dam` |长池；两侧均正水深的坝溃初态；激波与稀疏波|本地已有；本批未验证|
|`ch02-2-9-2-03-radial_release` |方池；中心高水深圆区；多方向波前|本地已有；本批未验证|
|`ch02-2-9-2-04-sloshing` |长池；倾斜自由水面；反射与振荡|本地已有；本批未验证|
|`ch02-2-9-2-05-bed_bump` |含床丘的池；水位扰动；地形与重力波|本地已有；本批未验证|
|`ch02-2-9-2-06-obstacle_wave` |有岛池；入射水深脉冲；绕射|本地已有；本批未验证|
|`ch02-2-9-2-07-cross_waves` |方池；两个垂直方向水深脉冲；波相互作用|本地已有；本批未验证|
|`ch02-2-9-2-08-friction_decay` |长池；相容速度扰动、线性摩擦；动量耗散|本地已有；本批未验证|
|`ch02-2-9-2-10-uneven_bed` |非对称池；非平床、非均匀水深初态；全湿正性与床源项|本地已有；本批未验证|

### 2.9.3 干湿变化浅水瞬态分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-9-3-01-dry_dam` |长干床池；左侧水柱；干床推进|本地已有；本批未验证|
|`ch02-2-9-3-02-radial` |方干床池；中央水柱；多方向润湿|本地已有；本批未验证|
|`ch02-2-9-3-03-slope_runup` |斜坡池；低处水体向坡面推进；爬坡与回撤|本地已有；本批未验证|
|`ch02-2-9-3-04-hump_overtop` |带床丘水道；上游水柱释放；漫顶与背水干区|本地已有；本批未验证|
|`ch02-2-9-3-05-island` |有岛干床池；坝溃来流；绕岛分叉|仅远端新定位；本批未验证|
|`ch02-2-9-3-06-two_fronts` |长干池；两端水柱释放；湿润前缘相撞|本地已有；本批未验证|
|`ch02-2-9-3-07-reservoir_flood` |开水道；储槽水深随时间上升；边界洪水入射|本地已有；本批未验证|
|`ch02-2-9-3-08-drainage` |含洼地的水道；湿初态、低位储槽排水；排水与残留水洼|本地已有；本批未验证|
|`ch02-2-9-3-10-compound_topography` |分叉水道；床台阶与坝溃；地形控制的分区干湿|仅远端新定位；本批未验证|

### 2.10.3 过渡区稀薄气体稳态分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-10-3-01-pressure_duct` |三维微管；两端Maxwell储槽压差；稀薄输运与分子通量|本地已有；本批未验证|
|`ch02-2-10-3-02-thermal_duct` |三维微管；等压不同温储槽；非平衡热输运|本地已有；本批未验证|
|`ch02-2-10-3-03-couette` |有储槽的薄盒；移动Maxwell壁；壁面动量交换|本地已有；本批未验证|
|`ch02-2-10-3-04-partial_accommodation` |微管；部分镜面/漫反射壁与压差；Maxwell混合反射|本地已有；本批未验证|
|`ch02-2-10-3-05-orifice` |有小孔隔板的三维域；储槽压差；孔口分子输运|本地已有；本批未验证|
|`ch02-2-10-3-06-bend` |三维弯管；储槽驱动；弯曲壁碰撞历史|本地已有；本批未验证|
|`ch02-2-10-3-07-obstacle` |带方柱的三维管道；两端储槽驱动；阴影与绕障输运|本地已有；本批未验证|
|`ch02-2-10-3-08-thermal_wall` |三维管道；热壁区与冷壁区；热壁再发射|本地已有；本批未验证|
|`ch02-2-10-3-09-cross_reservoir` |三维分支通道；多储槽温压不同；多方向半空间边界|本地已有；本批未验证|
|`ch02-2-10-3-10-mixed_reflection` |不等长宽高盒；不同墙分区的镜面/漫反射；三维非各向同性分布|本地已有；本批未验证|

### 2.10.4 自由分子气体稳态分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-10-4-01-pressure_duct` |三维微管；两端Maxwell储槽压差；稀薄输运与分子通量|本地已有；本批未验证|
|`ch02-2-10-4-02-thermal_duct` |三维微管；等压不同温储槽；非平衡热输运|本地已有；本批未验证|
|`ch02-2-10-4-03-couette` |有储槽的薄盒；移动Maxwell壁；壁面动量交换|本地已有；本批未验证|
|`ch02-2-10-4-04-partial_accommodation` |微管；部分镜面/漫反射壁与压差；Maxwell混合反射|本地已有；本批未验证|
|`ch02-2-10-4-05-orifice` |有小孔隔板的三维域；储槽压差；孔口分子输运|本地已有；本批未验证|
|`ch02-2-10-4-06-bend` |三维弯管；储槽驱动；弯曲壁碰撞历史|本地已有；本批未验证|
|`ch02-2-10-4-07-obstacle` |带方柱的三维管道；两端储槽驱动；阴影与绕障输运|本地已有；本批未验证|
|`ch02-2-10-4-08-thermal_wall` |三维管道；热壁区与冷壁区；热壁再发射|本地已有；本批未验证|
|`ch02-2-10-4-09-cross_reservoir` |三维分支通道；多储槽温压不同；多方向半空间边界|本地已有；本批未验证|
|`ch02-2-10-4-10-mixed_reflection` |不等长宽高盒；不同墙分区的镜面/漫反射；三维非各向同性分布|本地已有；本批未验证|

### 2.11.1 黏弹性流体稳态分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-11-1-01-lid` |方腔；Oldroyd-B顶壁驱动；弹性应力与压力|本地已有；本批未验证|
|`ch02-2-11-1-02-deep` |深腔；顶壁驱动；长松弛路径|本地已有；本批未验证|
|`ch02-2-11-1-03-opposed` |矩形腔；反向双壁驱动；对向弹性剪切|本地已有；本批未验证|
|`ch02-2-11-1-04-split` |宽腔；分段相向顶壁；拉伸与剪切共存|本地已有；本批未验证|
|`ch02-2-11-1-05-obstacle` |偏心方柱腔；外顶壁驱动；绕障构象输运|本地已有；本批未验证|
|`ch02-2-11-1-06-side_drive` |方腔；相邻双壁切向运动；非对称构象|本地已有；本批未验证|
|`ch02-2-11-1-08-prestrained_or_unequal` |深腔；不等速反向壁、无物理初态；真实聚合物预应变或构象各向异性|本地已有；本批未验证|
|`ch02-2-11-1-09-relaxation_or_segments` |方腔；三段顶壁的定常驱动；松弛或多剪切层|本地已有；本批未验证|
|`ch02-2-11-1-10-reversal_or_offcentre` |非对称腔；偏心内孔附近的不等速定常壁驱动；弹性记忆或非对称拉伸|本地已有；本批未验证|

### 2.11.2 黏弹性流体瞬态分析

|case身份／别名|工况|位置与资格|
|---|---|---|
|`ch02-2-11-2-01-lid` |方腔；Oldroyd-B顶壁驱动；弹性应力与压力|本地已有；本批未验证|
|`ch02-2-11-2-02-deep` |深腔；顶壁驱动；长松弛路径|本地已有；本批未验证|
|`ch02-2-11-2-03-opposed` |矩形腔；反向双壁驱动；对向弹性剪切|本地已有；本批未验证|
|`ch02-2-11-2-04-split` |宽腔；分段相向顶壁；拉伸与剪切共存|本地已有；本批未验证|
|`ch02-2-11-2-05-obstacle` |偏心方柱腔；外顶壁驱动；绕障构象输运|本地已有；本批未验证|
|`ch02-2-11-2-06-side_drive` |方腔；相邻双壁切向运动；非对称构象|本地已有；本批未验证|
|`ch02-2-11-2-07-inlet_memory` |直通道；速度入口给定SPD构象、完整牵引出口和自然记忆流出；入口构象不能省略；无回流、不添加应力扩散|仅远端新定位；本批未验证|
|`ch02-2-11-2-08-prestrained_or_unequal` |深腔；非单位SPD构象初态与不等速反向壁；二维Azz恒为1；真实聚合物预应变或构象各向异性|本地已有；本批未验证|
|`ch02-2-11-2-09-relaxation_or_segments` |方腔；壁速撤去后的弹性松弛，保留物理构象初态；松弛或多剪切层|本地已有；本批未验证|
|`ch02-2-11-2-10-reversal_or_offcentre` |非对称腔；分段线性壁速反转，保留物理构象与速度初态；弹性记忆或非对称拉伸|本地已有；本批未验证|

## FOAMBench／CFDCodeBench

先保留有完整case的来源题进入审查；不在本轮重排章节或隐式合并题目。

|题目|范围|case|
|---|---|---|
|2.12.1 斜向来流驱动的可压缩波系（变体7）|foambench|`case-27f52d058ae3d6335081cd76`|
|2.12.2 斜向来流驱动的可压缩波系（变体6）|foambench|`case-c02f90882ff1f8c919b22646`|
|2.12.3 斜向来流驱动的可压缩波系（变体3）|foambench|`case-79f656aa8d4f9722b3876efb`|
|2.12.4 斜向来流驱动的可压缩波系（变体5）|foambench|`case-4c9d24f52f0a867303ec80d7`|
|2.12.5 斜向来流驱动的可压缩波系（变体2）|foambench|`case-279201162df4a3d84b05dd38`|
|2.12.6 斜向来流驱动的可压缩波系（变体4）|foambench|`case-b98b1c4c8ced568d69bb7aa7`|
|2.12.7 斜向来流驱动的可压缩波系（变体1）|foambench|`case-e450e5d73819642073d4551b`|
|2.12.8 斜向来流驱动的可压缩波系（变体9）|foambench|`case-3756a2985e767e3b044f2f94`|
|2.12.9 斜向来流驱动的可压缩波系（变体10）|foambench|`case-919aa1d1de218bde35b06f54`|
|2.12.10 斜向来流驱动的可压缩波系（变体8）|foambench|`case-6192e0564384567da3d22b35`|
|2.12.51 可压缩气流越过前向台阶|foambench|`case-b2f4e7a84aa661af74055212`|
|2.12.52 可压缩气流越过前向台阶|foambench|`case-b62ce67fdd6d0855d132111a`|
|2.12.53 可压缩气流越过前向台阶|foambench|`case-64c009c8dd0949242b785ead`|
|2.12.54 可压缩气流越过前向台阶|foambench|`case-7660a5daec2e96c112d7b3a6`|
|2.12.55 可压缩气流越过前向台阶|foambench|`case-a9e7c9f079b0dfaae5c6e0da`|
|2.12.56 可压缩气流越过前向台阶|foambench|`case-3ae49d3c1eabfac3e981d919`|
|2.12.57 可压缩气流越过前向台阶|foambench|`case-e64dc3260c7cf56d1af2d030`|
|2.12.58 可压缩气流越过前向台阶|foambench|`case-24ff3fe32af537810b0f5fe8`|
|2.12.59 可压缩气流越过前向台阶|foambench|`case-d1717ac28bda0e28749d4de9`|
|2.12.60 可压缩气流越过前向台阶|foambench|`case-cb2ffcb58106f3c6d4c891a0`|
|2.12.71 超声速气流与楔面斜激波|foambench|`case-12f8a73cd1a03a8f972bfb33`|
|2.12.72 超声速气流与楔面斜激波|foambench|`case-ca4c6b07122b1cbdea3f03e3`|
|2.12.73 超声速气流与楔面斜激波|foambench|`case-65560b50862e3c0c3a9157b9`|
|2.12.74 超声速气流与楔面斜激波|foambench|`case-acdedbff07aabd749981d4f7`|
|2.12.75 超声速气流与楔面斜激波|foambench|`case-70f43a583a7f70f7607422b4`|
|2.12.76 超声速气流与楔面斜激波|foambench|`case-7b4904abf71bccb59728c2c8`|
|2.12.77 超声速气流与楔面斜激波|foambench|`case-1af4dce39c723ee6ad8b31db`|
|2.12.78 超声速气流与楔面斜激波|foambench|`case-ad0f82b9093e85a1f431623d`|
|2.12.79 超声速气流与楔面斜激波|foambench|`case-39751af221996627e284ba63`|
|2.12.80 超声速气流与楔面斜激波|foambench|`case-9b555f0cc0667c720565082b`|
|2.12.87 方形浅水床突起：初始自由面 0.01 m|foambench|`case-ef7135a11149dc8a35b31873`|
|2.12.91 湍流顶盖腔流：U=2 m/s，ν=0.001 m²/s|foambench|`case-1cdb429b906d19aacb0806eb`|
|2.12.92 湍流顶盖腔流：U=2 m/s，ν=0.0001 m²/s|foambench|`case-cf99d393b1614f832fe01374`|
|2.12.93 湍流顶盖腔流：U=1.5 m/s，ν=0.0001 m²/s|foambench|`case-eec84cc9def98bcc6a24960f`|
|2.12.94 湍流顶盖腔流：U=2 m/s，ν=1e-05 m²/s|foambench|`case-30b6fb4a9e726d6ed2b637aa`|
|2.12.95 湍流顶盖腔流：U=1.5 m/s，ν=1e-05 m²/s|foambench|`case-ae6dde2b6815634ce36b7a07`|
|2.12.96 湍流顶盖腔流：U=1.5 m/s，ν=0.001 m²/s|foambench|`case-e32f5e79b60c8f7d998bd062`|
|2.12.97 湍流顶盖腔流：U=1 m/s，ν=1e-05 m²/s|foambench|`case-2f27826bfbde6dc00039dd1f`|
|2.12.98 湍流顶盖腔流：U=3 m/s，ν=0.0001 m²/s|foambench|`case-f1271496d454634c8ea2804d`|
|2.12.99 湍流顶盖腔流：U=3 m/s，ν=0.001 m²/s|foambench|`case-659491e80b1e1396a4ccea4f`|
|2.12.100 湍流顶盖腔流：U=3 m/s，ν=1e-05 m²/s|foambench|`case-7b05d815c403a02e02414400`|
|2.12.101 偏置圆柱广义牛顿绕流：U=2 m/s，ν₀=0.1 m²/s|foambench|`case-d9132aaf54601d512bc17c82`|
|2.12.102 偏置圆柱广义牛顿绕流：U=2 m/s，ν₀=0.01 m²/s|foambench|`case-7c5f9af00683926fa02a4409`|
|2.12.103 偏置圆柱广义牛顿绕流：U=1.5 m/s，ν₀=0.01 m²/s|foambench|`case-1eeb49c92dc994bac7f243c5`|
|2.12.104 偏置圆柱广义牛顿绕流：U=2 m/s，ν₀=0.001 m²/s|foambench|`case-6fd0f009fb980806c112c72f`|
|2.12.105 偏置圆柱广义牛顿绕流：U=1.5 m/s，ν₀=0.001 m²/s|foambench|`case-33ba67ca13b06786288ff2a0`|
|2.12.106 偏置圆柱广义牛顿绕流：U=1.5 m/s，ν₀=0.1 m²/s|foambench|`case-0aadb90e7757021e1af3ab14`|
|2.12.107 偏置圆柱广义牛顿绕流：U=1 m/s，ν₀=0.01 m²/s|foambench|`case-db36283e8647f222f0727ceb`|
|2.12.108 偏置圆柱广义牛顿绕流：U=3 m/s，ν₀=0.01 m²/s|foambench|`case-933e79086810a268eda90b50`|
|2.12.109 偏置圆柱广义牛顿绕流：U=3 m/s，ν₀=0.1 m²/s|foambench|`case-841346e8ceeffbada3cd24bf`|
|2.12.110 偏置圆柱广义牛顿绕流：U=3 m/s，ν₀=0.001 m²/s|foambench|`case-75cc1c96aab8ee742f475114`|
|一维周期黏性 Burgers|cfdcodebench|`case-5390882b3086ee073725ac72`|
|一维矩形初态扩散|cfdcodebench|`case-9ff31700aa9f29249ea3ed44`|
|理想气体激波管|cfdcodebench|`case-28f510a4a44974560c6d0173`|
|一维周期对流扩散|cfdcodebench|`case-3a5317962ebd9952803bf4a4`|
|一维非线性熵输运|cfdcodebench|`case-3d51485d43e942d046f0ffa1`|
|二维黏性 Burgers|cfdcodebench|`case-fc80694115ec194556222d1c`|
|二维对角熵输运（终时 0.32）|cfdcodebench|`case-d1f7ff870daaa6c0afcc590a`|
|二维矩形初态扩散|cfdcodebench|`case-5184524280c8e692870618a4`|
|二维对角熵输运（终时 0.40）|cfdcodebench|`case-704821710cfe0edbe6ef1df9`|
|矩形混合边界 Laplace 势|cfdcodebench|`case-1b37c21a82fc6c79b15c2b97`|
|二维线性脉冲平移|cfdcodebench|`case-f2da240f1c6b1d7092a18f87`|
|不可压盖驱方腔（黏度 0.01）|cfdcodebench|`case-5a50e5aa6abcd56bbe5c98ae`|
|周期通道启动流|cfdcodebench|`case-16d26ea0dfec27aa05740026`|
|双 Gaussian 源 Poisson 势|cfdcodebench|`case-3cba5b83636f310810de3bfe`|
|四边恒温矩形稳态传热|cfdcodebench|`case-04e385900f33962af70318f0`|
|Gaussian 初温与持续热源|cfdcodebench|`case-df5cb01460655c0e7683fc47`|
|Cess 闭合双壁湍流通道|cfdcodebench|`case-a2505f8e6cd8d72951d2eb72`|
|不可压盖驱方腔（黏度 0.1）|cfdcodebench|`case-2e84a351917193882c861a23`|
|圆柱外圆环涡量流函数流动|cfdcodebench|`case-8c324d7724ce2f3aa6d6e7ee`|
|周期 KdV–Burgers|cfdcodebench|`case-6fecc6bf178d5d92bbcee935`|
|二维 Rayleigh–Bénard 对流|cfdcodebench|`case-98e927bc60fb44792c1ad75b`|
|周期剪切流与被动示踪剂|cfdcodebench|`case-887658c521f21ab1f95cfc3f`|
|圆管扰动的最右增长率|cfdcodebench|`case-0cd3ba14ec4c3394600134b2`|
|Lane–Emden 正基态|cfdcodebench|`case-d0737353898e08938bf00a94`|

## FOAMBench无正式case的75题：不纳入本次发行

|题目|来源身份|
|---|---|
|2.12.11 方截面回弯管的高温湍流输运（变体7）|`squareBend/7`|
|2.12.12 方截面回弯管的高温湍流输运（变体6）|`squareBend/6`|
|2.12.13 方截面回弯管的高温湍流输运（变体3）|`squareBend/3`|
|2.12.14 方截面回弯管的高温湍流输运（变体5）|`squareBend/5`|
|2.12.15 方截面回弯管的高温湍流输运（变体2）|`squareBend/2`|
|2.12.16 方截面回弯管的高温湍流输运（变体4）|`squareBend/4`|
|2.12.17 方截面回弯管的高温湍流输运（变体1）|`squareBend/1`|
|2.12.18 方截面回弯管的高温湍流输运（变体9）|`squareBend/9`|
|2.12.19 方截面回弯管的高温湍流输运（变体10）|`squareBend/10`|
|2.12.20 方截面回弯管的高温湍流输运（变体8）|`squareBend/8`|
|2.12.21 方形障碍旁的三维溃坝与自由面（变体7）|`damBreakWithObstacle/7`|
|2.12.22 方形障碍旁的三维溃坝与自由面（变体6）|`damBreakWithObstacle/6`|
|2.12.23 方形障碍旁的三维溃坝与自由面（变体3）|`damBreakWithObstacle/3`|
|2.12.24 方形障碍旁的三维溃坝与自由面（变体5）|`damBreakWithObstacle/5`|
|2.12.25 方形障碍旁的三维溃坝与自由面（变体2）|`damBreakWithObstacle/2`|
|2.12.26 方形障碍旁的三维溃坝与自由面（变体4）|`damBreakWithObstacle/4`|
|2.12.27 方形障碍旁的三维溃坝与自由面（变体1）|`damBreakWithObstacle/1`|
|2.12.28 方形障碍旁的三维溃坝与自由面（变体9）|`damBreakWithObstacle/9`|
|2.12.29 方形障碍旁的三维溃坝与自由面（变体10）|`damBreakWithObstacle/10`|
|2.12.30 方形障碍旁的三维溃坝与自由面（变体8）|`damBreakWithObstacle/8`|
|2.12.31 后向台阶及收缩通道的非定常平均流（变体7）|`pitzDaily/7`|
|2.12.32 后向台阶及收缩通道的非定常平均流（变体6）|`pitzDaily/6`|
|2.12.33 后向台阶及收缩通道的非定常平均流（变体3）|`pitzDaily/3`|
|2.12.34 后向台阶及收缩通道的非定常平均流（变体5）|`pitzDaily/5`|
|2.12.35 后向台阶及收缩通道的非定常平均流（变体2）|`pitzDaily/2`|
|2.12.36 后向台阶及收缩通道的非定常平均流（变体4）|`pitzDaily/4`|
|2.12.37 后向台阶及收缩通道的非定常平均流（变体1）|`pitzDaily/1`|
|2.12.38 后向台阶及收缩通道的非定常平均流（变体9）|`pitzDaily/9`|
|2.12.39 后向台阶及收缩通道的非定常平均流（变体10）|`pitzDaily/10`|
|2.12.40 后向台阶及收缩通道的非定常平均流（变体8）|`pitzDaily/8`|
|2.12.41 甲烷与空气对向扩散火焰：层流|`counterFlowFlame2D/7`|
|2.12.42 甲烷与空气对向扩散火焰：层流|`counterFlowFlame2D/6`|
|2.12.43 甲烷与空气对向扩散火焰：层流|`counterFlowFlame2D/3`|
|2.12.44 甲烷与空气对向扩散火焰：层流|`counterFlowFlame2D/5`|
|2.12.45 甲烷与空气对向扩散火焰：层流|`counterFlowFlame2D/2`|
|2.12.46 甲烷与空气对向扩散火焰：层流|`counterFlowFlame2D/4`|
|2.12.47 甲烷与空气对向扩散火焰：层流|`counterFlowFlame2D/1`|
|2.12.48 甲烷与空气对向扩散火焰：层流|`counterFlowFlame2D/9`|
|2.12.49 甲烷与空气对向扩散火焰：层流|`counterFlowFlame2D/10`|
|2.12.50 甲烷与空气对向扩散火焰：层流|`counterFlowFlame2D/8`|
|2.12.61 底部加热封闭腔的贝纳德对流|`BernardCells/7`|
|2.12.62 底部加热封闭腔的贝纳德对流|`BernardCells/6`|
|2.12.63 底部加热封闭腔的贝纳德对流|`BernardCells/3`|
|2.12.64 底部加热封闭腔的贝纳德对流|`BernardCells/5`|
|2.12.65 底部加热封闭腔的贝纳德对流|`BernardCells/2`|
|2.12.66 底部加热封闭腔的贝纳德对流|`BernardCells/4`|
|2.12.67 底部加热封闭腔的贝纳德对流|`BernardCells/1`|
|2.12.68 底部加热封闭腔的贝纳德对流|`BernardCells/9`|
|2.12.69 底部加热封闭腔的贝纳德对流|`BernardCells/10`|
|2.12.70 底部加热封闭腔的贝纳德对流|`BernardCells/8`|
|2.12.81 方形浅水床突起：初始自由面 0.07 m|`shallowWaterWithSquareBump/7`|
|2.12.82 方形浅水床突起：初始自由面 0.06 m|`shallowWaterWithSquareBump/6`|
|2.12.83 方形浅水床突起：初始自由面 0.03 m|`shallowWaterWithSquareBump/3`|
|2.12.84 方形浅水床突起：初始自由面 0.05 m|`shallowWaterWithSquareBump/5`|
|2.12.85 方形浅水床突起：初始自由面 0.02 m|`shallowWaterWithSquareBump/2`|
|2.12.86 方形浅水床突起：初始自由面 0.04 m|`shallowWaterWithSquareBump/4`|
|2.12.88 方形浅水床突起：初始自由面 0.09 m|`shallowWaterWithSquareBump/9`|
|2.12.89 方形浅水床突起：初始自由面 0.1 m|`shallowWaterWithSquareBump/10`|
|2.12.90 方形浅水床突起：初始自由面 0.08 m|`shallowWaterWithSquareBump/8`|
|2.12.111 双方形障碍物 SA 非定常绕流|`Double_Square_SA`|
|2.12.112 超声速楔面 SA 非定常流动|`wedge_SA`|
|2.12.113 偏置圆柱二维滤波非定常绕流|`Cylinder_LES`|
|2.12.114 菱形障碍物 k–ω SST 非定常绕流|`Diamond_Obstacle_KOMEGASST`|
|2.12.115 0.1 m 方腔 SA 非定常流动|`Cavity_SA`|
|2.12.116 甲烷与空气对向扩散火焰：SA平均流|`counterFlowFlame2D_SA`|
|2.12.117 斜激波二维滤波流动|`obliqueShock_LES`|
|2.12.118 0.2 m 方腔 SA 非定常流动|`Cavity_geometry_1`|
|2.12.119 菱形障碍物 SA 非定常绕流|`Diamond_Obstacle_SA`|
|2.12.120 甲烷与空气对向扩散火焰：k–ε平均流|`counterFlowFlame2D_KE`|
|2.12.121 方形障碍物 SA 非定常绕流|`Rectangular_Obstacle_SA`|
|2.12.122 轴对称燃料射流 SA 两相非定常流动|`nozzleFlow2D_SA`|
|2.12.123 0.1 m 方腔二维滤波非定常流动|`Cavity_LES`|
|2.12.124 方形障碍物 k–ω SST 非定常绕流|`Rectangular_Obstacle_KOMEGASST`|
|2.12.125 斜激波 k–ε 非定常平均流动|`obliqueShock_KE`|
|2.12.126 偏置圆柱 SA 非定常绕流|`Cylinder_SA`|

## 已确认的10例选样：2.1.1与2.1.3

用户确认使用现成版本；沿用独立组合checkout的data-manifest和chapter02-existing/selection.json，不重新从大池抽样。每题另有1个format样例，与正式001共享身份，不增加独立case数。

|题号|发行编号|来源编号|稳定case ID|
|---|---|---|---|
|2.1.1|001|046|`case-afbf4209dff6115ee3c9f591`|
|2.1.1|002|047|`case-8dffd16586459938e9c4f076`|
|2.1.1|003|040|`case-608f00ddf8c82077f0f1f19a`|
|2.1.1|004|044|`case-38351d24077b5a3c28b49210`|
|2.1.1|005|050|`case-8419ad4dbae71014b508de13`|
|2.1.1|006|059|`case-344712a9e42e7905fd2d80a9`|
|2.1.1|007|052|`case-2cbdc42d6ed8d1be7fe1280c`|
|2.1.1|008|038|`case-6628b5477d34975cb5731b7f`|
|2.1.1|009|043|`case-f3722c772c68eac103c06afe`|
|2.1.1|010|074|`case-2e375f460b651ceda6acbd29`|
|2.1.3|001|001-hydrostatic-01|`case-e215683cc2c314b54af53642`|
|2.1.3|002|018-hydrostatic-18|`case-7929e5931fb708f8e70982ab`|
|2.1.3|003|030-couette-12|`case-e99f37a0e69054be6b5d77d1`|
|2.1.3|004|033-couette-15|`case-79b044a49812b3c3d80dc7a9`|
|2.1.3|005|039-periodic-duct-01|`case-7a11ab77ce9cb54ba25a06d8`|
|2.1.3|006|043-periodic-duct-05|`case-9c4f48cfb074b831f9e5af55`|
|2.1.3|007|071-cavity-13|`case-eafeb2172a7d5e4888d59edc`|
|2.1.3|008|075-cavity-17|`case-b098c03a1e9c6a6ed4bcce0e`|
|2.1.3|009|085-plug-03|`case-9f21bdd96efd2e6fcc59f801`|
|2.1.3|010|086-plug-04|`case-449ea88b437e84552cfc36c6`|

## 下一阶段的发行门槛

有完整case后，还需通过题意／来源匹配、参考资格、判分真实消费、题面自包含、资源、许可和异机获取核验。未验证、失败、模型不匹配和只有原生场的项目留在维护账本，发行导航与默认任务集不含这些空缺。正式选样是后续明确操作；本轮不删除开发题、不变更池或环境。

完整记录：[chapter02-current.json](chapter02-current.json)；逐例远端证据：[case-scan.json](case-scan.json)；新增完整性：[new-payload-hashes.json](new-payload-hashes.json)。此前全题索引见[第一轮检查稿](../../release-task-case-review.md)，仅用于追溯和查漏，不代表本轮发行范围。
