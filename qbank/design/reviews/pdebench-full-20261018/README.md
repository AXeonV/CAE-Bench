# PDEBench 250000 条全量归档迁移

用户于 2026-10-18 明确授权启动三个问题族全量。执行范围为直接保留 HF 原始输入及轨迹，未增加求解器、公式补算、考生运行或正式选样。

## 已启动

2026-10-18 22:46（Asia/Shanghai）提交 [HF Job 6ad4dbdac6628814522749be](https://huggingface.co/jobs/jimzhouzzy2006/6ad4dbdac6628814522749be)，实际 CPU Basic，服务端已进入 RUNNING。目标为 [pdebench-full-20261018](https://huggingface.co/datasets/jimzhouzzy2006/CAE-Bench-OJ/tree/pdebench-full-20261018) 分支，main 未切换。提交参数、代码及运行包摘要由 launch.json 拥有。

来源报告固定 `3583c7a567d2fe2811af0035efa7caddca08e106`；从先导分支固定提交 `91e904bb85a0b6ae07f171069d08b7c1fb610517` 创建全量分支。云端已逐一核对400个先导描述绑定，继续复用；剩余249600条分250批，首批每文件为16..999，其余每1000行一批。plan.json完整列出互不重叠范围。顺序交错三族，单写入者发布，避免分支提交竞争。

进度由 HF 上 `migration-trials/pdebench/2026-10-18/full-archive/full-report.json` 唯一维护。基线400加已通过批次构成已完成数；当前批次未完成前不计入。初始状态见 initial-status.json，不把目标数称为已完成数。三族目标分别80000、120000、50000，最终还核对三池根计数。

## 预算与恢复

沿用旧 USD 1 累计上限；本长作业预留 .72311，包含72小时硬超时及启动余量。连同此前费用与未释放预留，总预算占用 .830295；这些是最坏占用，不是账单。当前估计和历史费用解释仍归[预算记录](../pdebench-calibration-20261018/BUDGET.md)。单个长作业逐批推进，不由本机不断提交Job，也不自动重试失败Job。硬超时由 HF 执行，内部提前停止，不因账户余额而扩支。

每批绑定固定来源/跨度/代码/运行包，planned→prepared→verified；先绑定不可变资产身份，后发布、固定提交重取、装配和逐字段无损消费。verified批次可在相同recipe下重新消费，prepared状态先停止核对，防止未知发布被盲目覆盖。整个云端执行器遇错停止并报告当前范围；未验证的批次不记完成。

每批清除自身临时数据、HF下载缓存、TAR解包缓存和旧索引缓存；禁用Xet块缓存积累。启动新批次前检查临时盘至少20GiB空闲，并检查硬时限的剩余余量。源场只在HF作业内处理，本地只传代码和小型JSON。

## 监视

本对话独立 heartbeat `pdebench-25`（PDEBench 25万条迁移监视）已启用，每30分钟读状态和小型进度JSON；同名旧四模型评测监视未修改。正常推进不逐轮通知，只在完成、失败、预算临界或同批连续两轮不推进时通知；终态报告后停用。监视不提交、重试Job，不修改运行代码或正式数据。

手动查看：

```sh
python3 src/utils/PDEBench/hf_archive_status.py --job-id 6ad4dbdac6628814522749be --settle-terminal --output runs/pdebench-cloud-trial/full-status.json
```

辅助命令只读取注册Job和小型进度JSON；只有指定终态结算时按共享锁与原有API身份/时长校验更新账本，未结束的Job始终保留全额预留。不会下载源场或case载荷。定时任务依赖本机app运行，HF迁移本身独立运行；说明见[官方scheduled tasks文档](https://learn.chatgpt.com/docs/automations?surface=app)。

## 验证

使用合成数组验证三族真实pack/TAR/assemble/strict verify无损消费；检查250批加400先导恰好覆盖全部25万来源、预算不足在提交前拒绝、72小时timeout/实际Basic硬件和继承固定提交到达真正Jobs调用。当前定向检查22项通过；没有另外提交付费测试。全量Job的云端初始化已核对先导并进入首个984条生产范围，尚未宣称千条批次或全量完成。
