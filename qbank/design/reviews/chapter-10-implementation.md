# 第十章实施、独立审阅与验证

## 范围及边界

2026-10-16，启动基线2f333e9，工作树干净，无第十章已有题面、数据或用户未提交修改。采用caeoj-author-section、caeoj-design-data、caeoj-configure-judge流程。用户授权整章规划、题面、自包含DATA、必要扩展、评测配置及独立考生审阅；正式数据、参考解、评测发布留后，不推送／合并。

原仅有章级方向，先保存[六节八题规划](../chapter-10-electrochemistry.md)及[有限逐题清单](../chapter-10-task-plan.md)，再分三批实施。范围覆盖平衡／瞬态自洽离子场、多通道混合电位、界面非线性动态／线性阻抗、传质—电极反应耦合、电池颗粒储能和燃料电池能量转换；区别不是来源或几何名称。明确与第九章给定外场迁移、第七章电路及第十七章跨场反馈的边界。不声称覆盖一般多维、浓溶液、移动形貌、多孔电极或热失控。

范围核对采用主来源：[COMSOL扩散双电层](https://doc.comsol.com/6.4/doc/com.comsol.help.models.fce.diffuse_double_layer/diffuse_double_layer.html)支持空间电荷与PNP自洽关系；[PyBaMM单颗粒模型](https://docs.pybamm.org/en/v25.12.0/source/examples/notebooks/models/SPM.html)支持球形固相扩散和双电极单颗粒分析边界；[COMSOL电化学反应热](https://doc.comsol.com/6.3/doc/com.comsol.help.echem/echem_ug_electrochem.06.108.html)支持区分热中性电压及电化学热。实际题目为独立选定的有限理想模型，逐题写明边界、材料及符号；不复制这些软件的默认参数、Stern层、完整多孔电极或数据库。有限库存阻抗由本题动态系统线性化，燃料电池有效BV电子数与热力学电子计数分别定义，不能从来源补题意。

## 归属与可维护性

考生只阅读本题instruction.md、DATA.md与通用CONTRACT.md。无COMMON、共享考生DATA或额外定义文档。points用于真实一维／径向观测，entities用于反应通道、半电池、频率、颗粒及工况。现有通用结构足够，不改CONTRACT、核心Schema、SDK、评分框架或发布器。

领域扩展为`qbank/extensions/caeoj_ext/electrochemistry/`，可信绑定为`electrochemistry.interfaces_transport`，诊断E_ELECTROCHEMISTRY；运行白名单仅带模块及models.json。扩展验证参数、单位、数量、采样、引用、位置、时间、初态及可检查组合；不积分、不求解、不制作参考，不投影或修复输入。electroneutrality使用标准库Fraction解释float64的精确二进制有理数，避免浮点点积掩盖残余电荷。

维护模板`qbank/maintenance/authoring/build_electrochemistry.py`可重建八题文档／配置及models.json，不生成数值数据。修订已回写模板，重跑后无diff。测试fixture位于tests，不属于正式数据，也不在公开闭包。运行装配和维护说明同步更新；新增领域未改变通用接口或流程，技能指令无需另建分支。考生仍一次普通安装、使用统一CLI与基础SDK，无注册步骤。

## 独立考生审阅与问题闭合

三位subagent以无历史上下文的独立考生身份，只读指定instruction、DATA及完整CONTRACT，未提供作者预设答案、实现、规划、维护记录或隐藏材料：

| 审阅者 | 覆盖 | 发现、修订与最终状态 |
|---|---|---|
| /root/review_electro_ions | 10.1两题、10.2一题 | 发现近似电中性与PNP初始零势冲突；改精确电中性，清理维度／频域残留、澄清字段时间轴；重读最终七文件通过 |
| /root/review_electro_interface | 10.3两题、10.4一题 | 清理动态／阻抗跨题初态条款及无关频率／有限维措辞，明确条件不含time_axis；推演有限库存、表面浓度耦合和初始不相容语义，重读最终七文件通过 |
| /root/review_electro_energy | 10.5、10.6两题 | 条件time_axis放置存在格式误读；改为引用字段属性，清理不适用频域／浓度／连续场条款，电池明确径向；重读最终五文件通过 |

实质反例与处理：原PNP电中性容差允许z=[1,−1]、c=[1,1+2^−40]，若F=96485、ε=7e−10、L=1e−3，零端电势下真实残余电荷给初始中点势约−1.5670106482e−5V，与硬编码零相差超过2e−6V评分绝对容差。当前PB与PNP要求存储binary64视为精确实数后的Σzc严格为0；无电中性容差、不投影，反例被声明校验拒绝。不是靠调整评分掩盖初态冲突。

时间轴格式修订：原条件说明把time_axis与role等并列，可能让考生往condition新增键。当前明确time_axis仅属于引用字段、条件对象不含该键；专项测试确认condition新增time_axis实际被拒绝。该修订消除格式误读，没有添加新通用结构。

其他反例尝试及结论：

- 混合电位I=0允许各通道有符号电流抵消，不能逐通道分别置零；正面积、速率及活度保证公共电位的总电流约束严格单调。
- 有限库存阻抗与无限储槽Rct并联电容不同。取n=F=R=T=A=V=Cdl=k=c*=ω=1、α=.25、cR=1、cO=4，按本题线性系统得到Z≈.06815487048−.56626506024i；错误无限储槽近似约.31426968053−.11111111111i。DATA已明确排除后者。
- 扩散电极取L=D_R=D_O=k=c*=nF=1、初始两态均1、α=.5、fψ=ln4，稳态耦合界面给j=3/7，直接代储槽值给3/2；DATA要求求表面迹，不存在两种同等合法解释。
- 球形扩散的颗粒表面积与电极几何面积通过a=3ε/R及厚度换算；正负极电流符号、OCP表面SOC、端电压均固定。审阅者以内存算例检查径向模态体均库存与积分通量相符，不将此称为完整数值参考验证。
- 燃料电池总反应电子计数2与有效ma、mc分别给定；负电压／电功及热不截零。P+Q=J Etn由公开定义成立，不额外叠加反应热或隐含水相态。

[审阅版本清单](chapter-10-review-manifest.json)保存17个最终公开文件SHA256；主Agent逐项复算，与审阅者最终实际读取版本一致。全部意见已闭合，无未决实质问题。通过仅表示此次检查范围内未发现未决问题，不保证无缺陷，不代表正式数据或参考已验证。

## 配置映射与真实消费点

本轮核对当前task_policy、resolve_policy、grade_arrays／grade_files、prepare_harbor.task_config及私有harbor/tests/judge.py：

| 题面要求 | 实际配置及验证 | 限制 |
|---|---|---|
| 全部quantity逐帧／对象／分量逐值比较 | grading.json v2按quantity＋unit绑定实际逻辑名，zero／nonzero参考、等号及nextafter边界两侧通过 | 数值容差尚未校准 |
| 电势基准不拟合；阻抗实虚独立比较 | pointwise、per_time、per_component，无偏置／相位修正；按自由逻辑名绑定 | 不评价隐藏模型专有变量 |
| 每例0/1，总分通过例数比值 | 私有judge汇总与现有混合通过／失败回归 | 第十章无真实案例运行 |
| 逐例墙钟240s；PB600s；电极扩散900s；PNP／颗粒电池1200s | judge-config.timeout_seconds，由私有judge.execute消费；八题加载值通过 | 未运行真实求解器及Linux容器 |
| 无独立输出字节上限 | max_output_bytes显式null，由output_limit消费 | 仍受公开逻辑规模、内存及时限约束 |
| 生成3600s、构建1800s、2CPU、4096MB、0GPU、Linux | 本题Harbor覆盖与共享模板实际合并并核对 | 合并通过不等于目标容器限额实测 |
| 独立verifier、逐例无网络 | 模板environment_mode=separate，network_mode=no-network | 本机macOS，目标平台执行留后 |
| 总verifier预算 | max(继承值,300+N×(逐例时限+60))，临时N=3验证公式 | 正式N和总预算未绑定 |
| 环境及依赖 | 共享环境＋每题SciPy1.18.1；工具闭包按项目依赖锁定 | 目标镜像、离线及跨平台安装未测 |

字段quantity、outputs逻辑名和HDF5 key分别处理；v2允许无正式数据时完成策略设计与临时绑定，不为适配judge固定逻辑字段名。专项检查坏候选输出为0、坏参考为score=null，输入／配置错误属于基础设施错误。完整执行失败分类由现有框架回归覆盖；未追加模型benchmark、正式案例或发布。

## 验证与重现

沿用项目已有隔离开发环境`runs/authoring/chapter-09/venv`（Python3.13.9，核心maint、独立开发provider、SciPy及准备模块可选依赖已安装），不污染系统环境。

- 六节分别运行`python .agents/skills/caeoj-author-section/scripts/check_statements.py --section qbank/10-electrochemistry/<section> --output runs/authoring/chapter-10/<number>-static.json`，覆盖八题，全部通过。
- `python -m unittest discover -s tests -p test_electrochemistry_contract.py -v`：7组专项通过。包括精确电中性／近电中性反例拒绝、初始电势、驱动覆盖、正频率／单位、零库存、BV系数边界、活度、表面／内部观测区别、径向身份、初始电流、独立实体行值、重复合法输出、字段引用与错误条件time_axis、SDK roundtrip、评分边界及资源合并。
- `python -m unittest discover -s tests -v > runs/authoring/chapter-10/full-tests.log 2>&1`：331项全部通过，无跳过。包含旧题、评分、装配、公开材料、Harbor及准备工具回归；没有因新增扩展放宽旧题检查。
- runtime_materials合并八题公开运行闭包20个文件，白名单排除caeoj_tools、maintenance、author、cases、reference。在全新`runs/authoring/chapter-10/public-venv`中普通非editable安装；移开装配源码，在/tmp以python -I交替加载八题，CLI info／validate-input／validate-output／grade及基础SDK全部通过，实际模块来自新环境site-packages；无task的歧义多题输入被拒绝。
- 安装脚本与日志位于`runs/authoring/chapter-10/{assemble.py,check_public.py,public-assembly.json,public-install.json}`，均为本地临时验证。只用零结果数组做协议身份判分，不称为正确物理参考，也不写正式samples路径。
- 模板重跑无diff，章内六节／八个唯一编号／计划映射／共享符号与单位核对通过，最终17个审阅散列匹配。完整机器证据见[验证摘要](chapter-10-validation.json)。

全部数值fixture仅在临时目录或runs；第十章无正式examples、samples、cases或reference数值文件，不对空数据调用发布器或Harbor prepare，不生成正式评测ZIP。待后续：正式数据及独立参考、物理适用性与全程状态界限、参考误差、容差与资源校准、真实案例数和数据绑定、Linux/AMD64容器限额／网络、正式发布。
