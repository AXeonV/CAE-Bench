# 第 0 章 smoke-test 迁移记录

日期：2026-10-15。

## 范围与决定

将 `tasks/smoke-test` 整体迁至 [第 0 章](../../00-basic-tests/README.md) 的 `0.1-io/smoke-test/`。任务标识仍为 `smoke-test`，回传规则及默认评分容差不变。此题是协议与判题链路测试，不属于 PDE／CAE 求解能力评测。

保留现有 11 组 cases、网格、HDF5 和参考程序，原编号跳过 07，不补编号或新增数据。迁移前后 44 个数据／参考程序文件逐一 SHA-256 相同；题面按三文件阅读边界修订，新增自包含 DATA.md。更新 CLI 默认位置、测试引用与文档入口，不保留旧目录副本。

原题没有 Harbor 配置或独立公开样例包，迁移后继续通过专用 smoke 命令运行。发布／Harbor 组装工具仍只支持 `tasks/<task>`；本次不扩展这些入口，也不新增虚假的配置就绪状态。发布器的“缺少公开样例”回归改为删除临时提取包内的样例，不再依赖 smoke-test 的旧位置。

## 独立考生审阅

独立 subagent 仅凭最终 instruction.md、DATA.md 与通用 CONTRACT.md 审阅，无源码、数据或维护规范帮助。首轮通过，提出两项精简：消除题面必须解析网格的误导，删除 DATA 中的迁移背景。修订后最终复核通过，可仅按三文件实现回传；此结论不替代运行或数据验证。

## 验证与证据

- 全量盘点 11 份实际输入及引用资产，无缺失项；逐份核对任务标识、fields/outputs 相等、位置、场类型、dtype、条件和可选 physics。DATA 覆盖实际分支。盘点及元数据覆盖记录位于忽略跟踪的 `runs/data-audit/smoke-test-migration/`。
- 在新默认路径执行 `python -m caeoj smoke`，11/11 通过，所有回传浮点场最大绝对误差为 0；报告位于 `runs/smoke/report.json`。
- 协议回归 40 项、grading 系列 36 项、equation grading policy 2 项、公开包回归 5 项，共 83 项通过。包含错误场值、结构错误及本地运行失败路径的既有测试；不是物理或模型精度验证。
- 修改 Markdown 的常规内联文件链接有效，活动源码／测试／文档没有遗留旧题路径，`git diff --check` 通过。

未运行 Docker／Harbor、模型评测或物理参考校准，未发布材料包。生成的日志、报告和临时数据均在忽略跟踪目录，不修改其余 PDE 题或第二章题面。
