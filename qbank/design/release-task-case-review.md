# 四章题目与case检查稿（第一轮）

这是供用户核对的候选目录，不是发行清单。先核定题目与case，再做参考资格、题面修订和发行装配。本轮只读盘点本地材料及历史记录，没有下载、组装、重算或连接Titan。

建议先保留第0、1、19章既有题及选样；第2章完整列出65道能力题，并将曾经建设的126道FOAMBench题、24道CFDCodeBench题补入审核范围，等待确认取舍与重叠。没有因不在当前分支就删除历史题，也没有自动把来源题合并到能力题。

## 先看范围

|范围|本轮列出的题|case依据与本地情况|逐题逐例清单|
|---|---:|---|---|
|第0章|2|现有17正式case角色、2样例；数值载荷仍需定位或按既有生成器后续恢复|[0／1章](reviews/release-inventory-2026-10-23/ch01.md)|
|第1章|13|11个PDEBench族210正式例＋22样例已本地定位；两道热学56正式角色＋4样例角色由57个独立缓存对象覆盖|[0／1章](reviews/release-inventory-2026-10-23/ch01.md)|
|第2章能力题|65|组合checkout已有40题329例；完整来源候选830项，不与329相加|[第二章](reviews/release-inventory-2026-10-23/ch02.md)|
|第2章FOAMBench历史题|126|51题各1例本地正式输入／参考；其余75题保留题面和来源，未定位正式case|[第二章附录](reviews/release-inventory-2026-10-23/ch02.md)|
|第2章CFDCodeBench历史题|24|每题1例，共24例本地正式输入／参考；另作format样例，同例不重复计数|[CFDCodeBench](reviews/release-inventory-2026-10-23/cfdcodebench.md)|
|第19章|22|252正式case，44公开样例与正式case重叠；本地输入／参考均存在|[第十九章](reviews/release-inventory-2026-10-23/ch19.md)|

原来102题只覆盖主工作树有题面的目录；追加150个历史来源题后，本轮共列252个题目条目，其中150项的最终纳入及章节组织待用户核定。题数、case数、来源候选数和副本数分别统计，不能相加充当就绪规模。

## 需要优先检查的边界

- 第2章：65道能力题与126＋24道历史来源题，哪些独立保留、哪些应作为既有问题族的case？本轮全部列出，未擅自合并。
- 2.1.1：本地100项候选，组合checkout只选10项；2.1.3：历史100项生产记录中72项通过、28项失败，72项实体已本地定位，组合checkout只选10项。请检查最终需要的覆盖，失败28项不计通过集合。
- 其余63题：每题原有10项设计，共630；309项已运输到本地并用于组合选样，仍明确未验证。历史running等状态仅是旧快照，不能视为实时生产状态。
- 第2章已有329例＝20项既有参考＋309项未验证候选。已装配不等于数值可信；这批数据不需要为盘点再次从HF取回。
- PDEBench的22样例：当前独立checkout已改为format，旧combined-pools仍留数值样例；相同case ID但描述SHA不同，不能混用。210正式例与样例分开。
- 热学存在3个样例／正式身份重用关系；修复题44个样例也与正式case重叠。清单保留这些关系，未重复算独立case。
- 不同checkout的task_id及题面版本可能分叉；先按路径、来源与case身份关联，最终发行前再确定稳定身份，不能覆盖旧记录。

## 全部题目索引

逐例内容、稳定ID、来源、角色、状态及路径在上方分章材料；可使用[可搜索的检查视图](reviews/release-inventory-2026-10-23/review.html)按题名、case ID或工况检索。现有选样与候选在不同表中展示，表的条目数不是独立case总数。

### 第0章

|题目|现有选样／待核定范围|
|---|---|
|简单测试 · `smoke-test`|11条角色记录；详见逐例清单|
|Case 判题链路测试 · `case-grading-test`|8条角色记录；详见逐例清单|

### 第1章

|题目|现有选样／待核定范围|
|---|---|
|二维空间变系数 Darcy 型稳态问题 · `darcy-flow-2d`|22条角色记录；详见逐例清单|
|二维稳态热传导 · `heat-conduction-steady-2d`|34条角色记录；详见逐例清单|
|一维 Freundlich 迟滞扩散 · `diffusion-sorption-1d`|18条角色记录；详见逐例清单|
|二维瞬态热传导 · `heat-conduction-transient-2d`|26条角色记录；详见逐例清单|
|一维 logistic 反应扩散 · `reaction-diffusion-1d`|34条角色记录；详见逐例清单|
|二维 FitzHugh–Nagumo 反应扩散 · `reaction-diffusion-2d`|18条角色记录；详见逐例清单|
|一维周期线性平流 · `advection-1d`|26条角色记录；详见逐例清单|
|二维浅水方程 · `shallow-water-2d`|18条角色记录；详见逐例清单|
|一维周期黏性 Burgers 方程 · `burgers-1d`|26条角色记录；详见逐例清单|
|二维非均匀强迫不可压缩流 · `incompressible-navier-stokes-2d`|18条角色记录；详见逐例清单|
|一维可压缩 Navier–Stokes · `compressible-navier-stokes-1d`|18条角色记录；详见逐例清单|
|二维可压缩 Navier–Stokes · `compressible-navier-stokes-2d`|26条角色记录；详见逐例清单|
|三维可压缩 Navier–Stokes · `compressible-navier-stokes-3d`|8条角色记录；详见逐例清单|

