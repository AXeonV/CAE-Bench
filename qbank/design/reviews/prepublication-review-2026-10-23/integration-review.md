# RC2 格式样例与 CFD 兼容集成审阅

日期：2026-10-23。独立审阅；除本报告外未修改代码。范围为本轮 `data_pool.py`、`data_pool_cli.py`、`assembly.py`、`publish_dist.py`、`prepare_harbor.py` 差异，以及 `format_examples.py`、CFD 声明检查、归一化 evaluator 和 runtime catalog。

## 发现与处置

1. **[P2，已修复并复核] 源码修复题与 format 首样例的组合曾生成失效判分命令。** `agent_readme(..., source_repair=True, kind='format')` 原先先进入源码修复分支，忽略 kind，仍输出 `samples/01/reference/grading.json`，且未声明输出为随机格式示例。发布收集器会移除该样例的 reference，因而 README 的路径不存在。已向主代理报告；主代理更新后，本审阅重跑小型复现，确认 format 分支保留 `public/run_case.py`、说明随机角色并不生成 grade 命令，graded 分支仍生成 grade 命令。建议将该双分支断言加入自动回归，并覆盖修复题的公开包实装。

复核结束时，在本审阅范围内未发现尚未处理的发布阻塞项。

## 已核对的行为

- format 为样例 selection 的显式 `kind`，CLI 使用 `--format-sample`；descriptor 还须声明 `example_kind=format`。普通 sample 不能静默消费 format descriptor。
- scored `cases` 始终按数值角色检查 reference 完整性并调用 `prepare_case`；仅 format 样例可免除 reference 完整性要求。format 不使同输入数值 case 自动就绪。
- format 装配只公开 input 与声明的 example 输出，不装配 reference/grading 或数值参考；同一 pool item 可显式同时选为 case 和 format sample，二者的组装路径及验证角色分别处理。
- 发布器对 format 分支只做结构校验，不把随机输出作为满分示例验证；单题/多题 MANIFEST 都保存 sample_kinds。独立公开 runtime 验证相应跳过 `prepare_case`，仍加载输入和输出。
- Harbor 会优先取 graded 样例作为运行/判分命令输入；仅有 format 时不追加公开样例判分命令，样例清单不会列出空 reference 路径。
- `public-materials.json` 的路径/哈希读取及源码修复配置、可信后端/运行环境相关入口仍在；多题包继续明确拒绝混入源码修复题。
- CFD catalog 保留已有 extension/task 映射，新增 24 个模型 selectors 及 24 个 task bindings；其发布 files 包含声明模块、models.json 和 normalized_fields.py。evaluator 仍从可信 reference 读取固定归一化规则，对候选溢出返回失败而非通过。

## 验证证据与边界

- 阅读已有 `format-tests.log`：5 tests，OK；阅读 `cfd-tests.log`：6 tests，OK。二者分别覆盖 format/numerical 角色、参考不公开、混合发布/Harbor，以及 24 模型声明与 evaluator 数值边界。此项为复用现有日志，未重复运行。
- 本审阅新增执行小型 Python 断言：修复题 README 的 format/graded 两个分支均通过，保留可信 driver 入口。
- 本审阅调用 `runtime_materials` 对 CFD 全部 24 题生成合并 runtime（22 个文件），核对 task 数与三个必要模块资源，运行 `validate_public_runtime` 成功。该次仅验证 runtime 闭包，不含题内样例。
- 未启动模型、求解器、编译器、Harbor 实际容器任务或外网数据池上传；未重复大型载荷。未对 CFD 来源物理方程、数值参考正确性和资源达标作认证。
- 数据池、完整公开包、Harbor、源码修复后端以及 public-materials 的广泛回归由主代理执行；本报告不将代码阅读与 fixture 成功替代真实 82 题数据的独立消费检查。

## 补充：冻结包的文档刷新审阅

审阅 `runs/prepublication-review-rc2/refresh_reviewed.py`，结论：在冻结 RC2 为可信基线、后续 RC3 builder 继续验证完整产物的前提下，该文档刷新方法无阻塞发现。这里的结论不是新增数值资格认证。

- 替换白名单只由本题 `instruction.md`、`DATA.md` 两个精确成员名构造；新增 ZIP 成员完全来自原 ZIP，原 MANIFEST 的成员集合与 ZIP 名单必须相等且无重复。其他成员逐块解压并原样写入，包含所有样例 HDF5、运行代码及其他公开材料。ZIP 压缩后的字节可变化，保留的是成员解压字节。
- 每个原成员即使被文档替换，也先完整 stream 计算 SHA-256 并与原 MANIFEST 对照；随后只更新替换文档的成员 hash。新 plan 更新 source_root、public_archive 及整个新 ZIP 的 SHA-256，不修改数据 manifest 或装配 receipt 内容。数值资产通过原 receipt 清单硬链接，已有目标要求 samefile。
- 脚本的 `current_runtime` 来自预先建立的 STAGE。为排除其已落后于工作树，本审阅实际对 82 题分别比较 ROOT/STAGE `runtime_materials` 完整字典：文件集合及每文件字节均相同，包括生成的 runtime 绑定与 pyproject。
- 本审阅额外打开冻结 RC2 的 82 个公开 ZIP，仅读取小型 runtime/manifest 元数据：逐题核对 `src/*` 与 pyproject 的完整集合恰等于当前 runtime_materials、所有 runtime 成员字节相同，MANIFEST.task 与题目一致、MANIFEST.assembly 与当前生成绑定一致。另核对所有公开 samples 成员名均属于 STAGE receipt 的选样文件清单。全部通过，未读取巨型 HDF5。
- 刷新脚本依赖普通 Python 模式下启用的 assert；此次并未为可供任意来源包使用的通用发布器作认证。冻结原包的完整样例 stream 校验由刷新执行负责，新包的最终成员 hash、公开/私有材料一致性与独立消费仍由后续 RC3 builder 及代表消费检查完成。本审阅未重复执行巨型样例校验或求解。
