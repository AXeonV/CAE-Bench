# 题目评测配置维护说明

本文件供维护方使用，不作为考生契约，不进入公开解题包。题面的任务、评分和资源，及 DATA 的观测定义仍是配置要求来源。配置／实现修订流程见 [配置技能](../../.agents/skills/caeoj-configure-judge/SKILL.md)。

## 当前配置与消费点

| 文件／字段 | 消费者与语义 |
|---|---|
| judge-config.json / timeout_seconds | 私有 judge 的逐例求解墙钟，含启动及求解程序自身 I/O |
| judge-config.json / max_output_bytes | judge 检查普通结果文件；null 不设独立字节上限，省略保持旧128MiB默认。题面未承诺该限额时不暗加限制，仍须满足公开的逻辑输出规模、内存及时限 |
| judge-config.json / verifier_budget | 组装器计算 `max(模板或逐题总时限, base_seconds + N × (timeout_seconds + per_case_overhead_seconds))`；N来自实际隐藏cases，不能用样例数、0或虚构数字代替 |
| grading.json v1 | 现有固定 outputs 逻辑字段的数值策略；两道热传导继续用 judge-config 中旧 atol/rtol 派生，不能同时再手写重复来源 |
| grading.json v2 | 按实际 outputs.quantity 与 unit 逐例绑定逻辑名，再交给同一数值引擎；未请求可选量不评分，未知quantity报错。仅第0章用default覆盖任意回传标签 |
| harbor/task.toml | 与共享模板合并，给出生成／构建预算、CPU与内存；GPU、OS及独立verifier网络策略也在合并结果中明确 |
| harbor/requirements.txt | 补充共享镜像与pyproject依赖；第二章固定SciPy版本，其余数值／开发库由共享基础设施提供 |

删除旧键前必须核对全部消费者。瞬态热传导的author/check.py仍以旧memory_mb检查进程RSS，因此保留该兼容键并与Harbor的1024MB保持一致；不能因共享judge不读取就删掉。

v2偏置只允许已公开的数值或显式 `{"parameter":"pressure_reference"}`。2.5—2.7 的压力容差相对该输入参数计尺度；2.1—2.4、2.8—2.11 仍使用零偏置，不将物理 reference_pressure 暗中变成判分偏置。详情见 [评分实现说明](../../docs/GRADING.md)。策略原模板哈希和逐例绑定哈希分别记录，不能改写参考／候选数值或重新对齐压力。

## Harbor 与环境

共享镜像固定 `linux/amd64`，模板为 Linux、0 GPU、独立 verifier，`verifier.network_mode="no-network"`；Agent 阶段仍可准备依赖。阶段网络字段已核对 [Harbor官方配置模型](https://github.com/harbor-framework/harbor/blob/f527f8e447038fd242d08ecfa8aaa8029100da97/src/harbor/models/task/config.py)，并用该提交的模型源码解析79份合并配置，确认资源和网络字段保留。检查范围是模型与本仓库组装，不等于完整安装版本兼容、镜像构建或容器限额／网络实测；实际执行主机须使用支持这些字段与separate模式的Harbor版本并验证生效。

第二章用 `memory_mb = GiB × 1024` 表达题面容量。第0章及两道热传导题没有专用CPU承诺，不在配置中添加CPU数量；热传导保留1024 MB内存。其余第一章资源和数值策略保留原值。所有配置暂记provisional，不能把配置完整误认为预算或连续参考精度已校准。

每题的 verifier 预算现取 base=300秒、每例额外开销=60秒，保留原来更大的总时限。这是组装预算策略，不能改变逐例求解时限或成绩；真实数据进入后还需按校验、复制、判分和报告的实际开销复核。数据未建时，已完成公式配置但尚无最终N或实际总预算。

## 数据就绪与使用

当前配置覆盖135题：第0章1题、第1章13题、第2章65题、第3章21题、第4章12题、第5章13题、第6章10题。第六章配置消费与验证见[第六章记录](../design/reviews/chapter-06-implementation.md)，正式数据与参考留后。第五章配置消费、独立安装及验证边界见[第五章记录](../design/reviews/chapter-05-implementation.md)，正式数据与参考留后。第3、4章的配置消费与验证分别见[第三章记录](../design/reviews/chapter-03-progress.md)、[第四章记录](../design/reviews/chapter-04-implementation.md)，两章正式数据及参考均留后；此总数不是已可运行评测数。第0章可用原11例运行本地 smoke，消费本题评分与时限配置；尚无Harbor所需的公开samples与独立reference文件，不为通过组装制造假数据。第一章已有292份清单，其中60份热传导输入及对应参考／公开输出完整，其余232份缺载荷；第二章仍无正式输入或参考。

可用两道热传导验证本地公开包与Harbor组装：

```sh
python src/utils/publish_dist.py --task heat-conduction-steady-2d
python src/utils/prepare_harbor.py --task heat-conduction-steady-2d
```

其余数据未齐的题目保持组装前置检查，不声称可运行。已生成的旧包应重建；不因为策略模板已可绑定就给空数据发布评测。新数据的实际输出集合、单位和压力参数必须通过加载预检；错误输入／参考／配置属于基础设施问题，不能记作考生数值失分。

实施证据、独立审阅与验证范围见 [本轮记录](../design/reviews/judge-configuration.md)。
