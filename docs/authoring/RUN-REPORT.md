# 2026-10-14 首次自动化出题运行

仓库：titan `/home/zhouzhiyu/code/CAE-Bench-OJ-zzy`；分支 `feat/automated-authoring-pilot`。提交位置：[Draft PR #4](https://github.com/AXeonV/CAE-Bench-OJ/pull/4)，未合并。原 master 无未提交修改，保留；新分支从最新 origin/master 建立。

来源发现使用 6 Luna；出题、数据准备、独立审查及独立终审由不同职责的 6.1 Sol 子 Agent 执行。角色与实际阶段见 roles/state。每题独立提交；修订意见有 initial/recheck 记录，复查最多两轮；终审实际 PR 与全部产物，结果见 `reviews/final.json`。

| 题目 | 已准备来源 case | 公开样例 | 无参考候选 | sample/selected/all 最小源下载 |
|---|---|---|---|---|
| calculix-truss | 2 个，同一三节点两杆物理实例，原 tag／重编号 | 1 个，两杆轴向应力 | 2 个，E／载荷变化 | 12,636,197 B 验证归档，提取 393 B 输入、1,676 B 参考；不下载完整算例库 |
| pinnacle-poisson-cg | 3 个，同一固定四孔 Laplace 模型，64／591／591 原始观测行 | 1 个，64 点 | 1 个，孔径变化 | 85,477 B 文本，完整 1,246 点；不是规模更大的全仓库数据 |

两题已完成静态审查与小样本准备。登记的源文件已完整获取；all 只指各题清单（2／3 个源 case），不代表上游所有材料或新增参数族已具备参考。新物理参考、数值验收、阈值和资源校准、来源资产复用条件仍待确认，`release_ready=false`。

公开草稿：`dist/calculix-truss-draft.zip`、`dist/pinnacle-poisson-cg-draft.zip`。ZIP 允许列表仅包含题面、DATA、通用协议/校验工具及公开样例，MANIFEST.draft=true；不包含 author、reference、cases、pending、隐藏参考公式或维护审计报告。源参考公开可获取，接口变体不构成保密的物理测试覆盖。

## 运行命令

在 titan 仓库根目录：

```sh
PY=/home/zhouzhiyu/venvs/caeoj/bin/python
$PY src/utils/authoring/workflow.py status
$PY src/utils/authoring/workflow.py prepare
$PY src/utils/authoring/workflow.py package

$PY tasks/calculix-truss/author/prepare.py --mode sample
$PY tasks/pinnacle-poisson-cg/author/prepare.py --mode sample
$PY tasks/pinnacle-poisson-cg/author/prepare.py --mode selected --case source-002
# 全清单只在显式选择时执行：
$PY tasks/calculix-truss/author/prepare.py --mode all --allow-all
$PY tasks/pinnacle-poisson-cg/author/prepare.py --mode all --allow-all
```

`--cache` 可指定新缓存；从空缓存的一键 sample 下载、转换及校验已经实际执行，两题均 cache_hit=false。CalculiX 12,636,197 B／7.782 s，Poisson 85,477 B／0.696 s；时间只是本次网络获取用时，不是求解时限。data Agent 另有冷下载记录及独立哈希复核，见 cold-download.json。

## 实际检查及限制

全部 10 个输入（5 源 case、2 样例、3 pending）结构合法；7 个源/样例参考输出满足契约；两题 inventory 无材料缺口，盘点成功不代表数值验收。下载器 7 项测试、draft 发布门槛 2 项测试通过；原发布器 5 项、Harbor 工具 11 项既有单元测试用于通用工具回归，其合成程序运行不属于这两题的工程求解评测。

PINNacle urllib 冷下载曾两次超时；改用自动优先 curl 后成功，另一独立 curl 请求仍在 45 s 预算超时。网络有间歇失败，工具明确报错并保留 partial 供来源支持时续传；不保证每次成功。CalculiX 初次归档成员路径错误已修复。B32 beamlin 候选因其参考不能默默改成连续杆模型而替换为离散桁架。

未执行：参赛 Agent、两个候选的求解器、求解程序评测、完整数值精度测试、参考收敛验收、阈值与运行资源校准。新增物理输入没有补造答案，未进入参考 case 集。遗留项见 evidence-queue.json；正式发布与 Harbor 组装保持阻断。
