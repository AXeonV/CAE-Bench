# 无人值守执行与恢复

用户在当前对话已明确授权：启动五路低频迁移；本人离开后，每 30 分钟监测；出现问题时自主停止当前任务、合并已核验成果、检查状态、修复并重做五路分工，累计 HF Jobs 预算 USD 1 内直接继续；完成或异常时通知。无需再等用户批准常规修复或下一恢复轮次。不得动用账户剩余余额突破 USD 1，不购买额外资源，不修改来源、契约、评分或正式选样，不运行求解器或考生。

## 当前轮次与监视

先检查 `runs/pdebench-cloud-trial/low-commit-recovery-intent.json`（若存在）：这是当前已授权本机串行恢复编排的 PID、唯一脚本路径/摘要、阶段及日志。PID 实际命令必须包含该脚本路径，文件 SHA 必须与登记一致；满足且日志/子进程按阶段推进时，不重复审计、合并或提交，不把旧 CURRENT 的终态当成新故障。它只顺序调用现有 merge/check/plan/preflight/launch 门禁，预算不足或任一步失败会停止，不绕过账本。检查日志新提交与修改时间；同一阶段连续两轮无新日志且排除正常等待时再检查子进程/服务端头，不因父 PID 尚活着永远忽略停滞。阶段 failed 或 PID 退出时读取日志并核对成果/未知提交再处置。handed_to_launcher 阶段由相同 PID exec 成付费启动器，转按下方 launch-intent/CURRENT 核对，不能把 exec 导致的命令变化误作故障。

先检查 `runs/pdebench-cloud-trial/low-commit-launch-intent.json`（若存在）：核对 PID 实际命令是该 cohort/plan 的 `hf_low_commit_launch.py --submit`。即使 CURRENT 仍指向上一轮终态，只要下一轮启动器仍在本机等待冷却，就保持安静、不得再次停止或重复重规划/提交。它不持有收费资源。启动器成功时 CURRENT 自动切换；若进程退出却未完成，先看对应日志并对照 launch/ledger/API，不盲重发。旧 PID 若被复用不视为启动器。

唯一当前轮次注册表：`runs/pdebench-cloud-trial/low-commit-current.json`，指向冻结 plan/launch。没有注册表时先检查 `runs/pdebench-cloud-trial/low-commit-launch.pid` 对应进程及 ledger；初始启动器会在本机无费用等待至北京时间 03:14:34 后才提交。等待或共享锁被启动器占用不算失败，不重复提交。

当前启动命令为 `python3 src/utils/PDEBench/hf_low_commit_launch.py --cohort r1 --submit`。低频轮次 evidence 在本目录 `runs/rN/`；尚无 Job ID 时不得宣称已运行。提交器对同轮次拒绝重复提交，先一次性预留五份再提交。

每轮执行：

```sh
python3 src/utils/PDEBench/hf_low_commit_status.py --settle-terminal --logs --output runs/pdebench-cloud-trial/low-commit-status.json
```

只读取 API、进度/根索引 JSON 与每个 Job 最近 20 条 non-following 日志，禁止本机获取源场、case HDF5 或 TAR。对比上一轮记录每组/三族核验量、服务端时长、实际提交控制日志、冷却重置和预算。已接受 baseline 只计一次；prepared 不能计为完成。

常态与不变状态保持安静。首次 429 等异常通知，但明确的配额冷却可在时限/预算内继续等待，不因等待马上取消整组；先区分正常时隙等待、配额冷却和真正停滞。实质失败、未知写入结果、不能在剩余硬时限完成或同批连续两轮未推进且排除正常等待时，进入下面恢复流程。通知异常后继续执行已授权恢复，不在发出通知后等用户回复。

## 停止、保全与检查

1. 只操作 CURRENT 指向的已登记 Job ID。停止该轮仍 RUNNING/STARTING/PENDING 的作业，确认 API 全部终态。未知取消结果保留预留，继续只读核查；不要猜测已停。
2. 运行 status 的 `--settle-terminal` 在共享预算锁内结算。HF 未返回 finished_at 时，辅助函数使用已认证的终态响应 Date、createdAt、实际 Basic 硬件且关闭端口/SSH 的证据作为保守上界。预留不是已花费，不能手工把未知预留归零。
3. 部分提交失败时先查 launch/ledger 和仍活着的启动器。submission_pending 不得重发；用账户 Job 列表的唯一 cohort/worker/name/代码绑定核对实际已创建的 Job，再补登记并停止。只有启动器已退出、该项始终 reserved 未进入 API 提交、且列表也无对应 Job 的明确未提交项，才可记录证据释放这项未使用预留。未知结果保留预留。
4. 为恢复证据创建新目录，例如本目录 `recovery-r1/`。不要改写旧轮次冻结 plan 或 receipt。

```sh
PYTHONPATH=src python3 src/utils/PDEBench/hf_partial_audit.py --cohort-plan <CURRENT中plan_path> --out <恢复目录>
PYTHONPATH=src python3 src/utils/PDEBench/hf_partial_merge.py --out <恢复目录> --destination pdebench-consolidated-20261019-after-r1 --apply
PYTHONPATH=src python3 src/utils/PDEBench/hf_partial_check.py --out <恢复目录>
```

