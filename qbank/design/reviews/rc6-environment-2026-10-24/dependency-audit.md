# RC6 环境依赖独立盘点

本报告只读检查已发布RC5的82题公开题面、DATA、公开SDK包元数据和运行资源配置；未读取隐藏输入／参考数值、未调用模型、未判分、未改源码或发布。

共82题、647正式case。43道第二章非CFDCodeBench题明确承诺SciPy；82个公开SDK依赖锁均没有SciPy。qbank.zip中各题harbor/requirements.txt数量为0（固定RC5源码存在71份，其中69份包含SciPy；发行工作目录未获得这些文件）。

## 共享缺口

- **ENV-1 / P1**：SciPy是43题明确承诺的求解环境依赖；固定RC5源码已通过题目harbor/requirements.txt声明它，但发行qbank.zip漏掉全部71份环境补充（69份包含SciPy）；提取后prepare_harbor因文件缺失写入空要求，导致独立verifier缺包。应修打包／提取／安装消费链，避免将领域求解依赖混进通用协议。
- **ENV-2 / P1**：仅分发题目、公开包与pip安装步骤不能完整复现开发环境。RC6必须含可实际消费的环境构建／安装和预检入口；不宜只修维护仓库Dockerfile。
- **ENV-3 / P2**：Gmsh系统动态库不是pip能补全的Python依赖；全部公开README已声明这一点，需要真实初始化验证。
- **ENV-4 / P2**：C++、OpenMP、OpenMPI、HDF5开发库承诺需要真实编译、链接与执行探针，不能仅用Python import代替。
- **ENV-5 / P2**：候选容器自行pip安装成功不能证明独立断网verifier可用；两个阶段必须分别从冻结基线启动。

## 逐题账本

完整证据行、公开SDK锁、资源覆盖值及实际配置见dependency-audit.json。下表“承诺组件”只根据明确环境措辞提取，不把数学文本中的库名推断成预装承诺。

