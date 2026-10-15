# 当前 Harbor 后端线索

2026-10-16 核对执行机安装的 Harbor **0.24.0**：CLI --help 及安装包 `harbor/cli/view.py`、`harbor/viewer/server.py`。本页不是未来版本的固定协议，执行时先核对安装版本与参数；不同主机须分别核查。

## 运行入口

- 维护准备：`src/utils/publish_dist.py --task <slug>`，随后 `src/utils/prepare_harbor.py --task <slug>`；本地公开ZIP和任务目录必须一致，不能沿用README历史嵌套路径。
- 当前生成目录：`runs/harbor/tasks/<slug>`。
- `harbor run` 是 `harbor job start` 别名。0.24.0支持 `--print-config` 查看解析后的JobConfig；`--dry-run` 不运行trial，需核对实际输出是否覆盖所需本地任务。
- 重复为 `--n-attempts`／`-k`，并发为 `--n-concurrent`／`-n`。单题 `-k 3 -n 1` 表示三次独立尝试串行执行，不是一个solver使用三个线程。
- 模型与适配器：`--agent`／`-a`、`--model`／`-m`；适配参数可用 `--ak key=value`，须核对 `harbor agent schema <agent>`，不要假设每个agent都支持相同推理参数。

命令模板（仅说明字段，调用时填写已确认值）：

```sh
harbor run --path runs/harbor/tasks/<task> --env docker --agent <agent> --model <model> --ak reasoning_effort=<effort> --n-attempts <attempts> --n-concurrent <concurrency> --job-name <run-id> --jobs-dir runs/harbor/jobs
```

长参数 `--path`、`--env` 等须以本机help为准，不能因为短参数历史可用便照抄。用户未要求时不使用 --upload、--launch、--public 或云端分享。凭据使用运行环境既有安全配置，不放入参数记录。

## Viewer

安装版默认：host=`127.0.0.1`，port=`8080-8089`。本技能为了保证用户在默认端口访问，显式使用：

```sh
harbor view runs/harbor/jobs --jobs --host 0.0.0.0 --port 8080
```

--jobs 使空目录也能启动，不依赖自动推断。--port单值使冲突明确失败，不静默回落8081。--host 0.0.0.0监听执行主机IPv4接口，浏览器访问本机127.0.0.1或该主机实际本地IP；不是公网发布。

实际ready核对：

- `/api/health` 返回 status=ok。
- `/api/config` 的 folder 是预期jobs绝对路径，mode=jobs。
- `/` 返回HTML页面；没有前端static资源时Harbor可能只启动API，不能报“监控页面可用”。先检查安装的 viewer/static/index.html，必要时按该版本 --build／安装方式修复；不启动与任务无关的长期dev服务器替代。

POSIX辅助脚本只负责受控进程生命周期和当前三个接口检查，不代替Harbor。若未来版本改变接口，查真实新接口后修脚本和测试，不放宽成“端口能连接即ready”。Windows用原生进程管理、同样的HTTP核查和已核对命令，脚本会明确拒绝不支持平台。

## 结果与续跑

job根下的 config.json／result.json 与各trial产物应相互核对；名称／schema以实际版本为准。仓库 judge 的 trial verifier/report.json 提供逐例状态、分数和错误，reward.txt 是汇总通过比例；没有report或覆盖不足不能仅凭reward认定完成。

当前 judge 入口为 `src/utils/harbor/tests/judge.py`。题目、参考或运行框架错误的 score可为null，不能按零分solver失败处理。重复统计包括每次尝试，基础设施补跑不得冒充新的独立样本或只取最佳值。

`harbor job resume`、regrade的具体筛选、重试和是否重新调用agent必须看当前help／源码。已有冻结提交的重判不自动重新生成solver。监控默认继续保留，只有用户要求或本次失败测试清理才停止明确属于自己的进程。
