# 第九章实施、审阅与验证记录

## 范围与依据

2026-10-16由基线19124d0启动；无已有第九章题面、数据或未提交用户修改。用户授权整章规划、题面、DATA、必要扩展、配置和独立审阅，按阶段中文commit，不推送／合并。采用author-section、design-data及configure-judge技能；正式数据、参考、发布留后。

[章规划](../chapter-09-species-reactions.md)和[清单](../chapter-09-task-plan.md)补足原来只有方向的第九章。7节8题覆盖全部已选择方向，各题物理／维度／时间／方法责任均明确，不按几何或来源划题。9.1与9.2区别为外场漂移，9.3两题区别为有限库存动力学与孔隙传输容量耦合，9.4与9.5区别为反应网络与空间对流扩散，9.6加入组成和温度反馈，9.7是相间分配的有限速率有符号交换。更高维／复杂物理是规划明确的后续能力，不伪称已实现。

用于物理范围核对的主来源：[COMSOL离子迁移](https://www.comsol.com/multiphysics/what-is-ionic-migration)说明外场漂移与扩散组合，[Cantera质量作用反应](https://www.cantera.org/stable/reference/kinetics/reaction-rates.html)说明按计量指数形成速率，[Cantera理想气体反应器](https://www.cantera.org/3.2/reference/reactors/ideal-gas-reactor.html)给出组分与内能的温度反馈。本章据此选定有限简化模型，并在DATA独立定义，不要求安装这些软件，也不从来源默认引入其全部模型。反应前因子采用归一化活度，热容限定常量，均为作者明确的契约选择，非上述软件的默认配置。

## 实现边界及维护入口

全部题意由逐题instruction、DATA和通用CONTRACT提供；未增COMMON、共享考生DATA或维护文档阅读依赖。通用entities、points、fields、conditions与时间轴足够，无核心／SDK／发布器修改。领域声明检查位于`qbank/extensions/caeoj_ext/species/`，可信provider绑定八题及运行白名单，沿用统一CLI和SDK。runtime错误类别为E_SPECIES。参数、单位、类型、范围、引用、采样、身份、计量守恒和组合在扩展检查；不实施积分、物理解或参考解。

维护端展开模板为`qbank/maintenance/authoring/build_species.py`，运行`python qbank/maintenance/authoring/build_species.py`可重建八题公开文档／配置及models.json，不生成数据。模板、测试fixture与正式数据分开；模板修订已回写，未来修改后须重新验证和独立审阅受影响文件。运行资源models.json由扩展白名单带入，维护生成器、测试、审阅记录、author、cases及reference不进入公开闭包。

## 独立考生审阅与闭合

三个独立subagent均以无历史上下文的考生身份，只读CONTRACT及分配题目的最终双文件，未提供作者预设答案、实现、维护说明或隐藏材料：

| 审阅者 | 覆盖 | 首轮发现及修订 | 最终结论 |
|---|---|---|---|
| /root/review_transport | 9.1、9.2、9.3四题 | 非吸附题q残留、有限对象题探针残留、entities uniform易误读、孔隙负载q(x,t)符号；均修订 | 重读最终8文件及CONTRACT，通过，无未决实质问题 |
| /root/review_reactions | 9.4、9.5两题 | q／探针／交换参数残留、速度正方向、s=1无法满足非平凡质量守恒；删除残留、澄清速度，反应题s改2..8 | 重读最终4文件及CONTRACT，通过 |
| /root/review_combustion_transfer | 9.6、9.7两题 | 探针残留、t=0派生量措辞、无用system对象、跨题参数措辞；均修订，燃烧s同改2..8 | 重读最终4文件及CONTRACT，通过 |

最终传质题几何段泛称“容器、反应或参数对象”的可选文风建议未再修改：该段解释entities的一般含义，下表与条件全集已准确列明本题vessels／links；没有额外反应对象或行为，避免将文风改动冒充语义修复。审阅者同意其不影响接口和答案。

具体反例：

- 吸附：ε=.5、ρs=2、c=1、q=0、qmax=ka=1、kd=0，局部dq/dt=1、吸附贡献dc/dt=−2，不能误用单位总体积浓度得−1；DATA容量和通量基准共同排除后一解释。
- 归一化反应：A→B、a=1、c*=2、cA0=2，t=1应为2exp(−.5)，不能把a当传统一级k得2exp(−1)。前因子单位与公式已排除误读。
- 流出端：v=D=L=1、左1右0、关闭反应，稳态中点为(e−sqrt(e))/(e−1)，不是误用零梯度得到的1；两端Dirichlet明确。
- 初态：knots=(0,.5,1)、c=(0,1,0)，t=0、x=.25输出.5，不是最近邻的0或1。
- 燃烧：2A→B、M=(1,2)、cv=(20,40)、uref=0、Tref=T0=300、c*=2、a=1、E=0、c0=(2,0)，t=1为(1,.5)；误把a当传统二阶k会得(.4,.8)，DATA已排除。
- 相间交换：两个单位容积、G=1、K=2、初态(1,0)，t=1浓度约(.482087,.517913)，N约.223130；倒用K会改变结果，DATA直接定义K及有向流率，排除歧义。

[最终版本清单](chapter-09-review-manifest.json)绑定全部17个公开文件的SHA256，由主Agent再次计算并与审阅者实际读取版本逐项一致。通过表示此覆盖内无未决问题，不保证没有缺陷，也不是数值或物理参考验证。

## 评分与执行配置

核对当前`caeoj_tools.grading_policy.task_policy`、`caeoj.grading_policy.resolve_policy`、grade_arrays／grade_files、`prepare_harbor.task_config`及私有`harbor/tests/judge.py`消费点：

| 公开要求 | 生效位置及验证 | 状态 |
|---|---|---|
| 每quantity逐值绝对＋相对误差，所有帧／对象／组分均须通过 | grading.json v2按quantity／unit绑定实际outputs逻辑名；零与非零参考、等号及相邻浮点边界两侧验证 | 已加载和执行，容差待数值校准 |
| 所有有效例等权0/1，总分为通过数比值 | 现有私有judge的save_report及回归中的混合通过／失败检查 | 框架回归通过，无第九章真实案例运行 |
| 浓度1e−6+.002|ref|，负载1e−8+.002|ref|；温度.02+.001|ref|、压力.1+.002|ref|、摩尔流率1e−9+.002|ref| | 逐题instruction与配置，专项测试独立写出公开数值并比较绑定结果 | 一致 |
| 逐例300s；孔隙吸附／反应传输900s；燃烧1200s；无独立输出字节上限 | judge-config timeout_seconds及max_output_bytes=null；私有judge消费 | 加载与路径核对；目标容器尚未执行 |
| 生成3600s、构建1800s、2CPU、4096MB、0GPU、Linux | 逐题harbor/task.toml和共享模板实际合并 | 八题合并值通过，实际容器限额未测 |
| 独立verifier，无网络 | 共享模板environment_mode=separate与本题network_mode=no-network合并 | 配置通过，Linux/AMD64目标平台执行待后续 |
| 总verifier预算 | max(继承总时限,300+N×(逐例时限+60))；N须真实案例数 | 用临时N=3验证公式，正式N及总预算未绑定 |
| Python/SciPy等环境 | 共享模板＋本题requirements.txt固定SciPy1.18.1 | 本地安装可用，目标镜像构建未执行 |

数据不存在时v2策略可先准确绑定任意合规逻辑名，不制造假正式样例或强制字段同名。输入、参考与配置错误不算考生失败；专项测试验证坏参考为score=null、缺候选输出为0。完整框架失败分类及汇总由既有回归覆盖；本轮未运行真实求解器或模型benchmark。

## 验证命令与证据

本地隔离开发环境在`runs/authoring/chapter-09/venv`，Python3.13.9；安装核心maint、独立开发provider和SciPy1.18.1。直接用系统python第一次因未安装provider而导入失败，随后在隔离环境安装后运行；没有把此错误当契约通过。

- 七节分别运行`.agents/skills/caeoj-author-section/scripts/check_statements.py --section qbank/09-species-reactions/<section> --output runs/authoring/chapter-09/<number>-static.json`，共八题通过。
- `python -m unittest discover -s tests -p test_species_contract.py -v`：八组通过；覆盖八模型SDK读写、合法／非法变体、常量引用拒绝、未知模型诊断、边界时间／空间重建、材料单位、容量、非连续ID及端点、相同长度错误location、重复合法观测、逐容器不同初态、守恒计量和独立评分阈值。
- `python -m unittest discover -s tests -v`：全仓结果及补充测试见机器摘要。第一次缺可选requests／PyYAML的准备测试跳过，补装后单独执行该完整模块。没有改动第一章正式资料；现有回归只在临时目录重建其fixture。
- 使用runtime_materials合并八题公开闭包（20个运行文件），在全新public-venv中普通非editable安装，移开装配源目录，在`/tmp`中用`python -I`反复切换八题。CLI info／validate-input／validate-output／grade和基础SDK均通过；实际导入位于新环境site-packages；歧义多题输入拒绝，无需用户注册扩展。只以零数组作协议身份判分，不能称为正确数值解。
- 八题都没有examples／samples／cases／reference正式数值文件；不调用第九章publish或prepare，不生成评测ZIP。公开闭包安装测试产物和协议fixture仅在runs。
- 生成器重跑与git diff检查、章内编号／覆盖／重复／共享语义核对，以及最终审阅散列检查见机器摘要。

本机是macOS；Linux容器、真实参考的精度、化学模型适用、非负性、刚性／尺度可解性、容差及资源校准、正式数据绑定与评测发布均留后。没有题意或接口层面的未决实质问题。
