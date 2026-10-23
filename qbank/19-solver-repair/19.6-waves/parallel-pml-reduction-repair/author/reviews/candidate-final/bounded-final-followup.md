# 最终公开材料有界复核

结论：原 REPORT.md 的 P1 输出支持数组冲突与 P2 包根命令路径问题均已关闭；本轮最终题面结论为 **本轮未发现未决问题**。原报告保留为旧版本证据。本次只复核已报告问题及公开包版本差异，不授予 native 执行、参考精度或资源预算验收。

## 材料与变化边界

- 旧公开 ZIP：`runs/harbor/tasks/parallel-pml-reduction-repair-frozen-v2/tests/agent.zip`，自核完整 SHA256 为 `53ab80e1e927c46b20bc2c12cb161e1b48cac988ec20b8cbb4e6ba25febecaeb`；只读 ZIP 内公开条目，未读取同目录其他材料。
- 最终公开 ZIP：`dist/parallel-pml-reduction-repair-agent.zip`，自核完整 SHA256 为 `9cd9a7479aaa7973194bfd5099e97fbc60f40c8133cddcce8b2e7552f54c3f39`。
- 全部解压逻辑条目逐字节对比：两包均44项，无增加、无删除，只有 `MANIFEST.json`、本题 `instruction.md`、`DATA.md` 三项变化。其余41项完全相同，含 CONTRACT、全部SDK/CLI与扩展、源码压缩包、公开运行工具和两样例输入/网格/参考/输出/评分；因此旧版完整样例读取及中性验证结论可复用，无公开数值或运行接口暗变。
- 最终三文件及公开资产与工作树对应文件 SHA 一致；public-materials.json 内全部白名单SHA校验通过。MANIFEST记录的每个文件SHA正确，覆盖全部43个非MANIFEST条目。
- 最终 `DATA.md` SHA256：`a457364c9332e1c2b75f8441fca2368a0fe05292e62e36577d33063c32c36cd2`；`instruction.md`：`459a6fa812bab350bb4e5b7bd4db4016d55879b7d5eb369b11be9bdf845c0bcc`；CONTRACT：`130d4416fd533812493780c8bc6afbc0a158de6800b59bbec14a852f3cf1c063`。全部44条目完整SHA、白名单SHA、两文件精确diff及工作树一致性见 `final-materials.json`。

## 逐项关闭

1. DATA「输出」现在只要求复制 `times`、`probe_ids`，并明确“不重复点坐标”。与CONTRACT §9、固定write_result接口、两公开reference/output的三dataset结构一致，P1关闭。
2. instruction安装说明现在明确在考试包根目录 `python -m pip install .` 后，执行 `cd qbank/19-solver-repair/19.6-waves/parallel-pml-reduction-repair/`，再执行 `public/run_case.py` 和 `samples/01/...`。所述cd目录及全部后续相对文件路径在ZIP内存在，P2关闭。

## 未执行项目

未运行真实Fortran/MPI构建、健康例、候选修复、原生solver或Linux性能测量；未执行完整离线pip安装。未读取author/隐藏cases/私有参考/求解实现。没有更改题目，也没有重审未发生变化的MOOSE材料。本次关闭只解决公开定义与公开包路径可用性，不证明native与资源要求已通过。
