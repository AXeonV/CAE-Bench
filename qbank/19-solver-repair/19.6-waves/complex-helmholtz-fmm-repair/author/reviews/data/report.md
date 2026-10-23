# Bempp 复波数题全量数据与参考审计

结论：**通过本次全量数据与参考审计；原 P2 已修复并独立有界复核。** 未发现 P0/P1 数据或参考错误。全部实际数据、数值参考和评分阈值检查通过。HF 空缓存装配、完整安装及正式 native 资源验收由协调者完成，本报告不将其计为已完成。最终 ZIP 身份及包内实际 SDK 已补做独立验证，见文末。

审计范围为 `work/repair-22/bempp-20/dataset-v2` 全部 12 个实际输入、12 个完整参考，以及题目 `samples/01`、`samples/02` 的实际输入和参考。全部 JSON、HDF5 dataset 和全部网格节点/面均完整加载；不存在抽样读取代替全量数组审计。只写本报告目录，未改题目实现，未调用付费模型，未重启高成本 native 流水线。

## 唯一实际发现

**P2（已关闭）：公开 extension 漏检固定输入文件名。** DATA 首段要求 `data_file: input.h5`，原 `extension/caeoj_task_ext/helmholtz.py:check` 未检查该字段。将真实 01 输入清单改为 `other.h5` 并复制完整同一 HDF5 至该路径后，原 core `check_problem` 与原公开 extension 仍均接受。初始证据为 `initial-full-variant-evidence.json`，亦有 `filename-variant`、`replay-evidence.json` 独立补证。影响为公开声明与实际声明校验不一致，不影响本批固定输入或参考数值。协调者已在题内 extension 增加精确文件名检查；当前同一磁盘变体返回 `E_HELMHOLTZ`、path=`$.data_file`，原 P2 关闭。

## 公开语义、结构与变体覆盖

对照题面、DATA 和 CONTRACT：任务标识、三参数及其精确单位/类型/范围，空 geometries/conditions、两操作 meshes/locations、时间标签、复值实虚分量顺序、全局 xyz 目标梯度、float64/int64、完整时间与实体轴、严格 ID 与输出复制轴、输入/输出 key 精确集合均检查。通用 components 表示适用于复势和六分量梯度；点源量纲 1 对应势 1/m、梯度 1/m2；曲面积分和 P1 质量表示对应 V 的 m、K 的 1、W 的 1/m，外势 S 的 m、D 的 1。W 的节点输出是固定 P1 弱泛函经质量逆所得系数，与 CONTRACT 节点 point 声明及 DATA 的明确解释相容，未当成连续尖角超奇异点值。

实际 6 点例覆盖源数 32、48、64、96、128、512，实波数与复波数、虚部上界 1.2、实部上界 3、负与复强度、平移、局部和真实快速路径。源/目标有跨表重复身份，按独立位置处理。实际 6 曲面覆盖 18/34/66/100 节点与 32/64/128/196 面、实/复波数、仿射与尺度变化、非连续且乱序存储的节点标签。所有网格的真实存储节点顺序均与 node_ids 顺序不同，参考检查按标签完成。所有节点被用到，面拓扑/外向/凸性/体积/目标外部距离等通过当前公开几何检查。精确数量、dtype、shape、所有数组极值、零/负分量数量和几何证据见 `evidence.json`；因此可区别已覆盖分支和未出现分支。

实际场分量均有正负复值，但本批没有零分量、纯零密度/强度，也没有正实部 0.5 的实际 case。独立补充合法性变体覆盖这些条件：真实磁盘 28 个变体经 core 与公开 extension 完整检查；另有声明层 24 个变体和 5 个非法输出。合法零场、非负零 ID、参数边界被接受；布尔波数/浮点 operation、负/乱序 ID、错误 dtype/shape、NaN、非零静态时间、额外/缺失数组、幅值越界、源源/源目标/目标目标碰撞、内点、全反向面和单面反向被拒绝。`full-variant-evidence.json` 中除上述 P2 外全部符合独立预期。这些是契约检查，不等于零场及全部合法几何极值已经执行 native 求值。

