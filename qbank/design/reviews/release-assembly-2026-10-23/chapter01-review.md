# 第0、1章发行候选组装交接

本轮只使用本地缓存、原生成器、既有源数据checkout与既有Docker镜像；没有下载、付费模型调用、修改原题选样或重算PDE科学参考。15题统一入口为 `release-plan-fragment.json`；机器审计为 `ch01-report.json`。

| 范围 | 题数 | 正式case角色 | 公开样例角色 | 消费核验 |
|---|---:|---:|---:|---|
| 第0章 | 2 | 17 | 3 | 当前工具pack/assemble/strict verify及公开包验证通过 |
| 热传导 | 2 | 56 | 4 | 本地HF cache组装+strict verify；稳态Linux新4秒32/32，瞬态Windows原5秒24/24 |
| PDEBench | 11 | 210 | 22 | 原checkout backend全量strict verify；210/210正式reference自判分 |

## 素材位置

- 第0章及热传导完整轻量source_root：`runs/release-assembly/ch01/stage`。题面、DATA、配置、运行时静态材料及装配数据均在此；新公开ZIP位于 `public/`。
- PDEBench source_root：`D:/Code/CAE-Bench-OJ-ch02-benchmark`。复用其中原公开ZIP、装配数据、原runtime和manifest。没有复制约8GiB正式数据。
- 新公共材料全部由现publisher生成并执行其运行时验证；ZIP均为普通文件，没有symlink。

## 修订与限制

1. `smoke-test`由原生成器重放原11个alias，部分mesh/input字节改变，因此部分case ID改变。`chapter0-fixture-revisions.json`记录生成器SHA、原manifestSHA与逐例ID映射。仅发行stage增加公开样例01，显式复用正式01-line-1d同一case；未新增独立case，未改源manifest。
2. `case-grading-test`原6正式与2样例case ID均保留；描述摘要重生，新manifest只在stage。
3. 稳态热传导原1秒预算Windows有5例timeout，既有Linux Docker bind环境32例均timeout。诊断15秒上限运行32/32数值通过，最大实测1.941757511秒。按ceil(2×max)发行stage改为4秒，保持0.01K阈值和32例选样。题面、README、judge-config同步4秒；Harbor verifier由现有prepare_harbor按配置和32例自动推导为4268秒，对应300+32×(4+60+60)。随后原check在相同Linux2CPU/1GiB、4秒限制实际32/32通过。原1秒失败记录保留，不能宣称原预算通过。
4. 瞬态热传导原5秒限制Windows实际24/24通过，最大实测约2.43秒；此结果不构成所有团队机器的性能保证。
5. PDEBench11题保留provisional评分/资源profile，参考自判分仅证明契约及评分消费链，不证明独立数值误差或资源校准完成。当前main backend拒绝原format样例manifest扩展；使用原checkout backend已经全量strict通过，未强行迁移其数据协议。
6. `PDEBENCH-NOTICE.md`依据冻结DESIGN记录保留PDEBench/DaRUS V8 DOI、CC BY4.0署名与转换说明，随原Apache-2.0 LICENSE供总装。数据许可不被扩展解释为生成器代码许可。

最终公开包SHA及许可证路径以 `release-plan-fragment.json` 为准。`public-report.json`保留最初publisher尝试记录；smoke增公开role及稳态4秒修订分别以 `smoke-public-revision.json`、`steady-resource-revision.json` 的后续结果为准。

## 关键证据

- `verify-report.json`：当前backend检查及热学装配结果。
- `chapter0-preparation.json`、`chapter0-fixture-revisions.json`、`smoke-public-revision.json`：有限生成、显式选样和公开包。
- `external-backend-verify.json`：原PDE backend11题实际strict通过。
- `pde-reference-replay.json`：逐例210项评分消费结果，全部accepted。
- `baseline-steady/report.json`、`baseline-steady-linux/report.json`：原1秒预算失败证据。
- `baseline-steady-numerical/report.json`：单进程独立baseline32/32数值通过，不宣称startup预算。
- `baseline-steady-linux-diagnostic/report.json`：完整32例15秒诊断，含逐例wall。
- `baseline-steady-linux-4s/report.json`：修订预算真实32/32通过。
- `baseline-transient/report.json`：24/24真实逐例执行、评分与资源测量。

本子任务无剩余运行进程或未完成数据构建。主代理负责总装源root混合、独立解压安装检查和最终目录冻结。
