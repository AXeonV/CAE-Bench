# 建设中：复波数 Helmholtz 快速算子

来源为bempp/bempp-cl issue20、PR45；基线84345ee9ee314c85750f045c7ad38090f5ea5f26，参考头2a353ef7cf73883fd761b400691dfb82cd7f614f，ExaFMMv0.1.0固定c9ad1980d50cb6ed5d01b2d5e65c7fce51bcfb05。三处实际库文件修复覆盖标量核；不把上游Maxwell变更当本题能力。

范围与独立设计：[范围卡](../../../../design/repair22-bempp20-scope.md)，设计审阅runs/design-review/repair22-bempp20/report.md。原型已实际运行真实点FMM/局部接口及三种边界、两种势，原件复波数失败，参考与独立核/梯度、稠密库路径及外部势独立三角积分核对。参考与缺陷数据、完整源码强制重编、HF固定提交、最终公开包、全量审计及正式Oracle均尚未完成；本题不计入22题已完成数。

最终合法范围和600秒预算是待验收的题目要求。原型资源测量不等于完整范围或最终包通过，任何后续调整应同步公开材料、配置及审阅。恢复记录runs/authoring/repair-22/bempp-20-handoff.md；原始取证和原型日志留在work/repair-22/bempp-20及runs/authoring/repair-22。

已实际构建包含分离旧库／SDK解释器的完整生产镜像，原始273文件及原生98文件来源可由prepare_runtime.py逐SHA复核。普通SDK依赖最初缺libGL而导入Gmsh失败，已通过真实依赖安装修正，原失败保留。12个正式候选输入已按CONTRACT MSH4.1和题内检查全部加载与序列化，但不因此声称数值通过。

正式参考第一轮失败已找到并实际复核根因：作者重放将原生FMM的GiB级预计算文件写入768 MiB临时内存盘，原生库未报告文件截断。相同镜像／源码／输入改为足量磁盘后，第二例误差从0.265降为4.1e-9，最大点例误差约6.7e-7。独立诊断在runs/authoring/repair-22/bempp-numeric-audit/report.md，原失败dataset-v1保留，未发布或计为合格。不能把截断归因为复波数修复错误，也不通过更改库算法绕过它。

修正后的dataset-v2使用每例独立磁盘目录、至少8 GiB可用空间、4 CPU／4 GiB、原生实际调用；12例参考与12例原件流水线正在执行。点参考须先通过闭式Green核与梯度逐标量核对；边界参考另以未修改原始库的稠密弱形式、独立P1质量矩阵逆及16／24阶独立三角积分核对，独立积分只用于验收，不生产reference。最终全量数值、资源、公开包、HF及后端验收仍待完成，不计入22题已完成数。


阶段证据已固定于[qualification-v2/index.json](data-evidence/qualification-v2/index.json)：12例真实参考完成；全部6点工况通过闭式核／梯度，全部6曲面工况通过原始库稠密弱算子＋独立质量矩阵及16／24阶势积分。生产镜像base/reference逐一核对273+98原始文件；reference恰替换声明3文件。12例耗时15.6至126.6秒，按实际逐例4 CPU／4 GiB环境测得；不等于所有合法输入的最坏界。

公开包241b6bad4d344139e034dd798638a0cb62d0a364ae28c9b999a41a7bb9e18e27已通过真实网络关闭、普通pip安装，移走包src后从安装产物加载全部12case和2sample并实际运行两份原始库样例（均正确判为缺陷0分）。独立考生审阅见[author/reviews/candidate/report.md](reviews/candidate/report.md)。真实后端7项探针完成：候选重编和sample求值、未来字节码时间戳、语法／额外／符号链接、原始编译器／运行故障分类、实际候选Python导入超时及进程终止、UID1000/禁止外网/源码字节码与隐藏材料权限；原始日志归qualification-v2。

HF固定提交d4011e0522e1e9dcbc8f228624fe7b1c02063928上传79文件，空缓存重新取回并装配77文件changed0，正式strict verify通过。数据池一致性独立于数值资格。全量数据审阅、原件12例差异和真实Harbor Oracle仍在运行或待审，不将以上阶段冒称最终完成。


全量独立审计随后发现公开检查器漏拒绝非`input.h5`文件名（题面已经限定），已修并在最终ZIP3b2f5344125bf5679bd026bef828bbe97a44c9a132cca97a5975a25ed8d319bf内实际隔离复核14份输入／参考、28磁盘变体及364阈值试验。题面同步明确根目录安装后切换题目目录再运行。新旧公开材料身份及原始报告入口见[public-artifacts.json](data-evidence/public-artifacts.json)；原生源码、驱动、输入与参考不变。旧241b6bad探针与Oracle保留原身份；最终新包Oracle单独运行。一次作者准备目录锁冲突导致的0-trial v2失败和72文件恢复亦单独保留，不混作考生成绩。
