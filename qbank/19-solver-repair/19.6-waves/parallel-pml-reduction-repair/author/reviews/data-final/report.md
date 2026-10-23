归档阅读副本：仅调整相对链接以适应归档目录；独立审阅原始字节保存在同名 `.source.txt`，数值与结论未改。

# SPECFEM661 独立全数据审阅

结论：**通过（P1已由文末有界复核关闭）**。初审发现 DATA 的 C-PML 外终端声明 Neumann，但固定原生求解器实际上强制零势；现已更正为真实Dirichlet。全量数据、参考绑定及独立数学核验未发现其他阻断问题。以下保留原发现证据，8/8 Oracle 或小的 Green 残差本身均不能关闭该冲突。

日期 2026-10-23；范围为 `qbank/19-solver-repair/19.6-waves/parallel-pml-reduction-repair`。应用 caeoj-data-review 与 caeoj-configure-judge 技能；不是候选盲审。不改题，不制作数值，不运行付费模型，不重跑原生制数流水线。独立检查脚本 [checks.py](checks.py) 与完整机器证据 [actualchecks.json](actualchecks.json.gz) 均保留；后者记录逐文件 SHA、逐数组值摘要、全部形状/范围/采样及逐例 grade。

## P1：C-PML 外终端并非公开声明的自然 Neumann

位置：DATA.md「声学边界和C-PML」第二段：`PML外终端z=0、800也采用chi的自然齐次Neumann边界，无额外Dirichlet强制值`。

真实链条为 `public/run_case.py:prepare` 将每个试件 PML 顶/底外面写入 DATA/absorbing（side 1/3）；`read_mesh_databases.F90:710–716` 因 nelemabs>0 设置 anyabs=true；`compute_forces_acoustic_calling_routine.F90:62–65` 在 PML 开启时调用 `pml_boundary_acoustic`；`pml_compute.f90:437–481` 对这些边界节点显式将 chi、chi_old、chi_t、chi_tt 全置零。该函数开头保留了一段“Neumann / nothing to enforce”的陈旧注释，但下方实际执行体相反，不能依据注释判断边界。

独立只读生产容器核验：pml_compute.f90 SHA256 `d828a6e341f45ae9cd59244ac15c020ba1067fb709bbbf6d8c4f973cc61aab4a`；calling routine SHA256 `3cb2e7625d798150983c654f93f5fcde54cdc73ae7f899532f65ea49bf4f1105`。全部 916 个 archive src 文件在 runtime 原件镜像无差异，production 镜像仅 get_MPI.F90 有差异。真实 production obj/exe 与最终 v3 Oracle 重编产物相同，排除了本地解压树与生产者不同的解释。08-serial-pml 的实际 absorbing 文件含64个顶/底面；04/05 同样提供相应外面。

影响：04、05、08 的固定离散参考和要求公开的外端边界不等价；有限 C-PML 很好地吸收并不能把二者数学上等同。最小修订为将公开外终端说明改成固定库实际的零 chi 强制约束，清楚区分物理内部/PML连续界面与外终端；保留原参考与原生实现。改动公开材料后重包并有界复核身份，旧包的 Oracle 不得改名成新包执行。若坚持原 Neumann 物理，则需改原生实现与参考生产，这超出本轮审阅范围。

## 全量覆盖

读取了 instruction、DATA、CONTRACT，全部8份 case JSON、HDF5的每个值、全部网格节点坐标与单元连接、8个隐藏 reference/grading、2个公开样例的完整 input/output/reference，以及每例原生 DATA、ASCII trace、mesher分区数据库和原件运行终态。没有只读元数据后声称全量读取。

| case | 单元 | Nt | 真正接口数/rank | 全参考grade | 最大Green相对L2 |
| --- | ---: | ---: | --- | ---: | ---: |
| 01-connected-sh | 2048 | 3200 | 1,2,1 | 1 | .006883 |
| 02-isolated-master-sh | 3072 | 3200 | 0,1,1 | 1 | .008300 |
| 03-isolated-last-sh | 4800 | 6400 | 1,1,0 | 1 | .001936 |
| 04-isolated-master-pml | 3072 | 3200 | 0,1,1 | 1 | .006149 |
| 05-isolated-last-four-pml | 4096 | 3200 | 1,2,1,0 | 1 | .006149 |
| 06-connected-acoustic | 2048 | 3200 | 1,2,1 | 1 | .000440 |
| 07-serial-sh | 1600 | 6400 | 0 | 1 | .001820 |
| 08-serial-pml | 1024 | 3200 | 0 | 1 | .000382 |

每例读取全部参考支持数组 times/probe_ids 和 wave_response；原始 ASCII 的全部采样值与 HDF5 参考逐位相同，ASCII 时间与精确支持时间误差在5e-8s内。按最终转换器重新序列化全部输入，不运行 solver，逐文件字节等于保留的原生 DATA。原件完成的01/06/07/08全部结果与参考逐位相等；02/04真实归约报错、03/05真实90秒超时由保留 failure/log 记录，不以失败例假造数值对照。

