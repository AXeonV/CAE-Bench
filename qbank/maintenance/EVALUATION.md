# 评测配置与消费

题面与DATA拥有公开要求，case的reference/grading.json拥有实际评价计划与数值规则。参考可以是完整输出或稀疏观测，运行器先预检，求解后完整校验提交，再提取和评分。配置语法及错误分类见[判题说明](../../docs/GRADING.md)，HF布局见[数据池设计](../design/DATA-STORAGE.md)。

## 运行设置

judge-config.json只定义执行设置，不提供评分或回退容差。timeout_seconds为逐例求解墙钟；max_output_bytes显式null不设独立文件字节限额，省略为128MiB；evaluation_timeout_seconds为独立评价worker时限，默认60秒。评价超时是基础设施错误，不能记考生零分。

verifier_budget按实际case数计算总时限，包含求解、评价及装载／报告开销；总预算不得截断合法逐例执行。Harbor模板和本题harbor/task.toml合并Agent、构建、CPU和内存资源；verifier独立且无网络。执行主机需验证阶段隔离和限额实际生效，解析配置不能替代执行证据。

瞬态热传导author/check.py的memory_mb本地RSS检查与Harbor容器内存声明应一致。

## 准备和发布

已有HF清单先按[数据操作](DATA-SYNC.md)装配并严格核验。当前发行版的公开样例仅含随机格式输出，不公开样例reference/grading.json，也不提供样例数值判分命令；隐藏case配置仅进入verifier。格式示例与判题参考分别验证，稀疏参考不冒充完整result.h5。Harbor 的样例说明根据已校验公开包的实际文件逐例生成，仅在包含 output/result.h5 时列出完整提交示例。

prepare_harbor预检全部case配置，核对公开包内容，隐藏参考仅装入独立verifier。每例配置及输入／参考／代码闭包摘要进入报告，不再维护虚假的全题单policy摘要。具有明确数值参考的作者侧验证与verifier调用同一case评价入口；随机格式样例只做结构验证。

制数模板保存在author/grading-template.json，由作者工具显式生成每例配置；它不是运行时来源。当前发行范围的数值题使用完整case配置模板，包含checks和显式scoring；旧题的内层policy模板由author_case_grading显式包装为direct_outputs配置，不能从metric猜测评分模式。新制数调用author_case_grading与write_case_grading保留完整策略，不用提取的author_policy重建配置而丢失scoring或领域变换。无数据题可维护模板及题面，不能据此宣称case绑定、数值参考或预算已校准。实际判题不提供题目级策略兼容或缺省评分。

case级策略只实现题面允许的判据。应用新的取样方法到真实题目前须公开其重建及误差含义并审阅；已有物理题保持原有完整输出直接比较。送分样例与去重边界见[数据池设计](../design/DATA-STORAGE.md)；公开 case 仍参与计分，报告标识 public_cases 和逐例 public_sample，不能当作未见输入的独立泛化证据。

维护测试使用 tests/task_fixtures.py 在系统临时目录生成输入、参考和样例；发布／Harbor 的源码项目也在临时目录装配。普通测试不读取源码树的题库载荷或回执，不联网拉取 HF。涉及清单及完整性消费时另建本地池并由真实 assemble 生成回执，不伪造已有回执。

## 连续评分维护

连续评分的配置与计算定义见[判题说明](../../docs/GRADING.md)，公开公式、权重及逐物理量scale_floor由各题instruction.md明确给出。每例保存显式scoring，旧二元配置不因安装新版运行时而改变语义。转换工具caeoj_tools.continuous_scoring仅在作者明确调用时迁移配置；它继承原NRMSE尺度下限，或将旧绝对容差／max_abs上限作为有单位的尺度下限，不把迁移当作数值校准，也不改参考数组。改变评分后须重建池描述、装配回执、公开包和RC，并验证5%、10%边界、中间分数、最大分量聚合、零参考、压力尺度与异常分类。