### 第2章·能力题

|题目|现有选样／待核定范围|
|---|---|
|2.1.5 2D 非牛顿流体不可压缩流动稳态分析 · `generalized-newtonian-incompressible-steady-2d`|组合选样8；来源候选10|
|2.1.7 3D 非牛顿流体不可压缩流动稳态分析 · `generalized-newtonian-incompressible-steady-3d`|组合选样7；来源候选10|
|2.1.6 2D 非牛顿流体不可压缩流动瞬态分析 · `generalized-newtonian-incompressible-transient-2d`|组合选样8；来源候选10|
|2.1.8 3D 非牛顿流体不可压缩流动瞬态分析 · `generalized-newtonian-incompressible-transient-3d`|组合选样8；来源候选10|
|2.1.1 2D 常黏度牛顿流体不可压缩流动稳态分析 · `newtonian-incompressible-steady-2d`|组合选样10；来源候选100|
|2.1.3 3D 常黏度牛顿流体不可压缩流动稳态分析 · `newtonian-incompressible-steady-3d`|组合选样10；来源候选100|
|2.1.2 2D 常黏度牛顿流体不可压缩流动瞬态分析 · `newtonian-incompressible-transient-2d`|组合选样10；来源候选10|
|2.1.4 3D 常黏度牛顿流体不可压缩流动瞬态分析 · `newtonian-incompressible-transient-3d`|组合选样10；来源候选10|
|2.1.9 2D 常黏度牛顿流体等温可压缩流动稳态分析 · `newtonian-isothermal-compressible-steady-2d`|组合选样3；来源候选10|
|2.1.11 3D 常黏度牛顿流体等温可压缩流动稳态分析 · `newtonian-isothermal-compressible-steady-3d`|组合选样3；来源候选10|
|2.1.10 2D 常黏度牛顿流体等温可压缩流动瞬态分析 · `newtonian-isothermal-compressible-transient-2d`|组合选样5；来源候选10|
|2.1.12 3D 常黏度牛顿流体等温可压缩流动瞬态分析 · `newtonian-isothermal-compressible-transient-3d`|组合选样5；来源候选10|
|2.10.4 自由分子气体稳态分析 · `free-molecular`|组合选样10；来源候选10|
|2.10.1 等温滑移气体稳态分析 · `isothermal-slip`|组合选样0；来源候选10|
|2.10.2 非等温滑移气体稳态分析 · `thermal-slip`|组合选样0；来源候选10|
|2.10.3 过渡区稀薄气体稳态分析 · `transition-gas`|组合选样10；来源候选10|
|2.11.4 非等温广义牛顿流体瞬态分析 · `thermal-generalized-newtonian`|组合选样0；来源候选10|
|2.11.5 非等温黏弹性流体瞬态分析 · `thermal-viscoelastic`|组合选样0；来源候选10|
|2.11.3 触变结构演化瞬态分析 · `thixotropic-transient`|组合选样0；来源候选10|
|2.11.1 黏弹性流体稳态分析 · `viscoelastic-steady`|组合选样9；来源候选10|
|2.11.2 黏弹性流体瞬态分析 · `viscoelastic-transient`|组合选样9；来源候选10|
|2.2.5 2D 无黏可压缩流动稳态分析 · `inviscid-compressible-steady-2d`|组合选样10；来源候选10|
|2.2.7 3D 无黏可压缩流动稳态分析 · `inviscid-compressible-steady-3d`|组合选样10；来源候选10|
|2.2.6 2D 无黏可压缩流动瞬态分析 · `inviscid-compressible-transient-2d`|组合选样10；来源候选10|
|2.2.8 3D 无黏可压缩流动瞬态分析 · `inviscid-compressible-transient-3d`|组合选样10；来源候选10|
|2.2.9 2D 牛顿流体可压缩流动与传热稳态分析 · `newtonian-compressible-steady-2d`|组合选样0；来源候选10|
|2.2.11 3D 牛顿流体可压缩流动与传热稳态分析 · `newtonian-compressible-steady-3d`|组合选样0；来源候选10|
|2.2.10 2D 牛顿流体可压缩流动与传热瞬态分析 · `newtonian-compressible-transient-2d`|组合选样5；来源候选10|
|2.2.12 3D 牛顿流体可压缩流动与传热瞬态分析 · `newtonian-compressible-transient-3d`|组合选样5；来源候选10|
|2.2.1 2D 牛顿流体低速流动与传热稳态分析 · `newtonian-lowmach-steady-2d`|组合选样10；来源候选10|
|2.2.3 3D 牛顿流体低速流动与传热稳态分析 · `newtonian-lowmach-steady-3d`|组合选样10；来源候选10|
|2.2.2 2D 牛顿流体低速流动与传热瞬态分析 · `newtonian-lowmach-transient-2d`|组合选样10；来源候选10|
|2.2.4 3D 牛顿流体低速流动与传热瞬态分析 · `newtonian-lowmach-transient-3d`|组合选样10；来源候选10|
|2.3.5 3D 等温可压缩湍流定常平均分析 · `isothermal-rans-3d`|组合选样7；来源候选10|
|2.3.1 2D 不可压缩湍流定常平均分析 · `rans-steady-2d`|组合选样8；来源候选10|
|2.3.2 3D 不可压缩湍流定常平均分析 · `rans-steady-3d`|组合选样7；来源候选10|
|2.3.4 3D 不可压缩湍流尺度解析统计分析 · `resolved-statistics-3d`|组合选样10；来源候选10|
|2.3.3 3D 不可压缩湍流非定常平均分析 · `urans-transient-3d`|组合选样10；来源候选10|
|2.4.4 3D 可压缩湍流传热定常平均分析 · `compressible-thermal-rans-3d`|组合选样0；来源候选10|
|2.4.1 3D 低速湍流传热定常平均分析 · `thermal-rans-3d`|组合选样9；来源候选10|
|2.4.3 3D 低速湍流传热尺度解析统计分析 · `thermal-statistics-3d`|组合选样10；来源候选10|
|2.4.2 3D 低速湍流传热非定常平均分析 · `thermal-urans-3d`|组合选样4；来源候选10|
|2.5.5 二维毛细与润湿瞬态流动 · `capillary-wetting-2d`|组合选样0；来源候选10|
|2.5.6 三维毛细与润湿瞬态流动 · `capillary-wetting-3d`|组合选样0；来源候选10|
|2.5.1 二维自由液面瞬态流动 · `free-surface-2d`|组合选样0；来源候选10|
|2.5.2 三维自由液面瞬态流动 · `free-surface-3d`|组合选样0；来源候选10|
|2.5.3 二维不混溶双流体界面瞬态流动 · `immiscible-interface-2d`|组合选样10；来源候选10|
|2.5.4 三维不混溶双流体界面瞬态流动 · `immiscible-interface-3d`|组合选样10；来源候选10|
|2.6.3 三维气泡与液滴分散输运 · `bubbles-droplets-3d`|组合选样0；来源候选10|
|2.6.2 三维颗粒双向动量反馈 · `coupled-particles-3d`|组合选样0；来源候选10|
|2.6.4 三维高浓度分散相流动 · `dense-dispersed-3d`|组合选样0；来源候选10|
|2.6.1 三维稀疏颗粒单向输运 · `passive-particles-3d`|组合选样0；来源候选10|
|2.7.3 三维均匀混合沸腾流动 · `boiling-3d`|组合选样0；来源候选10|
|2.7.4 三维等温空化流动 · `cavitation-3d`|组合选样0；来源候选10|
|2.7.2 二维蒸发冷凝界面流动 · `evaporation-condensation-2d`|组合选样0；来源候选10|
|2.7.1 三维不相变相间热质交换 · `interphase-exchange-3d`|组合选样0；来源候选10|
|2.7.5 二维熔化凝固伴随流动 · `melting-solidification-2d`|组合选样0；来源候选10|
|2.8.2 可压缩气膜润滑瞬态分析 · `gas-film`|组合选样10；来源候选10|
|2.8.1 等温液体薄膜润滑稳态分析 · `liquid-lubrication`|组合选样0；来源候选10|
|2.8.4 广义牛顿液体薄膜稳态分析 · `nonnewtonian-film`|组合选样0；来源候选10|
|2.8.3 非等温液体薄膜瞬态分析 · `thermal-film`|组合选样0；来源候选10|
|2.9.1 全湿浅水稳态分析 · `fully-wet-steady`|组合选样3；来源候选10|
|2.9.2 全湿浅水瞬态分析 · `fully-wet-transient`|组合选样9；来源候选10|
|2.9.4 两层深度平均流动瞬态分析 · `two-layer`|组合选样0；来源候选10|
|2.9.3 干湿变化浅水瞬态分析 · `wetting-drying`|组合选样7；来源候选10|

