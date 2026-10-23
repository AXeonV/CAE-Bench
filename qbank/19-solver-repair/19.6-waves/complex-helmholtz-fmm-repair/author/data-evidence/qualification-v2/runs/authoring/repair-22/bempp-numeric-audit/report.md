# 真实 Bempp / ExaFMM 数值审计：scratch 截断的独立定位

## 结论

已通过只改变 `/tmp` 容量的因果对照确认：此前 p10 远场 0.1…0.8 量级错误和同进程多 p8 实例错误，主要原因是 ExaFMM 预计算文件超过 768 MiB tmpfs，native 代码忽略文件写入／读取失败。不是 complex-k 公式缺陷、Numba 改写返回值或必须把固定展开阶降到 p8。

没有修改正式题面、DATA、driver、dataset-v1 或真实固定源码；没有编译替代 native，也没有编写候选替代求解器。所有计算直接使用原 reference image 的真实 `ExafmmInterface` 与 `exafmm.so`，`dense_evaluation=False`。独立闭式 Green 及其目标梯度只用于数值审计。

## 可重复因果证据

同一 `02-point-complex`，p10，ncrit16，OMP1，OPENBLAS1，4 CPU / 4 GiB，独立新容器：

| tmpfs 容量 | 实际单个预计算文件 | 可用空间 | 最大实/虚分量误差 | 原 1e-7+2e-6 容差最大占比 |
|---|---:|---:|---:|---:|
| 768 MiB | 805,306,368 B（被截断） | 0 B | 0.2652908917 | 2,558,369 |
| 2 GiB | 943,800,328 B（完整） | 1,203,679,232 B | 4.09193e-9 | 0.03725 |

参见 `02-point-complex-p10-n16-scale1-tmp768m.{stdout,stderr}.log` 与 `...-tmp2g.{stdout,stderr}.log`；命令与资源参数在 `state6.json`、`state7.json`。两次均未调用 local helper 后再计算误差，直接比较 evaluate 的返回结果，已排除后续 Numba 分配的 ownership 假设。

`04-point-far-tree` p10：768 MiB 时误差 0.58759225；2 GiB 时文件完整 1,232,998,408 B，误差恢复为 6.65704e-7。原容差最大占比 3.30，`atol=1e-6,rtol=1e-5` 的占比 0.411。这是剩余有限阶近似精度问题，与 0.58 的灾难性错误应明确区分。

另用原顺序在同一进程跑六个 p8 point fixtures：保留全部临时文件时，03/04/05 分别出现 0.00945/0.58759/0.02083；每次实例完成审计后只删除其不再使用的预计算文件，768 MiB 下恢复为独立进程的 1.56e-8/5.48e-6/4.38e-8。见 `same-process.stdout.jsonl`、`family-cleanup.stdout.jsonl`。这项清理仅是生命周期因果诊断，没有改库或生产 driver，也不能在还需要重用实例时删除其文件。

## 源码机制与磁盘预算

真实 v0.1.0 的 `include/fmm.h`：

- `save_matrix`、`precompute_M2L` 使用 ofstream.write，但不检查流状态。
- `precompute` 即使写入失败也继续返回。
- `M2L` 从实际文件尾倒推 M2L section 起点，再 read 固定矩阵大小，不检查读取状态。文件截断导致其 section 偏移及数据无效，仍能返回有限但错误的结果。
- Bempp 给每个 ExafmmInterface 分配唯一 `.tmp` 文件，默认仅在进程退出时集中清理，所以多实例的缓存文件会累计。

对复数 Helmholtz，p 阶、树深 d 的完整预计算文件长度是：

`8 + 20*(6*(p-1)^2+2)^2*(d+1)*16 + 26*(2*p)^3*128*d*8` 字节。

该公式与两个完整实测文件长度完全一致。最早 2 GiB stderr 中诊断脚本的 expected 字段暂误用 27 个 M2L 相对位置，多计了中心位置；原日志保留，脚本已纠正为 26。actual_file_bytes 是直接 stat 得到的真实证据，不受该诊断公式修正影响。

建议首先将 author/reference 与考试执行链的 ExaFMM scratch 移到具有明确磁盘预算的独立可写目录，并核验完整文件长度或可用空间。仅把 `/tmp` tmpfs 提高到 2 GiB 不是多算子的完整解决：多个 boundary/potential 实例仍可累加超限，且 tmpfs 占用实际内存。生产磁盘目录的生命周期与容量应由可信运行框架负责。无需修改三份允许 Python 源码来进行数值补偿或暗改 native。

## 剩余精度与范围建议

p8 独立进程现有六个 point fixture：01/06 约机器精度，02/03/05 最大分量误差约 5.05e-8/1.56e-8/4.38e-8；04 为 5.48e-6，不能满足当前极紧分量容差。native ncrit1024 的 direct/P2P 控制在 03/04 达 8.4e-17/2.4e-14，支持复数 Green 与目标梯度公式、输入布局正确；这只是诊断控制，不建议正式切换到该退化路径。

低频约束 `abs(k)*D_all<=6或8`、`Im(k)*D_all<=2` 单独不能证明统一绝对误差。04 源和目标统一缩放到 0.18/0.2 后满足这些耦合范围，p8 仍有 3.44e-5/3.00e-5 的绝对梯度误差；梯度随尺度缩小自然放大。实测 `atol=1e-5,rtol=1e-5` 在两者的最大占比分别 0.620/0.601。应先用充足磁盘恢复真实 p10 完整参考链，再根据所有实际 fixture 的独立闭式／genuineDense 误差选择合理容差，而不是以这些少量 probe 宣称任意几何稳定保证。无需仅因 scratch 截断就收窄原复杂核能力或放松到 0.1。

另有独立条件数诊断 `spectrum.jsonl`：按真实 geometry.h 的表面点规则，用闭式 Green 构造 check/equivalent 矩阵，p10 深层条件数可到 1e15，p12 到 1e18。它证实高阶存在数值条件风险，但本轮容量对照已明确此前灾难的直接原因是磁盘截断；不能把条件数推断当成已认证的失败归因。该谱分析未改变 native。

## 版本、独立性和限制

image ID `sha256:e23990b800639837e80467456a571adf25aa97208c732cbfc0212765a9c487b3`；Bempp base `84345ee9ee314c85750f045c7ad38090f5ea5f26`，PR45 head `2a353ef7cf73883fd761b400691dfb82cd7f614f`；ExaFMM v0.1.0 `c9ad1980d50cb6ed5d01b2d5e65c7fce51bcfb05`。归档及诊断脚本 SHA256 见 `evidence-manifest.json`，原始 probe 汇总见 `probe-results.json`。

本轮只认证这些 point probes 的数值和 scratch 因果对照；未完成所有 boundary/potential fixture 的独立数值认证，未运行收费模型 benchmark，未发布 HF 或考试包，未 Git 提交/推送。独立条件数用宿主 SciPy 1.17.0 / NumPy 2.4.1，其余 numerical probes 使用锁定真实 image 内 runtime。