| 公开定义 | 对照字段与实际读取证据 |
| --- | --- |
| 任务/模型/单位 | JSON顶层、physics全部6参数、fields/outputs逐项核对；SH/acoustic各自quantity/unit与分支匹配 |
| 坐标与身份 | Gmsh XYZ全部第三槽0；前两槽直接序列化为物理x,z；全部正quad tag与严格递增cell_ids完整覆盖；独立source/probe IDs与每一数组行对应 |
| 网格与分区 | 一/两完整均匀矩形、空隙、CCW连接、h/CFL范围；实际原生unformatted数据库完整读取，核对各rank单元数和接口数，包含合法无接口rank与仍需通信的其他rank |
| 初值与有限源 | zero initialfield；时间从-1.2/f开始；Ns1/2、正负幅度、多源同中心；原生Ricker带负号，SH直接负力，声学再以源注入负号及质量/kappa抵消得到公开正势源；没有将势当压力/位移 |
| 采样 | 全部times、static_time、坐标、[1,Ns,1]源、[1,Ne,1]标志；原始chi seismotype6、SH BXY，GLL空间插值；write_seismograms.F90明确sngl后E14.7，支持轴仍复制float64 |
| PML | 每试件上下三行类别2，内部0，左右无PML；L=3h；NPOWER2/Rcoef.001/damping_modified_factor_acoustic.5给出公开dz系数，K=1、alpha=pi*f*(1-eta)；外终端冲突单列上文 |
| 输出与评分 | 全time/probe完整标量结果，无坐标/附加场，两个样例grade1，8隐藏reference逐case grade1；两分支阈值和非法输出另实测 |

12个从 DATA 独立选取的输入变体均达到预期：普通、负源、非连续probe IDs合法；processes浮点、错误单位、时间平移、缺一PML格、x-PML类别1、声学非零cs、墙上probe、零源、逆序cell_ids拒绝。两分支各8个输出变体：在初态reference=0处选atol的.999/1/1.001倍，前二通过、后一失败；NaN、复制轴改变、缺IDs、多余dataset、float32均失败。脚本在真实数据副本操作，未改正式文件。

## 独立数值依据及界限

逐式审阅了二维因果Green核 `H(t-r/c)/(2*pi*c^2*sqrt(t^2-(r/c)^2))` 与有限起点 Duhamel。以 `s=t-(r/c)cosh(v)` 代换后，积分界0至acosh((t+1.2/f)/(r/c))，与生产数学核一致；SH系数-F/rho、声学+A。矩形Neumann图像源全为正，独立试件只计本体源。对每例全部time/probe重新计算128和256点积分，且另写10万点midpoint积分检查单个核（每例选一个非波前时刻），误差<1e-14。逐例因果界验证 |m|或|n|>=3的遗漏图像均在计算窗外，有限图像截断没有丢失可能到达的波。

这证明源符号、量纲尺度、坐标、传播速度与大部分反射响应一致，**不证明逐点计分容差内的连续解精度**；该题明确以相同真实离散响应为参考。最大全时程L2差0.8301%，SH离散色散主导；积分128/256差远低于1e-7。未把连续误差用作实际grade阈值。

PML独立基准使用理想open-z延拓与左右Neumann图像，绝非有限C-PML精确解。late严格为physical times>0.35s：04/05各1560样本，08为1320样本；另计算完全反射上下壁的返回场，分母非零，实际晚段残差/未吸收z返回波L2为.000453–.006303。全部后段参与检查，未截尾，但它只支持吸收有效及保留有限层残差，不能认证外终端Neumann、逐点微小反射或完整CPML离散实现。P1正是这个限制下发现的源码/公开定义冲突。

## 身份与交付边界

本轮冻结数据HF revision `917ce12944449597f47ca95c1433edbe07134baf`；本地52装配项与strict data verify有效，样例身份01/04，公开2+隐藏6，总分母8。独立执行 `.venv/Scripts/python.exe -m caeoj_tools.cli data verify --task parallel-pml-reduction-repair --strict` 退出0。本轮未再联网重取HF，固定提交全新cache装配证据来自既有receipt并与实际资产SHA交叉核对。

审阅时公开ZIP `9cd9a7479aaa7973194bfd5099e97fbc60f40c8133cddcce8b2e7552f54c3f39`；新prepared judge `5595500ff6c8612f4682f4eda0cdc6521c5af94343dcba6c825bb3555141180f`。原生来源baseline fa6e905bc5cd63487cc24f68233f5992830f8b6e，修复get_MPI blob d843513239390f2bdc18046514b6d4efb2f36235。逐文件SHA见actualchecks，后续文档修订属于新身份，不覆盖本报告所审的原版本。

同版本正式v3全8例返回数组核对、7个真实后端probe、真实两分支最大声明资源输入及构建产物另见 `runs/configure-judge/repair22-specfem661/report.md`。本报告不代替来源设计/盲审，也不把HF strict、Oracle或数学残差当作公开物理定义正确的证明。

## 最终22aa包有界闭包

根协调者修订DATA后，本审阅独立执行 [bounded_closure.py](bounded_closure.py)，证据 [bounded-closure.json](bounded-closure.json)：新ZIP SHA256 `22aa0bcf168c9cabd7853ec8a63e2498838968fb53aa996034cb3e48108144d7`，44成员集合完全相同，对旧prepared9cd包逐成员比较，仅DATA.md及MANIFEST.json变化；MANIFEST仅DATA条目的摘要变化，其全部新文件摘要均实际校验。新DATA与工作区UTF-8内容一致（装配换行归一化），工作区64项公开工具/extension/harbor/input/reference/sample/config资产相对于初审冻结摘要不变。

新DATA明确PML上下外终端chi=0齐次Dirichlet，保存旧chi、chi_t、chi_tt也置零，与独立读取的原生执行体一致；无PML四壁及PML左右Neumann不变。因此P1关闭，未重生产8份native reference。Green/open-z和late残余证据只能验证传播与吸收量级，不能反证旧Neumann误写。原v3的数值8/8仍准确绑定**9cd旧文档包**及559550 judge；本次只基于逐成员不变证明将原有数据/程序/参考数值证据有界复用于22aa文档修订身份，未称22aa已经运行新Oracle。根另行安排的候选/设计文档复核不属于本轮结果。
