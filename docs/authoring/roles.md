# 角色工单与文件所有权

所有角色都先读 README、CONTRACT、GRADING、已有题目组织、适用的 AGENTS.md 与审计 skill。titan 当前仓库及祖先没有 AGENTS.md；适用 skill 为 `.agents/skills/caeoj-audit-data/SKILL.md`。禁止求解器评测、参赛 Agent、完整精度测试，以及把未执行检查标为通过。

| 角色 | 模型 | 本次子 Agent | 写入范围 | 完成证据 |
|---|---|---|---|---|
| 主协调 | 当前主 Agent | /root | docs/authoring、发布门槛、workflow、提交 | state.json、PR、运行记录 |
| 来源发现 | gpt-6-luna | /root/discovery | /tmp 来源证据，最终由主 Agent 导入注册表 | 实取文件大小、SHA、固定版本、官方入口 |
| 出题 | gpt-6.1-sol | /root/author | 两题 instruction/DATA/DESIGN/TEST-CASES/README | 数学/工程模型、支持范围、连续含义 |
| 数据准备 | gpt-6.1-sol | /root/data | fetch.py、两题 author/cases/samples/reference | sample/selected/all 工具、映射、结构校验 |
| 独立审查 | gpt-6.1-sol | /root/review | docs/authoring/reviews/initial、recheck | 全输入 inventory、意见及复查 |
| 独立终审 | gpt-6.1-sol | 终审时独立派发 | docs/authoring/reviews/final | 实际 Draft PR 和全部产物 |

## 来源发现工单

实际读取官方网页和数据入口，不能仅靠摘要。记录 URL、版本/commit、获取方式、最小下载量、输入/参考输出、参考依据、代码/数据各自许可、待确认项。先筛选结构验证和公开参考数据各一例；材料不完整时保留失败证据后替换候选。

## 出题工单

编写可冻结后读取多个输入的问题族，逐项明示来源支持、OJ 新增定义、尚缺验证。物理变化与编号/文件名变化分别记录。明确模型、几何、材料、本构、边界/初值、单位、输出位置时刻；不用源单例标答猜测参数族。数学正确的解析方法与任意核心语言/算法/库均可使用，包装器遵循已有提交接口。

## 数据准备工单

先实现统一入口再实跑 sample。固定哈希，缓存每次检查，支持 Range 续传且验证响应，限制下载字节及时间。归档安全选择性提取，明确最小下载量。保留 source row/element 到 OJ 数组、IDs、位置及单位映射；禁止未经证明的插值/缩放答案。pending 输入只结构检查不数值评分。

## 独立审查工单

按 caeoj-audit-data 实跑 inventory，遍历全部输入分支，建立 key→DATA→语义→文件证据覆盖表；对照数学、来源、单位、参考可靠性、样例/隐藏分隔、生成器/下载器、判分门槛、防御性文字和题面无关信息。意见写 id、file/location、problem/evidence/impact/revision_required/status，作者分别修订，原审查者逐项复查，最多两连续轮。

## 独立终审工单

重新读实际提交/PR diff、所有新文件和 ZIP manifest，不只读聊天摘要。独立验证源文件/映射、公开包无 author/reference/cases/pending、静态检查日志真实，遗留项正确进入队列。明确结论适用范围；无数值证据不能标成正式可评测。
