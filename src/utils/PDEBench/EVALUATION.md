# PDEBench 试运行评测配置

11个方程族均提供唯一完整作者模板author/grading-template.json、执行配置judge-config.json和harbor/task.toml。它们仍属于试运行配置；参考数值资格、归一化尺度和性能预算尚未全部校准。

## 评分与执行来源

当前数值能力题使用显式max_nrmse连续评分：每个输出量、标量分量及请求时刻分别沿空间计算NRMSE，case取最大值；5%以内满分、10%起零分、中间线性。完整定义见[评分说明](../../../docs/GRADING.md)，考生要求与逐量尺度下限由本题instruction.md说明。

这11题使用等点空间权重，保留全部请求时刻和观测位置。原绝对容差继承为同单位scale_floor；原相对容差和0.1%偏差点规则已被替换，不能继续用于解释当前分数。继承尺度不是容差等价或科学校准。IDs、时间轴、shape、dtype及有限值仍严格检查。

制数通过author_case_grading读取完整作者计划，由write_case_grading写入每例reference/grading.json；运行时只读本例配置，不从模板或指标名称推断评分模式。历史冻结选样、源证书和成绩保留原版本，不重签为当前评分证据。

每例求解墙钟、评价worker预算、输出字节限额由实际judge-config.json维护；Agent、构建、CPU、内存与外层verifier设置由harbor/task.toml维护，见[配置消费流程](../../../qbank/maintenance/EVALUATION.md)。prepare_harbor按正式case数将外层预算至少设为base_seconds + case_count × (timeout_seconds + evaluation_timeout_seconds + per_case_overhead_seconds)，求解与评价分别限时。配置解析不代表容器限额或全部case运行已经验证。

memory_mb是Harbor环境容器限额，不是逐例进程的独立RSS限制。Docker主机须提供相应资源并留出系统开销；配置不会自动扩容Docker虚拟机。

题面只声明做题所需的任务、评分与资源。校准状态、执行证据和发行资格留在维护记录。评分变更后须重新生成每例配置、重建数据池并真实装配核验，再更新公开包和Harbor任务；旧包及历史成绩不会自动变更。输入和参考数组不变时无需重新下载或求解。需要同步HF时另行显式上传，离线RC装配不以重新上传为前提。

## 无 baseline 的运行路径

没有 `author/baseline.py` 的题目组装后标记 `oracle_available=false`，直接运行 Agent，跳过 Oracle；判分仍与已有 `reference.h5` 比较。有 baseline 时可先运行 Oracle 检查。

数据补齐后，在 Docker 和 Harbor 可用的环境中运行：

```bash
python src/utils/publish_dist.py --task advection-1d
python src/utils/prepare_harbor.py --task advection-1d
export CODEX_AUTH_JSON_PATH="$HOME/.codex/auth.json"
harbor run -p runs/harbor/tasks/advection-1d \
  -e docker -a codex -m openai/gpt-6-luna \
  --ak reasoning_effort=medium -n 1 -o runs/harbor/jobs
```

对于其他方程族替换任务名即可；缺少数值文件时先运行数据准备工具。报告保留每例连续分值，题目reward为全部正式case分数的平均；不得把partial_credit或CLI退出1一律归零。成绩不能直接解释为已校准的正式Benchmark能力指标。

## Apple Silicon 与镜像下载

Apple Silicon 的 Docker 默认构建 Linux ARM64；当前固定依赖 gmsh==4.15.2 没有可供该安装流程使用的 Linux ARM64 wheel。此环境在运行 Harbor 前设置：

```bash
export DOCKER_DEFAULT_PLATFORM=linux/amd64
```

该变量同时影响 Docker Compose 的镜像构建与容器平台选择；无需改动数学题面或降低 Gmsh 版本。x86-64 镜像会在 Apple Silicon 上通过模拟运行，因此其用时不应作为原生 ARM 性能结果。

若日志在拉取 python:3.14-slim 时显示 TLS handshake timeout，属于 Docker Hub 连接问题，Agent 尚未开始；可在连接恢复后先运行 `docker pull --platform linux/amd64 python:3.14-slim`，再重试原 Harbor 命令。LiteLLM 费用表下载警告需与 trial 的 exception.txt 区分，不能据此解释得分。
