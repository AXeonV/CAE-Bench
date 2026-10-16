# 第十一章实现、审阅与交付记录

范围为[6节8题清单](../chapter-11-task-plan.md)；依照author-section、design-data及configure-judge技能完成，正式数据、参考解和发布留后。启动基线aef73dc，规划提交daed25a，题面/契约/扩展/配置提交cd45988。没有第十一章既有题目需要迁移；不触碰启动时第1章5项用户修改。

## 交付及边界

[整章目录](../../11-semiconductor/README.md)覆盖全部编号11.1.1、11.2.1—2、11.3.1—2、11.4.1、11.5.1、11.6.1；逐题instruction、DATA、grading、judge-config和Harbor资源覆盖齐全。相邻能力由电荷自洽、时间演化、准稳态复合/显式陷阱记忆、低注入近似、弹道统计和量子本征态区分，不以几何或来源拆题。

考生只读本题instruction、DATA、通用CONTRACT。DATA逐题展开参数全集、单位、范围、输入场、位置/时间、conditions、重建及全部观测；未增加COMMON或其他题的依赖。输入剖面结点与输出点不等于求解网格。层、谱结点和均匀体用entities，真实空间点用points。Landauer能量用J、g已包括自旋、电流按负电子电荷；有效质量使用绝对kg、连续波函数与逆质量加权导数、有限箱体边界及逐态定相。

共享能力归`qbank/extensions/caeoj_ext/semiconductor`，可信注册`semiconductor.transport`；只检查公开声明，不计算物理解，不补隐藏条件。未修改核心、通用CONTRACT、Schema、SDK或发布器。已有核心结构足够，无需题目专用extension。维护模板与安装验证分别为`qbank/maintenance/authoring/build_semiconductor.py`、`verify_semiconductor_install.py`；模板和测试不进入公开装配。现有技能已引用当前RUNTIME和配置消费说明，新增能力及使用记录同步这些入口，无新工作流或废弃接口。

## 独立考生审阅

三个独立subagent以空历史启动，仅给真实实现任务及各题instruction、DATA、CONTRACT的只读权限，不提供代码、隐藏数据、维护记录或作者期望结论。review_classical覆盖平衡与两道漂移扩散，review_kinetics覆盖复合/俘获与少数载流子，review_quantum覆盖弹道与有效质量。均实际返回初审与最终复核；全部最终文件对应[审阅散列清单](chapter-11-review-manifest.json)，17份公开文件与审阅者回报逐一匹配。

| 问题/反例 | 修订及最终证据 |
|---|---|
| t=0初始密度在profile结点有折点，若接收点重合，左右电流可不同。独立反例L=1e−6、n=p=[1e16,2e16,1e16]、μ=0.1、T=300，中心左右Jn约±8.28 A/m² | 漂移瞬态observe首项严格>0；仍保留完整初态，不假定平衡重算。新增拒绝t=0回归；独立复核闭合 |
| 静态题只允许static轴却写initial也必须存在 | 逐题删掉不适用轴；工具接受/拒绝集合与DATA一致；独立复核闭合 |
| 模板残留wavefunction、无关层参数、实体无空间方程与PDE冲突 | 按本题能力展开位置、轴、角色和场条款；清理bulk/trap空间表述；独立复核闭合 |
| 宽高势垒近隔离双阱低态劈裂无法在float64稳定分辨，逐态波函数可能混合 | 添加相邻谱隙≥1e−6 Es的数据承诺，覆盖m+1态，要求独立谱/收敛/定相证据；声明工具明确不求谱。独立复核闭合，实际证据留数据阶段 |
| 体复合公式方括号后括号被Markdown识别为文件链接 | 改为显式乘号的等价公式，两文件同改，静态与独立复核通过 |
| 维护核查发现初稿shell入口不符当前执行器 | instruction全部修正为python solve.py --input/--output，明确可调用其他语言、每例无网络；逐题独立复核新入口并更新散列 |

审阅者留下的非阻断建议包括静态条件“非initial”和一般数值方法中“非线性求解”的冗余措辞；它们不增加字段、模型或算法要求，保留不影响实现与判分。通过仅表示该只读覆盖内未发现未决题意问题，不证明不存在缺陷或已有物理参考。

## 配置到实际消费者

核查源码为基线aef73dc的`caeoj.grading_policy`、`grading`、`caeoj_tools.grading_policy.task_policy`、`assembly.runtime_materials`、`prepare_harbor.task_config`与`harbor/tests/judge.py`。本次未改这些消费逻辑。