### 第2章·FOAMBench历史题

|题目|现有选样／待核定范围|
|---|---|
|2.12.118 0.2 m 方腔 SA 非定常流动 · `fb-advanced-cavity-geometry-1`|保留来源／题面；正式case待定位|
|2.12.123 0.1 m 方腔二维滤波非定常流动 · `fb-advanced-cavity-les`|保留来源／题面；正式case待定位|
|2.12.115 0.1 m 方腔 SA 非定常流动 · `fb-advanced-cavity-sa`|保留来源／题面；正式case待定位|
|2.12.120 甲烷与空气对向扩散火焰：k–ε平均流 · `fb-advanced-counterflowflame2d-ke`|保留来源／题面；正式case待定位|
|2.12.116 甲烷与空气对向扩散火焰：SA平均流 · `fb-advanced-counterflowflame2d-sa`|保留来源／题面；正式case待定位|
|2.12.113 偏置圆柱二维滤波非定常绕流 · `fb-advanced-cylinder-les`|保留来源／题面；正式case待定位|
|2.12.126 偏置圆柱 SA 非定常绕流 · `fb-advanced-cylinder-sa`|保留来源／题面；正式case待定位|
|2.12.114 菱形障碍物 k–ω SST 非定常绕流 · `fb-advanced-diamond-obstacle-komegasst`|保留来源／题面；正式case待定位|
|2.12.119 菱形障碍物 SA 非定常绕流 · `fb-advanced-diamond-obstacle-sa`|保留来源／题面；正式case待定位|
|2.12.111 双方形障碍物 SA 非定常绕流 · `fb-advanced-double-square-sa`|保留来源／题面；正式case待定位|
|2.12.122 轴对称燃料射流 SA 两相非定常流动 · `fb-advanced-nozzleflow2d-sa`|保留来源／题面；正式case待定位|
|2.12.125 斜激波 k–ε 非定常平均流动 · `fb-advanced-obliqueshock-ke`|保留来源／题面；正式case待定位|
|2.12.117 斜激波二维滤波流动 · `fb-advanced-obliqueshock-les`|保留来源／题面；正式case待定位|
|2.12.124 方形障碍物 k–ω SST 非定常绕流 · `fb-advanced-rectangular-obstacle-komegasst`|保留来源／题面；正式case待定位|
|2.12.121 方形障碍物 SA 非定常绕流 · `fb-advanced-rectangular-obstacle-sa`|保留来源／题面；正式case待定位|
|2.12.112 超声速楔面 SA 非定常流动 · `fb-advanced-wedge-sa`|保留来源／题面；正式case待定位|
|2.12.67 底部加热封闭腔的贝纳德对流 · `fb-basic-bernardcells-1`|保留来源／题面；正式case待定位|
|2.12.69 底部加热封闭腔的贝纳德对流 · `fb-basic-bernardcells-10`|保留来源／题面；正式case待定位|
|2.12.65 底部加热封闭腔的贝纳德对流 · `fb-basic-bernardcells-2`|保留来源／题面；正式case待定位|
|2.12.63 底部加热封闭腔的贝纳德对流 · `fb-basic-bernardcells-3`|保留来源／题面；正式case待定位|
|2.12.66 底部加热封闭腔的贝纳德对流 · `fb-basic-bernardcells-4`|保留来源／题面；正式case待定位|
|2.12.64 底部加热封闭腔的贝纳德对流 · `fb-basic-bernardcells-5`|保留来源／题面；正式case待定位|
|2.12.62 底部加热封闭腔的贝纳德对流 · `fb-basic-bernardcells-6`|保留来源／题面；正式case待定位|
|2.12.61 底部加热封闭腔的贝纳德对流 · `fb-basic-bernardcells-7`|保留来源／题面；正式case待定位|
|2.12.70 底部加热封闭腔的贝纳德对流 · `fb-basic-bernardcells-8`|保留来源／题面；正式case待定位|
|2.12.68 底部加热封闭腔的贝纳德对流 · `fb-basic-bernardcells-9`|保留来源／题面；正式case待定位|
|2.12.97 湍流顶盖腔流：U=1 m/s，ν=1e-05 m²/s · `fb-basic-cavity-1`|本地1例|
|2.12.99 湍流顶盖腔流：U=3 m/s，ν=0.001 m²/s · `fb-basic-cavity-10`|本地1例|
|2.12.95 湍流顶盖腔流：U=1.5 m/s，ν=1e-05 m²/s · `fb-basic-cavity-2`|本地1例|
|2.12.93 湍流顶盖腔流：U=1.5 m/s，ν=0.0001 m²/s · `fb-basic-cavity-3`|本地1例|
|2.12.96 湍流顶盖腔流：U=1.5 m/s，ν=0.001 m²/s · `fb-basic-cavity-4`|本地1例|
|2.12.94 湍流顶盖腔流：U=2 m/s，ν=1e-05 m²/s · `fb-basic-cavity-5`|本地1例|
|2.12.92 湍流顶盖腔流：U=2 m/s，ν=0.0001 m²/s · `fb-basic-cavity-6`|本地1例|
|2.12.91 湍流顶盖腔流：U=2 m/s，ν=0.001 m²/s · `fb-basic-cavity-7`|本地1例|
|2.12.100 湍流顶盖腔流：U=3 m/s，ν=1e-05 m²/s · `fb-basic-cavity-8`|本地1例|
|2.12.98 湍流顶盖腔流：U=3 m/s，ν=0.0001 m²/s · `fb-basic-cavity-9`|本地1例|
|2.12.47 甲烷与空气对向扩散火焰：层流 · `fb-basic-counterflowflame2d-1`|保留来源／题面；正式case待定位|
|2.12.49 甲烷与空气对向扩散火焰：层流 · `fb-basic-counterflowflame2d-10`|保留来源／题面；正式case待定位|
|2.12.45 甲烷与空气对向扩散火焰：层流 · `fb-basic-counterflowflame2d-2`|保留来源／题面；正式case待定位|
|2.12.43 甲烷与空气对向扩散火焰：层流 · `fb-basic-counterflowflame2d-3`|保留来源／题面；正式case待定位|
|2.12.46 甲烷与空气对向扩散火焰：层流 · `fb-basic-counterflowflame2d-4`|保留来源／题面；正式case待定位|
|2.12.44 甲烷与空气对向扩散火焰：层流 · `fb-basic-counterflowflame2d-5`|保留来源／题面；正式case待定位|
|2.12.42 甲烷与空气对向扩散火焰：层流 · `fb-basic-counterflowflame2d-6`|保留来源／题面；正式case待定位|
|2.12.41 甲烷与空气对向扩散火焰：层流 · `fb-basic-counterflowflame2d-7`|保留来源／题面；正式case待定位|
|2.12.50 甲烷与空气对向扩散火焰：层流 · `fb-basic-counterflowflame2d-8`|保留来源／题面；正式case待定位|
|2.12.48 甲烷与空气对向扩散火焰：层流 · `fb-basic-counterflowflame2d-9`|保留来源／题面；正式case待定位|
|2.12.107 偏置圆柱广义牛顿绕流：U=1 m/s，ν₀=0.01 m²/s · `fb-basic-cylinder-1`|本地1例|
|2.12.109 偏置圆柱广义牛顿绕流：U=3 m/s，ν₀=0.1 m²/s · `fb-basic-cylinder-10`|本地1例|
|2.12.105 偏置圆柱广义牛顿绕流：U=1.5 m/s，ν₀=0.001 m²/s · `fb-basic-cylinder-2`|本地1例|
|2.12.103 偏置圆柱广义牛顿绕流：U=1.5 m/s，ν₀=0.01 m²/s · `fb-basic-cylinder-3`|本地1例|
|2.12.106 偏置圆柱广义牛顿绕流：U=1.5 m/s，ν₀=0.1 m²/s · `fb-basic-cylinder-4`|本地1例|
|2.12.104 偏置圆柱广义牛顿绕流：U=2 m/s，ν₀=0.001 m²/s · `fb-basic-cylinder-5`|本地1例|
|2.12.102 偏置圆柱广义牛顿绕流：U=2 m/s，ν₀=0.01 m²/s · `fb-basic-cylinder-6`|本地1例|
|2.12.101 偏置圆柱广义牛顿绕流：U=2 m/s，ν₀=0.1 m²/s · `fb-basic-cylinder-7`|本地1例|
|2.12.110 偏置圆柱广义牛顿绕流：U=3 m/s，ν₀=0.001 m²/s · `fb-basic-cylinder-8`|本地1例|
|2.12.108 偏置圆柱广义牛顿绕流：U=3 m/s，ν₀=0.01 m²/s · `fb-basic-cylinder-9`|本地1例|
|2.12.27 方形障碍旁的三维溃坝与自由面（变体1） · `fb-basic-dambreakwithobstacle-1`|保留来源／题面；正式case待定位|
|2.12.29 方形障碍旁的三维溃坝与自由面（变体10） · `fb-basic-dambreakwithobstacle-10`|保留来源／题面；正式case待定位|
|2.12.25 方形障碍旁的三维溃坝与自由面（变体2） · `fb-basic-dambreakwithobstacle-2`|保留来源／题面；正式case待定位|
|2.12.23 方形障碍旁的三维溃坝与自由面（变体3） · `fb-basic-dambreakwithobstacle-3`|保留来源／题面；正式case待定位|
|2.12.26 方形障碍旁的三维溃坝与自由面（变体4） · `fb-basic-dambreakwithobstacle-4`|保留来源／题面；正式case待定位|
|2.12.24 方形障碍旁的三维溃坝与自由面（变体5） · `fb-basic-dambreakwithobstacle-5`|保留来源／题面；正式case待定位|
|2.12.22 方形障碍旁的三维溃坝与自由面（变体6） · `fb-basic-dambreakwithobstacle-6`|保留来源／题面；正式case待定位|
|2.12.21 方形障碍旁的三维溃坝与自由面（变体7） · `fb-basic-dambreakwithobstacle-7`|保留来源／题面；正式case待定位|
|2.12.30 方形障碍旁的三维溃坝与自由面（变体8） · `fb-basic-dambreakwithobstacle-8`|保留来源／题面；正式case待定位|
|2.12.28 方形障碍旁的三维溃坝与自由面（变体9） · `fb-basic-dambreakwithobstacle-9`|保留来源／题面；正式case待定位|
|2.12.57 可压缩气流越过前向台阶 · `fb-basic-forwardstep-1`|本地1例|
|2.12.59 可压缩气流越过前向台阶 · `fb-basic-forwardstep-10`|本地1例|
|2.12.55 可压缩气流越过前向台阶 · `fb-basic-forwardstep-2`|本地1例|
|2.12.53 可压缩气流越过前向台阶 · `fb-basic-forwardstep-3`|本地1例|
|2.12.56 可压缩气流越过前向台阶 · `fb-basic-forwardstep-4`|本地1例|
|2.12.54 可压缩气流越过前向台阶 · `fb-basic-forwardstep-5`|本地1例|
|2.12.52 可压缩气流越过前向台阶 · `fb-basic-forwardstep-6`|本地1例|
|2.12.51 可压缩气流越过前向台阶 · `fb-basic-forwardstep-7`|本地1例|
|2.12.60 可压缩气流越过前向台阶 · `fb-basic-forwardstep-8`|本地1例|
|2.12.58 可压缩气流越过前向台阶 · `fb-basic-forwardstep-9`|本地1例|
|2.12.7 斜向来流驱动的可压缩波系（变体1） · `fb-basic-obliqueshock-1`|本地1例|
|2.12.9 斜向来流驱动的可压缩波系（变体10） · `fb-basic-obliqueshock-10`|本地1例|
|2.12.5 斜向来流驱动的可压缩波系（变体2） · `fb-basic-obliqueshock-2`|本地1例|
|2.12.3 斜向来流驱动的可压缩波系（变体3） · `fb-basic-obliqueshock-3`|本地1例|
|2.12.6 斜向来流驱动的可压缩波系（变体4） · `fb-basic-obliqueshock-4`|本地1例|
|2.12.4 斜向来流驱动的可压缩波系（变体5） · `fb-basic-obliqueshock-5`|本地1例|
|2.12.2 斜向来流驱动的可压缩波系（变体6） · `fb-basic-obliqueshock-6`|本地1例|
|2.12.1 斜向来流驱动的可压缩波系（变体7） · `fb-basic-obliqueshock-7`|本地1例|
|2.12.10 斜向来流驱动的可压缩波系（变体8） · `fb-basic-obliqueshock-8`|本地1例|
|2.12.8 斜向来流驱动的可压缩波系（变体9） · `fb-basic-obliqueshock-9`|本地1例|
|2.12.37 后向台阶及收缩通道的非定常平均流（变体1） · `fb-basic-pitzdaily-1`|保留来源／题面；正式case待定位|
|2.12.39 后向台阶及收缩通道的非定常平均流（变体10） · `fb-basic-pitzdaily-10`|保留来源／题面；正式case待定位|
|2.12.35 后向台阶及收缩通道的非定常平均流（变体2） · `fb-basic-pitzdaily-2`|保留来源／题面；正式case待定位|
|2.12.33 后向台阶及收缩通道的非定常平均流（变体3） · `fb-basic-pitzdaily-3`|保留来源／题面；正式case待定位|
|2.12.36 后向台阶及收缩通道的非定常平均流（变体4） · `fb-basic-pitzdaily-4`|保留来源／题面；正式case待定位|
|2.12.34 后向台阶及收缩通道的非定常平均流（变体5） · `fb-basic-pitzdaily-5`|保留来源／题面；正式case待定位|
|2.12.32 后向台阶及收缩通道的非定常平均流（变体6） · `fb-basic-pitzdaily-6`|保留来源／题面；正式case待定位|
|2.12.31 后向台阶及收缩通道的非定常平均流（变体7） · `fb-basic-pitzdaily-7`|保留来源／题面；正式case待定位|
|2.12.40 后向台阶及收缩通道的非定常平均流（变体8） · `fb-basic-pitzdaily-8`|保留来源／题面；正式case待定位|
|2.12.38 后向台阶及收缩通道的非定常平均流（变体9） · `fb-basic-pitzdaily-9`|保留来源／题面；正式case待定位|
|2.12.87 方形浅水床突起：初始自由面 0.01 m · `fb-basic-shallowwaterwithsquarebump-1`|本地1例|
|2.12.89 方形浅水床突起：初始自由面 0.1 m · `fb-basic-shallowwaterwithsquarebump-10`|保留来源／题面；正式case待定位|
|2.12.85 方形浅水床突起：初始自由面 0.02 m · `fb-basic-shallowwaterwithsquarebump-2`|保留来源／题面；正式case待定位|
|2.12.83 方形浅水床突起：初始自由面 0.03 m · `fb-basic-shallowwaterwithsquarebump-3`|保留来源／题面；正式case待定位|
|2.12.86 方形浅水床突起：初始自由面 0.04 m · `fb-basic-shallowwaterwithsquarebump-4`|保留来源／题面；正式case待定位|
|2.12.84 方形浅水床突起：初始自由面 0.05 m · `fb-basic-shallowwaterwithsquarebump-5`|保留来源／题面；正式case待定位|
|2.12.82 方形浅水床突起：初始自由面 0.06 m · `fb-basic-shallowwaterwithsquarebump-6`|保留来源／题面；正式case待定位|
|2.12.81 方形浅水床突起：初始自由面 0.07 m · `fb-basic-shallowwaterwithsquarebump-7`|保留来源／题面；正式case待定位|
|2.12.90 方形浅水床突起：初始自由面 0.08 m · `fb-basic-shallowwaterwithsquarebump-8`|保留来源／题面；正式case待定位|
|2.12.88 方形浅水床突起：初始自由面 0.09 m · `fb-basic-shallowwaterwithsquarebump-9`|保留来源／题面；正式case待定位|
|2.12.17 方截面回弯管的高温湍流输运（变体1） · `fb-basic-squarebend-1`|保留来源／题面；正式case待定位|
|2.12.19 方截面回弯管的高温湍流输运（变体10） · `fb-basic-squarebend-10`|保留来源／题面；正式case待定位|
|2.12.15 方截面回弯管的高温湍流输运（变体2） · `fb-basic-squarebend-2`|保留来源／题面；正式case待定位|
|2.12.13 方截面回弯管的高温湍流输运（变体3） · `fb-basic-squarebend-3`|保留来源／题面；正式case待定位|
|2.12.16 方截面回弯管的高温湍流输运（变体4） · `fb-basic-squarebend-4`|保留来源／题面；正式case待定位|
|2.12.14 方截面回弯管的高温湍流输运（变体5） · `fb-basic-squarebend-5`|保留来源／题面；正式case待定位|
|2.12.12 方截面回弯管的高温湍流输运（变体6） · `fb-basic-squarebend-6`|保留来源／题面；正式case待定位|
|2.12.11 方截面回弯管的高温湍流输运（变体7） · `fb-basic-squarebend-7`|保留来源／题面；正式case待定位|
|2.12.20 方截面回弯管的高温湍流输运（变体8） · `fb-basic-squarebend-8`|保留来源／题面；正式case待定位|
|2.12.18 方截面回弯管的高温湍流输运（变体9） · `fb-basic-squarebend-9`|保留来源／题面；正式case待定位|
|2.12.77 超声速气流与楔面斜激波 · `fb-basic-wedge-1`|本地1例|
|2.12.79 超声速气流与楔面斜激波 · `fb-basic-wedge-10`|本地1例|
|2.12.75 超声速气流与楔面斜激波 · `fb-basic-wedge-2`|本地1例|
|2.12.73 超声速气流与楔面斜激波 · `fb-basic-wedge-3`|本地1例|
|2.12.76 超声速气流与楔面斜激波 · `fb-basic-wedge-4`|本地1例|
|2.12.74 超声速气流与楔面斜激波 · `fb-basic-wedge-5`|本地1例|
|2.12.72 超声速气流与楔面斜激波 · `fb-basic-wedge-6`|本地1例|
|2.12.71 超声速气流与楔面斜激波 · `fb-basic-wedge-7`|本地1例|
|2.12.80 超声速气流与楔面斜激波 · `fb-basic-wedge-8`|本地1例|
|2.12.78 超声速气流与楔面斜激波 · `fb-basic-wedge-9`|本地1例|

