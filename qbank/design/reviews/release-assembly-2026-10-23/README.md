# 题库内部RC装配与验收记录

发行标识：`caeoj-qbank-20261023-rc1`。本记录冻结本轮实际产物，不替代后续正式参考／资源资格认证。

交付归档：[caeoj-qbank-20261023-rc1.zip](<C:/Users/Jim Zhou/CAE-OJ-Releases/caeoj-qbank-20261023-rc1.zip>)。大小 `4683247814` bytes（约4.68 GB／4.36 GiB），SHA256：`e963a491691c5bedc350e9856cade6d01fa7260896d6ee94f12ce23ac8144e7c`。

解压后入口：[README.md](<C:/Users/Jim Zhou/CAE-OJ-Releases/caeoj-qbank-20261023-rc1/README.md>)；[逐题catalog快照](catalog.json)固定真实选样与profile；[完整性清单](SHA256SUMS.json)绑定发行目录48项资产，另含完成清单本身。

## 实际纳入

|章节|题数|正式case角色|公开样例角色|
|---|---:|---:|---:|
|00-basic-tests|2|17|3|
|01-prescribed-pdes|13|266|26|
|02-fluid-mechanics|26|44|26|
|合计|41|327|55|

样例可与正式case复用，角色数不相加为独立工况。第0章2题17例是基础设施检查，领域题为39题310例。2.1.1和2.1.3各使用用户确认的现有10例，不扩为100／72例维护池。

## 暂缓范围

|原因|题数|
|---|---:|
|reference_qualification_pending|92|
|no_usable_case|97|
|repair_interface_and_environment_pending|22|

合计211项。无case不进发行目录；309项本地及47项远端未验证候选不因产出而获得参考资格。FOAMBench51项已装配参考仍待数值资格，未纳本次默认包。第19章22题已有旧协议验收，但整仓patch接口、镜像可获取性／许可范围和异机交付尚未闭环，本次明确暂缓，未混称完成接口迁移。

## 已执行的验收

- 源资产：第0章有限生成并pack／assemble／strict verify；两道热学本地缓存装配核验；PDEBench原匹配backend的11题strict verify全部通过，210/210正式参考自判分通过。
- 第二章：2.1.1／2.1.3共20例、CFDCodeBench24例实际strict verify、输入／参考输出验证与参考自判分通过。CFD历史参考及资源记录摘要绑定；C19例外、C20—22同求解器加密局限保留。
- 装配工具：24项单元测试运行，23通过、1项因Windows创建symlink权限不足跳过；真实ZIP链接与路径负例另已覆盖。Harbor既有30项回归检查通过。独立实现审阅发现的format样例、私有材料泄漏、回执额外资产与目录冲突问题已修复并复审关闭。
- 最终目录：独立stdlib CLI verify实际通过，48项最终资产完整性匹配。
- 五类最终消费：smoke、稳态热学、Darcy、CFD一维扩散、三维稳态流动，从最终归档逐题提取，正常pip安装到独立target（复用已有Python第三方依赖），隔离Python实际验证输入、正确参考得1分、改动数值结果被拒绝；全部已加载项目模块位于新安装目录，无作者源码加载。
- 单文件交付：外层ZIP49项成员逐项流式SHA256／大小与已验证目录及完成清单匹配。未为验证再解压全部大数据。

## 稳态热学资源修订

原1秒预算在当前Windows进程和既有Linux Docker绑定环境失败。相同Linux 2CPU／1GiB的诊断重放32/32数值通过，最大实测1.941757511秒；按ceil(2×max)改为4秒，题面、README、judge-config同步，0.01K阈值和32例选样保持。新4秒实际整套重放32/32通过；Harbor verifier由现配置与实际例数推导4268秒，不另存重复覆盖值。详见[资源修订](steady-resource-revision.json)。

## 能力边界

这是题库与数据内部RC，不是完整CAE-OJ-Bench模型执行器；不含模型调用、凭据、大型求解器镜像、新repo_patch或fast判分。PDEBench的容差／资源仍为provisional，参考自判分不替代独立数值认证。五类消费验证在现Windows Python依赖环境完成；没有宣称所有团队机器／新Linux环境已验收。第三方源码与数据按各自许可署名，不能把所有来源统称项目Apache许可。

所有科学载荷均复用本地；没有重新从HF下载，没有移动Titan数值载荷或重算PDE参考，也未调用付费考生模型。临时原1秒失败、生成器修订与源码身份映射均在作者runs证据保留。

## 后续使用

解压整个交付包后，按其中README执行`python release.py list`、`verify`和按题`extract`。维护者持有qbank.zip与隐藏参考；只将对应public ZIP交给Agent。通用维护流程见[离线发行指南](../../../maintenance/RELEASE.md)。
