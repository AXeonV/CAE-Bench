# 80 例交付与重放

本批80例的 case ID、描述摘要、设计目的、预期难度与输出范围由 [catalog.json](catalog.json) 唯一记录；覆盖计数见 [coverage.json](coverage.json)，实际验收与局限见 [validation-summary.json](validation-summary.json)。原20例保持原身份，本批合入的独立池共有100例，正式 cases／samples 仍为空。

| 内容 | 独立 HF 分支 | 固定提交 |
|---|---|---|
| 100例 case 池 | `cases/2-1-1-extra80` | `a9d60bdfe9e9e810b5627960aefce2adfbe53bae` |
| 第二批维护证据 | `evidence/2-1-1-extra80-validation` | `8f79039f4800673812cfb9b863bb651e6f42075b` |

[HF PR #1](https://huggingface.co/datasets/jimzhouzzy2006/CAE-Bench-OJ/discussions/1) 已追加本批，固定审阅提交为 `a5ad1c4b2eaf7fd03f29538255cf7a9536fdc317`；保留第一批维护证据。代码审阅为 [GitHub PR #24](https://github.com/AXeonV/CAE-Bench-OJ/pull/24)。两边保持未合并，HF main 仍为 `d46b17a03d444646157e1e2fe4b4f00587dc5d89`。

## 固定版本下载、摘要校验与装配

在包含当前维护脚本的仓库根目录执行；维护环境安装见[数据池操作](../../../../../../maintenance/DATA-SYNC.md)。使用当前 Git 的下载／重放工具，归档中的 recipe-binding.json 和源码快照记录实际生产版本，不替换当前工具。后续缓存链接兼容和按 case ID 查找装配结果的修复均不改变冻结数值资产。

```sh
AUTHOR=qbank/02-fluid-mechanics/2.1-single-phase-flow/newtonian-incompressible-steady-2d/author
INDEX="$AUTHOR/data-evidence/supplement80-20261018/archive-index.json"
EVIDENCE=work/211-extra80-evidence
export PYTHONPATH=src:qbank/extensions
python "$AUTHOR/evidence_archive.py" fetch --index "$INDEX" --destination "$EVIDENCE" --cache-dir work/211-extra80-evidence-cache --include-raw
python "$AUTHOR/evidence_archive.py" verify --index "$INDEX" --destination "$EVIDENCE"
python "$AUTHOR/verify80.py" "$EVIDENCE/staged-selection100.json" work/211-replay100 work/211-replay100.json --expected-cases 100 --revision a9d60bdfe9e9e810b5627960aefce2adfbe53bae --cache work/211-extra80-case-cache
python "$AUTHOR/grade80.py" work/211-replay100 "$EVIDENCE" work/211-independent-replay.json
python "$AUTHOR/evidence_archive.py" verify --index "$INDEX" --destination "$EVIDENCE"
```

索引强制完整 HF 提交 ID，校验发布清单、归档、逐文件 inventory 的大小／SHA-256，再核对装配成员；官方 HF 缓存链接可在摘要验证后读取，装配目录中的链接仍拒绝。已有修改／未知文件不覆盖。`--include-raw` 下载并核验三份原始档案，保持不解包；仅重放采样与判分可省略它。改变 raw 选择时使用新目标目录。

上述流程已从独立缓存实际执行：100例、1个原标准方腔公开样例的严格装配与100个参考正例通过；取回的26档独立完整输出通过契约检查，8个最细档通过原判分；重放后冻结证据仍完整一致。后验回执见 [replay-validation.json](replay-validation.json)。本次未运行模型 benchmark。

PowerShell 使用 `$env:PYTHONPATH='src;qbank/extensions'`，将 AUTHOR／INDEX／EVIDENCE 设置为普通 PowerShell 变量，使用已安装维护依赖的 Python；其余参数相同。需要仅重放新增80例时，将选择改为 staged-selection80.json，并省略 --expected-cases 100。

## 以后指定这些 case 进行 benchmark 的选样

以下命令仅生成临时选择文件，不覆盖正式清单，也不启动模型：

```powershell
& ./qbank/02-fluid-mechanics/2.1-single-phase-flow/newtonian-incompressible-steady-2d/author/data-evidence/supplement80-20261018/select-extra80.ps1
& ./qbank/02-fluid-mechanics/2.1-single-phase-flow/newtonian-incompressible-steady-2d/author/data-evidence/supplement80-20261018/select-all100.ps1
```

前者明确选择本批80例（本地编号021至100），不选择样例；后者选择全部100例，并沿用原010标准方腔作为同时计分的公开样例。输出分别为 work/211-extra80-selection.json 和 work/211-all100-selection.json。两条命令均已实际验证。Python 不在本工作树 .venv 时，可传 `-Python <维护环境Python路径>`。

正式 benchmark 应再按运行技能审查并采用相应临时选择、严格核验和冻结；本交付不改变当前正式测试或样例角色。
