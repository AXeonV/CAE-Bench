# 首批 HF 数据迁移记录

## 范围与结果

2026-10-16 将第零章协议测试和第一章两道热传导题的现有数据迁入公开的 [HF 数据仓库](https://huggingface.co/datasets/jimzhouzzy2006/CAE-Bench-OJ)。数据提交为 [`1265d7fa13dd4fcec7313774503f0c3659fe2d42`](https://huggingface.co/datasets/jimzhouzzy2006/CAE-Bench-OJ/commit/1265d7fa13dd4fcec7313774503f0c3659fe2d42)。这是本次核验依据，不是要求今后一直下载该版本。

| 题目 | 迁移文件数 | 字节数 | 材料范围 |
|---|---:|---:|---|
| [smoke-test](../../00-basic-tests/0.1-io/smoke-test/data-manifest.json) | 43 | 208,502 | 11 组输入；无独立 reference 和公开 samples |
| [稳态热传导](../../01-prescribed-pdes/1.1-elliptic/heat-conduction-steady-2d/data-manifest.json) | 206 | 4,748,500 | 32 组输入及参考、2 个样例、现有参考和验证附件 |
| [瞬态热传导](../../01-prescribed-pdes/1.2-diffusion-reaction/heat-conduction-transient-2d/data-manifest.json) | 157 | 10,018,046 | 24 组输入及参考、2 个样例、现有参考和验证附件 |
| 合计 | 406 | 14,975,048 | 原始文件逐字节迁移 |

本次稳定题目 ID 由上述逐题清单的 `task_id` 维护。HF 保留完整 `qbank/` 路径，包含数据目录中的 `problem.json` 及其他小文件。未重排或去重现有网格，未创建 `shared/` 依赖。

406 个数据文件均已从 Git 索引移除，并由数据目录忽略规则覆盖；本地文件保留。没有删除 HF 文件、改写 Git 历史或重新生成数值数据。未迁移其他题目的材料，也未将作者程序、配置和题面上传 HF。

## 清单与就绪状态

每题清单枚举全部文件、大小、SHA-256、输入／参考分组和附件归属。第零章仍沿用现有 smoke runner 从输入数组构造参考的方式；其独立参考分组标记不完整，样例集合为空，不能据本次迁移宣称 Harbor 材料齐备。两道导热题的输入、参考与样例按现有材料标记完整。

首批没有共享分组。样例验证记录列入样例附件，额外参考记录和 catalog 等未归属具体 case 的文件列入题目附件，未遗漏或重解释原始材料。

## 核验

- 上传后从固定数据提交重新获取全部 406 个文件，逐文件核对大小和 SHA-256；检查远端数据路径集合与本地枚举完全一致。
- 用实际 SDK 读取重新获取副本中的 67 个 case 输入、56 份独立参考和 4 个完整样例；样例参考作为输出进行判分均通过。该判分检查消费链，不构成独立数值正确性证明。
- `python -m pytest tests/test_heat.py tests/test_transient.py -q`：25 项测试、289 项子检查通过，覆盖原有数值及消费回归。
- `python -m caeoj_tools.cli smoke`：11/11 通过。
- `python src/utils/publish_dist.py --task heat-conduction-steady-2d --task heat-conduction-transient-2d`：合包成功，并通过发布器已有的公开运行时验证。

本次未运行收费 Agent benchmark、Harbor 容器或重新校准参考精度和资源预算。未实现通用上传、拉取、自动清单刷新或自动 benchmark SHA 前置检查；目前按[维护操作](../../maintenance/DATA-SYNC.md)执行前置核验。生成器的输出位置不变，重新生成后仍需同步清单与 HF。

## 题内数据池迁移（2026-10-17）

上述镜像阶段现已被数据池替代。池上传提交为 [`8511dc8687e623fc58f18444db951d9541cb2d98`](https://huggingface.co/datasets/jimzhouzzy2006/CAE-Bench-OJ/commit/8511dc8687e623fc58f18444db951d9541cb2d98)，核验后在 [`07429d690588aa209b30f69bf3af8ebfa1be72f3`](https://huggingface.co/datasets/jimzhouzzy2006/CAE-Bench-OJ/commit/07429d690588aa209b30f69bf3af8ebfa1be72f3) 移除原 406 个镜像路径并更新数据集说明。未改写 HF 历史。

HF 当前为 68 个条目：smoke 11、稳态导热 33、瞬态导热 24。池共 463 个文件，包含描述、索引和附件；加仓库 README 与属性文件共 465 个文件。代码侧三个清单升级为版本 2，原有 task ID 保持不变，选择条目并绑定描述摘要；HF 描述和索引使用各自的版本 1。

迁移检查了本地源文件与旧清单一致，随后从固定 HF 提交重新获取并核对所有池文件的大小与 SHA-256。只使用下载的池内容和新选样清单装配到独立目录，恢复原 406 个文件，逐字节摘要和路径集合与原材料完全一致；SDK 加载全部 67 个测试输入、56 份独立参考和 4 组样例成功。smoke 仍没有独立 reference 或 samples，未补造数据。

样例与测试共享相同输入及参考时复用条目：稳态样例 01 对应测试 01，瞬态样例 01 对应测试 01、样例 02 对应测试 15。稳态样例 02 是单独条目。上述既有重叠被明确保留，不能将此次存储迁移当作正式选样质量或评测独立性通过；后续正式选样需处理这些重叠。

原作者解析附件、样例验证附件和 catalog 均保留可还原映射；能引用现有池文件的附件不再额外复制。未引入共享网格重排、改变数值、重选样例或执行 PDEBench 全轨迹转换。通用池上传、下载装配、远端恢复和自动 benchmark 检查尚未实现。
