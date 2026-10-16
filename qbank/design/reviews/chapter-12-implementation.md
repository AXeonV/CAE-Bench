# 第十二章实现、审阅与验证

启动2026-10-16，基线13f6d6b。使用author-section、design-data、configure-judge工作流，依[章规划](../chapter-12-granular.md)实施[6节7题](../chapter-12-task-plan.md)。规划提交32416d1，主体题面/契约/扩展/配置提交4adc56b，最终审阅修订和证据随收尾提交。正式数据、参考解及评测发布留后。

## 完整交付

[整章入口](../../12-granular/README.md)覆盖12.1.1受力运动、12.2.1耗散碰撞、12.3.1摩擦自转、12.4.1黏附、12.5.1周期散体宏观响应、12.6.1聚并和12.6.2破碎。全部逐题instruction、DATA、grading、judge-config和Harbor资源配置齐全，不以TODO或共享章节协议替代。三个实施/审阅批次为12.1—2、12.3—4、12.5—6。

出题先固定能力、材料响应、方法责任与观测，再由DATA定义字段/轴/重建；缺少几何或来源数据没有删题。固定球形、单值滑动力律及离散群体反应是公开比较范围，不冒充任意颗粒物理。候选可自由选择时间积分、邻域、刚性处理及语言；静摩擦历史、滚动/扭转阻力、一般活动壁面、非球形和双向流固反馈明确留后。周期题以宏观应力/接触网络观测及周期邻接为能力目标，非按容器形状拆碰撞题。

通用entities已经能表达运动颗粒、代表体、体积级和矩阵，无核心表示缺口。共享声明实现位于`qbank/extensions/caeoj_ext/granular`，可信能力`granular.dynamics`，公开白名单仅必要代码及models.json。无需修改核心、CONTRACT、通用Schema、SDK或发布器，也未新增本题extension。维护模板`qbank/maintenance/authoring/build_granular.py`及普通安装验证`verify_granular_install.py`不进入考生包。RUNTIME、核心/扩展职责、评测维护说明和README已同步；现有技能指向这些当前说明，不需新增安装、注册或阅读流程。

## 独立考生审阅与反例闭合

三位subagent以空历史启动，只给真实实现任务及负责题的instruction、DATA、CONTRACT路径，明确禁止读取代码、隐藏数据、其他题、维护规范或作者记录，且只读。review_granular_motion覆盖12.1—2，review_granular_contacts覆盖12.3—4，review_granular_bulk覆盖12.5—6。首轮问题处理后均读取最终版本复核；变化文件单独复核，未变文件不重复审阅。最终[15文件散列](chapter-12-review-manifest.json)与审阅者实际回报匹配。

| 问题及反例 | 修订与证据 |
|---|---|
| 周期段先定义最近像r，后又被普通接触段r=xi−xj覆盖。L=1、R=.01、x=.0099/.9901时最近像d=.0198有接触，直接距离.9802无接触，Z和应力不同 | 周期两文件删掉第二次r定义，明确全段使用最近像；独立复核闭合。回归包含跨边界合法接触、过大重叠及观测阈值 |
| m=1e−12、F=1e4、tend=10的单粒无阻运动到约5e17 m，float64 ULP=64而位置atol=1e−9 | 全程位置/速度尺度作为合法族承诺，数据须验证；自由题另加可由输入计算的充分位移界≤100m，工具拒绝巨大反例，独立复核确认 |
| 黏聚F0=1000、a=1e−8、m=1e−12，外力支持间隙附近小振动，原法向刚度界仍允许约1e11周期 | 加tend sqrt(πF0/(min m a))≤1e5，工具拒绝该难度反例；预算仍需实际验证，不宣称仅凭纸面证明超时 |
| μ=2、P=5000、vs=1e−8的摩擦滑动松弛极快，原法向界未覆盖 | 加基于速度及重叠界的保守Psum、质量/惯量响应难度界；工具拒绝反例，独立复核确认界的方向 |
| 共享模板残留bins、tensor及无自转题的ω规则 | 逐题按真实分支清理，模板同步，最终复核闭合 |
| 维护物理核查：小重叠时名义Ri/Rj力臂不共用作用点，会产生非物理净角动量误差 | 摩擦题改共同接触点ℓi=Ri−δ/2、ℓj=Rj−δ/2，接触速度和双体转矩同时使用这些力臂；最终两文件再由独立考生复核 |

摩擦修订的物理核查依据：ℓi+ℓj=d，轨道转矩r×Ft与两自转转矩之和相抵；滑动功率为Ft·vt=−μP |vt|²/sqrt(|vt|²+vs²)≤0。ℓi≤Ri，原Psum使用Ri²/Ii仍为保守界。这是公开模型内部一致性核查，不是一般DEM数值准确性证据。

粒群维护核查通过反应代数确认：聚并有限反应全集只保留i+j≤K，增益有序和乘1/2、损失不乘1/2，避免同类碰撞双计；对称核下体积一阶矩守恒。破碎b的行是子粒级、列是母粒级，Σj b_jk=k及a1=0保证体积矩守恒；分数期望子粒数允许。原值计算及容差诊断不意味着求解器可偷偷投影、归一化或添加溢出汇。

## 配置的实际消费与边界

核对13f6d6b的`caeoj.grading_policy.resolve_policy`、`caeoj.grading`、`caeoj_tools.grading_policy.task_policy`、`assembly.runtime_materials`、`prepare_harbor.task_config`、`harbor/tests/judge.py`，本次未改消费代码。

