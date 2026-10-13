# PDEBench 数据准备工具

统一入口为 `prepare.py`，支持 11 个 `PDEBench_` 方程族：按固定 DaRUS V8 清单获取选定数据，冻结公开/隐藏拆分，缓存选定轨迹，并生成符合各题 DATA.md 的 JSON/Gmsh/NPZ 输入。

**数据转换与参考解准备分别报告。** 平流使用分片常数初值的周期平移积分生成独立解析输出；其余族保留官方选定数组供作者对照，默认不将它们写成标答。对应连续初值、边界、黏性模型或域尺度的差异仍须按 DESIGN.md 审核；工具不改变题面来迁就来源轨迹。

## 克隆后使用

在仓库根目录运行：

```text
python src/utils/PDEBench/prepare.py --tasks all --budget-gb 60
```

需要 Python 3.11 或以上。缺少 Python 依赖时，入口自动在 `runs/pdebench/venv/` 创建环境并安装本项目的 `pdebench` 额外依赖，再执行准备流程。已有虚拟环境也可以先安装 `python -m pip install -e '.[pdebench]'`，再加 `--no-bootstrap` 运行。运行环境需能加载项目现有的 Gmsh 系统依赖。

不联网、不安装依赖的准备预览：

```text
python src/utils/PDEBench/prepare.py --plan --tasks all
```

单题准备和隔离试跑：

```text
python src/utils/PDEBench/prepare.py --tasks 1D_Advection
python src/utils/PDEBench/prepare.py --tasks 1D_Advection --max-cases 1 --output-root runs/pdebench/smoke/tasks --cache-root runs/pdebench/smoke-runtime
```

`--tasks` 可指定完整题名、去掉 PDEBench_ 前缀的名称，或 all；多个名称以空格分隔。`--max-cases` 只截取隐藏点前缀，始终保留两条公开样例，是试跑选项，不代表整题完成。试跑和完整准备使用不同输出目录。

已有完整 HDF5 文件可用 `--source-dir <目录>`，按文件名或官方相对目录查找；首次读取验证完整文件大小和 MD5；路径、大小及修改/变更时间未改变时复用本地校验记录，避免每个算例重扫大文件。此模式不联网取数据。HTTP 模式只获取必要字节范围，不会因为服务器不支持 Range 就下载整个族或整个文件。

## 数据与缓存布局

```text
src/utils/PDEBench/catalog.json       固定 V8 文件 ID、路径、字节数、MD5 和入口
runs/pdebench/cache/ranges/<ID>/      有校验和的字节块，单源缓存上限 64 MiB
runs/pdebench/cache/selections/<ID>/  选定帧、坐标和字段 HDF5，以及实际载荷 SHA-256
runs/pdebench/staging/               临时转换目录
runs/pdebench/reports/latest.json    每题状态、错误、当前占用和估算峰值

tasks/PDEBench_*/author/selection.json    已冻结的源文件、样本索引、特征分组、ID、格式变体
tasks/PDEBench_*/author/preparation.json  当前准备状态（本地生成）
tasks/PDEBench_*/samples/01/input/        公开输入：problem.json、mesh.msh、input.npz
tasks/PDEBench_*/samples/01/output/       参考已准备时生成 result.npz
                                        samples/02 同结构
tasks/PDEBench_*/cases/<ID>/             隐藏输入
tasks/PDEBench_*/reference/<ID>/         certificate.json、official-candidate.npz；参考已准备时另生成 reference.npz
tasks/PDEBench_*/author/sample-certificates/  公开样例的私有证书
```

选定源轨迹均留在私有缓存。工具同时生成私有 `official-candidate.npz`（公开样例的候选保存在 author/sample-certificates/）；它是转换后的源输出，证书明确标记 unreviewed_do_not_grade，既不进入 Agent 包，也不作为 reference.npz。它们不是完整官方文件，不能用官方整文件 MD5 校验此子集：工具用固定源身份、完整 Content-Range/长度、ETag（服务器提供时）、缓存块 SHA-256 和选定载荷 SHA-256 记录各自的完整性范围。只有 `--source-dir` 的完整文件执行整文件 MD5 校验。

生成的数值数据、状态和私有证书由 .gitignore 排除；题面、固定 catalog 和冻结的 selection.json 可纳入版本管理。将冻结选样清单纳入版本管理后，另一次克隆可复现同一选择。没有冻结清单时，工具按稳定排序扫描有上限的初值候选池，完成一次确定性选样。

## 选样与契约

