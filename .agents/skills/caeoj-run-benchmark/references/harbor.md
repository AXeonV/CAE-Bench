# Harbor 命令与监控

用于实际执行时核对命令和进程；本机 `harbor --version`、对应 `--help` 及实际配置为依据。题目资源和装配规则见[评测维护说明](../../../../qbank/maintenance/EVALUATION.md)，本页不另存参数默认值或资源表。

## 运行入口

当前任务路径为 `runs/harbor/tasks/<slug>`；以下模板填入已确认参数：

```sh
harbor run --path runs/harbor/tasks/<slug> --env docker --agent <agent> --model <model> --n-attempts <attempts> --n-concurrent <concurrency> --job-name <run-id> --jobs-dir runs/harbor/jobs
```

`--n-attempts`／`-k` 为独立尝试，`--n-concurrent`／`-n` 为并发，不代表 solver 线程数。适配参数通过 `harbor agent schema <agent>` 核对再用 `--ak key=value`，不能假定各模型支持相同推理选项。`--print-config` 或 `--dry-run` 只提供实际覆盖范围内的解析证据，不代表容器或 trial 已运行。

逐例 solver 限额与 Agent、构建及总 verifier 预算分开核对，命令覆盖不得改变公开资源承诺。默认不启用上传、公开分享或云端启动选项。

## Viewer 与进程

在执行主机显式启动：

```sh
harbor view runs/harbor/jobs --jobs --host 0.0.0.0 --port 8080
```

`--jobs` 支持空 jobs 根目录，单端口冲突应明确失败。`0.0.0.0` 是监听地址，用户访问 `http://127.0.0.1:8080` 或执行主机可达 IP；不自动改防火墙或建公网隧道，本机健康检查不证明跨主机可达。

必须核对 `/api/health` 的健康状态、`/api/config` 的绝对 folder 和 jobs 模式，以及 `/` 的实际 HTML 页面。缺前端静态资源时按本机安装／构建方式修复，API 存活或端口可连接不代表页面可用。

POSIX 可用本技能脚本，默认状态和日志位于 `runs/harbor/monitor`：

```sh
python .agents/skills/caeoj-run-benchmark/scripts/viewer.py start --jobs-dir runs/harbor/jobs
python .agents/skills/caeoj-run-benchmark/scripts/viewer.py status --jobs-dir runs/harbor/jobs
python .agents/skills/caeoj-run-benchmark/scripts/viewer.py stop --jobs-dir runs/harbor/jobs
```

Windows 用原生进程工具完成相同验证，后台启动使用隐藏窗口并记录 PID、命令和日志。只复用可确认同一 jobs 根目录的服务；端口被无关进程占用时给处理选项，不杀进程或擅自换端口。远程 URL 属于远端主机，转发须使用已授权连接并说明地址在哪台机器有效。

## 结果与续作

检查 job 的 `config.json`、`result.json` 和所有 trial；仓库 judge 在 `verifier/report.json` 提供逐例状态与错误，`reward.txt` 为汇总通过比例。缺报告或覆盖不足时不能只凭 reward 判完成。

坏输入、参考或配置归基础设施问题；当前 grade 返回退出码 2、score 为 null，Harbor judge 中止，不按 solver 零分处理。具体失败状态仍核对实际报告。

执行 `harbor job resume` 或重判前，核对筛选、重试及是否再次调用 Agent；冻结提交重判不自动重新生成 solver。记录进程身份并保留失败证据，默认保留监控供用户回看。