## 数值参考资格

1. 对全部 6 点例和点样例，直接用实际 HDF5 坐标、强度，独立计算 `exp(ikr)/(4*pi*r)` 及 `G*(ik-1/r)*(x-y)/r`。四个输出的全部目标、实虚、xyz 分量分别比较，全部在题面容差内。最紧为 04-point-far-tree，其真实 FMM 相对逐项容差的最大占用为 **0.4105441294**；其余点例最大占用不超过 0.004321。不能把点参考称为解析值逐位一致；FMM 有实测近似误差，仍满足给定阈值。
2. 对全部 6 曲面，从实际 Gmsh 标签和面连接独立建立 P1 质量矩阵，每面局部矩阵为 `area/12 * (ones+eye)`，并核对实际 native payload 的全部顶点/三角连接/密度/目标与输入逐项相等。使用已存在的**原始未修复 base 库 dense weak 输出 JSON**，独立计算 `M^-1 * weak` 对照全部三种真实参考边界输出。最大逐项容差占用为 **0.03559956615**（08 的 K），全部通过；质量条件数约 3.97–4.80。此检查独立于作者 strong_form 输出及其质量转换，未用参考自身冒充独立依据。
3. dense worker 与公开真实 driver 的文本严格仅有 `assembler='fmm' -> 'dense'` 及 `strong_form() -> weak_form()` 两类替换，仍调用真实 Bempp P1 API、Numba、regular 6/singular 8；其 LF 规范文本 SHA256 与原审计报告 `6d69a6a4...7490` 一致。Windows 文件原始 SHA 因 CRLF 不同，`replay-evidence.json` 同时记录文件原始 SHA，不混淆两者。worker 以 vertex→global DOF 映射写入 coeff、再逆取弱行；本次质量矩阵与输入标签顺序一致。没有新运行该 dense worker，检查的是其原始完整 JSON 和只读源码身份链。
4. 对全部 6 曲面及曲面样例，用实际网格 P1 密度和外向面法线独立作三角 Duffy 映射、14/22 阶 Gauss 积分，直接积分 G 及源法向导数。外部 S/D 的全部分量均通过；最大容差占用 **0.0233411600**，两阶收敛差约机器精度。该独立积分不导入 Bempp/ExaFMM，不读取作者积分代码以生成数值。
5. 全部 12 参考 HDF5 的每个数值输出与各自真实 replay stdout JSON 逐项一致。两样例清单、输入 HDF5、参考 HDF5 分别与 02/07 case 字节完全一致，因此曲面样例同受上述 dense weak/质量矩阵证据覆盖。
6. 重新读取完整两个公开源码 tar 的所有普通文件：原档 SHA 与所有相对路径文件 SHA 清单均匹配 `source-archives.json`。再对不可变 base/ref image 分别做一次不运行求解的只读容器哈希，**各 371 个源文件全部匹配**；base 对完整公开来源，reference 仅允许三文件替换为实际 author/generated 文件，其余 Bempp 与 ExaFMM 逐文件匹配。具体 image_id、完整 expected/actual 映射见 `variant-source-evidence.json`。这建立来源与实际 dense/FMM 镜像链；不把源码 SHA 匹配单独当作数值准确证明。

边界弱积分仍基于真实原始库的 dense 积分实现，与 FMM 共享其核/近场之外的通用库代码；本报告没有声称已用第二套独立奇异积分实现重算全部 V/K/W。这里评价对象正是 DATA 明确固定的该库离散与积分设置，原始未修改 dense 弱算子、独立质量逆、真实映射和独立外势积分共同足以支持本批固定离散参考，区别于只做结构或自判分。

## 评分检查与边界

