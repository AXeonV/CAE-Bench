# Darcy 来源核查与契约修复（2026-10-20）

结论：五档各一个实际缓存样本的参数、布局、中心坐标和转换链对应；修正本仓库的连续边界条件后，可以忠实使用发布单帧参考。未认证稳态收敛不再拦截整族，也不进行补算、修正或筛选。此次完成5条临时回放和2个引用example，未制作/安装20条正式case，未启动模型评测。

## 证据与范围

- [source-audit.json](source-audit.json)：读取133217–133221五个发布文件已缓存的HDF5头部、坐标和实际beta属性，并各核对一个既有选定载荷的SHA256/来源回执。载荷由历史直接选取阶段缓存，和后续重算参考不同；没有把历史修正参考用于本次回放。远程完整文件MD5只记录发布身份，未重新整文件校验。
- 五文件分别beta=.01/.1/1/10/100；`nu[10000,128,128]`和`tensor[10000,1,128,128]`分开；中心坐标为( i+.5 )/128。`tensor`只存一个输出切片，不能把部分文件遗留的10元素`t-coordinate`解释为该单帧的瞬态初始时刻。
- 缓存每例`diffusivity/state`形状均为[1,128,128,1]，有限值、系数0.1/1及坐标关联核对通过。轴顺序依据固定生成器的[x,y]写出和数组展平方式；HDF5自身没有维度标签，不能由同为128的两个维度独立证明。
- 本次没有重新从远端读取这些样本的全部源字节；完整性范围是缓存载荷SHA、既有来源回执及认证过的范围块。后续新选样仍由当前工具读取原始源并生成新的证据。

## 属于本仓库的边界错误及修复

[官方补充材料D.4，式13–15](https://proceedings.neurips.cc/paper_files/paper/2022/file/0a9747136d411fb83f0cf81820d44afb-Supplemental-Datasets_and_Benchmarks.pdf)定义单位方域、恒定f=beta以及边界u=0。现有题面把“外部虚单元置零”解释成连续边界“u=相邻原单元平均/2”，改变了数学条件，现恢复四边零Dirichlet；DATA和转换器同步改为boundary/state/dirichlet，显式value=0、unit=1。

[固定生成器](https://github.com/pdebench/PDEBench/blob/4ff3e3a4aa1561721b5571fa3a048a0a463e0568/pdebench/data_gen/data_gen_NLE/ReactionDiffusionEq/reaction_diffusion_2D_multi_solution_Hydra.py#L229-L249)使用算术面系数和中心差分更新，调用名为Neumann的边界分支；[该分支](https://github.com/pdebench/PDEBench/blob/4ff3e3a4aa1561721b5571fa3a048a0a463e0568/pdebench/data_gen/data_gen_NLE/utils.py#L1372-L1408)实际把虚单元置零，不能读成零通量。此闭合在半个单元边界距离上的通量系数与常见连续零Dirichlet离散不同。它是保留的来源离散差异，不再以改造连续题面或修正参考来消除。

## 采样、符号与稳态

源代码通量为负系数梯度，更新为负通量散度加beta，对应稳态-∇·(a∇u)=beta；没有发现本题方程符号、源项或空间坐标翻转。系数中心点双线性重建、外侧常值延拓和原单元面积平均输出保留为本题显式采样约定。源中心场与有限体积形式支持这一映射，但不构成对连续重建真解的精度认证，未假称HDF5证明了唯一连续插值。

[固定配置](https://github.com/pdebench/PDEBench/blob/4ff3e3a4aa1561721b5571fa3a048a0a463e0568/pdebench/data_gen/data_gen_NLE/ReactionDiffusionEq/config/multi/config_2D.yaml)指定有限终止时间2；演化器按时间结束，不设置稳态残差退出门槛。发布HDF5没有标出精确生成提交、原始终止时间或收敛证书，不能认定当前源码配置逐位重演了全部发布数据。历史“部分快照未充分收敛”仍作为已有局限记录，本批没有新增残差/精度筛查，也没有断言每例均未收敛。

因此不声称剩余问题只有收敛：历史版本、离散边界与连续采样误差也未认证。它们作为来源局限保留，不作为重新补算或拒绝整族的门槛。评分仍比较原始发布参考，不能把一次未通过一概解释为模型物理解错误。

## 工具与消费验证

- 去掉Darcy全族稳态门禁；逐源要求实际标量beta属性在五档支持范围，并与文件标签及最终输入source_strength一致；已有坐标、尺寸、形状和系数值域检查继续生效。
- [replay_cached.py](replay_cached.py)复用5个已审计真实载荷，在临时workspace调用现有prepare、example引用、verify和SDK读取；下载层用明确的缓存适配替代，未伪造全文件读取回执。见[回放报告](replay-report.json)。5条参考逐值等于缓存发布state，5条正控制得1、错误值控制得0；2个公开身份绑定通过。
- 原发布/Harbor装配器生成5case/2example，见[assembly-report.json](assembly-report.json)；未将这些临时选择安装到本题正式目录，未运行Docker考生/模型。
- 29项PDEBench回归通过，包括实际beta缺失、非标量、非法值、标签错配拒绝、非对称轴标记保留和非稳态合成值仍原样出参考。合成fixture仅验证契约，不冒充真实源数据。
- [独立公开题面审阅](CANDIDATE-REVIEW.md)通过，仅三份公开材料；不是参考正确性认证。

## 流量与运行隔离

场数据核查与回放新增网络响应体0。论文PDF资料本地下载失败于过小的文件大小断言，完整响应未落盘，保留8MB保守扣额，见[资料账目](document-network.json)；不把这部分丢弃流量记为0。加上并行不可压缩流全部预算，最坏累计3,769,404,524字节，仍小于用户3.80GB上限。

修复位于独立codex/darcy-source-audit分支，避免改变正在运行的不可压缩流批次所冻结的共享工具。旧selection/参考证书不能刷新哈希来冒充新契约，需在后续正式制数时新建选择。本次未推送、未发布HF、未补算或改写发布参考。

## 后续安装

当前分支已完成正式20case/2引用example，完整证据见[安装验收](../install-20261020/REPORT.md)。上文五条回放保留为前置核查的历史范围，未覆盖改写。
