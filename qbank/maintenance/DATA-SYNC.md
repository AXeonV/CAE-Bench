# 数据池操作

存储与清单职责见[存储设计](../design/DATA-STORAGE.md)。维护入口统一为 `python -m caeoj_tools.cli data`（安装后的 `caeoj-maint data` 等价），提供 `pack`、`upload`、`select`、`fetch`、`assemble`、`verify`。这些工具不求解物理问题或证明参考精度，不进入考生安装包。

## 环境与定位

在代码仓库根目录安装维护依赖：

```sh
python -m pip install -e '.[maint]'
python -m caeoj_tools.cli data --help
```

`--task` 使用唯一题目目录名。题目已有 `data-manifest.json` 时沿用稳定 ID 和仓库定位；新题先分配无重复的 `caeoj-000123` 形式 ID。HF 登录使用官方客户端的 `hf auth login` 或环境中的令牌，避免将令牌写入代码、清单和日志。

## 从生成数据制作池

生成器继续产生原有 `cases/`、`reference/`、`samples/`。审核材料后离线制池：

```sh
python -m caeoj_tools.cli data pack --task heat-conduction-steady-2d --output work/heat-pool
```

输出目录必须为空；输出包含 `repository/` 下可上传的池以及 `selection.json`。`--source <目录>` 可读取独立试跑/生成目录；新题没有清单时必须显式传 `--task-id`，可用 `--repo-id` 指定仓库。工具不自动分配 ID。

相同输入的样例复用池条目，重复文件在本题 `pool/shared/` 按内容复用。输入和参考完整性分别声明；输入完整性检查声明资产是否齐备，不等于实际 SDK 契约或数值检查。已有来源证书会核对输入绑定，并保存来源身份；制作过程缓存和作者代码不上传。题目级额外 reference/shared 附件保留装配映射。

制池不会修改题目的正式选样清单；需要先核对 staged `selection.json` 与实际意图。它保留来源目录的已有测试/样例重叠并报告，不为凑齐数据擅自重选。

## 上传

```sh
python -m caeoj_tools.cli data upload --bundle work/heat-pool
```

上传前校验全部索引条目、输入、参考、附件及摘要。读取一次远端提交，合并索引，保留其他条目，以该提交为父提交一次性发布；并发修改会使提交失败，应重新检查后重试。相同文件按远端 SHA-256 或 Git blob ID 跳过，不下载旧大文件来比较。

远端同路径或条目内容不同时默认停止；审核变化后加 `--update`。`--revision` 默认 `main`，也可显式指定已有分支；工具不创建仓库或分支。上传后固定到新提交重新核验 bundle 的条目和载荷。中断后可重跑，相同内容跳过；该行为不意味着 PDEBench 全轨迹转换或转换缓存已支持远端续作。

只上传本题池文件，不删除未选择或未包含的远端条目。上传不自动更新已有代码清单中的预期摘要；需要显式重选或采用审核后的 staged 选择。若远端上传成功而后续核验失败，保留提交 ID 并修复，不能据命令失败推定远端没有改变。

## 明确选样

先浏览 HF 的 `pool/index.json` 找到目标 case ID，再写入明确选择。例如：

```sh
python -m caeoj_tools.cli data select --task heat-conduction-steady-2d --case '001=<测试case-id>' --sample '01=<样例case-id>' --output work/heat-selection.json
```

`--case`、`--sample` 可重复，每个参数为 `[本地编号=]case-id`；省略本地编号则按参数顺序编号为 001、002 等。此命令生成整个选择集合，未列出的角色/条目不会自动保留。默认写回本题清单；建议用 `--output` 先检查提案，确认后将其保存为本题 `data-manifest.json`。

选择固定条目描述的路径与摘要，并绑定当前池索引中的题目级附件。检查输入/参考完整性、相同输入和已有来源轨迹身份，拒绝重复或不完整的正式选择；仅开发用途可加 `--allow-incomplete`，严格消费仍阻断缺失参考。池变化不会静默刷新旧绑定；显式重选后审核变更。选样不下载完整数值文件。

## 下载与装配

```sh
python -m caeoj_tools.cli data fetch --task heat-conduction-steady-2d
python -m caeoj_tools.cli data assemble --task heat-conduction-steady-2d
```

`fetch` 只下载、校验并缓存；`assemble` 同样获取所需数据，然后装配本地目录。每次命令固定同一个 HF 提交，默认官方 Hub 缓存，可用 `--cache-dir` 指定缓存，`--revision` 指定分支或提交。离线时用 `--source-dir <repository形状目录>`，根目录下应含清单中的 `qbank/.../pool/`。

只装样例：

```sh
python -m caeoj_tools.cli data assemble --task heat-conduction-steady-2d --cases --samples 01 --no-auxiliary
```

`--cases`、`--samples` 不传表示该角色全部选择；参数存在但不带名称表示不取该角色。`--no-auxiliary` 不取题目级维护附件。下载一个 case 默认仍取得对应参考与依赖。参考待补可供开发获取已有材料，但结果会列出 `incomplete`，不能视为完整成功。

池文件先检查大小和 SHA-256；装配保持字节内容，参考按角色映射到 `reference/<编号>/reference.h5` 或样例 `output/result.h5`。共享文件按描述中的 `source` 获取后物化到输入包内部，保留现有相对引用；不让考生通过向外路径读取本题共享目录。支持绑定的共享依赖描述，检测循环和目标冲突。

本地相同摘要跳过；不同摘要先停止，显式 `--update` 才覆盖。新集合先暂存，全部差异预检后写入，失败时回滚；回执最后更新。改变范围或选样会清理回执管理的旧文件，也需 `--update`；拒绝删除被用户改过的旧文件，不删除未知文件。不要并发装配同一题；异常进程留下锁时先核对 PID，再处理自己的遗留锁。

`.data-assembly.json` 回执记录本次选样、解析提交、原始描述和实际文件摘要，由 Git 忽略。不能编辑回执来“修正”数据；离线校验从其 SHA 绑定的原始描述重新推导预期文件，而不是信任回执的文件摘要。

## 校验与真实消费

```sh
python -m caeoj_tools.cli data verify --task heat-conduction-steady-2d
python -m caeoj_tools.cli data verify --task heat-conduction-steady-2d --strict
```

默认开发校验发 warning，报告 `valid: false` 并返回退出码 1；严格校验不一致时返回 2 并停止。检查选样变更、材料缺失、摘要差异和残留入口。`--strict` 还拒绝不完整参考及重复输入/来源轨迹。`--samples-only` 只核验完整样例，不要求测试数据已下载。

公开发布自动严格校验样例；Harbor 准备自动严格校验全部选中数据和重叠；均离线执行，不自动获取或重新选样。没有池清单的题目继续执行原来的材料检查。常规本地 smoke 使用开发警告模式。

首批迁移保留的历史样例/测试重叠会被正式准备阻断，应审核后重新选样，不能绕过校验。文件一致性、契约合法、参考数值正确及资源校准分别验证。完成装配后仍按题目 README 做 SDK、数值和公开包独立运行检查。

## 更新与提交

生成改变后重新制池、审核、上传，并显式更新选择和装配。只更新选择不意味着参考已校准。代码仓库保存工具、题意、审核证据和选样清单；本地装配、缓存、bundle 与令牌不提交。题目移动同步更新两边定位，保留稳定题目 ID。
