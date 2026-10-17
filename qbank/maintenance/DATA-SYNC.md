# 数据池操作

布局与字段的唯一说明见[存储设计](../design/DATA-STORAGE.md)。维护 CLI 为 `python -m caeoj_tools.cli data`（安装后等价 `caeoj-maint data`），支持 `pack/upload/select/fetch/assemble/verify`，不进行物理求解、判据修订或精度认证。

## 环境与制池

```sh
python -m pip install -e '.[maint]'
python -m caeoj_tools.cli data --help
python -m caeoj_tools.cli data pack --task heat-conduction-steady-2d --output work/heat-pool
```

`--task` 是唯一题目目录名。已有版本 4 清单时沿用身份和仓库定位；新题必须显式 `--task-id caeoj-000123`，工具检查编号不重复。可用 `--source` 读取独立生成目录，用 `--repo-id` 为新题指定仓库。输出必须为空。

bundle 的 `repository/` 包含索引、case 描述、输入及reference/grading.json绑定的全部判题资产。相同输入的样例复用 case；不同 case 的网格不共享。`evidence/` 单独收集非消费参考记录和样例验证材料，不会上传。已有来源证书核对输入绑定并在描述中保留必要身份，完整记录仍是作者材料。

生成器应把解析、catalog、验证报告直接写到 `author/data-evidence/`。审核 bundle/evidence 后将应维护的 JSON 证据归到该目录；数字中间件留忽略的工作空间，不为追求原目录还原而再次引入附件机制。制池不修改正式选样，不自动重新求参考，也不将材料齐备宣称为数值通过。

## 上传

```sh
python -m caeoj_tools.cli data upload --bundle work/heat-pool
```

使用既有 HF 登录（`hf auth login` 或环境令牌），不要将凭据写进代码和日志。上传验证全部索引条目与载荷，拒绝上传树中未声明文件；evidence 位于上传树之外。相同文件按远端摘要/Blob ID 跳过，不下载大文件来比较。索引合并保留其他 case，固定父提交原子发布；并发修改失败时先核对再重试。

远端内容不同时默认停止，审核后加 `--update`。`--revision` 默认 `main`，可指定已有分支，工具不自动创建仓库/分支或删除未选 case。完成后固定新提交重新核验，失败记录提交 ID，不能假设远端未改变。

旧版池必须先明确迁移；工具不合并旧版索引。上传不自动刷新代码选择中的描述摘要，需显式重选或采用审核后的 staged `selection.json`。

## 选样

浏览 `pool/index.json` 找到 ID 后：

```sh
python -m caeoj_tools.cli data select --task heat-conduction-steady-2d --case '001=<测试case-id>' --sample '01=<样例case-id>' --output work/heat-selection.json
```

参数可重复，格式为 `[本地编号=]case-id`；省略编号则依次为 001、002 等。命令生成完整选择集合，未列的角色/条目不保留。默认写回本题清单，建议先用 `--output` 审核，再保存为题目 `data-manifest.json`。

选择绑定 case 描述摘要，检查输入/参考完整性及输入/来源轨迹重复。仅开发用途可加 `--allow-incomplete`，正式消费仍阻断缺失参考。选样不下载数值载荷，不支持附件或跨case依赖声明。

## 下载与装配

```sh
python -m caeoj_tools.cli data fetch --task heat-conduction-steady-2d
python -m caeoj_tools.cli data assemble --task heat-conduction-steady-2d
```

`fetch` 下载并核验缓存；`assemble` 进一步装配原目录。每次固定一个远端提交，`--revision` 可指定分支/提交，`--cache-dir` 指定官方缓存。离线使用 `--source-dir <repository形状目录>`，其下包含清单中的 `qbank/.../pool/`。

只取样例：

```sh
python -m caeoj_tools.cli data assemble --task heat-conduction-steady-2d --cases --samples 01
```

`--cases`/`--samples` 不传表示该角色全部选择；出现但不带名字表示不取该角色。每个 case 默认取得输入和对应参考，不下载作者证据。参考待补时结果 `complete: false` 并列出缺失，不能报告完整成功。

case 输入原字节复制到本地 `cases/<编号>/` 或样例 `input/`；参考组装配到测试 reference/<编号>/ 或样例 samples/<编号>/reference/。仅声明了完整提交示例的case另装配样例output/result.h5；稀疏参考不作此映射。所有资产已经在输入目录内，不需要路径改写或跨目录读取。

相同文件跳过，差异先停止，显式 `--update` 才覆盖。装配先暂存、预检后写入，失败回滚，回执最后更新。改变范围/选样需清理旧已管理文件时也要 `--update`；被用户改过的旧文件和未知文件不静默删除。不要并发装配同题；异常进程留下锁时先检查 PID，再处理自己的遗留锁。

本地 `.data-assembly.json` 回执由 Git 忽略。不要编辑回执伪造通过；校验从其保留的 SHA 绑定原始描述推导预期数据。清理或更换已装配数据前，先归档需要保留的作者材料。

## 核验与消费

```sh
python -m caeoj_tools.cli data verify --task heat-conduction-steady-2d
python -m caeoj_tools.cli data verify --task heat-conduction-steady-2d --strict
```

开发不一致 warning、报告 `valid: false`、退出码 1；严格失败退出码 2。`--strict` 检查缺失、摘要、残留入口、不完整参考和重复输入/来源轨迹。`--samples-only` 只核验样例，无需测试材料。

发布器离线严格核验样例，Harbor 准备离线严格核验全套选样，不自动下载或重选。同一池条目同时选为测试与样例时允许“送分样例”，装配及核验报告的 public_cases 列出对应关系；Harbor 的 selection.json 和成绩报告保留该身份，仍参与原总数和计分。此例外要求 case ID 与描述绑定完全一致，不放行角色内部重复或不同条目的输入／轨迹重叠。通过后按题目 README 做 SDK、数值与公开包独立运行核验；文件一致性不证明参考精度或资源校准。

代码提交保存工具、题意、选择和应维护的作者证据；不提交缓存、bundle、装配数据或凭据。HF 只维护最新数据，历史来源和阶段证据另见维护记录。

## 无本地数据的代码树

HF 是题目输入与参考的存储位置；本地 `cases/`、`reference/`、`samples/` 和回执仅在需要消费时装配，不要求常驻。仅有 problem.json 而缺少资产的题库骨架不保留、不上传 HF。PDEBench 冻结来源选择和历史放在本题 `author/data-evidence/reference/`，它们是制作配方，不表示数据就绪。

清理前先固定 HF 提交并核对已上传载荷的大小与 SHA-256；删除本地数据时一并清除装配回执、暂存 bundle、下载缓存与包含数据的发布包。维护证据保留在 author 中。再次使用已有数据按上文 assemble 拉取；尚未制备上传的题目先走制作与发布流程。

每例判题配置与参考同属HF数据。pack、fetch及verify通过可信评价器检查参考覆盖，不仅检查文件存在；制数时由作者模板显式生成配置。完整性不包含参考精度认证。