14 份完整参考都通过 core 输出契约和真实 `grade_case`。逐份比对当前 operation 所有 quantity 的单位、pointwise、per_time、per_component、atol=1e-6、rtol=1e-5，与题面完全一致。对每份参考的每个输出及每个标量分量，单独扰动第一实体的一个分量为 0.99 与 1.01 倍 `atol+rtol*abs(reference)`，共 **364 次实际判分**：前者全部 accepted，后者全部 wrong_answer。每例的全部输出以 AND 聚合，不存在实虚合并范数、梯度漏项或跨分量平均抵消。另实际非法输出检查缺字段、额外字段、NaN、错误 ID 与缺时间轴，均拒绝。所有结果和 evaluator/依赖/输入 SHA 保存在 `evidence.json`。

## 未完成验收与最终冻结

- HF 固定提交 `d4011e0522e1e9dcbc8f228624fe7b1c02063928` 的 fresh 空 cache 装配、data verify、选择和包内文件身份由协调者管理，本次仅审计本地上述全部真实 staging 与 samples，未上传或重选。
- 原生实际零场/精确全部几何合法边界未重跑；4 CPU/4 GiB、600 秒、字节编译和只读/缓存资源路径亦未重新验收；正在运行 baseline/native pipeline 未触碰。
- 初始文件 SHA 见 `evidence.json.documents`，最终文件 SHA 与修订后复核见下一节。未重新执行初始版本全部 364 个阈值试验，因为数值评价实现与输入/参考未改变；修订后对 14 份完整参考实际重新评分，并重验全部 28 个磁盘变体。

## 最终修订与公开包有界复核

原 P2 修订后，对真实 12 case 与 2 sample 再完整加载输入/参考、执行最终 extension 及真实 grade，14/14 accepted；28 个实际磁盘变体全部符合预期，原 other.h5 变体被拒绝。证据为 `final-evidence.json` 与最终 `full-variant-evidence.json`。

又独立读取 `dist/complex-helmholtz-fmm-repair-agent.zip` 的全部 **41** 个 member，记录全部 SHA；逐份核对包内 instruction、DATA、CONTRACT、所有题目工具、源码档案、样例与工作区最终版本完全相同，包内 `src/caeoj_task_ext/helmholtz.py` 也与最终题内 extension 字节完全相同。将完整 ZIP 提取到本审计目录，启动 `.venv` Python 的 **`-I` 隔离子进程**，只将提取目录 `src` 插入模块搜索路径，实际导入 ZIP 内最终 SDK、绑定和 extension，重新对全部 14 输入/reference 运行完整输出校验及 grade，并通过包内绑定校验全部 28 实际磁盘变体。全部通过，且 other.h5 被包内最终 SDK 自动拒绝。此验证不依赖工作区通用 core 是否默认装配该题 extension，详细绑定 descriptor 与每例 binding SHA 见 `final-zip-evidence.json`。它不是 pip 离线安装验收，也不是 native Oracle 执行验收。

最终固定身份：

| 文件 | SHA256 |
| --- | --- |
| instruction.md | `43981ecd5688c0e15c18b852815ef6dea3adcbc346ad390bcbcef69cb284e678` |
| DATA.md | `dd1c8359f5e7747d9cced6b2a40b046f9dd0130689b6a4fcae4e60700a3fba25` |
| docs/CONTRACT.md | `130d4416fd533812493780c8bc6afbc0a158de6800b59bbec14a852f3cf1c063` |
| extension/caeoj_task_ext/helmholtz.py | `bf6ec9c9e2c4cef68d5fce00b86dcac6fa5d49a6e22303dbe2ec20385e74296f` |
| complex-helmholtz-fmm-repair-agent.zip | `3b2f5344125bf5679bd026bef828bbe97a44c9a132cca97a5975a25ed8d319bf` |

instruction 的新增切换到题目目录说明与包内实际层级一致。未将旧 Oracle-v1 的结果迁移为该最终 ZIP 的结果。

复现入口：`.venv/Scripts/python.exe runs/data-review/repair22-bempp20/checks.py`（全部数值及 364 判分）、`full_variant_checks.py`（28 磁盘变体）、`variant_source_checks.py`（声明/输出变体及完整来源哈希）、`replay_checks.py`（实际 replay/样例/worker身份链）。脚本均仅写本目录。
