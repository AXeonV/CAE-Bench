# 实现求解程序

阅读 `/app/${task_path}/instruction.md`、该目录中的 `DATA.md`和 `/app/docs/CONTRACT.md`。
实现题面范围内的通用求解程序，提交入口为 `/app/submission/solve.py`：

```text
python /app/submission/solve.py --input <problem.json> --output <result.h5>
```

共享工具与题目声明的依赖已安装。可用 `caeoj.sdk` 的 `load_problem`、
`read_constant`、`read_field`、`write_result` 读写数据，用法见 CONTRACT.md。

所需辅助 Python 文件也放在 `/app/submission/`；
提交后在独立环境中判题，只传递该目录，不保留开发环境的其他修改。
逐例运行时间上限 ${timeout_seconds} 秒，输出按题面公开的评分规则判分。

结构校验命令示例：

```bash
python -m caeoj validate-input /app/${task_path}/samples/${sample}/input/problem.json
python /app/submission/solve.py --input /app/${task_path}/samples/${sample}/input/problem.json --output /app/sample-result.h5
python -m caeoj validate-output --input /app/${task_path}/samples/${sample}/input/problem.json --output /app/sample-result.h5
```

${sample_materials}
校验器仅检查数据协议；数值正确性由独立判分器检查。
