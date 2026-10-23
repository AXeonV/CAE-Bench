---
name: caeoj-author-question
description: 为 CAE-Bench-OJ 规划并编写单题、节或章，协调 DATA 设计、独立设计审阅与考生审阅；适用于新题建设和题面重构。
---

# 出题

从真实开源求解器 issue 建设源码修复题时，来源、缺陷复现与可信编译要求见 [caeoj-author-repair-question](../caeoj-author-repair-question/SKILL.md)；题面和审阅仍按本流程完成，已完成的来源工作无需重启。

读取 [题库哲学](../../../qbank/PHILOSOPHY.md)、目标章／节规划和[出题工作流](../../../qbank/design/AUTHORING.md)；具体设计疑问再查[经验清单](../../../qbank/design/AUTHORING-LESSONS.md)。本技能拥有任务目标、能力范围、建模／方法责任、资源及评价设计。

1. 明确目标清单、交付阶段和数据是否在范围内。上级规划不足时，先按“章内各节 → 目标节逐题清单”补足必要范围，保存到 `qbank/design/` 并更新索引；不展开无关节。既有决定冲突或关键目标无法判断时提出具体选项，常规设计自主推进。评价按题目选择全场、观测点或二者结合，核对其与考察目标和可信参考覆盖相符；算例差异及参考来源要求由下述算例建设流程拥有，不以相似工况数量代表能力覆盖。
2. 规划与能力清单形成后调用 [caeoj-design-review](../caeoj-design-review/SKILL.md)，处理设计意见，再编写 instruction.md。
3. 调用 [caeoj-design-data](../caeoj-design-data/SKILL.md) 完成自包含 DATA.md，联合处理题面与接口问题。实现归属按[核心与扩展职责](../../../qbank/design/CORE-AND-EXTENSIONS.md)，公开边界按[公开接口](../../../qbank/design/PUBLIC-INTERFACE.md)。
4. 核查题面、DATA 和工具支持一致，运行下述静态检查；调用 [caeoj-candidate-review](../caeoj-candidate-review/SKILL.md)，默认题面模式。可复用 DATA 流程对同一最终版本的审阅；修订后复核受影响内容。设计目标改变时也复核设计。
5. 按用户阶段交付。涉及已有数据时交 [caeoj-data-review](../caeoj-data-review/SKILL.md)；要求评测配置时交 [caeoj-configure-judge](../caeoj-configure-judge/SKILL.md)。用户要求实际算例建设时交 [caeoj-source-cases](../caeoj-source-cases/SKILL.md)；数据制作和正式评测仅在任务包含时执行。

考生解释性材料仅为本题 instruction.md、DATA.md 和通用 CONTRACT.md；各自职责见出题工作流。设计审阅与考生审阅使用独立上下文，不能向考生补充作者解释或设计报告。

当前公开samples统一为随机格式输出：题面明确编号、只保证结构/dtype/IDs/时间轴以及不保证数值答案正确，不能只依赖作者manifest或包README说明。样例不带reference/或数值判分命令；正式case的隐藏参考仍须按数值规则验证。核对题面具备真实入口命令、参数和路径基准，维护checkout、生成器与最终公开包同步修订。

整章任务先列全目标，再按节或协议依赖分批实施。记录各项规划、题面、接口、审阅、配置、数据及未决状态；续作核对实际文件与记录。最后检查跨节覆盖、编号、重复和公共语义；共享接口变化时复核所有受影响题目。缺数据不阻止题面交付，但不能宣称数据就绪或正式发布。

题面阶段使用：

```sh
python .agents/skills/caeoj-author-question/scripts/check_statements.py --section qbank/<chapter>/<section> --output runs/authoring/<section>/static.json
```

脚本只检查节下直接题目目录的双文件、常规内联链接和 JSON 片段；不验证纯文本依赖、物理自包含或数值正确性。仅规划时无需运行。维护方还须按 [DATA 验证流程](../caeoj-design-data/references/workflow.md)核对契约与实现。

交付题目及必要规划、审阅意见处理和验证证据；逐阶段报告实际完成范围及未决项。维护记录保留理由和证据，公共说明只链接其权威位置。
