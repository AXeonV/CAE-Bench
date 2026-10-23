# 19.4.4 瞬时颗粒应力修复：独立考生审阅

## 结论、模式与边界

按 caeoj-candidate-review 先完成 statements，再检查 exam-materials。题面结论：**本轮未发现未决问题**。样例状态：**已检查**，公开01/02的输入、参考、评分、公开结果全部数组/粒子/分量都已读取，没有未读大数组部分。

解释题意只使用本题 instruction.md、DATA.md 和 docs/CONTRACT.md。data-manifest.json 只读取 samples 映射确认01/02公开身份，没有跟随cases/pool路径。ZIP只查看README/MANIFEST和提取中性SDK，不读任何driver、pair源码、机制、solver、作者/设计记录或隐藏case。没有读取源码归档，没有构建或执行真实LAMMPS，没有编写完整求解器，没有付费benchmark，没有改题。独立逐对计算仅为审阅两份公开瞬时状态的观测值。

最终 ZIP SHA256=c62ed786a6a952584d2e6d403ced5683034481008b278e7a3c6a8b0ed98beef6，和指定值一致。包MANIFEST中的三文档及十个样例文件摘要与实际工作树相符；README声明的源码提交职责、样例入口与题面一致。清单身份不等于真实库构建成功。

## Statements：题意与接口独立性

三文件明确限定三维球颗粒、单进程Kokkos CPU Serial、half邻居表、newton pair off、run 0、切向历史零、非周期固定边界、无墙/冻结/外力。Fn>0且切向力在0.8muFn以内，固定不进入摩擦截断分支；没有要求考生自行定义粘附、滑动历史演化、Hertz缩放或时间积分。kt为合法Hooke/history参数，但零历史时不产生初始切向弹簧力，不应擅自增加该项。

DATA给出粒子ID与system ID的身份、瞬时轴、所有字段及物理参数的单位/范围/分量/shape/dtype。参数值在JSON常量对象，不重复存HDF5。材料密度是球体体密度，质量需乘球体积；它不是颗粒总质量。位置与半径/0.1m箱内余量、中心距离和接触判据明确。粒子数组位置通过给定ID对应，不得重编身份。

实际支持组合自包含：模式0输出force/torque/pressure_tensor；模式1输出force/torque/particle_virial；模式2输出全部四项，不额外声明其他量。particles和system位置使用各自实体轴。只有压力除以箱体积L³；逐粒子virial不除粒子体积、不加动能，且与LAMMPS stress/atom NULL pair相反数。压缩为正。

具体反例核对：把每对完整W分给两粒子会使virial多一倍；逐粒子输出应各分一半。对切向接触一般Wxy与Wyx不同，应取dx*Fy而非dy*Fx或两者平均。压力张量是所有无序接触对W之和/L³，不能把逐粒子数组平均当总压。选particle-only模式不能仍要求system压力输出。这些反例均有DATA的明确文字可判别，不依赖driver实现补规则。

力与力矩定义包含相对平动/转动、有效质量、法/切向阻尼和两球接触点力臂；没有未声明的粒子体积归一化或应力对称化。只允许替换指定cpp/h、保留pair实现与公开接口、可信运行器写HDF5的边界清楚。四类输出的逐点逐分量容差、例内全通过/等权，以及4 CPU/8 GiB、300秒构建/60秒每例明确；构建参数和样例入口可辨识。本轮不把命令文字完整性外推为实测构建可用。

## Exam-materials：完整数组及评分检查

公开01含4粒子、3个接触对；02含2粒子、1个接触对。两者均tally_mode=2，输出包含四类全部观测。输入JSON的模型、3维、空几何/网格/条件、参数键与单位、location/time、输入/输出字段名与quantity、components/kind/shape/dtype及输入sampling全部与DATA一致。

HDF5逐个数组检查有限值、根层扁平dataset、属性/链接/外部/虚拟存储、允许压缩、精确shape/dtype。IDs严格递增且在1..1000000，system=[0]、times=[0]。输出ID/时间按输入原值/顺序/dtype保持，无多余或缺失key。所有实际值在DATA范围，球和0.1m余量严格在箱内；全部对中心距和实际接触的Fn/Ft限制均满足。

两份grading均direct_outputs引用reference.h5，policy v2完整覆盖force、torque、pair_virial、configurational_pressure；单位和pointwise/per_time/per_component规则一致。前三者atol=1e-7、压力atol=1e-9，rtol均1e-8，与题面一致。未使用平均值或放松某些分量。

## 独立逐对观测核对

使用中性NumPy/h5py，按DATA遍历两份公开状态的无序粒子对，直接算球质量、法向/切向相对速度、Fn/Ft及F。力按i加F、j减F；力矩按力臂−Ri*n和+Rj*n分别与两侧Ft叉乘。每对W=outer(xi−xj,F)，各粒子加W/2，全局只加一次；仅抽取xx/yy/zz/xy/xz/yz并以L³生成压力。没有对角外分量对称平均。

每个接触对的ID、距离、Fn/Ft、作用力、两侧力矩及完整W均留在`runs/candidate-review/repair22-lammps/evidence.json`。reference与public result分别逐元素和独立结果比较，所有项在声明容差内：

