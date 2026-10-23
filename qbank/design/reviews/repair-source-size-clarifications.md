# 有界变更独立复核：源码文件大小说明

结论：通过。此次复核只认证五题新增公开限制文字与此前已生效后端限制一致，不是重新盲审题目、重跑求解器或重新数值认证。

独立脚本 `check.py` 直接读取五份保存的旧 ZIP、新 dist ZIP、题内 source-size-clarification.json、旧 prepared task 的 agent.zip 和 source-repair.json，以及当前题内配置。机器结果为 `report.json`。

五题分别为 hysteretic-trial-state-repair、surface-flow-constraint-repair、two-temperature-state-repair、multisite-surface-concentration-repair、granular-pair-stress-repair。每题确认旧/新完整 ZIP SHA 与归档记录一致，文件清单完全一致，逐项字节变化仅有 instruction.md 与 MANIFEST.json。instruction 的变化严格为末尾追加空行及“每个提交文件不超过1 MiB（1,048,576字节）。”，原正文和原换行字节均保留。MANIFEST 的 files 映射只有该 instruction 散列变化，assembly 身份随之改变；其余声明和每个实际载荷散列都核对一致。

每题旧 prepared agent.zip 与保存旧 ZIP 散列一致；旧 prepared source-repair.json 与当前配置完全一致，并均已设置 `max_source_bytes=1048576`。后端对每个替换文件分别执行大小检查，与新增“每个提交文件”文字一致，未改成总提交大小，也未新增物理、模型、方法或数值义务。

SDK、输入、样例参考、评分、真实源码和驱动载荷逐字节不变，旧后端配置也不变，因此在原认证范围内复用先前数值、后端与 Oracle 证据充分；新公开 ZIP 的身份由本次新散列与差分证据单独绑定。不得将旧 Oracle 描述成曾运行新 ZIP；它运行旧已冻结材料的事实仍须保留。

附加源码只读检查：共享 source_repair 配置正则仅新增大写 `.C`，现有普通文件名/路径/替换目标与预算限制没有改变；suffix 测试循环增加 `.C`。这只证明配置入口接受该后缀，不证明 MOOSE 编译/运行已支持，后者仍需两题真实原型及后端探针。

可选 reviewed_links helper 的只读检查确认：未传参数仍使用原五个文档链接白名单；传入显式映射时逐项校验链接目标文本，并要求归一化目标在同一原始归档根内且指向真实常规文件。常规文件摘要与完整实际文件清单比较、复制链接字节比较及缓存中禁止实际symlink条件保留。该参数是调用者显式提供已审映射的扩展，没有放宽默认验证。既有两原始归档回归及 DOLFINx 显式映射/错误目标/变更缓存报告已只读核对；本段不将他人报告冒称本轮重新运行。
