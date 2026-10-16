# 第三章契约、评测与验证记录

本文件保留首版实现与验证历史；后续修订及当前证据以[第三章复审修订记录](chapter-03-revision.md)为准，旧文件散列和装配身份不代表当前版本。

日期：2026-10-16。实现核对基线95b0d1c，沿用当前 runtime v1、grading v2 和现有 Harbor 适配。没有修改通用核心、CONTRACT、发布器、执行器或已有题目。

## 归属与兼容

- `qbank/maintenance/solid-plan.json` 保存有限逐题清单；`solid_authoring.py` 是维护端题面渲染源，逐题展开完整 DATA。它不参与考生求解或运行装配，不生成正式输入或参考。后续修改生成源须重新生成并对受影响最终文件独立复核。
- `qbank/extensions/caeoj_ext/solid/` 拥有固体声明检查及随包资源 models.json。`solid.mechanics` 是中性物理能力身份，21个显式版本模型由可信目录绑定；不以章号分派。运行描述仅白名单公开该扩展代码／资源，没有题号专用模块或中央发布清单修改。
- 现有结构可表达节点／单元／真实区域聚合、边界引用、时间插值、参数和张量，不新增核心字段、伪探针或共享考生DATA。材料、载荷和观测在本题DATA就地给出，不依赖维护源码补定义。
- 开发环境 provider、公开装配和SDK使用同一检查器。普通装配通过一个发行包安装，考生不注册扩展；缺扩展是工具错误。物理参数不会从task或来源推断；未知solid模型拒绝，不退回半套通用校验。
- 旧流体和PDE语义不变；新增 `E_SOLID` 由扩展报告。弹性辅助 `elastic_constants` 没有混入核心SDK，也不是必用求解接口。

## 要求到实现及证据映射

| 公开要求 | 实际拥有者／消费点 | 本次验证 |
|---|---|---|
| 文件、形状、float64、引用、IDs、输出轴 | 现有caeoj.validation／sdk | 21模型真实临时MSH/HDF5输入与输出往返，错轴拒绝 |
| 显式材料模型、参数集合／单位／范围 | solid.check + models.json | 缺键、错单位、错误维度、未知模型、整数阶数、非物理范围拒绝 |
| 完整参考域、线性单纯形、整面Dirichlet闭包 | solid.check | 非连续tag；孤立约束节点拒绝；区域条件错支持拒绝 |
| 时间覆盖、全程常量、零初载、瞬态仿射位移与初态相容 | solid.check | 缺端点、错误区间、非零初载、位移折点拒绝；单帧全程常量接受 |
| 接触法向／半空间／排他、内聚配对／材料范围 | solid.check | 非单位法向、初始侵入、接触重叠、内聚自配对和错误开裂阈值拒绝 |
| 疲劳逐点previous块、末帧标记、范围与初始裂长 | solid.check | 负幅／率、过大均值、非法裂长、错误采样和末帧拒绝 |
| 必需输出quantity／SI单位／实体／整体积分及谱阶数 | solid.check | 缺输出、错单位／位置／value_kind／谱标签与阶数拒绝 |
| 数值目标逐值atol+0.01×绝对参考值，全字段AND | 每题grading.json v2→caeoj_tools.grading_policy.task_policy→caeoj.grading | 全21策略绑定逻辑名、quantity与array不同的真实临时输入；每quantity阈值等号接受、nextafter超限拒绝，非零参考相对项参与 |
| 逐例墙钟900／1500秒，无独立字节限额 | judge-config.json→现有harbor/tests/judge.execute和output_limit | 源码核对消费点，配置加载、null限额检查；未运行Linux超时探针或物理求解 |
| 4 CPU、8192 MB、0 GPU、Linux，生成3600秒、构建1800秒 | 每题harbor/task.toml→prepare_harbor.task_config | 21配置真实合并；未知资源键拒绝，保留separate verifier／no-network |
| 外层verifier总预算 | judge-config.verifier_budget→task_config | 用临时case_count=2验证300+N×(逐例时限+60秒)；真实N待正式数据绑定，N=0拒绝 |
| 各例等权汇总 | 现有judge.save_report | 源码为通过例数/总例数；既有Harbor回归覆盖部分完成和reward，不新增无人消费权重键 |
| 不增加安装和阅读负担 | caeoj_tools.assembly.runtime_materials | 21题合并闭包一次普通安装，CLI／SDK自动切换；包无维护工具、author、隐藏数据和流体模块 |

检查器对声明可判定的集合、单位、时间、几何和组合进行检查，**不证明物理适定性、结构稳定分支、内部尺度解析、接触解唯一、网格质量或预算内数值精度**。初始裂长失稳上限也不能仅由输入采样证明其整个求解历程；连续历程合法性需要后续参考制作验证。

