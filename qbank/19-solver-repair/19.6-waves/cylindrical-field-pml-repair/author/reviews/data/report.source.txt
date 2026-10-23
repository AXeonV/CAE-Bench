# Meep #2338 独立全数据审阅

结论：**通过**。本次只读题目、实现与既有原生证据，独立编写和执行数学、存储、声明及评分检查；没有重跑 FDTD、重新编译、调用收费模型或改动题目。审阅依据为最终 instruction.md、DATA.md、docs/CONTRACT.md，按 caeoj-data-review、caeoj-configure-judge 及 repair backend 工作流执行。结论针对下述固定材料与实际测试范围。

最终公开 ZIP SHA-256：`acac8a89d2b02b4aa1a753fcdd2354b836c2af0af1cb21748973ed41564e0027`。HF 固定提交：`7abc5ec8686026548ae4abdfeb4530a33ccd8332`。独立脚本、完整逐例结果、额外变体、严格校验和材料摘要均保存在本报告同目录。未以作者 data-audit.json 的通过声明作为独立验收。

## 全量盘点与公开契约映射

加载全部 8 个 cases 和 2 个 samples；每个实际 problem.json、surfaces.msh、input.h5、完整 reference.h5、grading.json 均实际读取，另读两份公开 output/result.h5。不存在只读 HDF5 头而跳过数组的条目。8 个 HF case 描述摘要逐项匹配 data-manifest，每个描述中的 3 个输入及 2 个参考文件同时核对大小和 SHA；本地独立 `data verify --strict` 返回 valid=true。装配回执也绑定上述固定 HF 提交，未刷新绑定或覆盖差异。

| JSON/HDF5/网格项目 | 公开依据 | 独立检查结果 |
|---|---|---|
| task / physics / spatial_dimension / geometries / conditions | DATA 开头、物理模型与参数 | 10 例均为固定二维柱坐标模型、空几何及条件；七参数的精确键集、整数类型、值域、幅度符号与单位相符 |
| observation / surfaces.msh | DATA 参数与文件 | 10 例均为 MSH4.1 ASCII，四节点坐标与本例 R/Z 一致，11:1→2、17:2→3、23:3→4 三条 type1 母线；实际附带每节点一个合法 type15 元素 |
| face_ids / probe_ids / probe_coordinates / times | DATA 数组与采样 | 全量读取；int64[3]=[11,17,23]、int64[1]=[7]、float64[1,2] 精确运算顺序生成的居中点、float64[1]=[0.]；恰四数组，无多余键 |
| outputs / spectral_flux | DATA 有限窗口、输出 | float64[1,3,1]，三独立外向整面积分；quantity、location、integral、unit=1、分量与静态轴均正确 |
| observed_dft | DATA 六分量及 DTFT 定义 | float64[1,1,12]，Er/Ephi/Ez/Hr/Hphi/Hz 的实虚顺序；六个复分量全部独立重算 |
| time_step / window_end | DATA 时间推进、输出 | float64[1,1,1]，每例实际 dt=.5/resolution、终点1080；0标签没有被当成实际演化终点 |
| 输出复制轴与额外键 | DATA 输出、CONTRACT §9 | 仅 face_ids、probe_ids、times 和四输出；SDK 实际写回同样恰七数组，不复制 probe_coordinates |

DATA 中 locations 的独立 JSON 示例可解析，且与实际声明逐项相同。全部输出通过实际 load_result 与 grade_case；完整参考不是稀疏参考，无额外插值解释。实际变体覆盖 ±m、正负幅度、R2/R3、Z1/Z2、r-PML1/2、z-PML1/2 与 res30/40；并未声称正式 8 例穷举所有允许参数笛卡尔积。

## 原始生产者与原生数值

独立打开原始 tar，逐文件校对 baseline-tree.json 中全部 700 个 SHA。再打开真实上游 head tar，独立得到差分恰为 `src/step_db.cpp` 与 `python/tests/test_ldos.py`，私有 producer 文件逐字节等于真实 head 的 step_db.cpp。两镜像另外由本次启动的只读容器逐文件核对：base 的 700 原件均不变；production 的原件中仅 step_db.cpp 变化，均另有 33 个 Autotools 生成文件，实际总数733。生产者未应用上游 Python 测试或作者物理改写。详细证据见相邻 configure-judge 审阅目录的 base-image.json、production-image.json。

独立读取全部 8 条完整 native trace.csv，共 540000 行、每行六复分量；7 例64800步，res40例86400步。检查每步时间、有限性、起止与 dt 后，逐分量用复指数和 dot 累积重算 `dt/sqrt(2π) ΣF exp(+2πit)`；H 使用 `t−dt/2`。未导入作者 independent.evaluate。12 个实数通道的最大绝对差为 **1.887379141862766e-14**，全部满足公开严格容差。

