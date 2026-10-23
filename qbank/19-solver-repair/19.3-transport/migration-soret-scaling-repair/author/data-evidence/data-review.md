# 全数据独立审计：migration-soret-scaling-repair

结论：**通过**。12个正式case、2个公开sample及其全部实际输入/参考均与最终三文件一致；结构、物理、离散数值、来源关联及固定HF回取均完成本轮核验，未发现未决问题。

角色边界：此次明确转为caeoj-data-review，允许读取作者证据、真实模块和可信驱动；本报告不称盲考生审阅。前次两个candidate-review报告仍保持其原有盲材料范围。本轮只写runs/data-review/repair22-elmer，未改正式题面、实现、数据、选择或回执；未执行修复、模型或付费benchmark。

## 冻结与完整覆盖

- HF固定提交：`4148aa0822f399d96b7d6aca9e24764dcca9b7af`，仓库jimzhouzzy2006/CAE-Bench-OJ，task_id=caeoj-190301。
- 最终公开ZIP SHA256：`9a660158718cf8b451985e8b70d684774b0b042efae20a487ab481c9035e5ba7`，收束时重新计算一致。
- 初审时本地assembly revision=local；随后官方fresh-cache固定提交回取complete=true、70 files、changed=0、incomplete=[]。本审计读取回取结果，并在其后逐一重新算70个本地资产SHA，与最终receipt全部吻合。所有已审计JSON/HDF5/mesh/reference在回取前后未变。
- .data-assembly SHA256：`6a67c3aecad521c607800762b35a7b7551b7f3ce6afea04147a0e150b4c70481`。选择包含12case+2sample，逐一核对descriptor原文SHA与选择绑定；sample01/02分别复用正式case01/02，是明确public_cases，不误算独立工况。
- 本审计另执行官方data verify --strict，回取前后均valid=true；最终结果在final-strict-verify.json。回取/作者strict收据哈希见evidence.json:hf_final，未自行编辑回执。

| 核心文件 | SHA256 |
|---|---|
| instruction.md | c273ff5c708efd7578852a06c565061205b3b28fd10a0bcf4f489f271cf4f8f6 |
| DATA.md | 099e93d85614463e91dfc69be52c68f9f2bd7ada09bb7d7235963cdbd433b578 |
| CONTRACT.md | 130d4416fd533812493780c8bc6afbc0a158de6800b59bbec14a852f3cf1c063 |
| data-manifest.json | 5e7c54e14513f157c82ab9ffe13667779ab9dce83c7d9f6f994c809d39757a85 |

实际覆盖：所有14入口的完整problem.json、完整输入HDF5六数组、全部Gmsh节点/连通/物理组；所有14份grading.json及reference.h5的全部五数组，均读取完毕，没有未读大数组或只用头部代替数值检查。每个输入、网格、参考、配置的精确SHA和shape/dtype记录在evidence.json:cases，全部70个资产已绑定。

inventory.py报告两处samples/*/output/result.h5缺失。核对MANIFEST、选择及descriptor均为example=null，公开资产实际提供samples/*/reference/reference.h5，并未承诺另一个output/result.h5，因此是通用盘点脚本对固定布局的缺口提示，未当作漏交公开输出。两份实际公开reference已完整检查。

## 声明到载荷的覆盖

| JSON/HDF5/网格项 | 文档约定 | 实际检查 |
|---|---|---|
| task/spatial_dimension/physics.model/geometries/meshes/fields | DATA声明段，二维规定模型、一个main网格、无外加场/几何 | 14/14一致，无未声明外部依赖 |
| physics.parameters六项及嵌套value/unit | DATA参数表，模式、单位、ρ/D/DT/z合法域和跨字段约束 | 全部六项及单位/有限性/范围检查；四个机制×单位交叉格各3正式case |
| conditions | DATA两模式PDE及六条上下边界，侧边齐次自然条件 | 所有role/operator/location/data.value与单位匹配；电迁移等温DT0；Soret z0、等电势、顶端零总通量 |
| node_ids及四边ids | DATA网格/位置，CONTRACT §3–4 | 正int64、严格递增唯一、全节点/全组边、稀疏tag身份而非行号，全部元素连通/CCW/外边父单元/笛卡尔网格检查 |
| times/instant | DATA稳态索引，CONTRACT §5 | float64[1]=[0]，所有输出保留时间轴 |
| 三个output元数据与数组 | DATA输出，CONTRACT §6、9 | 三场point scalar float64[1,N,1]、所有有限；复制node_ids、times逐值逐序一致，完整五key且不复制仅边界ids |
| grading.json | instruction点值绝对+相对容差，全部场全部节点 | 全部配置一致；14份现有参考按官方完整消费链自判通过，仅作合法性/覆盖检查，独立数值见后段 |