## 独立考生审阅与闭合

三个独立subagent分别为 review_linear（3.1—3.3，9题）、review_nonlinear（3.4—3.6，7题）、review_damage（3.7—3.9，5题）。初次仅给真实实现任务与各题instruction、DATA、CONTRACT路径，明确只读、禁止实现／维护／隐藏参考。作者实现者没有冒充审阅者。

| 初审发现 | 修订／处理 | 最终复核 |
|---|---|---|
| 节点Dirichlet缺完整面的支持定义 | 明确完整外面顶点闭包及精确节点并；禁止点／棱支撑冒充连续位移边界 | 9题组通过；其余连续体同源展开后两组也重读 |
| 瞬态PWL位移折点导致速度无唯一值 | 位移加载族明确限全程仿射；牵引／体力保留一般PWL；校验仿射和初态相容 | review_linear通过 |
| 单帧constant与覆盖t0到tf冲突 | 全程常量显式定义域[t0,tf]、存储在t0；不是外推 | review_linear通过 |
| 顶维输出子集与允许location冲突 | 允许仅供输出的cells子集，体力／材料仍覆盖全部cells | 三组最终重读通过 |
| 梁弯矩歧义、空参数表 | EI·w″明确写出，parameters={} | review_linear通过 |
| 超弹性σn和PN混用 | 该题牵引表专用为每参考面积名义死载PN | review_nonlinear通过 |
| 损伤energy表只写弹性储能 | 表内写完整弹性+梯度裂纹内部能积分 | review_damage通过 |
| 内聚界面切向约束与完整牵引±Tn过定 | ±Tn仅法向；切向反力由连续约束决定，不默认为0 | review_damage通过 |
| 裂尖不采样与裂尖位移矛盾 | 仅禁止裂尖点应力，允许位移及积分应力 | review_damage通过 |
| 固定疲劳频率与逐块r矛盾 | 统一为逐块给定循环频率；Paris参考K采用平方参数及显式开方，单位Pa2.m | review_damage通过 |

最终三组分别完整重读19、15、11文件；去重43文件全部实际SHA256与作者独立重算相同，清单见[审阅manifest](chapter-03-review-manifest.json)。没有剩余已发现的题意阻断。此结论仅关于公开契约可实现性；并不保证所有可能歧义或物理错误均已排除。

## 工具和安装证据

固体专项14组测试，包含21模型循环，不把循环数量当物理覆盖证明。21题静态检查按九节运行；全章额外核对规划slug、连续唯一编号、三文件阅读依赖和配置覆盖。报告位于 `runs/authoring/chapter-03/`；可复制命令：

```sh
.venv/bin/python -m unittest discover -s tests -p 'test_solid_*.py' -v
.venv/bin/python -m unittest discover -s tests
```

隔离安装位于 `runs/authoring/chapter-03/install-check/`，使用runtime_materials真实21题闭包生成**临时工具装配**，新venv执行普通pip install本地目录（非editable）。安装后移走源包、清除PYTHONPATH、启用Python隔离模式并更换工作目录；21模型均由venv的site-packages经公共CLI info、validate-input、validate-output、显式策略grade及稳定SDK读取／往返，错误物理单位仍拒绝，缺扩展仍报工具错误。参考=临时零数组只用于工具判分回传，不是数值参考，不进入qbank数据或发布产物。

该证据限当前macOS arm64／Python3.14构建环境，不证明Linux AMD64 Harbor容器已安装运行、离线依赖齐备或CPU／内存配额已在容器中实测执行。资源合并成功和源码存在消费点不冒称硬限额执行验证。

## 领域核查资料与后续

规划按能力而非来源建立。核查了开源作者的[固体力学数值教程目录](https://comet-fenics.readthedocs.io/en/latest/)和[线性问题目录](https://comet-fenics.readthedocs.io/en/latest/linear_problems.html)中的弹性、梁截面、模态、动力积分、黏弹性、塑性及屈曲范围；[内聚界面教程](https://bleyerj.github.io/comet-fenicsx/tours/interfaces/czm_interface_only/czm_interface_only.html)提示界面内部状态和卸载需要明确定义；[疲劳累计损伤官方说明](https://doc.comsol.com/6.3/doc/com.comsol.help.fatigue/fatigue_ug_sme.4.25.html)用于区分雨流计数与Miner累积。本题自行完整定义有限材料与分析族，不要求考生复现这些软件或引用这些资料，未复制来源算例或参考数值。

下一阶段需逐题建设真实数据与可信参考、审核全部输入输出、检验非线性分支及模型适用性、网格／时间／内部长度收敛、参考误差与工程证据，并校准容差及运行预算；之后才冻结真实实例数、制作公开样例和执行Linux目标平台评测发布。本次未写任何examples／cases／references数值数据，未生成正式评测包。
