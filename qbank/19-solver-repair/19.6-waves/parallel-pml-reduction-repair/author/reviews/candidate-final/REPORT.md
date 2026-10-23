# SPECFEM 独立考生审阅

模式：exam-materials。结论：**需修订**（两项公开材料问题）。样例状态：01、02 已检查全部公开输入数组、全部网格节点/单元、公开 reference/grading.json、reference.h5 与 output/result.h5；不代表数值参考认证或真实执行验收。

## 独立性与版本

只用 instruction、DATA、CONTRACT、public-materials.json 白名单工具与两公开样例；公共源码压缩包仅核 SHA，未解包/阅读求解实现。未读取 author、隐藏 cases、私有参考或设计。没有编写 solver、修改题目或派生子 agent。中性检查脚本为 inspect_public.py，逐文件完整 SHA256 与数组统计见 evidence.json 的 materials、archive_matches、samples。

实际最终考试包 SHA256：`53ab80e1e927c46b20bc2c12cb161e1b48cac988ec20b8cbb4e6ba25febecaeb`。包内三文件、全部白名单工具和两样例与工作树同路径文件逐字节 SHA 一致。SDK/CLI 直接取自该包，使用独立 PYTHONPATH，未从工具反推缺失物理。

## 确定问题

1. **P1：输出支持数组互相矛盾。** DATA.md:76 要求复制 `probe_coordinates`；CONTRACT.md:316 禁止重复输出点坐标且所有额外 key 不合法。反例：按 DATA 写四个 dataset 会违反 CONTRACT，按 CONTRACT 写 `wave_response,probe_ids,times` 会违反 DATA。两公开参考和公开输出实际均只有后三项，包内 SDK 验证和 grade 接受后三项。候选只交源码，输出工具固定，故照题面修复仍无法产出 DATA 要求的结构。最小建议：删除 DATA 输出中的 probe_coordinates，沿用通用协议，不向通用协议增加逐题例外。

2. **P2：包根运行示例路径无效。** instruction.md:17 将根目录安装说明紧接 `python public/run_case.py --input samples/01/input/problem.json ...`；实际 ZIP 根既无 public/run_case.py，也无 samples，两者位于 `qbank/19-solver-repair/19.6-waves/parallel-pml-reduction-repair/`。按根目录原样执行会文件不存在。建议根目录安装后明确 `cd` 到题目目录，或给包根完整相对路径。未将宿主 Windows 缺少固定 Linux 构建目录计作题目缺陷。

## 已完成覆盖

- 逐条检查 SH 的 rho*u_tt、线力 N/m 与二维 delta 的面积量纲、负号；声学 chi 的 kg/m、A 的 N、grad(chi)/rho 和 -chi_tt 的单位一致。cp 与 cs 分支意义清楚。
- 有限起点 -1.2/f、零位移/势及零一阶导数、非零 Ricker 尾部、同时多源与正负幅度、两试件独立性均明确。二维协议槽到物理 x/z 的映射明确，不需要猜测 y。
- GLL 点载荷、连续装配、tag 排序分区、P=1/3/4 方法限制、逐整步输出、空间 Lagrange 插值和 ASCII 单精度/7位观测明确。
- SH 无 PML；声学有/无上下三层 C-PML、自然 Neumann 外端、左右 Neumann、固定衰减剖面及记忆变量初态有定义。依固定真实库的 C-PML 离散属于题目明确方法要求，未要求考生补一个替代 PDE。
- 源文件完整替换、普通文件数与大小、原件/候选真重编、健康检查、CPU/内存/编译/执行/评分预算、逐项 pointwise 误差及等例计分清楚。
- 01：SH，2048 正方形单元、2145 节点、单试件 1600×800 m、h=25、P=3；02：声学，3072 单元、3234 节点、两个独立试件、h=25、P=3，上下三行 PML 全量吻合。CFL 分别 0.1737386354、0.0868693177，均低于 0.3。网格全部按四角顺序检查，所有源/接收点仅落在一块内，最小离墙距离大于4h，源接收最小距离100=4h（允许“至少”4h）。
- 两输入 Nt=3200、dt=0.00025、t_start=-0.06，完整时间轴与公式逐值一致，Nt*dt=0.8 s。全部场有限、dtype/shape 正确；初始公开响应严格零。公开结果与参考逐 dataset 完全相等；SDK 输入/输出通过；包内 CLI 两例均 accepted/exit 0，grading 中 SH/声学容差与 instruction 一致。

## 未完成与适用范围

未运行原生 Fortran/MPI 编译、健康算例、求解器或候选修复；未量测 Linux 4 CPU/4 GiB 预算；未执行完整离线 pip 安装（静态检查 pyproject 已含 setuptools build-system 与精确依赖声明）。未独立计算波动参考值、初始加速度和后段反射数值误差，未测试隐藏 P=1/4 或其他几何。上述材料检查不能证明解精度、实际资源达标或通信缺陷已修复。
