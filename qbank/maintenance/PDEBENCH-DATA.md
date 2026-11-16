# 获取已发布的 PDEBench 算例

题目的 `data-manifest.json` 保存正式 case 与 example 选择，字段和存储规则见[数据池操作](DATA-SYNC.md)。固定的 HF 提交及发布状态见[本批发布记录](../design/reviews/pdebench-hf-release-20261020/summary.json)；HF PR 合并前应显式指定该提交，不能使用尚未包含本批数据的 `main`。

## 获取与装配

安装维护工具，然后按题获取。将命令中的 `<固定HF提交>` 替换为发布记录中的 `final_commit`：

```sh
python -m pip install -e '.[maint]'
python -m caeoj_tools.cli data assemble --task advection-1d --revision <固定HF提交>
python -m caeoj_tools.cli data verify --task advection-1d --strict
python src/utils/publish_dist.py --task advection-1d
python src/utils/prepare_harbor.py --task advection-1d
```

只取公开样例：

```sh
python -m caeoj_tools.cli data assemble --task advection-1d --revision <固定HF提交> --cases --samples 01 02
python -m caeoj_tools.cli data verify --task advection-1d --strict --samples-only
```

`--task` 可替换为具有该清单的其他题目。获取时核对描述、大小和SHA256，装配及消费校验仍按通用工具执行。完整参考与样例的数学要求以题面和DATA为准；这些检查不认证上游数值精度。

## 来源维护

新增或重制来源仍使用[PDEBench按需工具](../../src/utils/PDEBench/README.md)。先在隔离workspace准备与验收，再按统一数据池流程制池、上传和显式重选；不要将直接来源安装回执与HF清单混用，也不要刷新旧证书来掩盖题面或载荷变化。实际输入、参考和样例不进Git，Git保存题面、工具、正式清单及作者证据。