## 全部工况与独立数值核对

不调用作者independent.py，也不从作者data-audit.json或12/12结论导出数值结论。沿前次盲审已推导的标准Galerkin均匀节点递推核对电迁移；令a=zeΔφ/(kBT)、r=(1-a/(2ny))/(1+a/(2ny))，u_j=u_0+(u_n-u_0)(r^j-1)/(r^n-1)，a=0使用线性极限。Soret核对u=u_bottom-(DT/D)(T-T_bottom)。温度、电势核对Laplace线性剖面。依据实际tag→坐标对所有节点计算，比较的是规定离散节点值而非连续迁移指数误差。

| case | 机制/单位 | ρ | z | DT符号 | nx×ny / N | 浓度最大绝对差 | 最坏三场误差/题面容差 |
|---|---|---:|---:|---|---|---:|---:|
| 01-migration-relative-public | 迁移/质量分数 | 1200 | 1 | 0 | 1×400 / 802 | 2.2371e-13 | 0.00018671 |
| 02-soret-absolute-public | Soret/质量浓度 | 1000 | 0 | + | 1×400 / 802 | 1.3016e-12 | 0.00020585 |
| 03-migration-absolute-pair | 迁移/质量浓度 | 1200 | 1 | 0 | 1×400 / 802 | 3.1844e-10 | 0.00018671 |
| 04-soret-relative-pair | Soret/质量分数 | 1000 | 0 | + | 1×400 / 802 | 2.7513e-15 | 0.00020585 |
| 05-negative-ion-low-density | 迁移/质量分数 | 0.2 | -2 | 0 | 2×320 / 963 | 2.6501e-13 | 0.00017915 |
| 06-unit-density-active-migration | 迁移/质量浓度 | 1 | 2 | 0 | 2×240 / 723 | 1.496e-13 | 0.00013491 |
| 07-negative-soret-cooling | Soret/质量分数 | 1 | 0 | - | 2×300 / 903 | 1.2008e-12 | 0.00043902 |
| 08-negative-soret-warming | Soret/质量浓度 | 250 | 0 | - | 3×280 / 1124 | 1.0716e-10 | 0.00020629 |
| 09-zero-ion-diffusion-control | 迁移/质量浓度 | 3 | 0 | 0 | 3×200 / 804 | 2.1194e-13 | 9.263e-05 |
| 10-zero-soret-control | Soret/质量分数 | 0.5 | 0 | 0 | 2×160 / 483 | 2.2887e-13 | 4.5774e-05 |
| 11-weak-drive-dense-fluid | 迁移/质量分数 | 5000 | 1 | 0 | 1×300 / 602 | 2.9243e-13 | 0.00018054 |
| 12-low-density-absolute-soret | Soret/质量浓度 | 0.2 | 0 | + | 3×400 / 1604 | 2.5675e-13 | 0.00021163 |

两sample是case01、02的同一绑定输入与参考，全部重读重算，数值结论相同。全部14组独立节点值比较通过，最坏误差/允许误差=0.00043902077，远小于1。两组物理等价单位配对c/ρ与Y的全部节点最大差：
- 01-migration-relative-public : 03-migration-absolute-pair: 5.10702591e-14。
- 04-soret-relative-pair : 02-soret-absolute-public: 1.45304775e-15。

差异覆盖不是12个全独立物理家族：01/03与02/04是特意的单位等价配对。其余工况覆盖正负离子、正负电势梯度、低/单位/高密度、DT正/负/零、升温/降温、z=0纯扩散控制、零Y边界、弱迁移、nx1/2/3及稀疏tag。07、08负DT的升降温方向与浓度升降都符合公开通量符号；12低密度绝对模式未施加额外ρ补偿。物理域由实际参数/边界逐值检查，未因参考内容扩大题意。

## 参考来源与实际生产链

