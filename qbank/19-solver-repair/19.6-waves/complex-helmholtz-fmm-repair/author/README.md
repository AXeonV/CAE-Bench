# 建设中：复波数 Helmholtz 快速算子

来源为bempp/bempp-cl issue20、PR45；基线84345ee9ee314c85750f045c7ad38090f5ea5f26，参考头2a353ef7cf73883fd761b400691dfb82cd7f614f，ExaFMMv0.1.0固定c9ad1980d50cb6ed5d01b2d5e65c7fce51bcfb05。三处实际库文件修复覆盖标量核；不把上游Maxwell变更当本题能力。

范围与独立设计：[范围卡](../../../../design/repair22-bempp20-scope.md)，设计审阅runs/design-review/repair22-bempp20/report.md。原型已实际运行真实点FMM/局部接口及三种边界、两种势，原件复波数失败，参考与独立核/梯度、稠密库路径及外部势独立三角积分核对。参考与缺陷数据、完整源码强制重编、HF固定提交、最终公开包、全量审计及正式Oracle均尚未完成；本题不计入22题已完成数。

最终合法范围和600秒预算是待验收的题目要求。原型资源测量不等于完整范围或最终包通过，任何后续调整应同步公开材料、配置及审阅。恢复记录runs/authoring/repair-22/bempp-20-handoff.md；原始取证和原型日志留在work/repair-22/bempp-20及runs/authoring/repair-22。

已实际构建包含分离旧库／SDK解释器的完整生产镜像，原始273文件及原生98文件来源可由prepare_runtime.py逐SHA复核。普通SDK依赖最初缺libGL而导入Gmsh失败，已通过真实依赖安装修正，原失败保留。12个正式候选输入已按CONTRACT MSH4.1和题内检查全部加载与序列化，但不因此声称数值通过。

正式参考资格尚未通过：首例真实执行通过独立核对；第二例p10原生FMM与闭式核／梯度有约0.265误差，局部核约1e-17，已被独立数学门槛阻止。没有发布该临时reference或计为合格数据。原始PR修复不自动保证新范围的整个原生FMM数值稳定性；p6/p8/p10与不同线程的小型诊断正在区分展开阶、几何尺度和多实例行为。真实错误及失败阶段保留于runs/authoring/repair-22/bempp-data-*及work/repair-22/bempp-20/dataset-v1，后续须先取得可公开操作范围或必要真实修复的数值证据，再冻结参数、范围及参考。
