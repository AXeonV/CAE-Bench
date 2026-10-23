# CFDCodeBench 本地迁移维护记录

本目录维护 2.13 的 24 个来源身份。考生只需本题 instruction.md、DATA.md 与通用 CONTRACT；这里的生产方法、来源、解法及验证记录均为作者材料。原生计算与完整日志暂存仓库忽略的 `runs/cfdcodebench-local-20261019/`；题库本地装配与选择由 [装配索引](local-assembly-index.json) 单独记录。当前 HF 独立分支、固定提交与下载验证见 [HF 发布索引](hf-release-index.json)；main 未修改。资源实测与正式 benchmark 分开记录。

## 冻结定义与来源

上游为 [NLR-Theseus/cfdllmbench](https://github.com/NLR-Theseus/cfdllmbench/tree/e37e8b61fbb1f3532dcfd2f2e8ab67e7c91c3ee2/CFDCodeBench/PDE_Benchmark)，固定提交 `e37e8b61fbb1f3532dcfd2f2e8ab67e7c91c3ee2`。`fetch_upstream.py` 下载原 prompt、程序、数组和许可证，`upstream-manifest.json` 记录每个文件 SHA256；`UPSTREAM-LICENSE.txt` 保留 BSD-3-Clause。第三方求解器各自的许可证仍适用。

| 项目 | 本次明确冻结的定义或来源差异 |
|---|---|
| C12、C18 | 用户批准修订：连续不可压 NS，保留盖板及其他速度边界；压力由方程确定，仅固定常数基准。原程序的整条盖板 p=0／全墙独立压力条件不作为物理要求。 |
| C17 | 用户批准采用作者实际程序：d=min(y,2-y)，对称双壁 Cess，μeff=μ+μt。不得直接把整条通道的 y 当最近壁面距离。 |
| C19 | 用户批准：原零内点涡量经 Dirichlet Poisson 解初始化流函数；内壁连续无滑移 ψ=20、ψr=0，外壁原 ψ、ω 保留。原程序黏性中心系数缺少因子 2，且最终 ψ、ω 更新时间不一致，原数组只作复现证据。 |
| C22 | 用户批准：对原速度作周期 Helmholtz 投影；示踪剂仍为原水平剖面。 |
| C24 | 采用三维球对称径向算子 f''+2f'/r；中心正则极限为 3f''(0)，仅取正、无内部节点的基态。 |
| C02、C06 | 原循环的最终时间与文字有舍入或多一步差异；迁移按 DATA 的精确终时取值。 |
| C08 | 原程序声明 nt=17，却实际调用 diffuse(50) 并执行 nt+1 步；不将其原数组误称为 t=0.3777 的解。 |
| C04、C20—C22 | 浮点 while／自适应时间推进最后一步截断到 DATA 的精确终时；不拿最后一次定期保存的早期快照代替终态。 |
| C07、C09 | 保留两个来源身份及不同终时；在 u=v 的不变量下明确为对角标量守恒熵解。 |
| C11 | 间断线取两侧均值，交叉角点四象限均值为 1.25。公开 DATA 明示。 |

`catalog.py` 是题内固定模型事实与生成材料的维护源；`render.py` 生成题面、DATA、模型声明和配置。改变物理定义须先更新这里的决策和公开 DATA，再重算与复核，不能只替换隐藏 reference。

## 生产者与独立验证的分工

上游 24 个原程序均在本地真实执行。40 个输出数组与固定提交中数组的最大绝对差均小于 1e-7，详见 `replay-array-comparison.json`；这证明复现一致，不证明连续方程精度。原件与修改后的程序分别保存。

| 题目 | 选定参考的生产表示／求解器 | 验证依据 |
|---|---|---|
| C01 | 作者 Cole–Hopf Gaussian 表示的稳定周期求和 | 原显式公式与周期像截断比较 |
| C02 | Dirichlet 热方程正弦展开 | 镜像热核独立积分；原程序精确终时与空间加密 |
| C03 | 理想气体精确 Riemann 表示 | Clawpack 独立 exact Euler，逐 rho、u、E 比较；波未到反射墙 |
| C04 | 周期 Gaussian 对流热核 | 独立 Fourier 积分与初态尾部界 |
| C05 | 周期 Burgers 熵解 Hopf–Lax 全局极小值 | 原 Lax 程序原数值循环经编译执行三档加密，不只测试残差 |
| C06 | 作者 CFDPython 二维 Burgers 离散程序，修正终时 | 81/161/321 三档与细档半时间步；独立 NGSolve P3 弱式 IMEX |
| C07、C09 | 对角不变量上的分段线性势 Hopf–Lax | 独立稀疏波／冲击相互作用显式表示 |
| C08 | 矩形初态乘积热级数 | 独立镜像核；原程序修正终时后三档加密 |
| C10 | 作者已有混合边界 Laplace 分离变量级数 | 独立 NGSolve P3 三档网格 |
| C11 | 特征线精确平移 | 独立几何回溯及边／角点约定检查 |
| C12、C18 | NGSolve 官方 Navier–Stokes IMEX 教程适配固定方腔 | 三档含角点加密的网格、细档半时间步；现成 OpenFOAM pimpleFoam 独立求解 |
| C13 | 启动 Poiseuille 正弦级数 | 独立 Dirichlet 热核积分 |
| C14 | Gaussian 源 Poisson 双正弦表示 | 独立 NGSolve P3 三档网格 |
| C15 | 四侧定温分离变量表示 | 独立 NGSolve P3 三档网格；统一 BoundaryCF 保留全部边值 |
| C16 | Gaussian 初态与持续源的 Duhamel 热级数 | 独立 NGSolve 稳态解加显式瞬态衰减界；不把稳态直接冒称终时解 |
| C17 | Cess 有效黏度下的一维通量积分 | 独立 solve_bvp 通量边值系统，三档求解容差 |
| C19 | 现成 OpenFOAM pimpleFoam 连续环域配置（R256-P384） | 独立 NGSolve 混合流函数／涡量配置，多网格及半步；重建误差单列 |
| C20—C22 | 作者 Dedalus 方程配置，应用已公开定义修订 | 三档谱分辨率与细档半时间步；不同求解器验证尚不能据此声称完成 |
| C23 | 作者 Dedalus disk EVP | 三档径向分辨率；独立无散多项式 Galerkin 广义 EVP、残差及质量矩阵条件数 |
| C24 | 作者 Dedalus NLBVP 正分支 | 三档径向分辨率；独立正则 IVP 首零点缩放 |

求解器版本为本地 Dedalus 3.0.5、NGSolve 6.2.2608、OpenFOAM 1912。`sources/validation-sources.json` 存补充文献／官方教程快照和摘要；教程动态 URL 的证据是实际下载文件的 SHA256，不冒称固定提交。Clawpack 验证固定在 `5b171f11fd7a3e810ee7a74a4d9f2dff01d65a6e`，代码许可证一并归档。NGSolve 官方教程见[不可压流](https://docu.ngsolve.org/latest/i-tutorials/unit-3.2-navierstokes/navierstokes.html)及[Poisson](https://docu.ngsolve.org/latest/i-tutorials/unit-1.1-poisson/poisson.html)，Dedalus 参考 [tau formulation](https://dedalus-project.readthedocs.io/en/latest/pages/tau_method.html)。

独立验证器不是参考来源的替代品：自写 Galerkin、混合有限元或 ODE 配置只承担交叉验证；引用 NumPy／SciPy 库本身不能证明某个 PDE 生产者已有明确出处。失败的环域谱配置及其非有限、秩亏证据保留在本地 `experiments/retired-adapters/`（含原脚本 SHA256 索引），不再保留为正常维护入口，不能算作通过。

## 解析表示的复核要点

`analytic.py` 只求值数学表示，不实现新的 PDE 时间推进器。`analytic_crosscheck.py` 使用不同表示验证同一固定问题。

- 齐次 Dirichlet 的矩形初态，先减背景，展开 sin(nπx/L)，系数由初始矩形的精确积分得到；乘 exp(-ν(nπ/L)^2 t)。二维分离初态为两个一维解乘积。镜像核是两组符号相反的 Gaussian 像，不复用正弦系数。
- 启动通道：稳态 uP=y(2-y)/(2ν)，解为 uP 减去该抛物线初态的齐次热演化；Green 核积分验证其终态。
- 周期黏性 Burgers：Cole–Hopf 的周期 Gaussian 像及其解析导数作比值，整体漂移 4。稳定求和只提取共同指数，未改变物理参数。
- 一维熵 Burgers：V(x,t)=min_y[V0(y)+(x-y)^2/(2t)]。C05 初速度的周期均值非零，原函数跨周期每圈增加 2；不能把原函数强行周期化。枚举驻点及分段端点后取全局最小，u=(x-y*)/t。
- 对角熵脉冲：沿 x-y 不变量化为一维高度 1 的凸通量脉冲并叠加背景 1。脉冲宽 W，稀疏波与冲击相遇后冲击位置 a+sqrt(2Wt)，相遇前 b+t/2。两种表示分别编码验证。
- Poisson／热／Laplace：将已知边界分离或减去边界抬升，展开相应本征基；源系数按实际 Gaussian 积分。Duhamel 系数为 Fmn(1-exp(-λmnt))/λmn，初态项独立保留。C16 的稳态交叉验证误差还必须加上 exp(-π²t/2) 乘初态与稳态差范数的界。
- Cess：由 (μeff u')'=-1 和对称性得到 μeff u'=1-y，积分并固定 u(0)=0。独立 BVP 直接解 u'=q/μeff、q'=-1，双墙 u=0。
- 管流 EVP：以 s=r²、螺旋速度 v±=ur±i uθ，采用 v+∝r^(m+1)(1-s)P(s)、v-∝r^(m-1)(1-s)P(s)、w∝r^m(1-s)P(s)。散度多项式为 (m+1)F+ +s F+' +F-' +ik Fw；先在其零空间投影再解广义 EVP。高阶质量矩阵病态必须记录，不能只凭小残差判正确。
- Lane–Emden：正则原点 IVP 从球对称级数起步，取首次零点 R 再按 f(r)=R θ(Rr) 缩放，分别满足中心正则与 f(1)=0；不接受其他带节点分支。

## 本地执行与数据装配

仓库 Python 负责协议与装配；科学求解器 Python 在本地 WSL。不要将以下 local 工作流替换为 titan 路径。各队列每个任务保存原配置、PID、实际返回码、墙钟时间、标准输出及原生场；未结束记录不能当成完成凭据。

```powershell
# 固定来源、重建公开定义（均不发布数据）
.venv\Scripts\python.exe qbank/02-fluid-mechanics/2.13-cfdcodebench/author/fetch_upstream.py
.venv\Scripts\python.exe qbank/02-fluid-mechanics/2.13-cfdcodebench/author/render.py
# 完成求解后按真实输出装配；不调用考生
.venv\Scripts\python.exe qbank/02-fluid-mechanics/2.13-cfdcodebench/author/build_local.py
.venv\Scripts\python.exe qbank/02-fluid-mechanics/2.13-cfdcodebench/author/certify_local.py
.venv\Scripts\python.exe qbank/02-fluid-mechanics/2.13-cfdcodebench/author/verify_local_install.py
.venv\Scripts\python.exe -m unittest discover -s tests -p test_cfdcodebench.py
```

科学环境运行 `replay_upstream.py`、`spectral_queue.py`、`cavity_queue.py`、`burgers_refine.py`、`cavity_openfoam.py`、`cylinder_openfoam.py` 及对应独立验证脚本。队列尚有活动进程时不可重开同一任务；先核对 PID、命令及实际输出，不能仅凭耗时重启。

本地池为 `local-pool/<task>/Cxx-base/{input,reference}`。参考包含 reference.h5 和实际 case 级 grading.json，输入含 problem.json/input.h5。`author/grading-template.json` 是共享 quantity 策略，`author/case-grading-template.json` 是带转换的完整 case 计划；最终判分以该 case 的 reference/grading.json 为准。

## 判分、验收和局限

当前发行范围使用各题instruction.md定义的连续max-NRMSE评分，author/grading-template.json保存完整case配置和显式scoring；实际依据仍是正式case的reference/grading.json。六题既有压力去均值／温度背景变换保留，其他物理定义不变。NRMSE下限继承既有1e-6；C23使用旧绝对误差限1e-4作为尺度下限，这不是旧判据的等价重写，也未新增数值校准。历史证书、分数及原始来源比较不能当作新版分数。权重、时间、ID、单位、维度与字段完整性由实际SDK检查。

参考内部目标比考生容差更紧：默认数值比较 NRMSE≤0.01，C23 绝对差≤1e-5；C19 经用户明确接受现有参考，按原目标 NMSE<0.01 验收（唯一例外配置见 reference-acceptance.json），历史更严格检查失败记录保留，并保留逐字段空间、时间及不同表示差异。解析题以表示等价性、截断／尾部界替代伪造的网格计算。数值阈值通过不自动证明数学模型无误；定义审阅、实际求解、独立核验与消费链分别记录。对强非定常 C21/C22，不做时间／相位对齐、不滤波，也不暗中改为统计量评分。

24题已在4CPU、8192MiB、无网络Docker中实际运行可通过评分的生产表示，测量与预算依据见 [资源索引](resource-calibration-index.json)。实际配置由各题 judge-config.json 与 harbor/task.toml 维护；科学生产者环境Python3.12的测量不代替候选Python3.14环境消费验证，也不保证任意数值方法都能满足限额。24 题已在 HF 独立分支发布并按固定提交重新获取验证；尚未运行 LLM 考生或 Agent benchmark。

实际逐题状态由[轻量验证索引](evidence-index.json)；详细依据为本地 `local-validation-summary.json`、每例 `validation.json` 及 `certification.json` 记录；`reference_self_grade=passed` 仅说明结构与判分链自洽，不能解释为 reference 已独立验证。未算完、验证失败或独立依据不足的题须保持未就绪，不静默放宽容差。

审阅完整证据在 `runs/design-review/cfdcodebench-implementation-20261019/`、`runs/candidate-review/cfdcodebench-20261019/`、`runs/design-review/cfdcodebench-judge-20261019/`、`runs/data-review/cfdcodebench-20261019/`；普通 wheel 安装、移走源码、切换工作目录、隔离解释器的 24 题 CLI/SDK 证据在 `runs/install-check/cfdcodebench-20261019/`。这些验证不代表正式 benchmark。

运行环境快照在本地 `scientific-environment.json`。专项判分 6 项、数量评分相关 68 项、领域装配 1 项与 runtime 非目录断言 6 项已分别实际运行。完整 runtime 目录测试遇到 HEAD 原有的 126 个 FOAMBench 题面无评分模板／无工具绑定，基线核对保存在 `runtime-suite-baseline.json`，没有借本次迁移补齐或掩盖这些题的未实施状态。


需要在现有长任务完成后收束时，可单次运行 `finish_local.py --wait-hours 24`。它只等待既有队列的实际结束记录，再重建已完成的 OpenFOAM 场、装配、审计并以正常安装的 CLI 消费真实数据；不会启动／重启求解器或创建定时任务。重复实例由本地锁拒绝，作者 Python 脚本在等待期间变化会要求人工复核。当前阶段与逐任务状态写在本地 `completion-pipeline.json`；等待到期不终止仍活跃的计算，也不声称任务完成。完整目录测试的既有 FOAMBench 缺项、资源待校准与独立求解器覆盖局限仍单独保留。


## 题库装配与固定提交恢复

当前 24 题均装配一个计分测试 `cases/001/`、`reference/001/` 与一个随机格式样例 `samples/01/`。[装配索引](local-assembly-index.json) 记录当前选择；[HF 发布索引](hf-release-index.json) 记录独立分支、main 起始提交、固定提交与摘要。每题 data-manifest.json 是选样配置；旧 23 题离线批次保存在 history，不代表当前状态。

`release_verified.py` 复用既有 pack/upload/select/fetch/assemble/verify，逐题绑定认证的 reference 摘要、固定 HF revision，并由正常安装的 CLI 实际判分。运行日志与完整回执位置见发布索引。所有上传显式指定独立分支，main 未写入；恢复时显式指定清单里的固定提交。

```powershell
.venv\Scripts\python.exe qbank/02-fluid-mechanics/2.13-cfdcodebench/author/release_verified.py --check
# 以下命令按当前已冻结 manifest 获取并严格装配。
.venv\Scripts\python.exe -m caeoj_tools.cli data fetch --task cc-1d-burgers-equation
.venv\Scripts\python.exe -m caeoj_tools.cli data assemble --task cc-1d-burgers-equation
.venv\Scripts\python.exe -m caeoj_tools.cli data verify --task cc-1d-burgers-equation --strict
```

原生场、prepared/bundle、题库载荷与完整装配回执不进 Git。资源预算已依据容器实测设置；正式 benchmark 仍须完成候选/verifier隔离与公开包消费预检。

## 随机格式示例

24 题均提供 `samples/01/input/` 与 `samples/01/output/result.h5`。输入与该题唯一计分测试相同，因此本批是公开输入测试，不能作为未见输入泛化证据。输出值使用固定种子的 NumPy PCG64 在 [-1,1) 上生成，不读取参考场；shape、dtype、ID 与时间轴服从真实输入。种子和摘要在每题 author/data-evidence/format-example.json。

格式示例不是正确解，仅用于结构校验；不含真实 reference 或样例 grading.json。发布流程核对 case ID、真实参考摘要、随机输出结构和普通安装 CLI 的消费结果。生成公开 ZIP 与正式 benchmark 分别记录。
