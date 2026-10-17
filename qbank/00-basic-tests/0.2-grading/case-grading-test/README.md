# Case 判题测试维护

[题面](instruction.md)与 [DATA](DATA.md)是考生契约。本题验证 case 级整场／稀疏观测评价及完整输出边界，区别于 0.1 的通用格式覆盖。它没有物理求解或参考精度的外部来源主张。

数据由 HF 管理，见 `data-manifest.json`；[数据池工具](../../../maintenance/DATA-SYNC.md)负责上传、选样和装配。生成器只显式写入指定空目录：

```sh
python qbank/00-basic-tests/0.2-grading/case-grading-test/author/generate.py --output work/case-grading-source
```

作者数值模板在 [author/grading-template.json](author/grading-template.json)，实际计划在各 case 的 reference/grading.json；运行器不读取作者模板。初始数据包含 6 个测试 case 与 2 个互不重叠的样例，覆盖整场、x／y／xy 测点、双项 AND 及整场与测点组合。观察点覆盖内部、共边和边界，多时刻且 tag、行顺序非平凡。

完整提交参考程序为 `author/baseline.py`。执行限制由 `judge-config.json` 与 `harbor/task.toml` 管理。制作依据、逐例验证及审阅证据见[实施记录](../../../design/reviews/chapter-00-case-grading.md)。实际 Linux 容器与 Agent benchmark 尚未执行。
