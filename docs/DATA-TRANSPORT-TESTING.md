# 本地目录、SCP 与 Hugging Face 传输测试

本指南用同一份 `smoke-test` 数据检查传输、装配、复用和损坏检测。通用配置、发布和版本锁定规则见[数据池操作](../qbank/maintenance/DATA-SYNC.md)。测试工具是 `src/utils/data_transport_lab.py`；它只提供本机只读 SSH 服务，接受临时测试密钥，支持 SFTP、旧 SCP 和恢复下载所需的受限块读取，不提供通用 shell。

所有命令使用 PowerShell，从项目根目录执行。准备数据、服务密钥、缓存和日志都位于 Git 忽略的 `runs/`。每次完整复现实验使用一个新工作目录；准备命令拒绝覆盖旧实验。

## 准备环境与数据

```powershell
$python = (Resolve-Path .\.venv\Scripts\python.exe).Path
$caeoj = (Resolve-Path .\.venv\Scripts\caeoj.exe).Path

# 只在测试环境安装；普通数据客户端不需要 Paramiko。
& $python -m pip install 'paramiko>=3.5,<5'

ssh -V
Get-Command ssh, scp, sftp

# 如果此题尚未装配，先从你有权限的来源获取，再严格校验。
& $caeoj data verify --task smoke-test --strict
```

SSH 传输会从 Python 的 `PATH` 解析 `ssh`、`scp` 和 `sftp` 的绝对路径，避免 Windows 原生库修改进程搜索路径后无法启动客户端。未安装客户端时会提示安装 OpenSSH 并加入 `PATH`；此时保留已有的部分下载文件。

