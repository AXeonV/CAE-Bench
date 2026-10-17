# 题内数据池

HF仓库为[jimzhouzzy2006/CAE-Bench-OJ](https://huggingface.co/datasets/jimzhouzzy2006/CAE-Bench-OJ)。一个case一个自包含目录：

```text
qbank/<章>/<节>/<题>/pool/
  index.json
  cases/<case-id>/
    case.json
    input/problem.json
    input/…输入资产…
    reference/grading.json
    reference/reference.h5
    reference/…配置声明的观测资产…
```

HF保存所有实际输入和判题数据，包括JSON、网格、数组及CSV，不按大小区分。共享代码和可信评价器在代码仓库；HF配置只选择已安装标识，不包含脚本、导入路径或跨case依赖。作者来源、解析与验证证据在本题author/data-evidence；制数模板在author/grading-template.json，均不进入考生材料。

## 身份和文件绑定

题目稳定ID由data-manifest.json唯一拥有。case ID由输入文件路径和SHA-256集合确定，与测试／样例角色无关；同输入复用case。仅修改评分或参考保持case ID，但必须更新描述摘要和选择。题意实质变化需新题ID。

当前选择schema_version为4；池索引和case描述均为3。描述恰含schema_version、case_id、origin、files、input、reference、example。files的每项为size_bytes和sha256，路径仅位于input/或reference/；两组files无重叠且完整覆盖。example为null或参考组中一个满足完整提交契约且通过本例评价的文件路径，不另存重复样例目录。

input.complete表示输入资产齐全；reference.complete表示配置和全部参考资产已通过case评价预检，不能仅按reference.h5存在判断。描述不是科学认证，获取及正式消费仍重做预检。索引保存发现与完整性摘要，选择保存明确case ID、描述路径及摘要，不由索引重排或随机种子改变。

## 装配与消费

默认获取输入及整个参考组，固定同一个HF提交，逐文件核对大小和摘要，再按契约预检。测试装配到cases/<编号>/和reference/<编号>/；样例装配到samples/<编号>/input/与reference/，声明example时同时装配output/result.h5。稀疏参考不会自动变成完整提交示例。

相同文件跳过，差异先停止，显式更新才覆盖；暂存、预检、提交失败回滚，回执最后更新。只删除未被用户修改的已管理旧文件，不静默删除未知文件。离线verify从SHA绑定描述推导预期，不信任回执中可修改的文件摘要。

公开包仅包含三文件契约、样例输入／判题材料、已提供的正确提交示例和必要工具；整题选择、隐藏reference、作者材料不进入Agent镜像。Harbor将所选测试及参考单独装入verifier，求解器只收到input。HF公开不改变此材料边界。

本地数据为按需装配结果，不要求常驻；清理前确认远端已验证。只维护最新格式和数据，不提供运行时兼容分支。版本修订需完整迁移已有case与选择，保留输入和判分含义，再验证真实消费链。

操作见[数据池操作](../maintenance/DATA-SYNC.md)，评分机制见[判题说明](../../docs/GRADING.md)。完整性、契约、数值精度和资源分别验证。测试与样例显式选择同一 case ID 和描述绑定时，视为参与计分的公开“送分样例”，通过严格核验并以 public_cases 单列；计入测试总数与分数。测试内部、样例内部的重复，及不同池条目的重复输入／来源轨迹仍拒绝。公开样例身份不能把其他相关轨迹变成独立测试。
