# 2.1.1 算例维护材料

- [初次制池与来源记录](data-evidence/supplement-20261017/README.md)：工况来源、Lethe 参考生产者、Ghia 中线比较、数值和资源验收、全部输入及判分链审计。
- [交付与选样入口](data-evidence/supplement-20261017/delivery.md)：固定 HF 分支及提交、20 个 case ID、逐例描述和显式指定 revision 的选样命令。
- [OpenFOAM 独立交叉验证](data-evidence/independent-openfoam-20261017/report.md)：其余 19 例的逐例差异、三档网格结果、判分链验证及局限；转换方法和复现命令见同目录 README。

正式数据清单只登记池位置，cases／samples 保持空。数据取得、装配与上传复用[数据池操作](../../../../maintenance/DATA-SYNC.md)；直接使用已交付的固定提交即可核验，不需重新运行历史建分支脚本。

Git 保留配方、说明、逐例结论和轻量索引；逐档配置／日志、详细审计、逐点差值、完整独立输出和原始场归档放在 HF 的独立维护目录，均不进入 case 池或考生公开包。原证据树按字节归档，历史报告、生产配方和全部摘要对应 [archive-index.json](data-evidence/archive-index.json) 的 source_git_commit；后续脚本只增加了指定验证报告输出位置的接口，不改变原数值计算。

## 固定版本获取与核验

以下命令在仓库根目录执行；安装维护依赖见[数据池操作](../../../../maintenance/DATA-SYNC.md)。源码维护环境同时加载当前 SDK 和仓库的显式扩展目录，使用 POSIX shell 时设置：

```sh
AUTHOR=qbank/02-fluid-mechanics/2.1-single-phase-flow/newtonian-incompressible-steady-2d/author
export PYTHONPATH=src:qbank/extensions
python "$AUTHOR/evidence_archive.py" fetch --destination work/211-evidence --cache-dir work/211-evidence-cache --include-raw
python "$AUTHOR/evidence_archive.py" verify --destination work/211-evidence
```

下载器读取 Git 中的 archive-index.json，强制使用完整 HF 提交 ID。它复用 HubStore 获取文件，先核对发布清单、归档及 inventory 的大小和 SHA-256，再逐成员核对并装配 729 个原证据文件；拒绝路径越界、链接、重复／缺失文件及摘要不符。已有目标目录必须完全匹配回执，修改或未知文件不会被覆盖或删除。

PowerShell 中使用 `$env:PYTHONPATH='src;qbank/extensions'`，并将 AUTHOR 作为普通 PowerShell 路径变量设置；其余 Python 参数相同。

`--include-raw` 额外下载四份原始档案到目标的 raw/，只校验并保留，不自动解包。如仅复核采样结果，可省略此选项，约需 1.45 MB 的结构化包。改变是否包含 raw 时使用新目标目录。完整独立输出位于 `work/211-evidence/independent-openfoam-20261017/runs/`；原 Lethe 配置和日志位于 `work/211-evidence/supplement-20261017/evidence/runs/`。本地回执与 inventory 以 `.evidence-` 开头。

## 真实消费链重放

使用取回的冻结选样清单，从固定 case 提交装配到新的隔离目录；不写回本题正式清单：

```sh
python "$AUTHOR/verify_pool_supplement.py" work/211-evidence/supplement-20261017/staged-selection.json work/211-case-check work/211-replay/pool.json --revision fbe115effe8131bd575c0cde1c9ca87a9d87fd3a --cache work/211-case-cache
python "$AUTHOR/assess_openfoam.py" work/211-case-check work/211-evidence/independent-openfoam-20261017 --grade --validation-output work/211-replay/openfoam
python "$AUTHOR/audit_openfoam.py" work/211-case-check work/211-evidence/independent-openfoam-20261017 qbank/02-fluid-mechanics/2.1-single-phase-flow/newtonian-incompressible-steady-2d --output work/211-replay/openfoam/interface-audit.json
python "$AUTHOR/evidence_archive.py" verify --destination work/211-evidence
```

第一步实际检查全部 20 例及判分正反例，后两步检查 19 例的独立完整输出与全部 57 档结果。新报告写入 work/211-replay，冻结证据保持不变。证据索引与 case 提交分别固定；分支名只用于定位，不代替固定提交。

## 更新证据

先取回原证据，在新的忽略目录制作追加记录，再使用 `evidence_archive.py pack <证据根目录> <新的输出目录>` 打包并生成 inventory。作者证据不是 case 附件，不用 data pack/upload 将它塞入 input/reference 组。审核后通过 HF 官方 API 在明确的证据分支、固定父提交上提交归档；重新固定实际提交、更新轻量索引并独立下载验证，再提交 Git 改动。不要覆盖或重算历史生产记录的摘要。
