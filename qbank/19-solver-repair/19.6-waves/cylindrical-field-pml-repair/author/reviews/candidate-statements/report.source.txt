# cylindrical-field-pml-repair 独立考生审阅：题面模式

日期2026-10-23。模式statements。结论：**本轮未发现未决题意问题**。样例状态：两份公开样例已在同一独立审阅的考试材料模式完整检查。

## 独立性与冻结材料

仅接收任务、公开白名单与冻结ZIP摘要，未接收作者答案解释、预设问题清单。未读本题author、hidden、作者参考/修复/设计/审阅记录；未实现题目、未运行付费模型、未执行作者求解代码、未提交Git。解释性要求只取自instruction.md、DATA.md、docs/CONTRACT.md；明确公开的样例reference/grading是考试包的公开检查资产，不是私有参考代码。已按AGENTS.md与caeoj-candidate-review技能/通用流程审阅。

实际ZIP `dist/cylindrical-field-pml-repair-agent.zip` SHA256：`acac8a89d2b02b4aa1a753fcdd2354b836c2af0af1cb21748973ed41564e0027`，符合冻结值。三文档与包内版本逐字节相同。

|文件|SHA256|
|---|---|
|qbank/19-solver-repair/19.6-waves/cylindrical-field-pml-repair/instruction.md|cc72311567a1d296bc15148368f6032dbc59db9e82f2a665aaef1f9256592cae|
|同目录DATA.md|0ca92ff6d60bfd1196b682b7c70d31b526da7bd205c3eda2aee09927bbe23ded|
|docs/CONTRACT.md|130d4416fd533812493780c8bc6afbc0a158de6800b59bbec14a852f3cf1c063|

检查时HEAD=`c58522950307d56936b0a389f0b0e29049839a0a`，题面/DATA为未跟踪文件，故以上文件摘要是实际版本依据。通用CONTRACT此前已在本独立审阅上下文完整阅读，本包摘要与已读版本一致。

## 考生实施路径判断

- 任务与提交边界明确：只交一个普通step_db.cpp，完整替换src/step_db.cpp，1 MiB上限、不能改头文件/驱动/构建、真实库及推进必须保留。错误分类与原件健康检查说明不要求考生承担基础设施故障。
- 物理模型明确：真空、零初态、无非线性/色散、复角模exp(i*m*phi)、右手旋转基、m=±1，r/z域与PML、柱轴正则条件及默认外端由冻结库实现。二维协议槽位为(r,z)，六个三维柱向分量以components承载，不会误读为二维向量。
- 源和尺度明确：归一化L0/T0/E0/H0、轴心复Er点源、固定GaussianSource/dipole、源电流离散差分、原库点源空间权重与幅度含符号均已说明。不能改为连续解析偶极或高斯余弦电流。
- 数据身份明确：MSH只是三条旋转观测面的母线，不是电磁内网格；四节点、三有向线及tag、可选point元素、无额外拓扑的范围精确。face_ids=[11,17,23]分别代表整块顶盖/侧面/底盖。底盖外法向符号明确，不按line方向任意重解释。
- 居中空间采样明确：probe_ids=[7]；r/z坐标指定float64运算顺序，避免运算重排跨格点；各分量经真实yee2cent/avg居中，不假定交错原生存储重合。
- 时间观测明确：dt=.5/resolution，n=1..2160*resolution，终止1080；E/H半步错时、正指数、dt/sqrt(2π)、stride=1；times=[0]只是静态标签，不代表推进终止0。
- 谱通量明确：三个面分别比较整块三维绝对尺度的带外法向积分，而非仅总量或归一化比例。DATA给出cross-conjugate、面积权重、底面负号、无额外1/2、真实离散库空间积分。此处“绝对”由公式确定为非归一化量，不要求对通量另取绝对值。有限窗口尺度明确，不误认瓦特/PSD/连续极限解析值。
- 输出与评分明确：四字段，12个复场实虚分量、3面谱通量、真实dt/window_end，以及必须复制的IDs/times，dtype/shape/unit/value_kind齐全。逐值容差、所有字段/请求共同通过和例分明确。
- 操作资源明确：真实原件/驱动/CMake/适配器、固定路径、逐项清理与重编命令、离线运行环境、4 CPU/4 GiB、编译300秒、原生执行1800秒、评分30秒。没有将“能读取数组”当作实际资源达标。

没有发现需要私有材料补足的模型或评价要求，也没有形成两个同时合法但评分不同的未消解解释。任务要求修复特定冻结实现，库自身的Yee/PML/采样规则是明确的方法约束，不应强迫考生重新实现一个连续模型。

## 检查界限

考试材料模式已完整读取两例全部JSON、MSH、HDF5数组，运行包内中性CLI/SDK和声明变体，报告为 `../repair22-meep2338-exam/report.md`。Windows主机缺少/opt下真实driver，两次run_case启动失败；没有锁定镜像安装、编译、FDTD求解、参考数值认证、隐藏覆盖或资源预算实测。该环境限制不被本报告误判为题目故障。

实际读取、哈希、比对及CLI命令证据保存在考试目录的audit_public.py/evidence.json。公开样例固定R=2/Z=1/PML=1/res=30，覆盖正负m；其他合法参数只做中性契约变体检查，不宣称已求解。
