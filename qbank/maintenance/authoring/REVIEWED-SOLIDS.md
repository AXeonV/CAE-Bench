# 导入已审阅的固体参考批次

此入口只迁移已审阅的数据并验证当前工具链，不生产数值参考。来源要求见[算例制作与溯源](../CASE-SOURCING.md)，池格式及远端操作见[数据池操作](../DATA-SYNC.md)。本批证据和未完成项见[审阅记录](../../design/reviews/solid8-reference-validation-2026-11-17.md)。

## 准备与导入

使用当前仓库的维护环境。输入为完整的、已冻结的 Solid26 作者工作区，至少包含 `task-manifest.json`、`reports/solid26/acceptance.json`、其中绑定的全部输入／参考、物理核验报告和基线输出。普通公开答题包不能代替该作者输入。

在仓库根目录运行，替换源路径，输出选择一个尚不存在的忽略目录：

```sh
python -m pip install -e '.[maint]'
PYTHONPATH=src:qbank/extensions python qbank/maintenance/authoring/import_reviewed_solids.py \
  --source /path/to/reviewed-solid-core-8 \
  --output work/solid8-reviewed \
  --task-id-start 83 \
  --write-author-records
```

编号起点是本批本地拟分配值。工具检查当前代码树的已登记身份；发布前仍须复核远端并发分配。已有题目清单时沿用其身份和仓库定位。未登记时，`--repo-id` 仅设置未来池的目标位置，不执行上传。

工具依次执行：

1. 核对已通过的批次清单、全部声明资产 SHA-256 和原题五份契约／执行配置。
2. 将输入平铺为 `cases/<编号>/`，参考平铺为 `reference/<编号>/`；公开算例同时作为 `samples/001/input/`。不改输入、网格、参考或评分文件字节。原参考来源记录和物理报告放在 `prepared/<题目>/author/data-evidence/`，不混入可上传载荷。
3. 调用现有池 API 制池，利用 `LocalStore` 在 `assembled-project/` 的隔离代码副本装配并严格核验。每题公开样例复用对应计分 case 的身份。
4. 用当前 grader 重评冻结的基线输出，保存逐例完整评分报告；生成公开 ZIP 并检查白名单和样例输入字节，再准备 Harbor 任务。
5. 写入 `IMPORT_RECEIPT.json`。指定 `--write-author-records` 时，成功后才更新八个题目 `author/data-evidence/solid8-2026-11-17.json`。

目标目录存在、源摘要不符、正式清单意外变化、评分或打包失败时停止。不要通过更改旧回执、放宽容差或覆盖冻结输入绕过失败；保留失败目录，修复后使用新输出目录。

## 查看交付

相对于 `--output`：

| 路径 | 用途 |
|---|---|
| `IMPORT_RECEIPT.json` | 批次计数、来源绑定、每例身份、评分报告摘要和公开包摘要 |
| `prepared/<题目>/` | 制池前的标准目录及作者证据 |
| `pools/<题目>/repository/` | 官方工具产生的可上传载荷 |
| `pools/<题目>/selection.json` | 本批隔离验证选择，尚非正式选样 |
| `grading/<题目>/<编号>.json` | 当前 grader 的实际逐项报告及评价代码／依赖绑定 |
| `assembled-project/qbank/.../<题目>/` | 已装配、可离线消费的任务副本 |
| `assembled-project/dist/` | 仅公开材料的答题 ZIP |
| `assembled-project/runs/harbor/tasks/` | 已准备的 Harbor 任务；准备不等于运行 |

只有公开输入和完整参考／判分资产作为样例公开；没有声明完整提交示例，因此不制造 `samples/001/output/result.h5`。原作者工作区的旧格式示例不作为正确答案发布。

## 后续发布与选样

本工具不访问 GitHub／HF，不覆盖主代码树的 `data-manifest.json`，不启动求解器、agent 或模型 benchmark。重评缓存不能证明当前候选程序在资源限制内完成求解。

正式发布前核对实际参考生产者与来源资格、数据再分发条件及稳定任务编号，按数据池操作上传已审核 bundle，保存真实 HF 提交，再从该提交重新装配核验。之后另行审核正式 cases／samples 选择；不将本地 `local` 回执冒充远端版本。上传、正式选样和模型评测各自记录，不能因本地核验通过而写作已完成。
