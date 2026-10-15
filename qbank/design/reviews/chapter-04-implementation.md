# 第四章实现、配置与审阅记录

日期2026-10-16。范围为6节12题的规划、题面、自包含DATA、必要表示与领域检查、评测配置、独立考生审阅；不生成正式数据、参考解或发布评测。基线6e7ccd0，原工作树干净。最终阅读入口见[整章目录](../../04-multibody-mechanics/README.md)，审阅文件版本见[25文件散列](chapter-04-review-manifest.json)，验证摘要见[机器记录](chapter-04-validation.json)。

## 规划与物理责任

原总体目录只有章级方向，先自主确定6节12题有限清单并保存选择依据，再按三批每批4题实施。运动学与逆动力学、约束与自由刚体、连接与部分驱动、柔顺接触与摩擦、速度跳跃、柔性模态与双向惯性耦合分别定义能力。空间自由刚体不是平面题换名：它明确考查姿态、随体惯性和陀螺项。首版柔性任务给定有限维材料／模态模型，不把模态提取、连续应力或截断准确性暗中加入任务；刚柔耦合明确只含平移载体。

固定的是物理响应和适用范围，不指定求解软件、坐标方法、积分器或参考离散。几何、载荷、参数和初态属于变化算例，不按机构名称或来源拆题。每题仅依赖instruction、DATA、通用CONTRACT；维护生成器逐题展开实际适用分支，无共享考生DATA或COMMON。

## 表示与实现归属

初稿采用points身份占位；维护核查发现它会要求伪坐标，不能准确表达离散实体。因此在通用层新增`kind=entities`，只含ids，不含坐标、网格或聚合source。它仍使用[T,N,*component_shape]和point表示逐实体状态，不是连续空间采样或整体积分；DATA拥有刚体、关节、碰撞对、模态系统及跨表ID的语义。

这是实际通用表示缺口：修改核心location Schema、通用位置与value_kind检查，以及CONTRACT 4.5；SDK本已按ids和time复制，无须增加专用接口。旧mesh、points、aggregate分支及量值含义不变，无迁移既有数据。新类型可在独立核心中校验，不依赖多体扩展。

机械模型的参数、单位、条件集合、矩阵／惯性声明、载荷采样、碰撞配对、输出覆盖和规模检查在`qbank/extensions/caeoj_ext/multibody/`；可信开发provider新增multibody.mechanics、12题绑定及未知模型名字空间诊断。未修改中央发布器、Harbor执行器或考生命令。公开闭包不含维护生成器、tests、author、隐藏数据或参考。

声明检查不积分运动，不证明关节全程满秩、初态与驱动相容、闭环分支唯一、接触全程小重叠或预算内可解。上述是正式数据接收条件，须后续独立核验。对称性、Cholesky／特征值和初始四元数检查也只是浮点声明检查，不是物理适定证明。

## 独立考生审阅与闭合

先由工作审阅者提出模板修订，新增entities后重查全章。最终独立考生证据来自另行启动的3名subagent（candidate_final_a／b／c），均以fork_turns=none隔离作者历史，每人仅收到4题instruction／DATA及CONTRACT的路径和真实实现任务；不接触实现、隐藏数据、维护记录、作者答案或期待结论。三组完整阅读全部最终公开材料；末次轻微措辞修订由对应独立考生只复核实际改变的两份DATA，未变文件沿用已核对散列。终检逐一比对25个不同公开文件，全部与最终独立审阅者报告一致。初步工作审阅记录不代替这次隔离考生证据。

| 发现 | 修订及复核 |
|---|---|
| 刚体题残留柔性系统、mode_count、modal_system；纯运动学混入loads和约束力 | 按题裁剪，模板同步回写；最终三文件复核闭合 |
| 无驱动题定义角驱动，接触题混入关节／弹簧／collision | 删除非适用定义，明确唯一算子全集；接触与冲击保持不同问题族 |
| 正值参数后重复非负范围，条件表头后空行断表 | 严格正值及表格统一，生成器与输出一致 |
| 评分残留不适用的四元数／角度拟合措辞，弹簧与接触剩余模板词；最终隔离考生发现逆动力学残留“连接”及空间题残留角度模运算 | 仅保留本题适用规则；对应最终文件再次复核 |
| 固定points占位不能真实表达对象身份 | 新增通用entities并删除伪坐标，三组全部重读共同协议和本组文件 |