三面谱通量逐例与原生 stdout 的三个**绝对值**精确相同，六复场也逐位相同；下端盖符号在真实 driver 的 `-C[0]` 处翻转，adapter 只 reshape/转储，没有归一化分配、额外1/2、替换负m或根据标答纠正数值。八例真实 Oracle result.h5 全部实际读取，七数组的 dtype/shape/值逐位等于本例正式 reference；没有把作者 output-bindings 的 exact:true 直接当成检查结果。

独立重判八份原件输出，只有正m的02/07通过，合计2/8；修复参考8/8。独立比较修复 ±m 实际数组：三通量精确相同，六复场按 `[+,-,+,-,+,-]` 奇偶关系精确对应。内部单点场对原件/修复缺陷本身没有独立检出承诺，它用于约束旋向，检出来自三面严格通量。

## 独立物理支持与适用边界

从 retarded Green 函数 `G=exp(ikr)/(4πr)` 的一、二阶径向导数独立实现 `E=ik(I+∇∇/k²)Gq`、`H=∇G×q`，保留近场项，未调用作者 nearfield。轴心离散环源的径向矩为 A/(4res)，角积分为 π(ex+i m ey)，故 q=π A Jhat/(4res)。本次对公开 dipole 独立数值积分，再用傅里叶微分 `Jhat=−iω dipolehat`，res30/40均得到 Jhat≈50，确认正相位、源符号及归一化量级。

独立六复 Green 核对所有正式例，最大相对复误差 **1.4598%**；res40对应例为0.8752%。从 `1+cos²θ` 直接做角积分，得到 `P0=k²|q_scalar|²/(3π)=π³ A²50²/(12res²)`，单端盖比例 `(4−3c−c³)/8`。三独立绝对通量均与该连续极限同量级，逐面相对差最大 **9.3983%**。另从原始同几何 R3/Z2/res30→40 native stdout 独立重算，绝对总量误差 **2.86087%→2.00605%**，端盖比例差 **0.00369955→0.00310634**。

上述连续 Green/P0 仅为有限源、有限网格、有限窗口及表面积分的物理支持，不是正式离散参考的1e-8精度证明，不声称已知收敛阶数。没有保存三面每个空间点的全时间 trace，因此没有宣称本次从独立时空面 trace 重建了每个离散通量；精确离散三通量来自真实固定 Meep 原生 accumulator、上游真实修复、逐位 Oracle 重放与边界/符号实现核查。六复场则有完整独立时间 DTFT 认证。归一化复场尺度 E0T0/H0T0、通量尺度 E0²L0²T0²/Z0 与 DATA 相符，不把结果解释为瓦特或平均稳态功率。

## 有区分力的声明、SDK和评分检查

本次独立执行 **31 个合法/非法声明与网格分支**：幅度端点及负整数、越界/布尔；整数参数的浮点整数/布尔、错误 mode/R/Z；独立PML厚度；res40精确采样坐标；多参数、错误单位、条件、偏移坐标、非零静态标签、错序IDs/错probeID、多HDF5键；输出分量、sampling、quantity、unit、value_kind；type15可完全省略、重复点元素拒绝、反向母线拒绝。结果全部与 DATA 预期一致。

四输出均分别验证0.999/1.001倍阈值两侧，共8检查；再对阈值附近可表示浮点数用 nextafter 向两侧扰动，共8检查，实际评分等于公开 `abs(error)<=atol+rtol*abs(reference)`。另9个输出损坏：额外键、缺场、float32、展平shape、错IDs、NaN、底面反号、实虚/分量反序、仅通量比例，均0分且区分 invalid_output 与 wrong_answer。SDK write_result 实际复制轴后仅产生契约所需七键。缺失 time_step 的坏 reference 返回 `evaluation_error, score:null`，未归入考生0分。

## 验证命令与剩余范围

实际命令使用 `.venv/Scripts/python.exe`：`independent_review.py`、`extra_checks.py`，以及 `-m caeoj_tools.cli data verify --task cylindrical-field-pml-repair --strict`。完整代码和实际 JSON 结果都在本目录；材料 SHA 在 materials-sha256.json，额外粗细网格原始证据 SHA 在 extra-evidence.json。后端实际隔离、安装、预算与探针另见 `runs/configure-judge/repair22-meep2338/report.md`。

本次未新增长运行、没有验证未装配的其他HF池条目、未跑付费模型Benchmark。未发现需要修订的公开定义、实际数据或评分冲突。