工况来源与生产者分开：cases.json明确正式工况是作者围绕固定上游机制改编，未宣称这些正式case是原始上游输入。真实来源为[Elmer issue870](https://github.com/ElmerCSC/elmerfem/issues/870)及[PR872](https://github.com/ElmerCSC/elmerfem/pull/872)，本轮读取官方页面核实两种单位模式下相反的多余密度系数机制。

- 基线a3f108c8580efd649e84b35842cd92a06c834331、修复head cd35f9d23145519973ed66c62661a0298105bf3a。直接重取官方raw固定版本模块并计算SHA，分别为`9758678f1cfd0d274e3dce05c3872aeb122227e07b54f4a27ed3a714efbec313`、`0f905d9e75ba747c546c849ad381883c8447c0c3a721fbf8ac282253bdd58dad`，与实际公开tar基线模块/author generated修复模块一致。
- 从公开tar完整读出源码闭包2468文件，逐文件与source-closure.json散列核对全部一致。机械将完整上游patch应用于该基线模块，重新算出的结果与官方固定head及实际修复模块一致，未发现作者附加物理补丁。
- reference生产者是实际HeatSolve、StatCurrentSolve和AdvectionDiffusion模块，生产镜像ID `sha256:bcf8db84ede5575993809588071cf61d8725d2e7a8b2a96ac7cfe78b6896b6e6`。本审计独立从12个实际输入重新转换case.sif及四个原生网格文件，排序+文件名NUL+原字节的摘要与reference-replay逐例全部一致。
- 12份实际原生case.result完整读取，最后帧三场与正式HDF5逐节点逐值一致，转换误差全部0；12份生产stdout均含ALL DONE，参考HDF5原字节SHA与记录逐一一致。日志退出/自评分未单独作为准确性依据，准确性由上节独立全部节点比较支持。
- 重新检查驱动系数不作ρ补偿，material收到原始ρ/D/DT/z；DT或z为0时对应关键词确实省略。12次重新生成SIF都使用Temperature Field Variable="ThermalField"及Conc EPotential Field Variable="ElectricField"，Absolute Mass位于Equation，QUAD4、无bubble/stabilization、直接求解及三场先后与公开定义一致。
- 真实修复模块中温度绑定读取在约365行，电势在约381–384行；已核对有效关键词。keyword-consumption.json的正确/错误绑定实验记录作为作者证据读入，未把它声称为本审计新运行；本次直接源码读取与实际SIF哈希链提供独立对应。

未重新运行真实Elmer构建/求解。作者原生生产资源记录与正式Oracle属于另一路执行证据，本报告不以其代替独立数值审核，也不认证预算。

## 官方SDK合法/非法变体

仓库裸src是generic-structure环境，不冒充题目全契约校验。本次使用冻结公开ZIP的完整装配src（geometry+本题extension），并确认实际仓库16个对应core/extension文件字节与快照相同。check_problem/load_problem/load_result/grade_case均消费这一官方公开装配。

根据最终DATA独立选24个变体，全部只生成于runs/variants，不改变实际资产。18个应非法变体全部被拒，6个合法变体全部接受；详情与原始diagnostics见evidence.json:mutations。

| 预期 | 具体变体 |
|---|---|
| 拒绝18项 | ρ=0、ρ超上界、D=0、D超上界、非整数z、z超界、mode/units非法枚举、迁移DT非零、Y负/超1、温度低于范围、迁移非等温、电势超范围、Soret z非零/电势不恒定/顶端总通量非零/平衡剖面越界 |
| 接受6项 | 零Y与z=0、零Δφ、ρ下端0.2、ρ上端5000、合法负DT、DT=0 |

未用与生成器同源的案例列表决定预期；没有把这一有限变体集称为全部非法空间的证明。

## 最终有界复核与限制

在HF回取完成后，重新核对最终四文档/选择SHA、70个已管理载荷SHA、14个已读输入/参考版本、descriptor与case_id绑定、最终ZIP SHA，并再跑严格verify，全部保持一致。初始local receipt不作为远端成功证据，最终已替换为上述固定提交的真实receipt。

没有未决数据或来源问题。本报告的“通过”针对所列12case+2sample的实际载荷、公开域、全场数值与固定来源关联；不外推到未选择池条目、所有可能输入、编译耗时或候选解法表现。没有重新调用真实求解器，也没有用作者12/12或baseline6/12替代独立结论。

证据：evidence.json（每例哈希/全部数组读取/节点误差/变体诊断/生产链/HF复核）、inventory.json、audit.py、check_provenance.py、final-strict-verify.json。

归档说明：诊断附件保留在原审阅目录，归档定位调整不改变独立结论。