审阅覆盖非连续ID、关节端交换、展开角、逆动力学转矩符号、载荷中间时刻、随体非对角惯性、四元数跨零符号、弹簧力矩、共享接触候选、摩擦接触点相对速度、碰撞配对与冲量自旋、模态矩阵布局及B双向耦合。最终在实际检查范围内无未决问题；这不保证没有缺陷，也不提供数值正确性证据。

## 配置到实际消费点

每题grading v2按quantity与unit绑定实际outputs逻辑名；field和array名称自由。真实task_policy／resolve_policy及grade_arrays已测试全部12策略、每个quantity的atol等号接受与nextafter超限拒绝；总判据是所有时刻／实体／分量逐值通过，rtol=0.01，无拟合或豁免。非法输出score=0，错误参考score=null。

每题judge-config显式timeout_seconds：两道瞬时碰撞120秒，其余900秒；max_output_bytes=null；stage=provisional。真实prepare_harbor.task_config合并agent=3600秒、build=1800秒、4CPU、8192MB、0GPU、Linux、独立verifier和no-network。总verifier预算为`max(1200,300+N*(逐例时限+60))`，其中1200来自共享模板；用临时N=3验证消费，碰撞题实际总预算1200而非840。没有正式案例数，不虚构最终N。逐题harbor/requirements.txt固定scipy==1.18.1，由prepare复制到候选与verifier的requirements并由Dockerfile安装，补足题面承诺的可用库；安装版本按本地已安装环境选择，相同requirements已在独立macOS安装环境实际安装并导入SciPy 1.18.1，目标Linux镜像仍需实测。CPU／内存／墙钟配置加载不等于目标容器中已实测硬限制。

本次未改变评分框架或判据，未运行Agent模型benchmark。正式输入、参考、公开样例和实际N缺失，因此不调用要求这些前置材料的发布／Harbor组装器，也不以临时fixture冒充正式可运行题目。

## 验证与范围

- 六节按author-section静态脚本全部通过；12个slug与规划一一对应，编号连续唯一；检查跨节边界和公共单位／身份／时间／参考系语义。生成器重建后25个已审阅文件散列不变。
- `tests/test_entities.py`独立核心往返，无坐标结果复制、非法键／value_kind／逆序IDs拒绝。
- `tests/test_multibody_contract.py`六组测试覆盖12模型HDF5／SDK往返、真实评分与资源消费、公开闭包，以及从DATA另选的反例：错误body ID、浮点形式ID、kn／vs／l0为零、负摩擦、bool模态数、e>1、非单位四元数、不满足主惯量三角不等式、B使完整质量不正定、非正定K／负阻尼、分离碰撞对、非外切、缺驱动力输出、重复候选对、错误quantity和时间重建。合法非对角M和负号初始四元数接受。
- 全仓`python -m unittest discover -s tests`：280项通过，47.047秒。日志`runs/authoring/chapter-04/regression.log`。它覆盖既有题库与工具回归，不意味着280项都是多体数值验证。
- 使用真实runtime_materials生成12题单一公开运行闭包，以新venv普通`pip install`安装。装配源目录移开、清除PYTHONPATH、工作目录换至/private/tmp、Python -I隔离后，全部12题CLI info／输入／输出校验／显式策略判分及SDK写回通过；坏单位拒绝，缺必需扩展明确报工具错误。安装装配身份与最终源码重新计算相同。平台仅macOS arm64／Python3.14，Linux AMD64容器与真实资源限额未实跑。

临时输入／输出只验证工具；零值输出不是力学参考解。全部fixture位于tests临时目录或runs，未写examples／cases／references，也未发布解题包。实际数据审计、数值解收敛、独立参考精度、误差／规模／预算校准及目标平台执行留待数据阶段。