| 公开要求 | 实际消费与验证 | 状态 |
|---|---|---|
| 每quantity逐值绝对+相对容差、全部时刻/点/分量通过 | grading v2以quantity/unit绑定任意逻辑名及array；相同quantity重复输出分别评分。真实task_policy与resolve_policy加载，零/非零参考、阈值等号及nextafter外侧执行 | 已验证；数值阈值待参考校准 |
| 正常退出、合法输出才接受，坏输入/参考不记失分 | SDK与grade_arrays检查IDs/时间/shape；独立安装CLI接受合法结构、坏候选退出1、坏参考退出2 | 已验证；仅合成工具数组 |
| 每例300/600/900秒 | judge-config.timeout_seconds由judge.execute传process.wait | 加载与调用链已核对；未实测Linux超时 |
| 2CPU、2048MB、0GPU、生成3600秒、构建1200秒 | Harbor覆盖实际合并模板，测试检查最终值；不写无人读取的执行键 | 配置已生效合并；容器配额未实测 |
| 无独立输出字节上限 | max_output_bytes=null由judge.output_limit读取 | 配置/消费核对完成 |
| 各例等权、分母计划总例数 | judge.save_report为通过数/total，complete前不写最终reward | 沿用当前汇总，未制作正式cases执行整场 |
| 外层预算覆盖逐例执行 | max(共享1200秒,180+N×(逐例秒+60))，测试N=4为临时检查值 | 公式实际加载通过，真实N待绑定 |
| 同一公开运行闭包一次安装 | 八题合并runtime_materials，固定白名单、strict_tasks；全新venv普通pip install，移开装配源码、换cwd、-I运行 | 已实测Windows；未发布包 |

## 验证与可复现入口

机器摘要为[chapter-11-validation.json](chapter-11-validation.json)，完整临时日志/fixture在`runs/authoring/chapter-11/`，不进入正式题目目录。测试环境为Windows AMD64 Python3.13.16，使用工作区`.venv`；旧文件默认GBK读取曾失败，统一`-X utf8`后相关回归通过，不改其他章源码绕过。

```powershell
python qbank/maintenance/authoring/build_semiconductor.py
Get-ChildItem qbank/11-semiconductor -Directory | ForEach-Object {
  python .agents/skills/caeoj-author-section/scripts/check_statements.py --section $_.FullName --output "runs/authoring/chapter-11/$($_.Name)-static.json"
}
./.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -p test_semiconductor_contract.py
./.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -p test_runtime_assembly.py
./.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -p test_optics_contract.py
./.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -p test_grading_policy.py
./.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -p test_grading.py
./.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -p test_quantity_grading.py
./.venv/Scripts/python.exe qbank/maintenance/authoring/verify_semiconductor_install.py
```

六节静态全部通过，8题无遗漏。7组半导体专项、8组运行装配、8组既有光学兼容、16组评分策略、14组评分、8组quantity绑定，共61项通过。覆盖正负掺杂、非连续ID、乱序/重复接收点、边界坐标、轴和初态相容性、陷阱f=0/1、零表面速度、低注入界、零透射、整数简并度、质量正值、界面采样、m=1仍为components等合法/非法分支。维护检查从最终DATA选择反例，不只接受生成器默认fixture。

八题合并闭包独立普通安装成功；源码目录改名后，从另一工作目录以隔离Python执行8组SDK读写与48条CLI命令（各题info、input、output、正确结构评分、坏候选、坏参考）。合成零输出仅检验工具，不冒充物理答案。运行装配ID和锁定依赖见机器摘要。安装脚本拒绝覆盖已有验证目录，复跑用`--output runs/authoring/chapter-11/install-check-new`选择新的目的地。没有创建公开ZIP或调用发布器/Harbor prepare。

章内覆盖、编号、重复和公共语义人工核查：8项均有目录映射及最终审阅，平衡与非平衡不混用Boltzmann密度，体复合与陷阱显式动态不双计SRH，少数载流子输出粒子通量不当电流，Landauer总电流不当面积密度，有效质量箱体不当无限包层。SDK始终同一入口，无额外安装/注册步骤。

## 后续状态

当前没有未闭合题意或配置映射事项。正式样例、cases、独立参考、模型适用性、稳态唯一性、谱隙承诺、收敛误差、精度/预算校准、真实N绑定、Linux容器限额及最终发布均待后续。声明合法和工具测试均不证明这些证据已建立。用户既有5项第1章改动保持未提交，本次提交范围无它们；全局工作树不伪称干净。

维护方核对物理符号时参阅了[维也纳工大漂移扩散说明](https://www.iue.tuwien.ac.at/phd/gehring/node26.html)、[SRH与陷阱动力学说明](https://iue.tuwien.ac.at/phd/entner/node11.html)、[非平衡输运理论](https://docs.nanoacademic.com/nanodcal/theory/introduction/)。来源只作范围/符号交叉核对，题意均在公开三文件完整给出，不要求考生追源。