审计会继承该轮 baseline，补入全部 verified 检查点，即使进度报告落后也不丢失已完成批次；保留未接受的旧 prepared。合并只纳入已核验选择，使用标准 stage_plan、HF 服务端复制不可变资产和原子根发布；本机只处理 JSON。合并器为单写入者低频提交，遇到明确 429 按服务器重置冷却后再核对 receipt/head 安全续做；未知提交结果先核对，禁止覆盖或盲重试。恢复 helper 的 `--out` 传具体目录，不要回退到旧的固定五作业审计默认值。

如果合并后恰好 250000 唯一来源、25 文件各 10000、三池 80000/120000/50000，完成最终固定提交/引用绑定核查并报告；不要提交五个空作业。全部真实批次消费验证回执仍为载荷依据，不把最后的元数据核查描述成一次新的数值验收。

## 修复与下一轮

找出实际原因，先补本地离线故障检查，再修复迁移/传输/监视代码；保留 case 含义、输入/参考和已接受绑定。共享发布器已支持资产+分区+根+prepared/进度的一次原子提交，核验后第二次提交 verified/累计进度。实际 commit POST 都通过全仓库时隙门控；包括 SDK 内部写入和归并，不能只在外层上传函数限速。429 尊重服务器重置；网络错误先证明是否已提交，不盲重发。

```sh
python3 src/utils/PDEBench/hf_recovery_plan.py --out <恢复目录>
PYTHONPATH=src python3 src/utils/PDEBench/hf_prepared_preflight.py --out <恢复目录>
python3 src/utils/PDEBench/hf_low_commit_readiness.py
python3 src/utils/PDEBench/hf_low_commit_launch.py --cohort r2 --plan <恢复目录>/plan.json
python3 src/utils/PDEBench/hf_low_commit_launch.py --cohort r2 --plan <恢复目录>/plan.json --submit
```

每次选择新的 rN，不能复用已登记轮次。计划按 accepted coverage 排除已完成来源区间，逐文件证明全覆盖、不重复；prepared 包存在时恢复原包，缺少整个原包且原/合并池均无相应 case 绑定时才允许按固定上游重制，保留旧候选检查点和关联证据；新候选必须逐条证明固定来源 recipe、输入 source/problem JSON 摘要、原始和映射场数组摘要、坐标、时间、dtype/shape 等均与旧候选一致。仅允许 HDF5 容器文件摘要引起的新 case/描述身份，不能覆盖任何已经发布或接受的绑定；仍需完整固定提交远端消费后才计数。若数值/JSON 不同必须停止并检查具体差异，不得反复付费重启相同错误。若发现部分孤立资产或绑定冲突，先查清；不能绕过预检强行计为完成。

新轮次按剩余工作量和分族实际生产耗时缩短限时，单作业不超过 12 小时。批次 elapsed 在 verified POST 前截取，规划必须另计核验提交门控等待、最终归并和启动；当前 measured_recovery_timeout_hours 将这些时间显式加回，再向上取半小时，按最新累计预算拒绝不可信的压缩。小时数可能为半整数，传 API/alarm 的 hard_timeout_seconds 必须是整数秒。`hf_low_commit_readiness.py` 真正运行本地检查并绑定代码摘要，不手工伪造 passed；代码变更后必须重跑。提交器先核对 accepted 基线证据、无旧写入者和实际 CPU Basic 分钟价，再对五项一次性锁定预算；未来 round 保留冷却门槛，本机等待不收费。

当前最初累计保守占用 .171774，r1 五个 12 小时预留合计 .609550，累计 .781324。以后必须从共享账本重算，不能反复使用这个旧数。若预算不足以给剩余任务安排五份可信限时，不提交新作业：合并并交付已核验部分，明确预算边界并通知。账户 $100 余额不构成额外授权。临界告警若仅由本轮已批准硬限时的未来预留超过 $0.95 引起，首次通知后正常推进保持安静；总占用仍不超过 $1、没有其他实际异常时，不为释放预留而取消健康作业，也不把预留称为已花费。新费用只能在真实终态结算后重新判断。

新轮次提交成功后 CURRENT 自动更新；定时器继续跟随 CURRENT，无需另建重复监视。完成或异常处理结果报告固定提交、各族核验数、实际 Job 状态及生命周期费用保守上界，账单未核对要说明。全量成功，或预算/外部状态使安全恢复无法继续时，报告最终状态并暂停监视；正常恢复成功后保持每 30 分钟监视。

## 本机监视的临时保活

本轮创建了限时 24 小时的 `caffeinate -i` 空闲防休眠断言，所有权记录为 `runs/pdebench-cloud-trial/monitor-awake.json`，不修改永久电源设置。全量成功或决定最终停止后，核对该记录 PID 的实际命令仍是对应 caffeinate，再终止本轮拥有的进程并记录释放；不要杀其他人的电源断言。App 仍须运行，强制休眠或关机不能由此保证。