- 首批目标为 22 个公开样例、210 个隐藏点；各题分组见 [项目索引](../../../README.md)。Sod6 实际只有一条轨迹，隐藏组调整为一个点。
- 每文件一般扫描最多 8 个初值；按特征分组的单文件族使用 `--candidate-pool`（默认 64）。不可压缩族使用种子排序前 8 个发布分片的候选。来源内容或候选组不足会明确失败，不用重复轨迹凑数；可以在独立输出目录增加候选池再审核。
- 公开/隐藏按源轨迹拆分，公开初值指纹也从隐藏候选中排除。同一轨迹的格式变体、重编号和时间裁剪不能跨拆分。
- 标量浓度/圆形水深按初值特征四分位分组；双场反应扩散按梯度/RMS 中位数组合分组；不可压缩按速度/初始 χf RMS 中位数组合分组；各参数配置内部选取分散的初值特征。
- 保留原空间分辨率；公开最多 5 个、隐藏最多 9 个输出时刻，直接取实际有效帧的均匀索引，包含 t=0 和末帧。Darcy 为单个稳态时刻。已确认的 NLE 多余尾部时间坐标不算轨迹帧。
- 一阶线、矩形四边形和六面体网格采用显式 C-order 源索引关联；连续与递增稀疏编号、ASCII 与 binary 交替覆盖。输入不含源文件名、MD5、源索引或参考证书。
- FHN 源码存储 y/x 轴，转为 x/y；其细网格步进抽样坐标可能偏离粗单元中心，工具将有序样本作为题面定义的粗单元初始平均值，并在私有证书保存实际源坐标。参考必须针对该连续初值重新审核。Darcy 的 float32 二值系数显式规范为题面常量 0.1/1。
- 不可压缩速度与强迫使用题面单位正方形的中心点解释，原始速度不提前替参赛程序投影；连续 Helmholtz 投影和 χf 耦合仍是题目定义。源域尺度与正时间参考待审核。

冻结清单绑定 catalog、题面版本与选样选项。存在不一致时工具停止，避免静默重选隐藏数据。重跑会校验已准备文件和选定缓存，复用完整条目、修复损坏的工具生成条目，并记录转换器源码摘要。不会覆盖不属于工具的同名算例。

## 参考解与返回状态

| 退出码 | 意义 |
|---|---|
| 0 | 本次选择的输入与参考均已准备；不等于评测配置已完成 |
| 2 | 输入与私有源子集已准备，有参考仍待审核 |
| 1 | 获取、预算、来源、选样或转换错误；详情见报告 |
| 130 | 被中断；完整缓存块与已提交条目可复用 |

全族运行会继续处理相互独立的题目，并汇总失败；一个题目失败不会被写成成功。尚未完成的题目不会得到假的 result.npz/reference.npz。工具不生成未校准的 judge-config.json，不自动发布或组装 Harbor。

可用 `--reference-dir <目录>` 接入独立审核的参考。目录结构为：

```text
<目录>/<task>/sample/01/reference.npz
<目录>/<task>/sample/01/evidence.json
<目录>/<task>/case/001/reference.npz
<目录>/<task>/case/001/evidence.json
```

每份 evidence.json 必须提供：`status="audited"`、`method`、`error_evidence`、`contract_sha256`、`input_files`、`reference_sha256`。contract 和 input_files 从工具生成的私有 certificate.json 取得；参考摘要为实际 reference.npz 的 SHA-256。证据必须绑定此次题面及三个真实输入文件（problem.json、input.npz、mesh.msh），并通过输出结构校验。记录保留为外部审核声明；工具不把声明的存在当作自己完成了科学验证。

只有真实公开样例、全套同契约参考、误差阈值和执行资源均准备好，才能进入既有 publish_dist.py / prepare_harbor.py 流程。当前 Harbor 判题器还硬限制输出文件为 128 MiB，部分三维载荷超过它，须另行审核调整，不能靠减少要求变量或假定压缩率来绕过。

## 占用与恢复

默认硬预算为十进制 60 GB：计算工具 runtime（含自动依赖环境）、全部 PDEBench 题目目录、缓存、临时目录和生成结果的同时占用，不计算用户无关文件或显式传入的外部完整源目录。下载块与转换/参考载荷在写入前检查预算及可用空间；高维算例顺序处理，缓存单源磁盘 64 MiB、内存 4 个块。预算不足会停止，不静默缩小已冻结测试集。

所有步骤使用同一入口。字节块、选定载荷及 JSON 通过临时文件替换；case 输入目录通过备份/重命名提交，状态证书最后写入。异常中断留下的未完成条目重跑重新准备，已经校验的条目直接复用。运行锁防止两个进程同时使用同一共享预算；进程已不存在的有效 PID 锁会自动回收，损坏锁需要先检查后处理。

## 检查

```text
python -m pip install -e '.[pdebench]'
python -m unittest discover -s tests -p 'test_pdebench_prepare.py' -v
```

本地测试覆盖范围读取、缓存损坏修复和恢复、拒绝整文件回退、预算、11 族协议与编号关联、FHN 空间轴、平流积分参考、拆分复用，以及未审核轨迹不会变成标答。这些是工具验证，不是其余族的连续 PDE 数值参考验证。
