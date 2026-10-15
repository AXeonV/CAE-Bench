# 第 0 章：基础测试

本章用于检查程序入口、通用数据协议、结构校验与判题链路，不考查 PDE 或 CAE 物理求解能力。

| 节 | 题目 | 任务 |
|---|---|---|
| 0.1 输入输出测试 | [smoke-test](0.1-io/smoke-test/instruction.md) | 按清单回传输入场，保持实体、时间、分量和数值对应关系 |

题目数据定义见题目自己的 DATA.md；考生只需该题 instruction.md、DATA.md 和通用 CONTRACT.md。

## 本地维护与验证

`smoke-test` 从 `tasks/` 迁至本章，任务标识保持不变。11 组现有 `cases`、回传参考程序 `solve.py` 均保留。以下命令在项目根目录、已安装项目依赖的 Python 环境中运行：

```sh
python -m caeoj smoke
```

默认读取本章 `0.1-io/smoke-test/cases/`，执行同题 `solve.py`，每例默认墙钟时限为 10 秒（可用 `--timeout` 修改）。逐例参考来自输入数组；输出与日志写入忽略跟踪的 `runs/smoke/`。此本地工具没有独立 CPU／内存配额或容器隔离，不代表 Harbor 环境测试。

需要重新生成协议测试数据时，可显式选择临时目标，不覆盖现有数据：

```sh
python -m caeoj make-cases --output runs/smoke-generated/cases
python -m caeoj smoke --cases runs/smoke-generated/cases
```

本次迁移不新增 Harbor 配置或发布材料包；当前发布与 Harbor 组装入口仍面向 `tasks/<task>`，本题继续使用专用 smoke 命令。
