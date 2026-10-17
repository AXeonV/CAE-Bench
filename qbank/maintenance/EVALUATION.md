# 评测配置与消费

题面与DATA拥有公开要求，case的reference/grading.json拥有实际评价计划与数值规则。参考可以是完整输出或稀疏观测，运行器先预检，求解后完整校验提交，再提取和评分。配置语法及错误分类见[判题说明](../../docs/GRADING.md)，HF布局见[数据池设计](../design/DATA-STORAGE.md)。

## 运行设置

judge-config.json只定义执行设置，不提供评分或回退容差。timeout_seconds为逐例求解墙钟；max_output_bytes显式null不设独立文件字节限额，省略为128MiB；evaluation_timeout_seconds为独立评价worker时限，默认60秒。评价超时是基础设施错误，不能记考生零分。

verifier_budget按实际case数计算总时限，包含求解、评价及装载／报告开销；总预算不得截断合法逐例执行。Harbor模板和本题harbor/task.toml合并Agent、构建、CPU和内存资源；verifier独立且无网络。执行主机需验证阶段隔离和限额实际生效，解析配置不能替代执行证据。

瞬态热传导author/check.py的memory_mb本地RSS检查与Harbor容器内存声明应一致。

## 准备和发布

已有HF清单先按[数据操作](DATA-SYNC.md)装配并严格核验。发布器只公开样例reference/grading.json及声明资产，不导出题目级策略或隐藏case配置。正确提交示例与判题参考分别验证，稀疏参考不冒充完整result.h5。

prepare_harbor预检全部case配置，核对公开包内容，隐藏参考仅装入独立verifier。每例配置及输入／参考／代码闭包摘要进入报告，不再维护虚假的全题单policy摘要。样例本地判分与verifier调用同一case评价入口。

制数模板保存在author/grading-template.json，由作者工具显式生成每例配置；它不是运行时来源。无数据题可维护模板及题面，不能据此宣称case绑定、数值参考或预算已校准。实际判题不提供题目级策略兼容或缺省评分。

case级策略只实现题面允许的判据。应用新的取样方法到真实题目前须公开其重建及误差含义并审阅；当前题目保持原有完整输出直接比较。历史样例／测试重叠仍按严格检查阻断，不因迁移取消。
