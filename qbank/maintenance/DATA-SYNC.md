# 数据池操作

布局与字段的唯一说明见[存储设计](../design/DATA-STORAGE.md)。维护 CLI 为 `python -m caeoj_tools.cli data`（安装后等价 `caeoj-maint data`），支持 `pack/upload/select/fetch/assemble/verify`，不进行物理求解、判据修订或精度认证。

## 使用已发布数据

使用者统一运行 `caeoj data`，未安装命令时运行 `python -m caeoj data`。在项目目录操作，或通过 `--root <项目目录>` 定位；不要求题库随Python安装目录分布。

```sh
caeoj data list --chapter 02
caeoj data fetch --task heat-conduction-steady-2d --dry-run
caeoj data fetch --task heat-conduction-steady-2d
caeoj data fetch --chapter 02 --kind samples
caeoj data verify --task heat-conduction-steady-2d --strict
```

`--task`（同义 `--problem`）接受稳定ID或题目slug，可重复；与 `--chapter` 互斥。`list`、`verify` 不指定范围时检查所有题目；`lock`、`fetch` 必须显式选择题目或章节，避免误下载全库。`--kind` 可重复，支持 `cases`（测试输入）、`references`（测试参考及判题配置）、`samples`（完整公开样例）和 `all`（默认）。按类别增量获取会保留其他仍匹配清单的已装配类别；单独准备输入或参考不代表整题可评测。

`list` 和 `fetch --dry-run` 完全离线且不创建缓存，报告文件数、装配大小、去重后大小与预计新增下载量。状态包括 `unregistered`（无选择）、`unlocked`（未固定元数据）、`incomplete`（所选类别待补齐）、`missing`、`partial`、`needs-assembly`（文件存在但回执不匹配）、`present`（文件摘要及回执绑定匹配）。`present` 仍需正式消费时的契约预检，不证明数值正确。未发布／未锁定内容不能当作可下载数据；章节失败逐题汇总，保留其他成功题目。

新入口的 `fetch` 一次完成下载、校验和装配；维护入口的 `fetch` 仍为作者侧只准备缓存的低层操作。二者共用同一数据池实现。获取前在stderr显示计划，最终JSON在stdout；再次执行复用通过SHA检查的本地文件或对象缓存。缓存默认 `.caeoj/cache/`，可用 `--cache-dir` 覆盖；缓存、半成品、锁和回执不进Git。正常成功退出0；非严格verify不匹配退出1；严格校验或操作失败退出2。

## 配置本地与云端来源

复制[配置示例](../../docs/data-sources.example.toml)至用户目录 `~/.config/caeoj/data.toml`，或使用 `--config <文件>`／环境变量 `CAEOJ_DATA_CONFIG`。相对本地来源路径以配置文件所在目录解析；相对缓存路径以项目根解析。没有配置时默认来源为HF。

```sh
caeoj data source list
caeoj data fetch --task heat-conduction-steady-2d --source local
caeoj data fetch --task heat-conduction-steady-2d --source scp
caeoj data fetch --task heat-conduction-steady-2d --source hf
caeoj data fetch --task heat-conduction-steady-2d --source-dir <本地发布根目录>
```

本地和SSH来源根目录下都保留 `qbank/<章>/<节>/<题>/pool/` 布局。镜像必须提供清单绑定的相同描述及载荷，不能用最新版本替换旧版。工具不在失败后静默切换来源；访问失败时检查当前配置及权限。

SSH来源使用系统OpenSSH工具、SSH配置／代理及known_hosts，批处理不交互索要密码，不关闭主机校验。先由用户配置可用的SSH身份与可信主机；可用 `ssh_config` 指定配置文件，未指定port时沿用SSH配置。默认SFTP传输使用reget恢复下载；`transport="scp"` 使用旧协议scp首次传输，保留半成品后通过ssh和服务器POSIX `dd` 从完整1MiB块恢复。为避免Windows旧scp对特殊文件名的转义差异，这类名称首次获取也用ssh块读取。旧SCP来源因此需提供可执行dd的SSH shell；不支持时会报错，不能宣称已续传。下载后始终核对全部文件摘要，失败重试默认3次，`--retries` 范围1～10。HF使用官方SDK固定提交下载及官方断点缓存。

不要在配置中写密码、私钥正文或HF令牌。HF沿用官方登录／环境令牌；主机、身份文件和跳板通过SSH配置管理。公开样例与隐藏评测参考应由存储权限分别控制，必要时分设公开／私有仓库或服务器目录；打包白名单不能替代远端权限。

本机只读 SSH 服务、三种来源的独立传输测试及 HF 私有测试仓库操作见[传输测试指南](../../docs/DATA-TRANSPORT-TESTING.md)。

## 发布并锁定元数据

作者完成下面的制池、上传和选样后，再固定远端提交及完整文件元数据：

```sh
caeoj data lock --task heat-conduction-steady-2d --source hf
caeoj data lock --task heat-conduction-steady-2d --source hf --revision <完整提交SHA>
caeoj data lock --task heat-conduction-steady-2d --source-dir <本地发布根目录>
```

只有 `lock` 允许把分支／标签解析为固定提交。它读取所选case描述而不下载数值数据，生成每题 `data-lock.json`；已有不同锁时先审核，再显式 `--update`。本地／SSH锁可按内容摘要固定版本；若还要使用HF镜像，应从相应HF提交生成锁以记录固定SHA。本机来源位置不写入锁。

Git提交保存选样清单、生成锁、代码、文档和应维护的作者证据。清单改变后重新锁定；锁改变后重新获取以更新回执。尚未制数的题目保持未登记状态，不伪造发布记录。先发布并核验实际载荷，再提交绑定；保留所有仍被代码提交引用的数据版本。完整提交步骤见[开发与Git交付](../../docs/DATA-DEVELOPMENT.md)。

寻找来源、实际求解器计算及参考验证由 [caeoj-source-cases](../../.agents/skills/caeoj-source-cases/SKILL.md) 按[算例制作与溯源](CASE-SOURCING.md)协调；本页只拥有通用数据管理操作。入池不自动改变正式选样。

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

作者侧 `fetch` 下载并核验缓存；`assemble` 进一步装配原目录。已有数据锁时默认使用锁内HF提交；没有锁的制作流程才默认解析main，正式发布仍要求先生成锁。`--revision` 显式指定来源分支/提交，但装配不能与已审核锁冲突；`--cache-dir` 指定官方缓存。离线使用 `--source-dir <repository形状目录>`，其下包含清单中的 `qbank/.../pool/`。

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

代码提交保存工具、题意、选择、数据锁和应维护的作者证据；不提交缓存、bundle、装配数据或凭据。HF与服务器保留被代码版本引用的已发布数据；历史来源和阶段证据另见维护记录。

## 无本地数据的代码树

HF 是题目输入与参考的存储位置；本地 `cases/`、`reference/`、`samples/` 和回执仅在需要消费时装配，不要求常驻。仅有 problem.json 而缺少资产的题库骨架不保留、不上传 HF。PDEBench 冻结来源选择和历史放在本题 `author/data-evidence/reference/`，它们是制作配方，不表示数据就绪。

清理前先固定 HF 提交并核对已上传载荷的大小与 SHA-256；删除本地数据时一并清除装配回执、暂存 bundle、下载缓存与包含数据的发布包。维护证据保留在 author 中。再次使用已有数据按上文 assemble 拉取；尚未制备上传的题目先走制作与发布流程。

每例判题配置与参考同属HF数据。pack、fetch及verify通过可信评价器检查参考覆盖，不仅检查文件存在；制数时由作者模板显式生成配置。完整性不包含参考精度认证。