|样例|粒子/接触对|力最大绝对误差N|力矩最大绝对误差N*m|逐粒子virial最大绝对误差N*m|压力最大绝对误差Pa|
|---|---|---:|---:|---:|---:|
|01|4/3|2.27374e-13|0|5.68434e-14|8.88178e-16|
|02|2/1|2.27374e-13|0|1.13687e-13|4.44089e-16|

公开result和reference的上述误差一致；最大误差/允许误差小于5e-8。本轮没有只凭两份输出互相相等就宣布数值正确。

从本ZIP提取的中性SDK在独立Python子进程运行，逐个load_problem/load_result读取两样例reference/public result，4次均通过；另外把公开样例副本仅按DATA调整tally_mode和输出声明/键集合，global-only、particle-only、both三个契约组合也都能加载。它们是协议fixture，不是实际LAMMPS模式执行证据。再以本ZIP CLI grade实际比较两个公开输出和相应参考，两次exit0。导入路径及结果分别见`runs/candidate-review/repair22-lammps/sdk-loads.json`、`runs/candidate-review/repair22-lammps/zip-grading.json`。

## 覆盖缺口与未验证范围

两个公开输入都为零速度、零转动、零法/切向阻尼，直径均为1；因此本轮虽然检查了全部力矩分量，但力矩预期全为0。实际接触虽有三维方向，均为中心弹簧力，W在这些样例中对称；不能借此认证切向非对称分量选取或阻尼/转动路径正确。两个样例都请求both，真实库的global-only/particle-only路径未执行；SDK副本检查不能代替该验证。也未覆盖无接触、不同粒径、完整N上限或所有参数极端。

题面清楚声明这些合法分支，样例不是全域限制。没有据样例缺少某分支判题意缺陷，也没有读取隐藏数据来填覆盖。没有实测构建、运行、内存或其他后端；不证明参考生产者来源/真实库实现、隐藏参考精度、正式评测或资源达标。当前公开材料未发现需修订或待核实的矛盾。

## 实际文件SHA256

路径相对仓库根目录。SDK只为中性消费工具；解释材料仍限三文件。

|文件|SHA256|
|---|---|
|qbank/19-solver-repair/19.4-observations/granular-pair-stress-repair/instruction.md|47e8fce53843e29f3824abd3b25aeb24edc37e5785776168f92aa0636a1193fb|
|qbank/19-solver-repair/19.4-observations/granular-pair-stress-repair/DATA.md|b38e80d72ae2116f0050be3c69f01592197ce356bac713c9915da53675427197|
|docs/CONTRACT.md|130d4416fd533812493780c8bc6afbc0a158de6800b59bbec14a852f3cf1c063|
|qbank/19-solver-repair/19.4-observations/granular-pair-stress-repair/data-manifest.json|07367a268933036f540840b914eb0ce7f0a56a1e416cdf378d277c5e8b086d09|
|dist/granular-pair-stress-repair-agent.zip|c62ed786a6a952584d2e6d403ced5683034481008b278e7a3c6a8b0ed98beef6|
|dist/granular-pair-stress-repair-agent.zip::MANIFEST.json|e2a11bae8578fdc73fce6b0f065f2c6b94b8fb409e76633471c1f2242ee551bc|
|dist/granular-pair-stress-repair-agent.zip::README.md|6ca0977d3e0c69fdec0208eac9d2a1067128a635181401a552c4122aeff96e30|
|qbank/19-solver-repair/19.4-observations/granular-pair-stress-repair/samples/01/input/problem.json|0d52e8973d719f8ff3b770887766a251807a32d7c5d4f41ce75b584e4e3a2e4e|
|qbank/19-solver-repair/19.4-observations/granular-pair-stress-repair/samples/01/input/input.h5|cacf90a8603edf7e8ce965e53bd2d1effd27d2b5598f541153b4179c6defd84b|
|qbank/19-solver-repair/19.4-observations/granular-pair-stress-repair/samples/01/reference/grading.json|446b04b0760467e0654c8826efb65ad10fa35680dee1ebe10cbda98cc114be56|
|qbank/19-solver-repair/19.4-observations/granular-pair-stress-repair/samples/01/reference/reference.h5|d439162a01367d7f500ebd64cdeda8273961a228503b6eeae83eb8e61f19a759|
|qbank/19-solver-repair/19.4-observations/granular-pair-stress-repair/samples/01/output/result.h5|d439162a01367d7f500ebd64cdeda8273961a228503b6eeae83eb8e61f19a759|
|qbank/19-solver-repair/19.4-observations/granular-pair-stress-repair/samples/02/input/problem.json|1633900c0a21e722aeb3f366cf0c5138c2a2da0710b01ea9165986492aa27ab7|
|qbank/19-solver-repair/19.4-observations/granular-pair-stress-repair/samples/02/input/input.h5|6dc56270c4587ebcfea8c685b09ff8d328355831194caf9ea6efde2e8792689f|
|qbank/19-solver-repair/19.4-observations/granular-pair-stress-repair/samples/02/reference/grading.json|446b04b0760467e0654c8826efb65ad10fa35680dee1ebe10cbda98cc114be56|
|qbank/19-solver-repair/19.4-observations/granular-pair-stress-repair/samples/02/reference/reference.h5|2300e288ea0dfaca7fe6d6d4492972b69a6bbea2eb228119cc82ba618644138f|
|qbank/19-solver-repair/19.4-observations/granular-pair-stress-repair/samples/02/output/result.h5|2300e288ea0dfaca7fe6d6d4492972b69a6bbea2eb228119cc82ba618644138f|
