# 材料组织演化声明维护

仅供维护，不增加考生题意，不进入公开包。各题instruction、DATA及通用CONTRACT拥有完整物理、接口、规模、资源及评分定义。一般参数合法不等于物理解、参考准确或预算可达。

共享扩展`microstructure.phase_field`在`qbank/extensions/caeoj_ext/microstructure/`，包含精确模型资源及声明检查；可信runtime显式绑定七个slug和model，并保留microstructure-名字空间诊断E_MICROSTRUCTURE。复用现有entities、points、fields、conditions及时间轴，无新核心Schema、SDK接口、发布器特例或考生注册步骤。

检查器核对参数／量纲、周期矩形及真实探针、模式身份、整数波矢规范方向／唯一性、cos／sin轴、各状态初值的保守幅值界、三元迁移率完整对称正定及条件数、公开尺度／时程、控制覆盖、全部quantity与数组形状。尺寸、能量、界面比例、时程和控制界限由各题DATA公开；有限float64可表示性和连续收敛仍需正式数据验证。检查器不演化相场、求导、制作参考或静默修复材料。

维护展开器：`python qbank/maintenance/authoring/build_microstructure.py`。它只写文档、配置及声明资源，不生成数值数据；重建后须核对最终审阅散列。领域按物理复用，文件目录拆分不增加考生阅读。

专项：`python -m unittest discover -s tests -p test_microstructure_contract.py -v`。临时HDF5在runs中独立生成，不是假正式样例。普通安装审计：`python tests/microstructure_install_check.py --work runs/authoring/chapter-16/install-new`，要求新空目录；创建全新venv、一次普通pip安装、移开装配源码并用-I从其他目录检查CLI、SDK、坏输入和缺扩展。需要可获取的依赖；Windows运行旧题库兼容测试时明确`PYTHONUTF8=1`。

配置继续消费grading v2的quantity+unit、prepare_harbor.task_config及现有judge。数据缺失时不得用临时fixture绕过正式publish／prepare前置检查。技能工作流与现有通用接口仍适用，无接口迁移。证据及限制见[进度](../../design/reviews/chapter-16-progress.md)。
