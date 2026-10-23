# MOOSE 独立考生审阅

初始模式：statements，仅 instruction.md、DATA.md、docs/CONTRACT.md。题面结论：**本轮未发现未决问题**。初始样例状态：未纳入（严格依白名单，没有因目录存在而读样例）。随后经根任务明确扩展为独立 exam-materials 阶段：最终公开 ZIP 的两样例已作中性检查，结果见下；未以工具补题义。

## 独立性与材料版本

未读取 MOOSE author、隐藏 cases、私有参考、求解实现、设计材料；公开源码 tar 只核 SHA，未解包。没有写 solver、修改题目或派子 agent。数学判读只依据本题三文件，没有从 SPECFEM 借定义。

公开 ZIP：`C:/Users/Jim Zhou/.cache/caeoj-repair22/moose30236-dist-v1/grand-potential-derivatives-repair-agent.zip`，完整 SHA256 为 `04563d1ff3576d2ee759f620f3f8ae3d73dfb40a7aacab75912ccefde57e26cc`。三文件与工作树逐字节匹配；所有包条目完整 SHA256、读取范围和两例数组统计见 evidence.json。公开 public 适配/驱动和源码仅作字节哈希，没有从其实现推断数学要求。inspect_public.py 只读包内 SDK/CLI、公开 JSON/HDF5。

## statements 覆盖与判断

- SI 输入已明确：Va[m3]、k[J/m3]、w[J]，Va*k 为 J；C/D 为1/J；数密度 w/(Va²k) 与1/Va 同为1/m3；巨势两项均为J/m3。PARABOLIC 无隐式 eV/K 换算。
- ceq 的1/2双和与上三角非对角 Bij 展开关系明确。完整 q=(phi,eta0..3) 梯度、行优先25分量 Hessian、对称两侧、inactive行列为零均可唯一确定；phi–eta 混合项不会误解为只求对角。变量内部别名不会改变输出身份。
- 五次 h 的夹持、越界试探状态和 phi=0/1 一二阶导数零均已明确；strict=0/1 在观测量上同义。零值是实际零，不采用相对误差单独判断。
- 残量符号 c−A−Bc−(C+D)w 明确。线段无面积/厚度、P1基函数和两点Gauss完整确定有限元积分；节点基态相同仍独立扰动的说明消除了以共同扰动替代单节点列的可能。由题面可确认每个节点残量为 L/2 倍局部约束，浓度Jacobian为标准 L/6*[2,1;1,2]，w列为其乘−(C+D)，状态列为其乘−[对应A/Bc导数+w(C/D导数)]，单位分别m与m/J。这只是核对公开定义的一致性，未实现提交或全套参考。
- native residual 首向量、解析Jacobian、INITIAL材料属性、DOF真实映射均已明确；不允许以差分矩阵或迭代后状态代替。20个state分量按变量再行再列、w/c四分量和20个材料输出总数可确定。
- Ei=Va*ki 为每例全局常数、严格正，指向C/D各自能量明确。将 Ei*|误差|≤1e-10+1e-10*Ei*|参考|除以Ei，正好给出1e-10/Ei的原单位绝对容差；端点和近纯相也有绝对误差兜底，零不需除以参考值。容差不是更改输出单位。没有发现由量纲或端点定义导致的不可实现要求。
- 两个指定普通源码文件（即使无需改也交）、1MiB限制、类与接口/真框架限制、run_case参数、真实增量构建目标、固定环境、4CPU/4GiB、300s构建/30s运行及等输入计分均明确。

## 后续 exam-materials 检查

两公开样例所有输入 HDF5 dataset 和完整输出/reference dataset 均读入，有限值、dtype、shape、身份/时间轴通过该ZIP SDK。每份结果22个dataset，即20个输出加program_ids/times。两份公开结果分别与同例参考逐数组精确相等；公开CLI grade均exit 0、accepted。包内 grading 的各物理量单位/atol/rtol符合 instruction，包括C三个输出 atol=5208333333.333334 1/J、D三个输出 atol=7812500000.000001 1/J，对应各自1e-10/Ei。此阶段没有发现新增材料缺口或矛盾。

## 未完成

没有运行真实MOOSE编译、libMesh/PETSc装配、材料API、候选修复或性能预算；没有独立认证参考数值正确性。未读public驱动实现，因此不声称驱动实际实现了全部数学要求；未执行完整离线安装。结论仅说明公开定义足以确定局部材料/算子、公开样例可由其提供的中性工具读取和评分，不外推隐藏覆盖或实际运行可靠性。