### 第2章·CFDCodeBench历史题

|题目|现有选样／待核定范围|
|---|---|
|一维周期黏性 Burgers · `cc-1d-burgers-equation`|1条角色记录；详见逐例清单|
|一维矩形初态扩散 · `cc-1d-diffusion`|1条角色记录；详见逐例清单|
|理想气体激波管 · `cc-1d-euler-shock-tube`|1条角色记录；详见逐例清单|
|周期 KdV–Burgers · `cc-1d-kdv-burgers-equation`|1条角色记录；详见逐例清单|
|一维周期对流扩散 · `cc-1d-linear-convection`|1条角色记录；详见逐例清单|
|一维非线性熵输运 · `cc-1d-nonlinear-convection`|1条角色记录；详见逐例清单|
|二维黏性 Burgers · `cc-2d-burgers-equation`|1条角色记录；详见逐例清单|
|二维对角熵输运（终时 0.32） · `cc-2d-convection`|1条角色记录；详见逐例清单|
|二维矩形初态扩散 · `cc-2d-diffusion`|1条角色记录；详见逐例清单|
|二维对角熵输运（终时 0.40） · `cc-2d-inviscid-burgers`|1条角色记录；详见逐例清单|
|矩形混合边界 Laplace 势 · `cc-2d-laplace-equation`|1条角色记录；详见逐例清单|
|二维线性脉冲平移 · `cc-2d-linear-convection`|1条角色记录；详见逐例清单|
|不可压盖驱方腔（黏度 0.01） · `cc-2d-navier-stokes-cavity`|1条角色记录；详见逐例清单|
|周期通道启动流 · `cc-2d-navier-stokes-channel`|1条角色记录；详见逐例清单|
|双 Gaussian 源 Poisson 势 · `cc-2d-poisson-equation`|1条角色记录；详见逐例清单|
|二维 Rayleigh–Bénard 对流 · `cc-2d-rayleigh-benard-convection`|1条角色记录；详见逐例清单|
|周期剪切流与被动示踪剂 · `cc-2d-shear-flow-with-tracer`|1条角色记录；详见逐例清单|
|四边恒温矩形稳态传热 · `cc-2d-steady-heat-equation`|1条角色记录；详见逐例清单|
|Gaussian 初温与持续热源 · `cc-2d-unsteady-heat-equation`|1条角色记录；详见逐例清单|
|圆柱外圆环涡量流函数流动 · `cc-flow-past-circular-cylinder`|1条角色记录；详见逐例清单|
|Cess 闭合双壁湍流通道 · `cc-fully-developed-turbulent-channel-flow`|1条角色记录；详见逐例清单|
|Lane–Emden 正基态 · `cc-lane-emden-equation`|1条角色记录；详见逐例清单|
|不可压盖驱方腔（黏度 0.1） · `cc-lid-driven-cavity`|1条角色记录；详见逐例清单|
|圆管扰动的最右增长率 · `cc-pipe-flow-disk-evp`|1条角色记录；详见逐例清单|

