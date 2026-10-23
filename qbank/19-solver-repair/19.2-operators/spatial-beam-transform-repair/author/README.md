# 19.2.1 空间梁方向变换：作者与验收材料

来源为[Kratos issue #14657](https://github.com/KratosMultiphysics/Kratos/issues/14657)及[PR #14680](https://github.com/KratosMultiphysics/Kratos/pull/14680)。基线为`f4b2e970ede622ab54548c0661637f90e5ddd419`，上游head为`e7976668c8904bd29b8bb3a51ab5a0db38322422`，完整提交及摘要见[取证](data-evidence/source.json)。机械应用六条乘法修复与实际head文件逐字节相同。公开材料只含原始基线，维护者修复答案不进入公开包。

参考明确包含三项，不能称为上游原样版本：

1. PR的RotateLHS、RotateRHS、RotateAll六条乘法方向修复。
2. 作者补足Assemble旋转块：内部局部y转角的符号必须作用于行，即D R；原来的列翻转为R D，任意3D刚体转角会产生虚假应变能。
3. 作者实际重放发现的体载面积补足：继承2D GetCrossArea以strain_size==3读CROSS_AREA，否则读THICKNESS；3D law维数6导致体力面积为零。只将允许3D.cpp中的两个体力积分入口改读CROSS_AREA，未在驱动伪造THICKNESS。

范围及两次增量设计复核在`runs/design-review/repair22-kratos/report.md`，三项分别保留证据。题目限定零初态、线性两节点单元三API及夹持静力；不覆盖非零状态内部力、动态质量、全局装配或完整StructuralMechanicsApplication适用性。

## 制作与复现

`prepare_source.py`取得固定原始归档及head文件，校验摘要并制作上游原样与作者补足两个参考；网络可选`--proxy`，不关闭TLS验证。`pack_source.py`保留真实Core、结构力学源码及第三方许可证，排除无关应用和测试。公开源码闭包5.67MB，已独立解包配置，并与真实编译的915个上游源码/头文件依赖逐字节匹配，见[闭包证据](data-evidence/source-closure.json)。

`build_runtime.py --work <new-directory>`从公开源码构建真实Core和七个原始结构力学源文件的梁组件。实际工具链为Clang19.1.7、C++20、O1；未修改Core逻辑。GCC14在未改的cfd_variables.cpp触发内部编译器错误，已保留实际重放日志，属于基础设施问题。

可信C++驱动调用真实CalculateLocalSystem、CalculateLeftHandSide、CalculateRightHandSide；Python只完成协议转换、能量共轭单位缩放及夹持线性系统求解。`generate.py`制作正式输入；`replay.py --image <image> --mode reference|defect|upstream`实际生产或重放。`independent.py`依据Timoshenko解析单元矩阵、虚功坐标变换及一致均布载荷核对；端载工况另用闭式梁柔度核对自由端。该独立矩阵程序只作验证，参考生产者是真实Kratos。

`original_issue_replay.py`另跑issue文字中L=4m、0.3×0.7m矩形截面、E=200GPa、ν=0.3、X/Y/Z方向单位端力。其完整材料参数中J和ρ由作者补齐，不影响被测端力位移；它独立于较小截面正式数据，不冒称所有case都是上游原例。

## 实际结果

10个正式case、每例4根独立梁覆盖对齐回归、斜置/一般3D、轴拉、扭转、剪切主导弯曲、均布体力、对称截面、反向构件及截面转动；2个case显式兼作公开样例，另外8个隐藏。案例身份见[清单](data-evidence/cases.json)。

- 作者补足参考：10/10，完整矩阵/载荷独立核对全部通过。
- 原始基线：1/10；上游PR原样修复：1/10。后者仍被完整全局转角和体载义务检出，不能作为物理标答。
- 最大绝对差：刚度2.3842e-7N/m，一致节点力5.6844e-14N，自由端归一化位移4.2224e-15m；另一路闭式柔度差1.0919e-14m。详见[reference](data-evidence/reference-replay.json)、[baseline](data-evidence/defect-replay.json)、[upstream](data-evidence/upstream-replay.json)。容差保留双精度积分/坐标转换和刚度条件数余量，不能把所测误差外推为全声明参数域的保证。
- 手工Docker+真实judge链的可信源码后端Oracle：10/10、reward1。真实强制原件构建19.25秒、候选10.55秒，均低于各自预算；原件真实API探针通过。[Oracle摘要](data-evidence/oracle.json)及三个构建回执保留冻结源码、库和输入/参考摘要。
- [六项实际后端探针](data-evidence/backend-probes.json)：未来mtime仍重建并加载新库；语法错误归候选失败；Clang缺失及原件运行入口缺失归基础设施；额外文件/符号链接拒绝。UID1000不能读隐藏case/reference/log，也不能写冻结源码/库/驱动；网络隔离和4CPU/8GiB的实际cgroup值均核查。未声称这是全部容器安全性证明。
- 正式Harbor生命周期Oracle：`repair22-kratos-harbor-oracle-v1`，单次Oracle trial、无exception、10/10、reward1、returncode0，总运行约68秒；冻结任务及逐例摘要见[正式job](data-evidence/harbor-oracle-job.json)与[正式评分](data-evidence/harbor-oracle.json)。与前项手工链分别记录，未启动模型考生。
- [独立安装](data-evidence/public-install.json)：仅公开ZIP和缺陷runtime、无网络，从包正常安装后移出源码目录运行，原件公开样例01得1、02得0；修复版通过另行Oracle验证。
- 全部正式输入、参考、样例及评分消费已实际审计；安装的严格task SDK同时拒绝6类非法声明，见[数据审计](data-evidence/data-audit.json)。[独立全数据审阅](data-evidence/independent-data-review.md)已通过，并另核查40根梁的刚体模态、矩阵秩/半正定性、物理柔度和体载荷，16个非法及5个合法契约变体。

HF池已原子发布到`cases/repair-22-20261023`的固定提交`2ebfb364340fb0928dc2fd95d610aa2e1ebd4ed6`，稳定ID`caeoj-190201`。官方上传后的验证及独立新缓存固定提交装配/严格核验均已完成（50文件、changed=0）；最终题面、公开考试材料、完整数据及可信后端独立审阅均已通过，正式Harbor Oracle已闭环；当前题目验收完成。本轮未调用付费考生Benchmark。原始重放、构建日志及正式job留在`runs/authoring/repair-22/`和`runs/harbor/jobs/`，题内只维护必要摘要。

