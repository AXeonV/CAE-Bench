# 离线题库候选发行版

发行装配冻结已经装配、明确选样的题目，不制作参考、不更改数值判据，也不访问HF。完整性检查、参考数值资格、资源校准和模型Benchmark分别记录；内部RC可以保留明确的资格局限，不能据文件校验宣称最终验收完成。

## 准备与选择

先按题目目录和资产账本确定纳入项。无可评分case的题不进入发行目录；输入／参考存在但仍待数值核验的候选留在排除清单。对修复题，应记录真实提交接口和运行环境可获取性，不能把旧文件替换接口标成完整仓库patch。

本地已有载荷优先复用。需装配的题使用[数据池工具](DATA-SYNC.md)完成离线assemble与strict verify；不要为了制发行包重新下载相同数据。不同历史工具版本的manifest／format样例应使用匹配的既有运行闭包，不能补造数值参考或静默降级验证。

作者计划JSON包含：

- `release_id`、`stage`及实际`capabilities`；
- `tasks`：每题的`task`、`chapter`、`title`、`source_root`、相对`task_path`、现有`public_archive`、明确的`profile`和`limitations`、实际`license_files`；
- `excluded`：未纳入的题目身份与具体原因。

`source_root`和许可证原位置只用于作者侧装配计划；最终catalog不依赖这些机器路径。公开包先经现有`publish_dist.py`或匹配版本的发布器生成，包含独立的严格运行闭包；它不得含正式隐藏case、参考、作者材料或装配回执。

## 冻结归档

```sh
caeoj-maint release build --plan /path/author-plan.json --output /path/empty-release
```

目标必须是新目录或空目录。工具逐项核对manifest、回执、描述摘要及资产全集，流式写入ZIP，并拒绝源／目标冲突、链接、越界、身份冲突及公开包混入私有材料。原manifest与选样映射保持原样；失败会保留诊断用的部分文件，不写完成校验清单，不能分发为完整发行版。

主要产物：

|产物|用途|
|---|---|
|`qbank.zip`|选中题面、配置、实际case、参考、样例及绑定回执；仅给维护方|
|`public/*-agent.zip`|每题独立考生材料与SDK闭包；只给Agent这部分|
|`catalog.json`|题目身份、选择、资格profile、局限和排除记录|
|`licenses/`|按内容摘要去重的实际许可／署名材料及逐题归属|
|`release.py`|不依赖作者仓库的stdlib检查、列题和按题提取工具|
|`README.md`、`SHA256SUMS.json`|实际使用步骤与全部产物的完整性绑定|

组装前核对临时磁盘峰值。大型载荷不需要再建一份解压副本；归档仍需足够磁盘空间。发行包的实际内容与校验清单均完成后才进入分发检查。

## 独立消费与验收

在发行目录执行：

```sh
python release.py list
python release.py verify
python release.py extract task-slug /path/empty-task-workspace
```

按题提取合并公开运行闭包与本题私有判题材料，并校验重叠文件；这份工作目录只适合维护者，不能整目录交给考生。Agent使用对应public ZIP。每题严格运行闭包的任务绑定不同，安装与运行应使用各自隔离环境。

进入提取目录后按公开README安装工具，用`python -m caeoj validate-input`、`validate-output`、`grade`检查实际输入和已有输出。普通pip安装仍需要匹配的Python依赖及Gmsh系统动态库；数据离线不表示发行包已提供全部系统镜像。模型执行器、凭据、未交付镜像、fast模式或新提交接口未实现时须在capabilities与README明确。

至少验证来源路径不参与提取、公开包无隐藏参考、正式配置完整，以及代表性题目在提取后的独立安装与真实判分。记录实际覆盖与失败；不以参考自判分代替独立数值资格。装配工具改动应复核路径边界、format／数值样例、资产遗漏、损坏检测及独立CLI，再更新本流程和相关技能。