### 第19章

|题目|现有选样／待核定范围|
|---|---|
|19.1.1 双边距离约束系统的加速度与反力求值 · `constrained-assembly-repair`|20条角色记录；详见逐例清单|
|滞回材料试探状态恢复 · `hysteretic-trial-state-repair`|10条角色记录；详见逐例清单|
|巨势材料系数的一致导数 · `grand-potential-derivatives-repair`|12条角色记录；详见逐例清单|
|空间梁方向变换修复 · `spatial-beam-transform-repair`|10条角色记录；详见逐例清单|
|变形边界切向约束修复 · `deformed-tangential-boundary-repair`|12条角色记录；详见逐例清单|
|漂移与热扩散的浓度单位一致性 · `migration-soret-scaling-repair`|12条角色记录；详见逐例清单|
|19.3.4 多占位表面浓度与耦合管流修复 · `multisite-surface-concentration-repair`|9条角色记录；详见逐例清单|
|重构状态的能量一致性修复 · `reconstructed-energy-repair`|9条角色记录；详见逐例清单|
|19.3.2 表面反应管流物种约束修复 · `surface-flow-constraint-repair`|9条角色记录；详见逐例清单|
|19.3.3 双温等离子体状态关系修复 · `two-temperature-state-repair`|12条角色记录；详见逐例清单|
|19.4.2 扩散元件的电压贡献与热功率 · `diffusion-element-heat-repair`|16条角色记录；详见逐例清单|
|19.4.1 梯度电极的锂库存观测修复 · `graded-electrode-inventory-repair`|14条角色记录；详见逐例清单|
|瞬时颗粒应力修复 · `granular-pair-stress-repair`|12条角色记录；详见逐例清单|
|19.4.3 开路电势滞回的热源修复 · `hysteresis-heat-repair`|14条角色记录；详见逐例清单|
|固流传热能量观测接口修复 · `solid-fluid-energy-observation-repair`|12条角色记录；详见逐例清单|
|壁面能量离散与热流报告修复 · `wall-heat-flux-repair`|10条角色记录；详见逐例清单|
|19.5.2 最近投影与单元插值回退修复 · `nearest-projection-repair`|10条角色记录；详见逐例清单|
|19.5.1 域外点归属与可选外推修复 · `point-ownership-repair`|12条角色记录；详见逐例清单|
|复波数 Helmholtz 快速算子修复 · `complex-helmholtz-fmm-repair`|12条角色记录；详见逐例清单|
|柱坐标波场与吸收层修复 · `cylindrical-field-pml-repair`|8条角色记录；详见逐例清单|
|19.6.1 非线性场观测的DFT降采样修复 · `dft-decimation-repair`|9条角色记录；详见逐例清单|
|并行波动求解的接口归约修复 · `parallel-pml-reduction-repair`|8条角色记录；详见逐例清单|

## 证据与限制

主要新增定位为 `D:/Code/CAE-Bench-OJ-ch02-benchmark`（独立checkout，非当前仓库worktree），另关联 `D:/Code/CAE-Bench-OJ-211`、211补充工作树、当前HF缓存及既有runs。只检查相关本地目录和元数据，不声称遍历所有磁盘或远端。

原始分章账本JSON与调查报告保存在同一审阅目录；[追加资产定位](reviews/release-inventory-2026-10-23/extra-findings.md)记录独立checkout和环境缓存边界，[材料摘要](reviews/release-inventory-2026-10-23/materials.json)固定本轮记录版本。文件存在、元数据匹配、历史数值资格和新发行验收分别记录。

本轮尚未进行Titan实时只读连接；本地已取回候选与历史远端记录可先供核对。没有将本轮清单写成新正式选样，也未完成逐题许可、环境分发或科学审阅。用户指出遗漏后，继续补入同一检查稿并保留版本证据。
