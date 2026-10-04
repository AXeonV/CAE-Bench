# 实现求解程序

阅读 `/app/tasks/${task}/instruction.md`、该目录中的 `DATA.md`（若有）和 `/app/docs/CONTRACT.md`。
实现题面范围内的通用求解程序，提交入口为 `/app/submission/solve.py`：

```text
python /app/submission/solve.py --input <problem.json> --output <result.npz>
```

共享工具与题目声明的依赖已安装。所需辅助 Python 文件也放在 `/app/submission/`；
最终判题在干净、无网络的环境中运行，只传递该目录，不保留开发环境的其他修改。
逐例运行时间上限 ${timeout_seconds} 秒，输出按题面规定的误差阈值判分。

请在实现与调试时使用以下结构校验命令，根据 JSON 诊断修正输入输出理解：

```bash
python -m caeoj validate-input /app/tasks/${task}/samples/${sample}/input/problem.json
python /app/submission/solve.py --input /app/tasks/${task}/samples/${sample}/input/problem.json --output /app/sample-result.npz
python -m caeoj validate-output --input /app/tasks/${task}/samples/${sample}/input/problem.json --output /app/sample-result.npz
```

校验器仅检查数据协议；数值正确性由独立判分器检查。
公开示例的完整正确输出位于 `/app/tasks/${task}/samples/${sample}/output/result.npz`。
