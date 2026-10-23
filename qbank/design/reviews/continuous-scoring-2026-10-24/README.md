# 连续NRMSE评分与RC5

当前发行范围82题、647个正式case、96个随机格式样例。第1／2章80题630个case采用统一连续评分；第0章2题17个case保留原二元规则。

对每个请求输出量、标量分量和时刻分别计算空间加权NRMSE，case的E取最大值。E≤0.05得1分，E≥0.10得0分，中间得(0.10-E)/0.05。题目reward是全部正式case分数的算术平均。格式错误、程序失败及超时零分；基础设施错误不算考生零分。CLI部分分退出1，真实分值从JSON.score读取。

交付：[RC5 ZIP](<D:/Code/CAE-Bench-OJ/runs/releases/caeoj-qbank-20261024-rc5.zip>)，4910246276 bytes，SHA256 `8c2ddb61ae54aed470aba9d62f1ff2e346e26f573db52d76a13a6e456b547cf1`。使用[发行README](<D:/Code/CAE-Bench-OJ/runs/releases/caeoj-qbank-20261024-rc5/README.md>)。RC4及之前历史包保留不变。

## 配置、材料与验证

- [逐题账本](scoring-ledger.json)与[迁移配置](preparation.json)覆盖82题、647个case。630份数值配置与80个完整作者模板一致，17份接口配置字节未改；所有case与样例输入身份保持RC4。
- 既有正式输入、参考数组、观测资产及随机样例字节保留，仅数值case的grading配置变化。[来源身份恢复](provenance-preservation.json)核对旧receipt、descriptor摘要及全部非grading资产，保留旧origin；真实pool select／assemble／strict生成新回执，不伪造新证书。新描述仅在本地池和本包，未上传HF。
- [核心实现](core-report.md)：显式scoring、每时刻／分量NRMSE及max聚合、部分分报告和Harbor实分汇总。最终核心91项及154子测试通过，包含真实worker的1＋0.6→reward0.8；补边界30项及兼容23项与前者有重叠，不相加。
- [作者入口](policy-report.md)：80题完整outer模板成为唯一制数来源，删除24份CFD重复模板；热、PDEBench、CFD和维护验证入口保留完整scoring。历史来源快照不重签。具体分批测试及旧fixture失败闭环见日志。
- [独立实现审阅](independent-review.md)及24项实际边界／负例通过；[配置映射](independent-mapping.json)逐项核对80模板、630新配置与17原配置。
- [独立考生审阅](candidate-review.md)：80题公开三文件的评分定义及关联观测语义完成复核，单点权重P3已修。未复查未变样例、不认证物理参考或资源。
- [最终独立消费](independent-consumption.json)：10题从RC按题解压并普通pip安装，复用现有第三方依赖；项目模块均来自新安装目录。实际参考满分，7题构造NRMSE为2.5%／7.5%／12.5%的输出分别得1／0.5／0且NaN拒绝；另含第0章两题和大型三维可压流参考判分。记录本机实际评价耗时与预算，不外推到全部case或异机。随机样例格式检查通过。
- 完整发行目录和[外层ZIP逐成员摘要](delivery-verification.json)通过；公开三文件及核心代码字节与最终源码一致。
- [资源调整](resource-adjustment.json)：三维可压流代表例在新安装公开运行包中评价57.391秒，原60秒预算余量不足；将本题独立评价预算改为120秒，求解时限不变，外层verifier按6例公式同步为12180秒。[独立实际预算消费](independent-resource.json)通过。此测量不等于全部case或异机资源资格。

## 迁移含义与剩余资格

NRMSE使用既有空间权重，没有显式权重的题使用等点权重。原pointwise／违例比例的atol继承为同单位scale_floor；原NRMSE保留floor；EVP继承原max_abs阈值作为floor。每题题面明确列出。这是评分政策变化，不与旧容差等价，也未完成科学校准。温度的绝对表示、压力参考尺度和近零场仍须科学评估。

原有六题固定背景／压力去均值变换保留；多相两题的压力偏置仅影响参考RMS分母，不消除候选绝对压力误差。不同单位的场不拼接，不以均值掩盖最坏字段或时刻。

[RC4记录](../random-format-samples-2026-10-24/README.md)及其指向的全题审查中的参考数值资格、输入覆盖、压力尺度、资源和异机资格限制继续有效。新分值不可与旧二元成绩直接横比。本版仍是内部试运行RC，ready_for_formal_benchmark=false；未重新求解参考、调用考生模型或上传HF。
