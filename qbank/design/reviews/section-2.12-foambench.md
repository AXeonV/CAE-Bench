# 2.12 FOAMBench 题面移植实施记录

日期：2026-10-19。分支 `codex/foambench-statements`，起点 `1740d71a86bcb9260b3b3fdde7feb6ab28ed2735`。用户范围：全部题目、独立一节、使用本仓题面与数据协议、不绑定 OpenFOAM、不修改哲学，仅题面阶段。

## 交付

[目录](../../02-fluid-mechanics/2.12-foambench/README.md)保留 Basic 110、Advanced 16，共126题的一一对应；每题独立 instruction.md、DATA.md 与作者来源记录。[规划](../section-2.12-foambench.md)说明与核心通用题的边界。现有 2.1—2.11 题号、HF、选样和配置均未变；PHILOSOPHY.md 未改。

上游固定提交 `e37e8b61fbb1f3532dcfd2f2e8ab67e7c91c3ee2`。来源两个JSON的摘要、逐题原ID及prompt摘要由[轻量索引](../../02-fluid-mechanics/2.12-foambench/author/source-index.json)唯一维护。Git保留公开题面、完整DATA、来源许可、改编记录、可重建脚本与审阅证据；不保存整套原软件配置或数据载荷。

## 审阅与修订

按 author-question、design-data、design-review、candidate-review 工作流执行；出题按三组Basic与一组Advanced编写，独立审阅使用三个新上下文分别进行设计、考生三文件审阅、源题完整性审计。报告保留初轮与修订复核，不把作者自审当成独立结论。

| 检查 | 覆盖及最终结论 | 证据 |
|---|---|---|
| 独立设计 | 全126题，已列问题闭合，未发现未决设计问题 | [初轮](foambench-20261019/design-initial.md)、[复核](foambench-20261019/design-final.md) |
| 独立考生 | 全126题，statements模式，无样例；未发现未决题面问题 | [初轮](foambench-20261019/candidate-initial.md)、[复核](foambench-20261019/candidate-final.md) |
| 独立来源审计 | 全126映射、prompt、变体差异，原模型放宽等问题已修复 | [初轮](foambench-20261019/source-initial.md)、[复核](foambench-20261019/source-final.md) |

主要修订：不可压贝纳德初态改为明确无散流函数；障碍绕流原始速度采用公开Helmholtz投影；压力开口分开法向与切向；楔面SA明确壁距包含滑移固壁；LES明确固定物理滤波长度、模型、测试滤波与输出身份；可压k–ε明确总能量定义；火焰统一原子量保证化学计量质量/元素守恒，惰性N2无反应源。上述属于明确的题面规范化，不宣称逐格复现源软件reference；逐题改编依据保存在相应author/source.json。

## 实际文档验证

- `python qbank/02-fluid-mechanics/2.12-foambench/author/verify_statements.py --output runs/foambench-import/final-structure.json`：126题来源身份、prompt、公开入口、本地链接及JSON片段核查通过；462条本地链接、102个JSON代码块。
- `python .agents/skills/caeoj-author-question/scripts/check_statements.py --section qbank/02-fluid-mechanics/2.12-foambench --output runs/foambench-import/final-static.json`：126题双文件静态检查通过。
- 固定源revision实际下载，SHA-256校验通过；`author/rebuild.py`全量重生成前后392份节内文件字节一致（涵盖252公开文件、来源与维护文件；不含后补审阅索引）。
- `git diff --check`通过。逐题最终公开材料和source.json摘要见[覆盖索引](foambench-20261019/coverage.json)；独立完整覆盖记录摘要同存该索引。

这些检查只验证文档、来源与可重建性，不证明模型数值适定或参考正确。

## 本次未进行

未制作problem.json、Gmsh、HDF5、公开样例、隐藏输入或reference；未注册新模型检查器、评分配置及运行装配；未执行求解器、LLM考生或benchmark；未创建或更新HF分支/main。数值阈值、资源、模型参考及运行环境未校准。本批是题面与接口文档交付，不是可运行评测发布。后续需分别完成协议实现、实际制数与独立数值验证、资源和精度校准、正式配置及发布验证。
