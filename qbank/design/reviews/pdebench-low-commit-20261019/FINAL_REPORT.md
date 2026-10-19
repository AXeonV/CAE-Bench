# PDEBench 全量迁移完成记录

核验时间（UTC）：2026-10-19T13:15:41.215202+00:00。最终状态：completed，r3 五个 HF Jobs 全部 API COMPLETED，监视已暂停，本轮临时 caffeinate 已释放。

## 范围与验收

- 250000 条唯一来源轨迹；固定 25 个来源文件，每文件 10000 条。
- 平流 80000、Burgers 120000、一维可压缩流 50000。
- 沿用全部逐批固定提交的真实消费核验回执；合并后额外真实消费抽检每族 1 条。
- 状态辅助程序核对报告身份、分配区间无重复、来源覆盖、三池计数和最终固定提交池根。最终消费抽检由云端完成；本轮本机只获取 JSON/API/有界控制日志，没有下载数值载荷。
- 未补算参考，未修改正式选样；迁移完成不表示正式 benchmark 选样或数值误差阈值已校准。

## 固定成果

- [最终数据池](https://huggingface.co/datasets/jimzhouzzy2006/CAE-Bench-OJ/tree/2b7512285aacbeeabb116f154915ee1384ff74eb)：`2b7512285aacbeeabb116f154915ee1384ff74eb`。
- [最终报告](https://huggingface.co/datasets/jimzhouzzy2006/CAE-Bench-OJ/blob/01d7b4d6c369a59086fdf5cbc7ada23d89bfe7ae/migration-trials/pdebench/2026-10-19/low-commit/r3/final-report.json)：`01d7b4d6c369a59086fdf5cbc7ada23d89bfe7ae`。
- 迁移完成时成果分支为 `pdebench-low-commit-20261019-r3`；随后经用户授权合入 `main` 并清理迁移分支，见下方收束记录。
- 本机完成快照：忽略目录 `runs/pdebench-cloud-trial/completion.json`；预算事实归属共享 `budget.json`。

## 费用

全历史已结算 Job 生命周期费用保守上界 USD 0.817850；另保留历史未知费用 USD 0.060000。累计保守占用 USD 0.877850，低于原累计上限 USD 1，无当前作业未来预留。账单尚未核对，这些数字不应称为实际账单费用；未知历史费用没有手工清零。

## 本轮作业

- w1: `6ad58c5cc66288145227f1e8` — COMPLETED
- w2: `6ad58c5f5ccb47ba0f7cd854` — COMPLETED
- w3: `6ad58c62c66288145227f1eb` — COMPLETED
- w4: `6ad58c655ccb47ba0f7cd858` — COMPLETED
- w5: `6ad58c685ccb47ba0f7cd85d` — COMPLETED

## HF 分支收束

用户随后明确授权合并本次 PDEBench 迁移内容并删除 38 个迁移分支。

- HF `main` 合并提交：`efe3e36b55e7ba2265edfa0ddace34ef38f1e5be`，保留原主分支及验收来源的提交历史；未改写主分支历史。
- 基于真实 Git 三方合并树，合入仅增加 `qbank/01-prescribed-pdes/pdebench-archive/` 与 `migration-trials/pdebench/`，未修改或删除原主分支文件。
- 服务端最终树共 6382 个文件，逐文件核对 blob ID 和字节数与原主分支、验收版本均一致；三池仍为 80000/120000/50000，最终报告覆盖 25 文件各 10000 条。
- 38 个迁移分支各建立 `archive/<原分支名>` 注释标签，核对剥离后的 commit SHA，再删除分支；38 个历史入口均保留。其他 5 个题目相关分支及其头提交保持不变，最终剩余 6 个分支（含 main）。
- 使用 HF Git protocol v2 的 `blob:none` 部分获取，只传输提交与目录对象，本机对象包约 1.3 MiB；没有下载源场、case 或 TAR，没有新增 HF Jobs。
- 本次为逐文件身份和索引计数检查，没有重新运行数值消费；载荷消费证据仍采用上面的逐批验收与最终抽检回执。
- 完整分支/标签映射与收束回执：`HF_BRANCH_CLEANUP.json`。
