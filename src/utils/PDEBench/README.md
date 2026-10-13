# PDEBench 数据准备工具

统一入口为 `prepare.py`，支持 11 个 `PDEBench_` 方程族：按固定 DaRUS V8 清单获取选定数据，冻结公开/隐藏拆分，缓存选定轨迹，并生成符合各题 DATA.md 的 JSON/Gmsh/NPZ 输入。

默认按用户选择的**官方生成器对齐与逐例数值参考审核**准备输入和答案。每例核对来源、配置、坐标、时间、完整初值、数组关联与模型一致性，保存指标和局限；官方数值输出不被称为精确连续真解。二维反应扩散恢复原 512² 初值并逐值验证发布的初始子集；Darcy 对发布空间算子求稳态，避免把未收敛的有限时间快照当成椭圆答案；一维反应扩散的官方轨迹存在远离反应平衡的停滞，工具保留差异证据并以同一 PDE 的独立空间/时间加密计算替换答案。判分阈值、网格收敛精度与执行资源仍待校准。

本轮发现的差异、处理方式和证据边界见 [审核记录](AUDIT.md)。

题面与现行设计的一致性修订、正式评分前仍需验证的事项见 [题面审阅记录](STATEMENT_REVIEW.md)。

## 试运行评测

仓库已提供 11 题的公开 grading.json（沿用各题 atol/rtol，每时刻每字段允许最多 0.1% 偏差空间点）、judge-config.json 与 Harbor 资源配置，详见 [试运行参数和运行步骤](EVALUATION.md)。baseline 可选，尚未正式校准；数据准备工具不覆盖这些已追踪配置。

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
runs/pdebench/cache/candidates/       绑定来源和读取器版本的候选特征，逐条保存以恢复扫描
runs/pdebench/staging/               临时转换目录
runs/pdebench/reports/latest.json    每题状态、错误、当前占用和估算峰值

tasks/PDEBench_*/author/selection.json    已冻结的源文件、样本索引、特征分组、ID、格式变体
tasks/PDEBench_*/author/preparation.json  当前准备状态（本地生成）
tasks/PDEBench_*/samples/01/input/        公开输入：problem.json、mesh.msh、input.npz
tasks/PDEBench_*/samples/01/output/       源对齐审核通过后生成 result.npz
                                        samples/02 同结构
