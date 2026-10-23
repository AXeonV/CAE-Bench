# 修复求解器

阅读 `/app/qbank/19-solver-repair/19.6-waves/complex-helmholtz-fmm-repair/instruction.md`、该目录的 DATA.md 和 `/app/docs/CONTRACT.md`。按题面修复指定源码并提交到 `/app/submission/`。仅此目录传入独立 verifier；最终提交只包含题面列出的源码替换文件。不提交 solve.py。编译和调用由可信后端执行。

公开样例材料：

- 样例 `01`：`/app/qbank/19-solver-repair/19.6-waves/complex-helmholtz-fmm-repair/samples/01/`。
  - 输入：`/app/qbank/19-solver-repair/19.6-waves/complex-helmholtz-fmm-repair/samples/01/input/problem.json`。
  - 参考与判分材料：`/app/qbank/19-solver-repair/19.6-waves/complex-helmholtz-fmm-repair/samples/01/reference/grading.json`、`/app/qbank/19-solver-repair/19.6-waves/complex-helmholtz-fmm-repair/samples/01/reference/reference.h5`。
- 样例 `02`：`/app/qbank/19-solver-repair/19.6-waves/complex-helmholtz-fmm-repair/samples/02/`。
  - 输入：`/app/qbank/19-solver-repair/19.6-waves/complex-helmholtz-fmm-repair/samples/02/input/problem.json`。
  - 参考与判分材料：`/app/qbank/19-solver-repair/19.6-waves/complex-helmholtz-fmm-repair/samples/02/reference/grading.json`、`/app/qbank/19-solver-repair/19.6-waves/complex-helmholtz-fmm-repair/samples/02/reference/reference.h5`。
公开样例判分：python -m caeoj grade --input /app/qbank/19-solver-repair/19.6-waves/complex-helmholtz-fmm-repair/samples/01/input/problem.json --output /app/sample-result.h5 --grading /app/qbank/19-solver-repair/19.6-waves/complex-helmholtz-fmm-repair/samples/01/reference/grading.json
本次环境 CPU 配额：4 核。
可用内存：4096 MB。
