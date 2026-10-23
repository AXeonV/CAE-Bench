# RC2 范围独立复核

状态：实际 RC2 的范围及元数据完整性复核通过；数值资格、题面审阅与异机验收不在本次结论内。

## 范围及算术

- RC1 实际 catalog 为 41 题、327 正式 case 角色、55 样例角色：第0章2、第1章13、第2章26。
- 用户范围文件包含43个唯一流动能力题；其中2个已在RC1，新增41题恰好都在RC1排除表中。
- RC2 预期集合 = RC1全部41题 ∪ 范围文件43题 = 82题。不可因参考资格待验证而再次删除这些已授权纳入题。
- 2.1.1、2.1.3分别保留用户确认的既有10例身份及顺序；大池100/72例不替换这两套选择。
- 新增选样预期 = 38题既有309例 + 2.2.9四例 + 2.2.11三例 + 2.4.4四例 = 320例。总正式角色预期647。
- 样例角色预期96，以实际 manifest/catalog 确认为准；样例及正式角色可能身份重叠，不能相加称独立工况。
- RC1排除211项应去除新增41流动题，剩170项：FOAMBench有case但待资格51 + 无case97 + 修复题22。

## 产物验收口径

1. 精确核对82题集合、唯一task/task_id/path，无纳入与排除冲突；固定20例选择与原始范围逐项一致。
2. 新增41题 catalog 的 profile/limitations 忠实说明候选参考未验证；不得将完整性校验描述成数值资格或异机验收。
3. 检查647/96角色、每题选择、元数据与公开/私有边界、许可及SHA；对新三题检查真实输入/参考文件，与最近Titan证据可追溯。
4. 不实现快速判分、不调用模型、不修改RC1；完整运行器/修复接口仍未交付。
5. release.py 的 build 校验装配receipt、descriptor及资产逐流摘要，并检查公开包的清单、hash、无正式参考与元数据混入。独立复核仍需检查真实产物，不仅阅读实现。

## 材料基线

Git HEAD: 1f2b256c30b126b64c90c1482e21e618473d93a5

| 材料 | SHA256 |
|---|---|
| `qbank/design/release-flow-scope.json` | `941bba195e5ce2bbf4043e360ac5fd5888e958361526a32170636797f879d899` |
| `qbank/design/reviews/release-assembly-2026-10-23/catalog.json` | `bcfb81caee2525aa657edca68e0b5887beff4165df0306aff77afc5f2e30df9f` |
| `qbank/design/reviews/titan-inventory-2026-10-23/chapter02-current.json` | `4127b415d9009b82599c22f2b3628e1900ee2987c2048da5658f687cadcf6bea` |
| `src/caeoj_tools/release.py` | `4f27c810170b8aca24b30779197ee3e6844dccebc7cb398fcb907633a1d633ea` |

## release_notes 小改动复核

只读检查三个文件 diff，未发现阻塞问题。可选 release_notes 在写输出前校验列表及非空字符串项，省略兼容；catalog 与 README 都受原有产物 SHA 完整性检查保护。新增测试覆盖交付与空项拒绝。维护指南允许按用户确认范围纳入未验证审阅 RC，并明确不得称数值验收已通过。调用方报告26项测试25通过1跳过，本审阅未重复运行。

- `src/caeoj_tools/release.py` SHA256 `7aa1c5293f1ab979f316bb1cfb9e4dd14aabadf4c7d90fa4445ff1c25de158d1`
- `tests/test_release.py` SHA256 `4d1d925b9e1a047abcefd9acbe43b25f2bb58e1e478219bad47b36757545f984`
- `qbank/maintenance/RELEASE.md` SHA256 `92057cf9a05f81337857b2c6595e1ec8e69c27d8c75eafcc148663a9439d9218`

## 实际 RC2 最终复核

产物：`C:/Users/Jim Zhou/CAE-OJ-Releases/caeoj-qbank-20261023-rc2`。

- catalog 精确82题（第0章2、第1章13、第2章67），647正式case角色、96样例角色、170排除项；无任务ID/路径重复，无纳入与排除交叉。
- 新增41题全部保持 `unvalidated-reference-rc` 及资格缺口文字，release_notes 与 README 保留审阅RC及非数值认证说明。
- 对照冻结计划和源manifest确认全部case/sample选择；旧RC1所有41题选择不变，固定20例身份及顺序精确一致。
- qbank.zip 4222个成员与catalog文件集合完全一致，逐项大小一致；对1960个文本元数据逐项验证SHA256。
- 82个公开ZIP共2884个成员；清单集合一致，无作者目录、其他题、正式输入/隐藏参考、judge/manifest/Harbor私有配置混入；公开/私有重叠材料摘要一致。
- 117条许可原文记录逐项hash/大小验证并关联题目。此处只确认记录完整，不作第三方数据再分发权利法律认证。
- 未重复读取全部大型数值载荷；完整流式校验由协调方另行执行。未运行模型、求解器、重新验证数值或判定题面可接受。

机器结果：`plan-scope-review.json`、`final-scope-review.json`。catalog SHA256：`b22f75537116860a41ff7f99e9a34d838f957b93b9f36661a83e0804aaa41d17`。

本轮未发现范围或元数据装配的未决阻塞问题。后续题面/case联合审查与数值资格仍需实施，不能把该结论外推为正式Benchmark验收。
