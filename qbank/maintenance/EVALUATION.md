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
| harbor/requirements.txt | 补充共享镜像与 pyproject 依赖，逐题声明需要固定的版本 |

瞬态热传导的本地 `author/check.py` 使用 `judge-config.json` 的 `memory_mb` 检查进程 RSS；Harbor 使用本题 `harbor/task.toml` 的容器配额。两者的内存承诺应一致，由回归测试核对。

v2 偏置只允许已公开的数值或显式 `{"parameter":"pressure_reference"}`，不根据物理参数名自动启用偏置。策略模板哈希与逐例绑定哈希分别记录；绑定不能改写参考／候选数值或重新对齐压力。详情见 [评分实现说明](../../docs/GRADING.md)。

## Harbor 与环境

共享镜像固定 `linux/amd64`，模板为 Linux、0 GPU、独立 verifier，`verifier.network_mode="no-network"`；Agent 阶段仍可准备依赖。实际执行主机须使用支持阶段网络字段及 separate 模式的 Harbor 版本，并验证容器限额和网络配置生效；配置解析不能代替运行验证。

CPU／内存承诺来自题面，并在合并后的容器配置中核对；未声明时不凭空添加配额。verifier 总预算按逐题配置和实际案例数计算，包含校验、复制、判分与报告开销，不能改变逐例时限。临时 fixture 和配置解析不证明目标容器限额、参考精度或预算已经校准；标记为 provisional 的配置仍需真实数据验证。

## 数据就绪与使用

题目与数据状态见[题库设计](../design/README.md)及各题 README；配置存在不表示评测已就绪。公开材料发布要求完整可用的样例输入与输出；Harbor 组装还要求实际隐藏 cases 和对应 reference，不能用空目录或临时 fixture 替代。

已有 `data-manifest.json` 的题目先按[数据获取与维护](DATA-SYNC.md)从 HF 获取并核对所选输入、参考与共享依赖的完整性、大小和 SHA-256；不一致时停止正式 benchmark。当前该核验是维护方前置步骤，装配器尚未自动执行；网上公开数据也不改变考生与 verifier 的材料装配边界。

可用两道热传导验证本地公开包与Harbor组装：

```sh
python src/utils/publish_dist.py --task heat-conduction-steady-2d
python src/utils/prepare_harbor.py --task heat-conduction-steady-2d
```

其余数据未齐的题目保持组装前置检查，不声称可运行。已生成的旧包应重建；不因为策略模板已可绑定就给空数据发布评测。新数据的实际输出集合、单位和压力参数必须通过加载预检；错误输入／参考／配置属于基础设施问题，不能记作考生数值失分。

实施证据、独立审阅与验证范围见 [本轮记录](../design/reviews/judge-configuration.md)。
