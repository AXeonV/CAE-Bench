# 算例来源与参考

本目录记录当前算例的来源和参考证据，不定义题目方程，也不进入 Agent 公开包。当前数据来源为 PDEBench / DaRUS V8，许可 CC BY 4.0；题目本身按数学问题命名，后续可加入满足同一契约的其他来源。

- [DESIGN.md](DESIGN.md)：数据集版本、来源许可、配置对应、转换差异及参考局限。
- [selection.json](selection.json)：逐例 `kind`、`id`、`source_id`、源样本 `index`、分组与格式变体；`source_files` 给出源文件 ID、文件名、URL 和 MD5。`kind=case` 对应 `../cases/<id>/`，`kind=sample` 对应 `../samples/<id>/`。
- [SAMPLES.md](SAMPLES.md)：当前公开样例的选择与参考规划。
- [TEST-CASES.md](TEST-CASES.md)：当前隐藏测试的分组与覆盖。
- `history/`：旧冻结清单，保留当时的题目 ID 与契约哈希供追溯。
- `<id>/certificate.json`：隐藏参考绑定的输入哈希、参考方法及误差证据（准备后生成）。
- `sample-certificates/<id>/`：公开样例的私有参考与审核证据（准备后生成）。

数值数组和网格需重新准备；旧题目 ID 下的参考证书不能当作新输入字节的有效证明。原始转换对照与可判分参考分别保存；具体物理、数值与误差限制见 DESIGN.md 及逐例证书。
