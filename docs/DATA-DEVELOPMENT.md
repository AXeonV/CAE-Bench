# 数据管理开发与Git交付

数据命令、配置与发布顺序见[操作指南](../qbank/maintenance/DATA-SYNC.md)。本页只说明无Git元数据的开发副本如何交付回原仓库，不创建与原仓库无关的新历史。

## 本地验证

在开发副本安装仓库与扩展，使用独立虚拟环境：

```sh
python -m venv .venv
python -m pip install -e '.[maint,heat,pdebench]' -e qbank/extensions
python -m unittest discover -s tests -p 'test_data*.py' -v
python -m unittest discover -s tests -p 'test_publish.py' -v
python -m unittest discover -s tests -p 'test_harbor.py' -v
```

先激活该虚拟环境再运行上述安装和检查。准备真实数据时分别验证本地、SSH服务器和HF来源；离线fixture测试不等于远端服务已验收。公开包须在离开源码树后仍能独立校验，不携带维护工具、数据锁或隐藏参考。

可选的 `test_data_ssh_integration.py` 使用本机OpenSSH客户端与临时只读SSH测试服务器，验证SFTP、旧SCP和真实续传；需在测试环境另装paramiko并设置 `CAEOJ_TEST_SSH=1`。它不使用用户的服务器或凭据，也不代替目标服务器的权限验收。

## 回到原仓库的分支

解压目录没有 `.git` 时可以先开发，但不要对它初始化新历史后强推原仓库。取得仓库访问权限后，克隆原仓库并基于维护者指定的目标分支创建功能分支：

```sh
git clone <原仓库地址> <新的工作目录>
git switch <目标分支>
git switch -c feat/data-management
```

在新工作目录操作；尖括号是需替换的占位符。将审核过的差异补丁应用到该目录：

```sh
git apply --check <开发副本生成的补丁路径>
git apply <开发副本生成的补丁路径>
```

若目标分支已经变化，先处理冲突并重新验证。没有网络时可由维护者提供包含原历史的Git bundle，克隆bundle后同样创建功能分支；获得远端访问权限后再关联原仓库。

## 暂存、推送与合并

逐项暂存本次修改，包括新增代码和已核实的清单／锁。确认生成数据没有被跟踪：

```sh
git status --short
git diff --check
git diff --cached --stat
git diff --cached
git ls-files 'qbank/*/*/*/cases/*' 'qbank/*/*/*/reference/*' 'qbank/*/*/*/samples/*'
git commit -m "feat(data): add unified local SCP and Hugging Face data management"
git push -u origin feat/data-management
```

`git diff --cached` 检查已暂存内容，暂存使用 `git add <本次修改路径>`。如果数据原先已被跟踪，`.gitignore` 不会取消跟踪；先核验外部备份，再由维护者显式停止跟踪。不得提交用户配置、凭据、虚拟环境、缓存、实际数据、发布包或运行日志。

在托管平台创建PR／MR，记录问题、改动、验证范围和未完成的真实服务验收。遵循项目要求使用Squash and merge。代码推送不代替HF／服务器数据发布，两者分别管理。
