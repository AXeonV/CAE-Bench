# 公开输出样例统一为随机格式示例

当前发行范围82题、96个公开样例角色全部为format，并且每例都有output/result.h5。只保证结构、dtype、IDs与时间轴正确，不保证数值答案正确；不提供公开sample/reference，也不引导对随机输出执行数值判分。

本次将4题7例从数值样例转为随机格式输出（含补齐smoke原reference-only角色的输出）；其余78题89例保持原始随机输出字节。正式case身份及样例输入身份与冻结RC3一致，4题共437份原正式输入、grading与reference资产字节全部保留。样例描述和相关case描述摘要因角色／示例文件变化更新，不宣称描述绑定摘要未变。

修订版：[RC4 ZIP](<D:/Code/CAE-Bench-OJ/runs/releases/caeoj-qbank-20261024-rc4.zip>)，4911922815 bytes，SHA256 `a7c4bbe290055471f2744c51f25c9a4caeed666e1abde16fc0b6c2db6337c68b`。使用[发行README](<D:/Code/CAE-Bench-OJ/runs/releases/caeoj-qbank-20261024-rc4/README.md>)。RC3等历史包保持。

## 对齐与验证

- [生成器](generator-report.md)：float64、int64、bool按dtype独立随机；保留全部组件shape和复制轴。三个原sample生成器及PDEBench准备流程均使用随机格式输出，不再写公开样例参考。PDEBench仍保留作者侧私有求解证据与正式case参考。
- [实际转换](conversion-report.json)：复用已有离线pack／select／assemble／strict verify；原输入与参考逐文件摘要核对。当前4题已装配相同缓存，新池未上传HF，跨机器应直接使用自包含RC或按证据取本地pool，不假称远端已更新。
- [独立考生审阅](candidate-review.md)：4题公开三文件及7组真实样例逐份检查通过；旧78题材料与其先前审阅版本一致。随机输出不接受物理正确性的承诺，也不声称随机值每项必错。
- [独立策略审阅](policy-review.md)：82题／96例角色、正式身份与437资产保持；数值正式判题未放宽。对有效格式包及缺／错角色、漏输出、额外公开reference的区分验证记录保留。
- 生成器专项5项通过；PDEBench追加4项离线测试通过；format/publish/Harbor的46项以44项及修正后2项分批通过；装配器27项运行，26通过、1项Windows symlink权限跳过。4题静态检查通过。具体命令／失败修复与边界见各日志，不把分批运行写成一次全量重跑。
- [最终独立消费](independent-consumption.json)：6类代表题提取并普通安装，复用既有第三方依赖；样例输出实际validate-output通过且无reference目录，正式case正确参考得1分、改坏的数值被拒。完整目录verify及[外层ZIP逐成员摘要](delivery-verification.json)通过。
- 装配器对public_sample_policy=random-format-only实际强制角色、样例资产完整性及无公开reference；解压公开包重新发布时从MANIFEST恢复format身份，不把缺失marker误判为数值样例。

## 基线与剩余边界

正式case保持的基线为已分发RC3。本轮开始时smoke主分支清单保留更早生成版的11个ID；本次主分支清单同步到RC3实际选择，不将此历史差异说成相对HEAD完全未变。逐题身份与差异边界见[sample-ledger.json](sample-ledger.json)。

前轮[全题审查](../prepublication-review-2026-10-23/README.md)所列参考数值、分支覆盖、压力评价尺度、资源与异机资格限制继续有效。统一随机样例不改变正式评分或授予最终Benchmark资格。本轮没有HF上传、重新求解正式参考或考生模型调用。
