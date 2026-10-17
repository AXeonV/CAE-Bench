# 当前消费者定位索引

需要定位配置读取者或实现适配时查本页。字段及默认值不在此重复维护，见[评测配置](../../../../qbank/maintenance/EVALUATION.md)、[评分](../../../../docs/GRADING.md)和[运行装配](../../../../qbank/maintenance/RUNTIME.md)。修改前搜索实际调用及相关测试。

| 要核对的机制 | 当前入口 |
|---|---|
| case计划预检、可信评价器注册、观测提取与评分 | `src/caeoj/case_grading.py`；`qbank/extensions/caeoj_bundle/runtime.json` 的 `evaluators`；`src/caeoj/grading_policy.py`、`grading.schema.json`、`grading_metrics.py` |
| 逐例执行、错误分类和汇总 | `src/utils/harbor/tests/judge.py`；`src/caeoj/cli.py` |
| 任务目录、资源覆盖及总预算 | `src/utils/prepare_harbor.py`、`src/utils/harbor/task.toml`；本题 `judge-config.json`、`harbor/` |
| 公开包、运行闭包、依赖锁 | `src/utils/publish_dist.py`；`src/caeoj_tools/assembly.py`、`dependencies.py` |
| 公开模型元数据和可信 provider | `src/caeoj_tools/author.py`；`src/caeoj/runtime.py`；`qbank/extensions/` |
| 数据绑定与前置校验 | `src/caeoj_tools/data_pool.py`；本题 `data-manifest.json` |
| 本题额外执行消费者 | 本题 `author/`，检索字段全部读取者，不假定 Harbor 是唯一消费者 |
| 现有验证 | `tests/grading_fixtures.py`（实际 case 评价 fixture）、`qbank/maintenance/authoring/verify_install.py`（共享安装验证），以及评分、装配、Harbor 与领域专项测试 |

题目目录和配置存在不表示数据就绪；单点 CLI 成功也不表示容器资源、网络隔离或完整 benchmark 已验证。
