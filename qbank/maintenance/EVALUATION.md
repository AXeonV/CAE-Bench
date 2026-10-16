# 题目评测配置维护说明

本文件供维护方使用，不作为考生契约，不进入公开解题包。题面的任务、评分和资源，及 DATA 的观测定义仍是配置要求来源。配置／实现修订流程见 [配置技能](../../.agents/skills/caeoj-configure-judge/SKILL.md)。

## 当前配置与消费点

| 文件／字段 | 消费者与语义 |
|---|---|
| judge-config.json / timeout_seconds | 私有 judge 的逐例求解墙钟，含启动及求解程序自身 I/O |
| judge-config.json / max_output_bytes | judge 检查普通结果文件；null 不设独立字节上限，省略保持旧128MiB默认。题面未承诺该限额时不暗加限制，仍须满足公开的逻辑输出规模、内存及时限 |
| judge-config.json / verifier_budget | 组装器计算 `max(模板或逐题总时限, base_seconds + N × (timeout_seconds + per_case_overhead_seconds))`；N来自实际隐藏cases，不能用样例数、0或虚构数字代替 |
| grading.json v1 | 固定 outputs 逻辑字段的数值策略；所有题目均显式提供评分策略，judge-config 不定义容差 |
| grading.json v2 | 按实际 outputs.quantity 与 unit 逐例绑定逻辑名，再交给同一数值引擎；未请求可选量不评分，未知quantity报错。仅第0章用default覆盖任意回传标签 |
| harbor/task.toml | 与共享模板合并，给出生成／构建预算、CPU与内存；GPU、OS及独立verifier网络策略也在合并结果中明确 |
| harbor/requirements.txt | 补充共享镜像与pyproject依赖；第二章固定SciPy版本，其余数值／开发库由共享基础设施提供 |

瞬态热传导的本地 `author/check.py` 使用 `judge-config.json` 的 `memory_mb` 检查进程 RSS；Harbor 使用本题 `harbor/task.toml` 的容器配额。两者均为 1024 MB，由回归测试核对一致。

v2偏置只允许已公开的数值或显式 `{"parameter":"pressure_reference"}`。2.5—2.7 的压力容差相对该输入参数计尺度；2.1—2.4、2.8—2.11 仍使用零偏置，不将物理 reference_pressure 暗中变成判分偏置。详情见 [评分实现说明](../../docs/GRADING.md)。策略原模板哈希和逐例绑定哈希分别记录，不能改写参考／候选数值或重新对齐压力。

## Harbor 与环境

共享镜像固定 `linux/amd64`，模板为 Linux、0 GPU、独立 verifier，`verifier.network_mode="no-network"`；Agent 阶段仍可准备依赖。实际执行主机须使用支持阶段网络字段及 separate 模式的 Harbor 版本，并验证容器限额和网络配置生效；配置解析不能代替运行验证。

第二章用 `memory_mb = GiB × 1024` 表达题面容量。第0章及两道热传导题没有专用CPU承诺，不在配置中添加CPU数量；热传导保留1024 MB内存。其余第一章资源和数值策略保留原值。所有配置暂记provisional，不能把配置完整误认为预算或连续参考精度已校准。

每题的 verifier 预算现取 base=300秒、每例额外开销=60秒，保留原来更大的总时限。这是组装预算策略，不能改变逐例求解时限或成绩；真实数据进入后还需按校验、复制、判分和报告的实际开销复核。数据未建时，已完成公式配置但尚无最终N或实际总预算。

第十一章采用 base=180秒、每例额外开销60秒，仍保留共享模板至少1200秒的verifier总预算；逐例300/600/900秒、2CPU、2048MB、生成3600秒、构建1200秒，逐题instruction与配置相同。八题v2按quantity及单位绑定，全部时刻/点/分量逐值判分。配置加载和临时工具fixture验证不等于Linux容器限额或参考精度验证；尚无正式案例数N。记录见[第十一章交付](../design/reviews/chapter-11-implementation.md)。

第十二章采用逐例300秒（独立受力及粒群分布）或900秒（接触/宏观散体），2CPU、2048MB、生成3600秒、构建1200秒。最多128粒子/64粒级及单例至多2000000标量为初版规模，预算和逐值精度须独立校准；不会由合法结构反推可解。七题评分均v2、无背景偏置；verifier取base=180秒、每例额外60秒并保留模板更大值，真实N留数据阶段。需求映射与工具验证见[第十二章记录](../design/reviews/chapter-12-implementation.md)。

## 数据就绪与使用

各题均已提供评分及执行配置，目录见[题库设计](../design/README.md)。第 2～12 章的正式 cases、reference 和完整公开样例尚未制作；第 1 章部分题目需要运行数据准备工具补齐数值文件。第 0 章用于本地 smoke，尚未提供 Harbor 所需的独立公开样例与参考；配置存在不表示数据或评测已就绪。

可用两道热传导验证本地公开包与Harbor组装：

```sh
python src/utils/publish_dist.py --task heat-conduction-steady-2d
python src/utils/prepare_harbor.py --task heat-conduction-steady-2d
```

其余数据未齐的题目保持组装前置检查，不声称可运行。已生成的旧包应重建；不因为策略模板已可绑定就给空数据发布评测。新数据的实际输出集合、单位和压力参数必须通过加载预检；错误输入／参考／配置属于基础设施问题，不能记作考生数值失分。

实施证据、独立审阅与验证范围见 [本轮记录](../design/reviews/judge-configuration.md)。

第九章采用quantity／unit绑定的v2 pointwise策略，逐帧、逐对象和逐组分比较，资源覆盖及配置验证见[第九章实施记录](../design/reviews/chapter-09-implementation.md)。真实案例数、参考及Linux容器限额尚待数据阶段验证，临时协议fixture不是已发布评测。

第十章采用quantity／unit绑定的v2逐值策略，时间、对象、复量实虚均独立比较。逐题资源配置与执行状态见[第十章实施记录](../design/reviews/chapter-10-implementation.md)。正式数据、参考、容差／预算校准、实际案例数与目标容器执行留后，配置加载和临时fixture不代表正式评测就绪。
