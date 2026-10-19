# 题内数据池

HF仓库为[jimzhouzzy2006/CAE-Bench-OJ](https://huggingface.co/datasets/jimzhouzzy2006/CAE-Bench-OJ)。每个 case 在逻辑上为自包含目录；小池可直接保存以下布局，大池按下文分片保存同样的文件：

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

当前选择schema_version为4；直接目录池索引为3，分区池根索引为4；case 描述仍为3。描述恰含schema_version、case_id、origin、files、input、reference、example。files的每项为size_bytes和sha256，路径仅位于input/或reference/；两组files无重叠且完整覆盖。example为null或参考组中一个满足完整提交契约且通过本例评价的文件路径，不另存重复样例目录。

有来源证书时，origin.certificate_identity保留受支持的来源身份及契约／工具摘要。归档文件可用source_id、source_md5、sample_index识别轨迹；HF来源可用source_repository、source_sha256、sample_index识别轨迹，并保存source_file和固定source_revision用于定位。SHA256为上游文件内容身份，不标成MD5；同内容换文件名或提交不构成独立轨迹。元数据中的上游摘要不代表已经下载并验证整文件，实际获取范围及载荷核验另记作者证据。

input.complete表示输入资产齐全；reference.complete表示配置和全部参考资产已通过case评价预检，不能仅按reference.h5存在判断。描述不是科学认证，获取及正式消费仍重做预检。索引保存发现与完整性摘要，选择保存明确case ID、描述路径及摘要，不由索引重排或随机种子改变。

## 装配与消费

默认获取输入及整个参考组，固定同一个HF提交，逐文件核对大小和摘要，再按契约预检。测试装配到cases/<编号>/和reference/<编号>/；样例装配到samples/<编号>/input/与reference/，声明example时同时装配output/result.h5。稀疏参考不会自动变成完整提交示例。

相同文件跳过，差异先停止，显式更新才覆盖；暂存、预检、提交失败回滚，回执最后更新。只删除未被用户修改的已管理旧文件，不静默删除未知文件。离线verify从SHA绑定描述推导预期，不信任回执中可修改的文件摘要。

公开包仅包含三文件契约、样例输入／判题材料、已提供的正确提交示例和必要工具；整题选择、隐藏reference、作者材料不进入Agent镜像。Harbor将所选测试及参考单独装入verifier，求解器只收到input。HF公开不改变此材料边界。

本地数据为按需装配结果，不要求常驻；清理前确认远端已验证。只维护最新格式和数据，不提供运行时兼容分支。版本修订需完整迁移已有case与选择，保留输入和判分含义，再验证真实消费链。

操作见[数据池操作](../maintenance/DATA-SYNC.md)，评分机制见[判题说明](../../docs/GRADING.md)。完整性、契约、数值精度和资源分别验证。测试与样例显式选择同一 case ID 和描述绑定时，视为参与计分的公开“送分样例”，通过严格核验并以 public_cases 单列；计入测试总数与分数。测试内部、样例内部的重复，及不同池条目的重复输入／来源轨迹仍拒绝。公开样例身份不能把其他相关轨迹变成独立测试。

## 大池的分片与分区索引

`pack --shard-mib 128` 制作物理分片；不加参数仍制作直接目录池。两者保持同样的 case ID、描述和载荷字节，消费方自动识别。TAR 以完整 case 为边界，单例过大时可超过目标；当前单例下载所在整片，缓存复用，不支持 HTTP range。按下载粒度需要可降低分片目标。

分区池的 `pool/index.json` 使用 schema_version=4、kind=partitioned-case-pool，只拥有总条数和至多 64 个哈希分区的路径、大小、摘要与条数。分区位于 `pool/partitions/<bucket>/<sha256>.json`，按 case ID 的首字节除以 4 路由；每条绑定 case 描述摘要、完整性、描述 JSON 和不可变批次 transport。描述在分区中重复其规范 JSON 表示，读取时重算摘要；选样只读取根和所需分区，不下载 TAR。每次按固定提交读取，不靠分区顺序确定选样。

批次资产位于 `pool/batches/<catalog-sha256>/`，包含 transport.json、批内 index.json、selection.json、TAR 及 locator。批内沿用已验证的 TAR 目录格式；transport 绑定分片与 locator，locator 绑定成员路径、大小、摘要。禁止链接、重复或未声明成员；归档先核对整体摘要，再按成员位置读取并验证。历史试验路径的 `ShardStore` 不承担生产池发现。

上传先完整消费全部索引条目并验证默认选择，再以分组提交暂存不可变批次资产，最后将变动分区和根索引在同一父提交上原子发布，保留其他批次。同身份重复发布保留原传输绑定，未变分区不改写；相同输入但参考/评分发生变动须显式 `--update`。提交冲突、未知提交结果或不可变资产差异停止；重新运行前先核对远端身份，不能盲目重试。

直接目录池与分区池分别有明确格式；上传不会自动将已有目录池升级为分区池。迁移已有池须显式制备、验证和审阅，再切换根索引；不能混合两种根。正式选择格式及离线回执保持不变，分片/分区只是物理存储与发现机制。
