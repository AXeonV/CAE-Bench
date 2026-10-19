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
- 成果分支：`pdebench-low-commit-20261019-r3`。没有另行写入 HF 主分支。
- 本机完成快照：忽略目录 `runs/pdebench-cloud-trial/completion.json`；预算事实归属共享 `budget.json`。

## 费用

全历史已结算 Job 生命周期费用保守上界 USD 0.817850；另保留历史未知费用 USD 0.060000。累计保守占用 USD 0.877850，低于原累计上限 USD 1，无当前作业未来预留。账单尚未核对，这些数字不应称为实际账单费用；未知历史费用没有手工清零。

## 本轮作业

- w1: `6ad58c5cc66288145227f1e8` — COMPLETED
- w2: `6ad58c5f5ccb47ba0f7cd854` — COMPLETED
- w3: `6ad58c62c66288145227f1eb` — COMPLETED
- w4: `6ad58c655ccb47ba0f7cd858` — COMPLETED
- w5: `6ad58c685ccb47ba0f7cd85d` — COMPLETED