准备工具使用项目中已经严格校验的原始字节，按现有锁文件重建镜像。若缺少数据，先按[来源配置与获取](../qbank/maintenance/DATA-SYNC.md#配置本地与云端来源)准备该题。HF 是否需要申请权限以仓库当时的访问设置为准。

```powershell
# 首次实验可使用这组路径与端口；若已有服务，改用新目录和空闲端口。
$lab = Join-Path $PWD 'runs\data-lab'
& $python src/utils/data_transport_lab.py --work-dir $lab prepare --task smoke-test --port 22222
$config = Join-Path $lab 'sources.toml'

& $caeoj data source list --config $config
```

生成的目录包括：

```text
runs/data-lab/
  repository/qbank/.../pool/    本地来源与 SSH 服务共用的发布数据池
  targets/local/               空数据、独立缓存的本地目录测试目标
  targets/scp/                 空数据、独立缓存的 SFTP 测试目标
  targets/scp-legacy/          空数据、独立缓存的旧 SCP 测试目标
  targets/hf/                  空数据、独立缓存的 HF 测试目标
  sources.toml                三类来源配置
  ssh_config                  独立 SSH 配置，不改用户 ~/.ssh/config
  known_hosts                 绑定本次生成的服务端公钥
  host_key, client_key        仅本实验使用的临时密钥
```

Windows 下准备工具会移除两个临时私钥继承的 ACL，仅授权当前用户，避免 OpenSSH 因权限过宽拒绝使用。重新创建实验时密钥也会改变，应使用同一实验生成的 SSH 配置。

## 启动本机服务

另开一个 PowerShell 窗口，在同一项目根目录执行：

```powershell
.\.venv\Scripts\python.exe src/utils/data_transport_lab.py serve
```

默认使用 `runs/data-lab`；指定其他实验时把 `--work-dir <路径>` 放在 `serve` 前。看到 `127.0.0.1:22222` 表示开始监听。关闭这个窗口中的服务可按 Ctrl+C。

回到原窗口验证密钥认证：

```powershell
ssh -F "$lab/ssh_config" caeoj-lab 'echo connected'
```

预期输出 `connected`。服务只绑定 `127.0.0.1`；不需要管理员权限或修改系统 sshd、防火墙。服务器仅允许读取实验数据池，上传和交互 shell 不属于此测试服务功能。

若使用后台方式启动，可以隐藏窗口并保留日志：

```powershell
Start-Process -FilePath $python -WindowStyle Hidden -WorkingDirectory $PWD.Path -ArgumentList @('src/utils/data_transport_lab.py', 'serve') -RedirectStandardOutput "$lab/server.stdout.log" -RedirectStandardError "$lab/server.stderr.log"
```

这条命令对应默认实验路径；使用前确认端口空闲且未在另一个窗口启动服务。后台服务实际进程号记录在 `server.json`，Windows 虚拟环境启动器的进程号可能与服务进程号不同。停止前检查进程身份：

```powershell
$server = Get-Content "$lab/server.json" | ConvertFrom-Json
$processInfo = Get-CimInstance Win32_Process -Filter "ProcessId=$($server.pid)"
if ($processInfo.CommandLine -like '*data_transport_lab.py*') {
    Stop-Process -Id $server.pid
}
```

## 完整自动测试

以下命令要求 `targets/local`、`targets/scp` 和 `targets/scp-legacy` 尚无数据及缓存：

```powershell
& $python src/utils/data_transport_lab.py --work-dir $lab test
```

它分别完成首次获取、严格校验、再次获取、修改测试目标文件、检测损坏、显式 `--update` 修复及再次严格校验。破坏和修复仅针对生成的实验副本。预期首次下载数量大于 0、再次下载和修改均为 0、损坏被检测并修复。结果写到 `results.json`，CLI 原始输出保存在 `logs/`；服务器访问记录保存在 `server-events.jsonl`。

较大文件的恢复下载及带空格路径另外运行真实 OpenSSH 集成测试：

```powershell
$env:CAEOJ_TEST_SSH = '1'
& $python -m unittest discover -s tests -p test_data_ssh_integration.py -q
Remove-Item Env:CAEOJ_TEST_SSH
```

该测试使用另外的临时服务与随机端口，比较完整字节，覆盖 SFTP `reget`、旧 SCP 首次下载、SSH 块恢复及特殊文件名。

## 手动获取本地与 SCP 数据

若自动测试已完成，可创建新目标来观察首次实际传输，而无需删除既有数据：

```powershell
& $python src/utils/data_transport_lab.py --work-dir $lab target --name local-manual
$localRoot = Join-Path $lab 'targets/local-manual'
& $caeoj data fetch --root $localRoot --task smoke-test --source local --config $config
& $caeoj data verify --root $localRoot --task smoke-test --strict

& $python src/utils/data_transport_lab.py --work-dir $lab target --name scp-manual
$scpRoot = Join-Path $lab 'targets/scp-manual'
& $caeoj data fetch --root $scpRoot --task smoke-test --source scp --config $config
& $caeoj data verify --root $scpRoot --task smoke-test --strict

& $python src/utils/data_transport_lab.py --work-dir $lab target --name scp-legacy-manual
$legacyRoot = Join-Path $lab 'targets/scp-legacy-manual'
& $caeoj data fetch --root $legacyRoot --task smoke-test --source scp-legacy --config $config
& $caeoj data verify --root $legacyRoot --task smoke-test --strict
```

`scp` 来源配置使用 `transport="sftp"`；`scp-legacy` 使用 `transport="scp"`。它们都通过系统 OpenSSH 客户端实际连接本机服务。缓存默认位于各 `--root` 下的 `.caeoj/cache`，互相独立。重复同一条 fetch 命令，预期 `downloaded_files: 0`、`changed: 0`。

本地目录也可以直接指定，跳过命名来源：

```powershell
& $caeoj data fetch --root $localRoot --task smoke-test --source-dir "$lab/repository"
```

## 用下载数据运行一次程序和判题

以下示例使用手动 SFTP 目标；也可把 `$scpRoot` 换为其他已完整获取的目标：

```powershell
$taskDir = Join-Path $scpRoot 'qbank/00-basic-tests/0.1-io/smoke-test'
$inputFile = Join-Path $taskDir 'cases/01-line-1d/problem.json'
$outputFile = Join-Path $lab 'manual-result.h5'
$gradingFile = Join-Path $taskDir 'reference/01-line-1d/grading.json'

& $python -m caeoj validate-input $inputFile
& $python "$taskDir/solve.py" --input $inputFile --output $outputFile
& $caeoj grade --input $inputFile --output $outputFile --grading $gradingFile
```

`smoke-test` 是数据回显与协议测试，判题通过说明这些下载数据可以进入现有消费流程，不代表 PDE 数值精度验收。

## Hugging Face：测试现有仓库下载

先在浏览器打开题目清单中指定的数据集。若仓库启用访问申请，登录账号并申请；人工审批模式需要维护者批准后再下载。随后在终端登录同一账号：

```powershell
.\.venv\Scripts\hf.exe auth login
.\.venv\Scripts\hf.exe auth whoami
```

使用尚未写入数据和缓存的 HF 目标测试完整闭环：

```powershell
& $python src/utils/data_transport_lab.py --work-dir $lab test --sources hf
```

若此前失败产生了缓存或半成品，创建另一个空目标后手动执行：

```powershell
& $python src/utils/data_transport_lab.py --work-dir $lab target --name hf-manual
$hfRoot = Join-Path $lab 'targets/hf-manual'
& $caeoj data fetch --root $hfRoot --task smoke-test --source hf --config $config
& $caeoj data verify --root $hfRoot --task smoke-test --strict
& $caeoj data fetch --root $hfRoot --task smoke-test --source hf --config $config
```

`GatedRepoError` 应检查账号登录、仓库访问审批和令牌可读权限。`--dry-run` 完全离线，适合看大小和选样，不能验证网络或权限。

## Hugging Face：测试自己的私有仓库上传与下载

这组命令由你在自己的账号下执行。登录凭据需要具有创建仓库与写入测试仓库的权限。只上传 `repository/`，临时 SSH 密钥、配置和日志留在其外部。

```powershell
$repoId = '你的HF用户名/caeoj-data-test'

.\.venv\Scripts\hf.exe auth login
.\.venv\Scripts\hf.exe repos create $repoId --repo-type dataset --private
.\.venv\Scripts\hf.exe upload $repoId "$lab/repository" . --repo-type dataset

# 在新的消费副本中切换 repo_id，并去掉旧仓库的锁，保留主项目清单。
& $python src/utils/data_transport_lab.py --work-dir $lab target --name hf-private --hf-repo $repoId
$privateRoot = Join-Path $lab 'targets/hf-private'

# lock 将 main 解析为固定提交，并生成这个实验副本自己的数据锁。
& $caeoj data lock --root $privateRoot --task smoke-test --source hf --config $config
& $caeoj data fetch --root $privateRoot --task smoke-test --source hf --config $config
& $caeoj data verify --root $privateRoot --task smoke-test --strict
& $caeoj data fetch --root $privateRoot --task smoke-test --source hf --config $config
```

首次 fetch 应实际下载载荷，第二次应复用已有文件。锁定操作只下载描述元数据，因此其缓存不应让首次载荷传输变成零下载。`data-lock.json` 中的 `hf_revision` 应为完整固定提交 SHA。将同一私有目标与其清单、锁复制到另一台有权限的机器后，可再次验证跨机器复现。

HF 官方说明：[CLI 登录、建仓和上传](https://huggingface.co/docs/huggingface_hub/en/guides/cli)、[受限数据集访问申请](https://huggingface.co/docs/hub/en/datasets-gated)。