| 题目 | 明确承诺Python组件 | 固定源码requirements | case |
|---|---|---:|---:|
| 简单测试 | 未逐项承诺；仍有公开SDK安装依赖 | 有 | 11 |
| Case 判题链路测试 | 未逐项承诺；仍有公开SDK安装依赖 | 有 | 6 |
| 二维空间变系数 Darcy 型稳态问题 | 未逐项承诺；仍有公开SDK安装依赖 | 无 | 20 |
| 二维稳态热传导 | 未逐项承诺；仍有公开SDK安装依赖 | 有 | 32 |
| 一维 Freundlich 迟滞扩散 | 未逐项承诺；仍有公开SDK安装依赖 | 无 | 16 |
| 二维瞬态热传导 | 未逐项承诺；仍有公开SDK安装依赖 | 有 | 24 |
| 一维 logistic 反应扩散 | 未逐项承诺；仍有公开SDK安装依赖 | 无 | 32 |
| 二维 FitzHugh–Nagumo 反应扩散 | 未逐项承诺；仍有公开SDK安装依赖 | 无 | 16 |
| 一维周期线性平流 | 未逐项承诺；仍有公开SDK安装依赖 | 无 | 24 |
| 二维浅水方程 | 未逐项承诺；仍有公开SDK安装依赖 | 无 | 16 |
| 一维周期黏性 Burgers 方程 | 未逐项承诺；仍有公开SDK安装依赖 | 无 | 24 |
| 二维非均匀强迫不可压缩流 | 未逐项承诺；仍有公开SDK安装依赖 | 无 | 16 |
| 一维可压缩 Navier–Stokes | 未逐项承诺；仍有公开SDK安装依赖 | 无 | 16 |
| 二维可压缩 Navier–Stokes | 未逐项承诺；仍有公开SDK安装依赖 | 无 | 24 |
| 三维可压缩 Navier–Stokes | 未逐项承诺；仍有公开SDK安装依赖 | 无 | 6 |
| 2.1.1 2D 常黏度牛顿流体不可压缩流动稳态分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 10 |
| 2.1.3 3D 常黏度牛顿流体不可压缩流动稳态分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 10 |
| 一维周期黏性 Burgers | 未逐项承诺；仍有公开SDK安装依赖 | 有 | 1 |
| 一维矩形初态扩散 | 未逐项承诺；仍有公开SDK安装依赖 | 有 | 1 |
| 理想气体激波管 | 未逐项承诺；仍有公开SDK安装依赖 | 有 | 1 |
| 一维周期对流扩散 | 未逐项承诺；仍有公开SDK安装依赖 | 有 | 1 |
| 一维非线性熵输运 | 未逐项承诺；仍有公开SDK安装依赖 | 有 | 1 |
| 二维黏性 Burgers | 未逐项承诺；仍有公开SDK安装依赖 | 有 | 1 |
| 二维对角熵输运（终时 0.32） | 未逐项承诺；仍有公开SDK安装依赖 | 有 | 1 |
| 二维矩形初态扩散 | 未逐项承诺；仍有公开SDK安装依赖 | 有 | 1 |
| 二维对角熵输运（终时 0.40） | 未逐项承诺；仍有公开SDK安装依赖 | 有 | 1 |
| 矩形混合边界 Laplace 势 | 未逐项承诺；仍有公开SDK安装依赖 | 有 | 1 |
| 二维线性脉冲平移 | 未逐项承诺；仍有公开SDK安装依赖 | 有 | 1 |
| 不可压盖驱方腔（黏度 0.01） | 未逐项承诺；仍有公开SDK安装依赖 | 有 | 1 |
| 周期通道启动流 | 未逐项承诺；仍有公开SDK安装依赖 | 有 | 1 |
| 双 Gaussian 源 Poisson 势 | 未逐项承诺；仍有公开SDK安装依赖 | 有 | 1 |
| 四边恒温矩形稳态传热 | 未逐项承诺；仍有公开SDK安装依赖 | 有 | 1 |
| Gaussian 初温与持续热源 | 未逐项承诺；仍有公开SDK安装依赖 | 有 | 1 |
| Cess 闭合双壁湍流通道 | 未逐项承诺；仍有公开SDK安装依赖 | 有 | 1 |
| 不可压盖驱方腔（黏度 0.1） | 未逐项承诺；仍有公开SDK安装依赖 | 有 | 1 |
| 圆柱外圆环涡量流函数流动 | 未逐项承诺；仍有公开SDK安装依赖 | 有 | 1 |
| 周期 KdV–Burgers | 未逐项承诺；仍有公开SDK安装依赖 | 有 | 1 |
| 二维 Rayleigh–Bénard 对流 | 未逐项承诺；仍有公开SDK安装依赖 | 有 | 1 |
| 周期剪切流与被动示踪剂 | 未逐项承诺；仍有公开SDK安装依赖 | 有 | 1 |
| 圆管扰动的最右增长率 | 未逐项承诺；仍有公开SDK安装依赖 | 有 | 1 |
| Lane–Emden 正基态 | 未逐项承诺；仍有公开SDK安装依赖 | 有 | 1 |
| 2.1.2 2D 常黏度牛顿流体不可压缩流动瞬态分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 10 |
| 2.1.4 3D 常黏度牛顿流体不可压缩流动瞬态分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 10 |
| 2.1.5 2D 非牛顿流体不可压缩流动稳态分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 8 |
| 2.1.6 2D 非牛顿流体不可压缩流动瞬态分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 8 |
| 2.1.7 3D 非牛顿流体不可压缩流动稳态分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 7 |
| 2.1.8 3D 非牛顿流体不可压缩流动瞬态分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 8 |
| 2.1.9 2D 常黏度牛顿流体等温可压缩流动稳态分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 3 |
| 2.1.10 2D 常黏度牛顿流体等温可压缩流动瞬态分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 5 |
| 2.1.11 3D 常黏度牛顿流体等温可压缩流动稳态分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 3 |
| 2.1.12 3D 常黏度牛顿流体等温可压缩流动瞬态分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 5 |
| 2.2.1 2D 牛顿流体低速流动与传热稳态分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 10 |
| 2.2.2 2D 牛顿流体低速流动与传热瞬态分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 10 |
| 2.2.3 3D 牛顿流体低速流动与传热稳态分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 10 |
| 2.2.4 3D 牛顿流体低速流动与传热瞬态分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 10 |
| 2.2.5 2D 无黏可压缩流动稳态分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 10 |
| 2.2.6 2D 无黏可压缩流动瞬态分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 10 |
| 2.2.7 3D 无黏可压缩流动稳态分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 10 |
| 2.2.8 3D 无黏可压缩流动瞬态分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 10 |
| 2.2.10 2D 牛顿流体可压缩流动与传热瞬态分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 5 |
| 2.2.12 3D 牛顿流体可压缩流动与传热瞬态分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 5 |
| 2.3.1 2D 不可压缩湍流定常平均分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 8 |
| 2.3.2 3D 不可压缩湍流定常平均分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 7 |
| 2.3.3 3D 不可压缩湍流非定常平均分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 10 |
| 2.3.4 3D 不可压缩湍流尺度解析统计分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 10 |
| 2.3.5 3D 等温可压缩湍流定常平均分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 7 |
| 2.4.1 3D 低速湍流传热定常平均分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 9 |
| 2.4.2 3D 低速湍流传热非定常平均分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 4 |
| 2.4.3 3D 低速湍流传热尺度解析统计分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 10 |
| 2.5.3 二维不混溶双流体界面瞬态流动 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 10 |
| 2.5.4 三维不混溶双流体界面瞬态流动 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 10 |
| 2.8.2 可压缩气膜润滑瞬态分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 10 |
| 2.9.1 全湿浅水稳态分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 3 |
| 2.9.2 全湿浅水瞬态分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 9 |
| 2.9.3 干湿变化浅水瞬态分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 7 |
| 2.10.3 过渡区稀薄气体稳态分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 10 |
| 2.10.4 自由分子气体稳态分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 10 |
| 2.11.1 黏弹性流体稳态分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 9 |
| 2.11.2 黏弹性流体瞬态分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 9 |
| 2.2.9 2D 牛顿流体可压缩流动与传热稳态分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 4 |
| 2.2.11 3D 牛顿流体可压缩流动与传热稳态分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 3 |
| 2.4.4 3D 可压缩湍流传热定常平均分析 | Python、NumPy、SciPy、h5py、Gmsh、jsonschema | 有 | 4 |

## 建议的RC6验收

1. 复用固定源码已有的题目harbor/requirements.txt，将其纳入发行白名单、摘要与提取；Harbor与发行安装入口共同消费，共享基线集中维护，SDK本身保留协议职责。
2. 全82题分别在全新考生容器、独立且断网的verifier容器中运行适用依赖探针；保存镜像身份、包版本、真实导入、Gmsh初始化及本地编译能力证据。
3. 独立验证无Agent安装副作用继承、隐藏材料不可由solver用户读取；不追加收费模型试跑。
4. RC6明确网络构建前提、系统依赖和安装步骤；若不附OCI镜像／wheel，则不能声称环境完全离线。
5. 用文件摘要证明题目、case、参考、评分和角色未变；独立记录环境／安装材料／打包差异。
6. RC5保留，Release顶部勘误；本次按用户指示不更正受影响成绩，不将环境验证宣称为数值或异机资源最终验收。

本报告是需求与打包静态盘点；实际实现和全容器验证完成后仍需复核。
