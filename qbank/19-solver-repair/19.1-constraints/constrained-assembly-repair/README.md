# 双边距离约束系统的加速度与反力求值

这是指定源码修复题：考生修改真实 Chrono 的装配实现，提交一个 C++ 源文件。公开要求由 [instruction.md](instruction.md)、[DATA.md](DATA.md) 和通用 CONTRACT 定义。

制作与复现流程见 [author/README.md](author/README.md)。源代码下载/打包配方、数据及参考生产工具保存在 author；公开源码归档和数字载荷不提交 Git。上游 BSD 许可随源码归档保留，代码来源和实际生产者见 [provenance.json](author/data-evidence/provenance.json)。

正式数据通过本题 data-manifest.json 选择。按[数据池操作](../../../maintenance/DATA-SYNC.md)获取时，使用 `author/data-evidence/hf-upload.json` 记录的固定提交或本任务的 HF 分支；具体发布/重取状态以该记录为准。不要从 HF main 假设本题已合并。

题目运行装配：

```text
python -m caeoj_tools.cli data assemble --task constrained-assembly-repair --revision <已记录的固定HF提交>
python -m caeoj_tools.cli data verify --task constrained-assembly-repair --strict
python src/utils/publish_dist.py --task constrained-assembly-repair
python src/utils/prepare_harbor.py --task constrained-assembly-repair
```

发布前须按 author 流程制作本地源码资产及构建缺陷核心镜像，再进行公开包独立运行和 verifier 验证。评测接收源码替换件；通用 solve.py 提交规则不适用于本题。

实施、独立审阅及实际评测状态见[维护记录](../../../design/reviews/chrono-846-repair-implementation.md)。运行日志、冻结计划和逐例报告保存在 runs，不把 Oracle 或结构校验说成 Luna 成绩。
