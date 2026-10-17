# 算例制作与溯源

[caeoj-source-cases](../../.agents/skills/caeoj-source-cases/SKILL.md)负责把指定题目的具体工况和参考制作成可验证 case。HF 存储格式由[数据池设计](../design/DATA-STORAGE.md)拥有，制池、上传及装配命令由[数据池操作](DATA-SYNC.md)拥有，实际接口审计复用[数据审计技能](../../.agents/skills/caeoj-data-review/SKILL.md)。本流程不运行 LLM 考生，不自动加入正式选样。

## 确定来源并取得结果

从题面与 DATA 的合法范围选择工况，核对几何、参数、边界／初态、采样、输出及公开评价含义。可采用文献、数据集、公开报告或实际求解器计算；用户指定来源或求解器时按该指示执行，不能以另一来源替代后仍声称完成原要求。来源中未给出的建模假设必须有公开题意依据。

来源记录区分三种角色：工况出处、参考值生产者、独立验证依据。文献给工况、求解器生成参考、文献曲线用于验证时，分别归属，不把求解器全场标作文献解，也不把与同一参考自比较称为独立验证。

按来源保存足够精确的定位与复现证据：

| 取得方式 | 必要记录 |
|---|---|
| 文献／报告 | 作者、题名、DOI 或稳定链接、版本、表／图／页及工况编号；取点方法、坐标标定和取点不确定度 |
| 数据集 | 仓库与固定版本、文件／轨迹／切片编号、原始文件摘要、获取与再分发条件 |
| 求解器计算 | 求解器版本及构建／依赖、可复现输入与命令、网格、物理与离散配置、收敛／终止条件、实际运行和输出摘要 |

只记录与本例有关的内容。原始大文件可通过固定版本和摘要重取；需要保存的配方、转换脚本和精简证据留在 author/。受限原始材料不随公开数据上传，说明取得方式与可公开的派生范围。不记录令牌、认证链接或机器私有凭据。

## 转换、参考和验证

保留原始身份到本题输入／参考的映射：单位、坐标系、tag、时间、分量、区域、符号、压力基准和归一化。任何截取、重采样或重建均记录方法与参数；文献误差、取点误差和数值误差分别说明。来源只有中线或其他稀疏数据时，参考完整性按实际评价计划判断，不填充未提供的全场值。

运行指定求解器并取得输出；按问题风险选择网格／时间收敛、守恒、解析解或独立数据比对等证据，不机械要求所有方法同时执行。成功退出、低残差和格式合法都不单独证明参考准确；用户指定的求解器也需说明验证依据和局限。资源不足、计算失败或未收敛时保留配方与真实状态，不把未执行步骤写成完成。

用实际输入与参考预检 case 判题计划，并验证实际读取、输出契约和判分；有完整提交可运行参考程序检查正例，按判据选择有区分力的错误输出。稀疏参考不能冒充完整候选输出；没有完整候选时明确未执行的完整提交验证。共享评价能力按[判题说明](../../docs/GRADING.md)实现，不在 HF 携带任意代码。

将本批全部实际输入、参考与已声明公开输出交数据审计，对照题面／DATA／CONTRACT 处理问题。数值验证与接口审计分别记录；不运行 LLM，也不以 benchmark 成绩反向调整参考或阈值。

## 证据关联与入池

在本题 `author/data-evidence/` 保存来源定位、制作与验证记录，以原始资产摘要、输入文件摘要、生成脚本／配置版本、池 case ID 和描述摘要关联；上传后补充 HF 提交，代码提交绑定维护配方。既有证书沿用工具支持的输入绑定，不手改 pool schema 或虚构通用来源字段。当前 case 描述的 origin 保留工具生成的输入身份及已支持的证书身份；任意文献的详细溯源依靠作者证据与 case 的摘要关联，不声称 HF 描述独自包含完整文献记录。

只把可直接消费的输入、配置、参考／观测和已声明示例纳入池，作者报告留上传树之外。通过现有工具 `pack --source <本批生成目录>`、审核 bundle、`upload` 并固定实际远端提交重新获取核验。相同输入身份可更新参考；远端有差异时按数据管理流程审核并显式更新，不因追加 case 覆盖其他条目。

**入池不等于选样。** `pack` 产出的 selection.json 是本批验证选择，不自动替换本题 data-manifest.json；保留既有 cases／samples 映射及其绑定。题目首次入池先在无清单时用 `pack --task-id <新编号>` 检查身份唯一性；上传后从 staged selection 派生定位清单并清空 cases／samples，可建立包含现行 schema_version、task_id、仓库／池定位及 `cases: {}`、`samples: {}` 的空选择清单，复用当前 selection 格式；这只登记数据位置，不把新例纳入默认评测。

首次登记清单的结构示例（编号和路径须按实际题目分配；不复制示例编号）：

```json
{
  "schema_version": 4,
  "task_id": "caeoj-000123",
  "repository": {
    "repo_id": "jimzhouzzy2006/CAE-Bench-OJ",
    "repo_type": "dataset",
    "path": "qbank/02-fluid-mechanics/2.1-single-phase-flow/newtonian-incompressible-steady-2d"
  },
  "pool": {"index": "pool/index.json"},
  "cases": {},
  "samples": {}
}
```

审计本批时记录隔离的生成／装配位置，避免拿只含正式选样的目录代表新增批次。当前 CLI 的 assemble/verify 只消费 canonical 清单，不能用 `--manifest` 把装配输出重定向到临时目录；隔离核验复用现有 Python API，不另写同步实现：

```python
from pathlib import Path
from caeoj_tools import data_pool as pool

bundle = Path("work/case-pool")
choice = pool.manifest(bundle / "selection.json")
check = Path("work/case-pool-check")  # 使用新的空目录
check.mkdir(parents=True)
pool.write_json(check / "data-manifest.json", choice)
pool.assemble(check, choice, pool.LocalStore(bundle / "repository"))
pool.verify(check, strict=True)
```

上传后的远端复核换一个新验证目录，将 store 换为 `pool.HubStore(choice["repository"]["repo_id"], revision=hf_commit, cache_dir="work/case-cache")`，其中 hf_commit 为 upload 返回的实际提交。其余步骤相同，不能仅核验本地 bundle 后声称远端已验证。完整角色语义见[数据池操作](DATA-SYNC.md)。记录数值、完整性、入池和未完成项；清理缓存／中间件前先保留配方及证据并确认远端载荷完整。

## 后续 benchmark 选样

交付每例 case ID、描述摘要和固定 HF 提交，并给出临时选择命令，例如：

```sh
python -m caeoj_tools.cli data select --task <task> --revision <HF提交> --case '001=<case-id>' --output work/<task>-selection.json
```

此命令只生成明确列出的选择，不启动模型；未列出的角色不会自动保留。以后用户运行 benchmark 时，再审核并采用此次运行的选择，按[运行技能](../../.agents/skills/caeoj-run-benchmark/SKILL.md)装配、严格核验和冻结；仅入池本身不授权这些后续步骤。