| 题面要求 | 实际生效位置及验证 | 状态 |
|---|---|---|
| 逐值atol+rtol、全部输出/时刻/分量 | grading v2由quantity/unit绑定自由逻辑名与array；重复quantity独立判分 | 实际加载、零/非零参考、等号与nextafter外侧通过；阈值未校准 |
| 合法结构及失败分类 | SDK/output校验、grade_arrays及独立安装CLI | 坏候选退出1、坏参考退出2且基础设施错误score=null；合成数组只证明工具 |
| 逐例墙钟300/900秒 | judge-config.timeout_seconds被execute的process.wait读取 | 消费点核对、配置加载通过；Windows未实测Linux执行超时 |
| 2CPU/2048MB/0GPU、生成3600秒、构建1200秒 | Harbor覆盖与共享模板合并 | 最终字段实际合并通过，容器限额未执行 |
| 无独立字节限额 | max_output_bytes=null由judge.output_limit消费 | 保留公开数组规模/内存约束 |
| 总verifier预算 | max(模板1200秒,180+N×(逐例秒+60)) | N=5临时合并检查通过，真实N后续绑定 |
| 例等权、计划总数为分母 | judge.save_report使用passed/total，complete前不写最终reward | 沿用现行汇总，未虚构正式cases执行整场 |
| 候选和verifier共用闭包 | runtime_materials合并7题并求必要白名单 | 独立普通安装/隔离CLI和SDK通过，无额外扩展注册 |

最多128颗粒及64粒级，输出/输入场各至多2000000标量；2CPU及2048MB为这些有限状态与工具开销选定的初版目标，接触900秒与无接触/分布300秒区分相互作用处理成本，不声称已实测足够。全程小重叠、响应尺度、观测接触裕量和难度界是实际数据验收承诺；声明工具只检查可从输入直接确定的部分，绝不以校验通过证明全程适用。

## 验证与重现

[机器摘要](chapter-12-validation.json)保存最终静态、专项/相关回归、独立安装及版本证据；临时载荷、日志和完整命令结果在`runs/authoring/chapter-12/`。未向examples、samples、cases或reference写数值文件。

```powershell
python qbank/maintenance/authoring/build_granular.py
Get-ChildItem qbank/12-granular -Directory | ForEach-Object {
  python .agents/skills/caeoj-author-section/scripts/check_statements.py --section $_.FullName --output "runs/authoring/chapter-12/$($_.Name)-static.json"
}
./.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -p test_granular_contract.py
./.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -p test_semiconductor_contract.py
./.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -p test_multibody_contract.py
./.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -p test_runtime_assembly.py
./.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -p test_grading_policy.py
./.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -p test_grading.py
./.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -p test_quantity_grading.py
./.venv/Scripts/python.exe qbank/maintenance/authoring/verify_granular_install.py
```

Windows AMD64 Python3.13.16，独立安装锁定依赖和装配ID见摘要。颗粒9组、半导体7组、多体6组、装配8组、评分策略16组、评分14组及quantity绑定8组，共68项通过。首轮有一条测试用例错误地将t b/m=1e4当超界；改用确实超过1e5的质量/阻力组合后通过，没有为错误测试放宽公开约束。

测试覆盖字段与身份、drive线性采样、质量/半径正值、初始最近像/接触/过重叠、摩擦与黏聚难度反例、spin阻力、K身份及整数、零聚并核、空粒群、分数子粒数、矩阵转置、质量不守恒、输出张量/point语义、重复quantity、atol/rtol边界、资源真实合并及白名单隔离。它们不求解DEM或群体平衡，也不提供可信物理参考。

7题合并闭包在全新venv正常`pip install`后，将装配源码目录移走，从另一工作目录以隔离Python运行：7组SDK读写及42条CLI（各题info、输入校验、输出校验、相同工具数组评分、坏候选、坏参考）通过。代码导入来自site-packages，无开发provider或源码目录兜底。合成零输出仅作工具结构测试，不声称物理正确。复跑安装脚本用`--output runs/authoring/chapter-12/install-check-new`选择新目录，脚本拒绝覆盖旧证据。未生成公开ZIP，未调用publish或Harbor prepare，不把安装验证说成评测发布。

章内人工核查：6节7项编号和slug全部对应，语义与上下界一致；前五题运动粒子用entities状态，后两题bins是真实体积级；黏附不强制粘合、滑动不暗含静摩擦、周期应力不重复计无序对、统计粒群不伪装单粒轨迹。没有新增考生阅读或安装工作。

## 未完成证据与用户改动

当前无未闭合的题意或配置映射事项。后续正式数据、独立参考、全程响应/小重叠/接触裕量验证、模型适用性、数值收敛、精度与预算校准、真实案例数绑定、Linux容器配额/网络/超时执行及发布均未完成，不由上述68项或空数据清单代替。

启动时第1章5项用户修改完整保留且未提交。本次文件均按阶段提交；不清除用户改动以制造全局干净工作树，未推送或合并。

维护方查证颗粒法向力、接触方向与模型边界时参考[LAMMPS granular说明](https://docs.lammps.org/pair_granular.html)，应力符号与动理学/virial区分参考[应力说明](https://docs.lammps.org/compute_stress_atom.html)。本题的力律、力臂、正则化及观测均已完整公开，不要求安装或复现LAMMPS，不把来源配置变成题意。
