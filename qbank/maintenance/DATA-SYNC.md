# 数据获取与维护

HF 采用题内数据池；本地 `cases/`、`reference/`、`samples/` 由选样装配产生。格式职责见[存储设计](../design/DATA-STORAGE.md)，已迁移范围与核验见[迁移记录](../design/reviews/data-storage-migration.md)。现有逐题清单采用 `schema_version: 2`；远端旧镜像路径已移除。

## 定位并获取

clone 代码后先读取本题 `data-manifest.json`，核对 `task_id`、`repository` 和所需的 `cases` 或 `samples` 选择。HF `pool.index` 用于浏览和筛选；已经明确选择的条目可直接按其 `item.path` 获取，不要求先下载整个池。

安装官方客户端：

```sh
python -m pip install huggingface_hub
```

先将本次远端分支解析为一个提交，所有后续请求使用同一个 `--revision`，避免跨更新读取。例如将所选条目描述下载到独立暂存目录：

```sh
hf download jimzhouzzy2006/CAE-Bench-OJ 'qbank/<章>/<节>/<题>/pool/items/<case-id>/item.json' --repo-type dataset --revision '<commit>' --local-dir runs/hf-pool
```

`item.path` 相对 `repository.path`，实际远端文件路径由两者拼接。核对描述文件 SHA-256 与选样中的 `item.sha256` 一致后，再按描述的 `input.files`、`reference.files`、所选附件和 `shared_dependencies` 获取实际文件。普通 case 默认获取输入和参考；只取样例时也取得其完整输入输出及依赖。参考待补可供开发取得已有输入，但不能报告完整成功。

当前没有通用下载装配 CLI。官方客户端不会识别本项目选样、摘要或覆盖规则，也不会自动组装；不要直接把池目录下载到本地数据目录后宣称已经可用。

## 按清单装配

先检查条目内实际文件的字节大小和 SHA-256，再在暂存区按下列映射形成目录。条目 `files` 路径均相对 `item.json` 所在目录。

| 选样角色 | 来源 | 本地目标（相对题目目录） |
|---|---|---|
| `cases.<编号>` 输入 | 条目 `input.files`，去掉 `input/` 前缀 | `cases/<编号>/` |
| `cases.<编号>` 参考 | 条目 `reference.files`，去掉 `reference/` 前缀 | `reference/<编号>/` |
| `samples.<编号>` 输入 | 条目 `input.files`，去掉 `input/` 前缀 | `samples/<编号>/input/` |
| `samples.<编号>` 输出 | 首批条目的 `reference/reference.h5` | `samples/<编号>/output/result.h5` |
| 样例指定附件 | 选择的 `attachments` 键为条目内来源路径，值为样例内目标 | `samples/<编号>/<目标>` |

样例不自动携带参考目录中的作者解析记录。题目级 `auxiliary` 绑定的描述维护额外附件映射：每个 `files` 键是本地题目相对目标，其 `source` 是远端题目相对来源，同时记录大小和摘要。某些附件可引用已有条目文件，避免重复存储。这些维护附件不自动进入考生包。

首批没有共享依赖；未来引入后需取依赖闭包并按协议处理引用，不复制全池。先核验装配结果，SHA 相同跳过，SHA 不同提示，显式更新才覆盖。旧选样残留不能进入发布或评分；不静默删除用户修改或未被管理的文件。装配回执保留来源、选样、映射和实际文件摘要。

## 校验与使用

PowerShell 可用 `Get-FileHash -Algorithm SHA256 -LiteralPath '<file>'` 查看摘要。本地开发不一致时 warning；正式 benchmark 必须核验条目绑定、实际输入、参考与依赖闭包，不符即停止。发布器和 Harbor 装配器尚未自动消费池清单，当前需维护方前置核验并保存证据。

还需核对样例与测试的来源身份和输入重叠。首批迁移为保持原材料一致，保留了原有重叠；不能因迁移与摘要校验通过就宣称新的不重叠评测已就绪。文件完整性不替代契约、数值精度或资源验证。

通过后按题目 README 做本地检查与发布。全池公开不改变考生包白名单；池索引、条目描述、整题选择和非样例参考不进入考生环境。

## 制作与更新

生成器仍在原位置产生本地数据，目录被 Git 忽略；生成不等于发布。审核新数据后制作池条目、上传并核验，再更新选样绑定；无需为样例重复上传条目。首批使用一次性迁移脚本，尚无通用上传、清单刷新或远端恢复工具，PDEBench 也未全轨迹入池。

池条目更新不会自动刷新已有选择的预期摘要；先检查差异再显式更新。迁移保留本地副本，不改写 Git 历史。改名时同步迁移两边题目路径和清单定位，保持 `task_id`。
