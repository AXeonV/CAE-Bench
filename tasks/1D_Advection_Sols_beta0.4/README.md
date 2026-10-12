# PDEBench 一维周期平流题

使用 PDEBench 已发布文件中的 12 个完整样本，保留全部 1024 个空间单元与 201 帧。题面见 [instruction.md](instruction.md)，字段与周期条件见 [DATA.md](DATA.md)，来源核验和协议覆盖见 [DESIGN.md](DESIGN.md)，测试选择见 [TEST-CASES.md](TEST-CASES.md)。

## 文件

| 路径 | 用途 |
|---|---|
| `instruction.md`、`DATA.md` | 公开题面与输入输出含义 |
| `samples/01/`、`samples/02/` | 完整公开输入和正确输出 |
| `cases/<case>/` | 网格、初值、参数和完整时间轴 |
| `reference/<case>/` | 官方完整轨迹及转换核验记录 |
| `author/SOURCE.json` | 官方来源、样本索引与原数组 SHA-256 |
| `author/download.py` | **获取数据**：分段读取官方 HDF5 的完整选定样本并核对哈希 |
| `author/generate.py` | **协议对接**：匹配单元位置、转换数组并直接导出官方轨迹 |
| `author/baseline.py` | **独立求解**：计算给定初始单元场的周期平流，只读取输入 |
| `author/check.py` | **逐例验证**：判分、计时与采样峰值内存 |
| `judge-config.json` | 误差阈值和单点执行时限 |

## 出题与验证

```powershell
& $caePython -m pip install -r tasks/1D_Advection_Sols_beta0.4/author/requirements.txt
& $caePython tasks/1D_Advection_Sols_beta0.4/author/generate.py
& $caePython tasks/1D_Advection_Sols_beta0.4/author/check.py
```

原始选定样本保存在 `runs/pdebench-official/`，无需下载整个官方文件。共享发布、组装与 Harbor 命令见项目 README。

每点全部值绝对误差≤0.08 得 1 分，否则 0 分；单点 5 秒，容器 CPU 与内存采用默认分配。`tests/test_pdebench_advection.py` 检查完整轨迹、原值一致性、编号关联、样例判分和公开材料隔离。