tasks/PDEBench_*/cases/<ID>/             隐藏输入
tasks/PDEBench_*/reference/<ID>/         certificate.json、official-candidate.npz；审核或稳态修正通过后生成 reference.npz
tasks/PDEBench_*/author/sample-certificates/  公开样例的私有证书
```

选定源轨迹留在私有缓存。工具保存原始转换对照 official-candidate.npz 及审核状态，公开样例的原始对照只位于 author/sample-certificates/。Darcy 的原始快照与修正答案分别保存，证书记录稳态残差和改变量；一维反应扩散保留官方轨迹与同一 PDE 重算结果的差异；其余族审核通过后以官方数值轨迹生成答案。原始对照和证书不进入 Agent 包。远程子集不能用整文件 MD5 验证：工具记录源身份、Content-Range/长度、ETag（有则使用）、块 SHA-256 和选定载荷 SHA-256；只有 --source-dir 的完整文件执行整文件 MD5。

所有生成数值数组和网格（NPZ/MSH/HDF5）、本地恢复记录和运行状态由 .gitignore 排除；题面、固定 catalog、冻结的 selection.json、公开/隐藏 problem.json 及 certificate.json 纳入版本管理。参考证书和隐藏定义属于作者材料，不进入 Agent 公开包。将冻结选样清单纳入版本管理后，另一次克隆可复现同一选择。没有冻结清单时，工具按稳定排序扫描有上限的初值候选池，完成一次确定性选样。新克隆会保留完整问题定义；工具允许已有定义而无数值载荷的状态，并在补齐时比较生成定义、原样保留已版本管理的文件。若定义与冻结来源转换不一致，会停止该例并保留原文件，不静默覆盖作者修改。

## 选样与契约

- 首批目标为 22 个公开样例、210 个隐藏点；各题分组见 [项目索引](../../../README.md)。Sod6 实际只有一条轨迹，隐藏组调整为一个点。
- 每文件一般扫描最多 8 个初值；按特征分组的单文件族使用 `--candidate-pool`（默认 64）。不可压缩族使用种子排序前 8 个发布分片的候选。来源内容或候选组不足会明确失败，不用重复轨迹凑数；可以在独立输出目录增加候选池再审核。
- 公开/隐藏按源轨迹拆分，公开初值指纹也从隐藏候选中排除。同一轨迹的格式变体、重编号和时间裁剪不能跨拆分。
- 标量浓度/圆形水深按初值特征四分位分组；双场反应扩散按梯度/RMS 中位数组合分组；不可压缩按速度/初始 χf RMS 中位数组合分组；各参数配置内部选取分散的初值特征。
- 保留原空间分辨率；公开最多 5 个、隐藏最多 9 个输出时刻，直接取实际有效帧的均匀索引，包含 t=0 和末帧。Darcy 为单个稳态时刻。已确认的 NLE 多余尾部时间坐标不算轨迹帧。
- 一阶线、矩形四边形和六面体网格采用显式 C-order 源索引关联；连续与递增稀疏编号、ASCII 与 binary 交替覆盖。输入不含源文件名、MD5、源索引或参考证书。
- FHN 源存储 y/x 轴，转为 x/y。发布的 128² 值是原 512² 网格的子集；工具以组配置的 seed 使用历史 MT19937 恢复完整初值，并要求所有发布初值逐值匹配 float32 精度。审核源码的 default_rng 生成器不满足这个历史重建，不能直接使用。输入只含完整字段，不含 seed。输出采用原细网格的明确单元子集。
- Darcy 系数是中心点的 0.1/1 采样，使用双线性重建；外部零单元对应的边界采用题面规定的单元平均耦合。工具对同一源空间算子独立求稳态并记录发布快照残差，残差不是连续误差界。
- 吸附采用正则化迟滞系数和明确的单元平均耦合边界，匹配源外部单元闭合的连续表达。
- 可压缩流采用源代码密度加权定向黏性通量，η/ζ 单位 m2/s；输出速度与压力由平均守恒量反算，不是体积平均原始变量。证书记录正性、压力下限值及周期质量/能量变化。
- 不可压缩流采用发布配置的 [0,1]² Box，工具对每个分片用短时标量输运区分单位域与当前源码的 grid_size Box；t=0 保留未投影的原始记录，正时间采用投影后的速度和 χf 耦合。归档生成器提交链与中心/交错采样误差未被此结构审核证明，证书明确记录这些局限。

冻结清单绑定 catalog、题面版本和选样选项。不一致时默认停止。作者明确审核题面修订后可使用 --refresh-contract，将相同来源和选样选项的已有选择绑定到新契约，并在 author/history/ 归档旧清单；不会重选或忽略已知的候选池/算例数变更。此次源对齐修订使用该选项；新克隆无需它。

重跑校验文件和选定缓存，复用完整条目，修复损坏的工具生成条目，并记录转换器源码摘要；保留 .gitkeep，不改动不属于工具的同名算例。

## 参考解与返回状态

| 退出码 | 意义 |
|---|---|
| 0 | 本次选择的输入与数值参考均已准备；不等于连续误差已验证或评测配置已完成 |
| 2 | 输入与私有源子集已准备，独立参考模式下仍有尚未实现的参考 |
| 1 | 获取、预算、来源、选样或转换错误；详情见报告 |
| 130 | 被中断；完整缓存块与已提交条目可复用 |

全族运行会继续处理相互独立的题目，并汇总失败；冻结选样后，单个算例获取或转换失败也会继续其余算例，报告保留已完成记录及逐例错误。一个题目失败不会被写成成功。尚未完成的题目不会得到假的 result.npz/reference.npz。工具不生成未校准的 judge-config.json，不自动发布或组装 Harbor。

可用 --reference-mode independent 切换到已有平流解析积分、Burgers Cole–Hopf 积分和一维反应扩散空间/时间加密参考；未实现的族会明确 reference_pending。可用 `--reference-dir <目录>` 接入外部审核的参考。目录结构为：

```text
<目录>/<task>/sample/01/reference.npz
<目录>/<task>/sample/01/evidence.json
<目录>/<task>/case/001/reference.npz
<目录>/<task>/case/001/evidence.json
```

每份 evidence.json 必须提供：`status="audited"`、`method`、`error_evidence`、`contract_sha256`、`input_files`、`reference_sha256`。contract 和 input_files 从工具生成的私有 certificate.json 取得；参考摘要为实际 reference.npz 的 SHA-256。证据必须绑定此次题面及三个真实输入文件（problem.json、input.npz、mesh.msh），并通过输出结构校验。记录保留为外部审核声明；工具不把声明的存在当作自己完成了科学验证。

初始输出按显式位置 IDs 与初始字段关联后逐值检查，支持完整初值上的输出子集；不可压缩流也必须保留契约要求的预投影 t=0 记录，不能跳过首帧检查。

只有真实公开样例、全套同契约参考、误差阈值和执行资源均准备好，才能进入既有 publish_dist.py / prepare_harbor.py 流程。当前 Harbor 判题器支持 judge-config.json 的 max_output_bytes；旧任务缺省仍为 128 MiB，PDEBench 三维试运行配置为 2 GiB，不缩减要求的输出变量。正式资源与误差校准仍需完成。

## 占用与恢复

默认硬预算为十进制 60 GB：计算工具 runtime（含自动依赖环境）、全部 PDEBench 题目目录、缓存、临时目录和生成结果的同时占用，不计算用户无关文件或显式传入的外部完整源目录。下载块与转换/参考载荷在写入前检查预算及可用空间；高维算例顺序处理，缓存单源磁盘 64 MiB、内存 4 个块。预算不足会停止，不静默缩小已冻结测试集。

所有步骤使用同一入口。字节块、选定载荷及 JSON 通过临时文件替换；case 输入目录通过备份/重命名提交，状态证书最后写入。异常中断留下的未完成条目重跑重新准备，已经校验的条目直接复用。运行锁防止两个进程同时使用同一共享预算；进程已不存在的有效 PID 锁会自动回收，损坏锁需要先检查后处理。

## 检查

```text
python -m pip install -e '.[pdebench]'
python -m unittest discover -s tests -p 'test_pdebench_prepare.py' -v
```

大字段的当前读取请求会合并至最多四个已有粒度的块，减少请求延迟；小头部读取不额外扩大下载范围。块校验、缓存上限与断点恢复语义保持一致。

不可压缩流的时间戳逐个存储在压缩块中。候选只读取真实 t=0，选定轨迹只读取所需输出帧的真实时间戳，域尺度审核只读取真实前三帧时间；不会为获取时间轴扫描所有无关帧，也不按配置重新生成时间值。

本地测试覆盖范围读取、缓存损坏修复和恢复、拒绝整文件回退、预算、11 族协议与编号关联、FHN 空间轴、平流积分参考、拆分复用，以及未审核轨迹不会变成标答。这些是工具验证，不是其余族的连续 PDE 数值参考验证。
