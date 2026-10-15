# 归档题目

以下旧题目已从当前 `tasks/` 题库移入此目录，保留题面、数据、标答和出题工具：

- [1D_Advection_Sols_beta0.4](1D_Advection_Sols_beta0.4/README.md)
- [navier-stokes-steady](navier-stokes-steady/README.md)
- [navier-stokes-transient](navier-stokes-transient/README.md)

题目 ID 与数据契约保持不变。当前发布及 Harbor 组装入口只接受 `tasks/` 中的题目，归档题目不在其范围内。历史评测结果仍保留在 [AGENT-RESULTS.md](../docs/AGENT-RESULTS.md)。

在项目根目录准备上述三题数据后，可单独运行归档回归测试：

```sh
python -m unittest discover -s legacy/tests -v
```

两道 NS 题共用出题工具，测试依赖两题数据。公开材料测试将归档题临时复制到隔离目录中验证打包，不恢复当前题库中的入口。
