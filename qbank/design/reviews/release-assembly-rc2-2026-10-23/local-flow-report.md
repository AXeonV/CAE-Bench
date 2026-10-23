# RC2 本地新增流动能力题装配证据

38题沿用现有manifest的309正式例及38公开格式样例；没有更改原题、选样、参考或判分规则，没有下载、求解或模型调用。

全部题使用匹配来源checkout的data_pool.strict verify、输入/输出结构验证及实际prepare_case/参考自判分。消费通过不能证明参考数值正确。

profile统一为`unvalidated-reference-rc`：待题面与case审阅、独立数值资格、资源与异机验收，不得当成正式Benchmark成绩。

下表manifest身份、逐case ID、摘要、source candidate及来源记录由同目录JSON承载。公开包题面、DATA与所有样例文件逐文件对比；原包一致时复用，差异时调用原publisher仅重发公开包。

|题号|task|正式例|样例|消费检查|重发公开包|
|---|---|---:|---:|---|---|
|2.1.2|newtonian-incompressible-transient-2d|10|1|True|False|
|2.1.4|newtonian-incompressible-transient-3d|10|1|True|False|
|2.1.5|generalized-newtonian-incompressible-steady-2d|8|1|True|False|
|2.1.6|generalized-newtonian-incompressible-transient-2d|8|1|True|False|
|2.1.7|generalized-newtonian-incompressible-steady-3d|7|1|True|False|
|2.1.8|generalized-newtonian-incompressible-transient-3d|8|1|True|False|
|2.1.9|newtonian-isothermal-compressible-steady-2d|3|1|True|False|
|2.1.10|newtonian-isothermal-compressible-transient-2d|5|1|True|False|
|2.1.11|newtonian-isothermal-compressible-steady-3d|3|1|True|False|
|2.1.12|newtonian-isothermal-compressible-transient-3d|5|1|True|False|
|2.2.1|newtonian-lowmach-steady-2d|10|1|True|False|
|2.2.2|newtonian-lowmach-transient-2d|10|1|True|False|
|2.2.3|newtonian-lowmach-steady-3d|10|1|True|False|
|2.2.4|newtonian-lowmach-transient-3d|10|1|True|False|
|2.2.5|inviscid-compressible-steady-2d|10|1|True|False|
|2.2.6|inviscid-compressible-transient-2d|10|1|True|False|
|2.2.7|inviscid-compressible-steady-3d|10|1|True|False|
|2.2.8|inviscid-compressible-transient-3d|10|1|True|False|
|2.2.10|newtonian-compressible-transient-2d|5|1|True|False|
|2.2.12|newtonian-compressible-transient-3d|5|1|True|False|
|2.3.1|rans-steady-2d|8|1|True|False|
|2.3.2|rans-steady-3d|7|1|True|False|
|2.3.3|urans-transient-3d|10|1|True|False|
|2.3.4|resolved-statistics-3d|10|1|True|False|
|2.3.5|isothermal-rans-3d|7|1|True|False|
|2.4.1|thermal-rans-3d|9|1|True|False|
|2.4.2|thermal-urans-3d|4|1|True|False|
|2.4.3|thermal-statistics-3d|10|1|True|False|
|2.5.3|immiscible-interface-2d|10|1|True|False|
|2.5.4|immiscible-interface-3d|10|1|True|False|
|2.8.2|gas-film|10|1|True|False|
|2.9.1|fully-wet-steady|3|1|True|False|
|2.9.2|fully-wet-transient|9|1|True|False|
|2.9.3|wetting-drying|7|1|True|False|
|2.10.3|transition-gas|10|1|True|False|
|2.10.4|free-molecular|10|1|True|False|
|2.11.1|viscoelastic-steady|9|1|True|False|
|2.11.2|viscoelastic-transient|9|1|True|False|

`local-flow-report.json`保留strict verify、每例真实消费、ZIP差异及主checkout题面比较；`local-flow-selection.json`保留完整选样与来源候选摘要关联；`local-flow-plan.json`供发行器消费。
