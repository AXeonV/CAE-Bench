# 82题审阅RC装配记录

发行标识：`caeoj-qbank-20261023-rc2`。本版按已确认清单纳入82题；保留[RC1历史记录](../release-assembly-2026-10-23/README.md)，不覆盖旧归档。完整性、可消费性与数值资格分别陈述。

交付包：[RC2 ZIP](<C:/Users/Jim Zhou/CAE-OJ-Releases/caeoj-qbank-20261023-rc2.zip>)，`4910051915` bytes，SHA256 `7b10307a9ff5b983ead18b25b50612cfbed526bc1e58f26b9ed892bcfee2adb0`。

解压后入口：[README](<C:/Users/Jim Zhou/CAE-OJ-Releases/caeoj-qbank-20261023-rc2/README.md>)；[catalog快照](catalog.json)为逐题身份、真实选样、profile、局限与排除原因的归属；[完整性清单](SHA256SUMS.json)绑定最终目录。

## 纳入范围

|章节|题数|正式case角色|公开样例角色|
|---|---:|---:|---:|
|00-basic-tests|2|17|3|
|01-prescribed-pdes|13|266|26|
|02-fluid-mechanics|67|364|67|
|合计|82|647|96|

第2章含43道流动能力题和24道CFDCodeBench。2.1.1、2.1.3各沿用原10例；其余38题沿用本地309例，另3题补取11例。320个新增正式case角色统一标记`unvalidated-reference-rc`，没有将356项候选全选。样例和正式case可共用身份，角色数不等于独立工况数。

排除170项：97项无可用case、51项FOAMBench参考资格待核验、22项修复题接口与环境待交付。第19章仍待整仓patch接口和可交付环境；FOAMBench候选未在本版追加。完整候选的43道流动题均已进入本RC，没有因数值待审再次移出。

## 实际执行与证据

- [本地38题](local-flow-report.md)：匹配来源backend严格装配校验、逐例输入／参考输出结构、prepare_case和参考自判分；公开ZIP题面、DATA和样例与源资产一致。原选样未改。
- [新增3题](new-flow-report.md)：只读补取Titan已有11例必要载荷10,755,958 bytes，摘要全部匹配；原工具pack／assemble／strict verify及逐例实际消费通过，公开随机format样例不冒充数值答案。来源元数据原件及摘要索引随维护证据保存。
- 发行工具26项测试：25通过，1项因Windows symlink权限跳过；可选发行说明进入README和catalog，独立复核见[审阅](scope-review.md)。
- [最终独立消费](independent-consumption.json)：完整目录verify；9个代表题从最终归档提取，正常pip安装到独立target，隔离Python实际验证输入、参考得1分、数值变异被拒。所有项目模块均来自新安装目录。复用现有第三方Python依赖，未宣称干净Linux或全部团队机器验收。
- [单文件交付校验](delivery-verification.json)：外层ZIP逐成员实际流式SHA256／大小与已验证目录匹配。

本轮未下载HF、未求解重算、未调用模型、未实现快速判分。新增题题面、DATA、判分阈值和资源原样冻结，仍待题面与case联合审查、独立数值资格、许可范围和资源／异机验收。参考自判分不能证明数值正确，本包不是已验收的完整CAE-OJ-Bench模型执行器。

## 团队使用

按发行README运行`python release.py list`、`verify`和按题`extract`。维护者持有含隐藏参考的`qbank.zip`；只将对应`public/*-agent.zip`交给考生。安装所需第三方依赖和系统动态库仍须准备，求解器镜像与模型执行器不在本包中。通用操作见[发行流程](../../../maintenance/RELEASE.md)。
