# 22074 最终独立考生审阅

结论：**本轮未发现未决问题**。模式为 `exam-materials`；公开样例状态为**已检查**。此结论限于指定公开版本的可理解性、资产完整性、中性加载与公开样例消费链，不认证真实 MOOSE 编译、数值参考精度或资源达标。

## 独立范围与版本

唯一题目来源为协调方指定的 `solid-fluid-energy-observation-repair-agent.zip`。先用 `Get-FileHash -Algorithm SHA256` 实算，确认 SHA256 为 `307d4652af831c8ccaa15ba8ef509caa2d4786a7cbd56d89479510838537b0f2`，随后才提取；实际43成员，与预期一致。提取到独立临时目录 `C:/Users/Jim Zhou/.codex/tmp/repair22-moose22074-final-candidate`。`materials.json` 逐项保留43成员解压前原始内容 SHA256、长度及三份解释材料的单独清单。

解释性材料仅阅读ZIP内 instruction.md、DATA.md、docs/CONTRACT.md。另读取两份公开 problem.json、两份公开 grading.json，完整加载全部6个公开HDF5；SDK/checker只作为中性结构、读写和评分工具调用，未阅读其实现补物理。未读取仓库题目、author、hidden、cases、生成器、设计报告、任何数值或MOOSE源实现；ZIP内 native 源tar、公开运行器与模板只做字节哈希，未展开或阅读。没有编写 solver、调用付费模型或覆盖 prepared。

## 逐项覆盖

|检查|依据及判断|
|---|---|
|缺失接口与交付|instruction明确恰交完整 .C/.h 两文件、两新增路径、普通与AD注册类型、temperature/velocity及cp/rho属性名参数、block选择。源码是提交件；五项HDF5是可信原生运行/转换后的评价观测，不要求另交自产答案。库观测修复边界及禁止改方程/运行器/答案已明确。|
|全部模型|DATA的十行表覆盖Cartesian/RZ、普通/AD、标准/重命名共八显式族，以及RZ稳态/瞬态两耦合族。属性名由cp/rho参数选择，物理量与SI单位不变。|
|输入与身份|两个components字段的10/12分量、顺序、shape、单位、归一化坐标及RZ零分量均明确；耦合族两数组保留但全零。experiments为单实验实体[1]，没有网格节点/单元身份歧义；积分是该实验定义的整体观测，DATA显式说明不是连续空间点值。|
|两时轴|initial_time=[0]仅供输入系数；frames的times为显式/稳态[0]或瞬态逐步时刻。稳态逻辑0为收敛终场；瞬态0为初场，随后为隐式Euler步终场，禁止跳过/重采样。|
|几何与权重|Cartesian3D域、HEX27几何与RZ2D域、QUAD9几何及r=x、绕y轴、2πr体权重/2πLx壁面积均明确。固流各半径向分区、界面测度零且贴网格。无平面单位厚度解释空间。|
|稳态/初态/瞬态|显式族只插值观测不解PDE/Robin；耦合方程、源随时刻变化、初速度/温度、入口与自然出口、外壁/绝热边界、离散阶次及固定稳定化责任均就地定义。|
|五项积分与符号|Es/Ef不减Tref；Qadv为流体非守恒u·gradT体积分，普通/AD均须相应属性接口；已给非零散度时与边界焓流差项。Qsrc正为加热、Qrobin正为散热；稳态收支与瞬态储能差商符号清楚，禁止强行收支归零，初态无前步差商。|
|输出与评分|五项float64[nt,1,1]及J/W、experiment_ids/times必需支持量明确；输入系数及initial_time不额外输出。绝对/相对误差、全时刻五项、非有限值、等权计分、公开样例进分母及源码方法核查均有题面说明。|
|资源与使用|4 CPU/4GiB、两次各300秒编译、每例60秒、每文件1MiB、离线基线位置、pip安装及原生运行入口、可信重建边界已说明。这里只检查声明自包含，不声称真实环境可满足。|

## 样例及工具实测

`verify.py` 可复现本轮检查，`verification.json` 保存实际argv、每次退出码、完整stdout/stderr、全部HDF5数组值和两个自构合法输入。运行命令为 `python runs/candidate-review/repair22-moose22074-final/verify.py`；脚本把ZIP内src加入PYTHONPATH，不使用仓库SDK。

两个样例各实际执行一次 `load_problem`、`validate-input`、`info --input`，对公开result与reference各执行 `validate-output`，对result执行 `grade`。再用SDK `write_result` 写临时roundtrip文件，断言全部支持量/输出dtype、shape和值与原result一致，再评分。14次CLI调用均退出0。两份 grading.json 的五量J/W、pointwise/per_time/per_component、atol=1e-5、rtol=1e-9与题面一致。样例01为Cartesian普通标准显式，样例02为RZ耦合稳态；两者公开输出与参考数值逐项相同。

6个HDF5无未读数组：每个input的5数组与每个output/reference的7数组均使用dataset[()]完整加载，总计38数组。每个input含两个系数数组、experiment_ids、initial_time、times；每个output/reference含五项观测、experiment_ids、times。全部值、shape及dtype见verification.json，未以切片抽检替代加载。

## 两个合法输入理解校验

1. `rz-ad-renamed`：由公开样例元数据复制，模型改为 explicit-rz-ad-renamed-v1；Lx=Ly=1、RZ的Lz=nz=0、两相ρ=c=1，T=300+2ξ、u=(ξ,0,0)，s=1，其他必需显式参数保持合法值。中性输入检查与load_problem通过。由题面直接积分得 Es=451π/6 J、Ef=1357π/6 J、Qadv=7π/6 W、Qsrc=π/4 W、Qrobin=0。错误的平面权重给Qadv=0.75 W；RZ速度div u=2，边界焓流应为Qadv+2Ef，与要求差异显著。该反例区分RZ权重、温度绝对基准、流体选择、非守恒对流及AD重命名属性；这些为纸面语义检查，未运行native数值求解。
2. `transient-initial`：模型改为coupled-rz-transient-v1；两相ρ=c=1，Lx=Ly=1、RZ的Lz=nz=0，Tref=300，U=0.1，s0=1、sr=sz=0、α=1，dt=0.1、step_count=2，两系数数组全零，times=[0,0.1,0.2]。中性输入检查与load_problem通过。初态应为Es=75π J、Ef=225π J、Qadv=Qrobin=0、Qsrc=π/4 W，不能将零系数读成零温度，或把逻辑0读为稳态终场。三帧Qsrc依次为π/4×[1,1.1,1.2] W；n≥1储能差商加入收支，n=0没有前帧。后续温度/速度与积分须由固定原生离散求解，未以收支补造。

## 缺口与边界

未实施真实MOOSE构建、类型注册加载、完整public/run_case.py或native健康检查，未验证普通/AD重命名接口的二进制行为，未认证稳态/瞬态参考的数值精度、隐含数据或4GiB/编译/求解时限。公开两样例不包含其余八模型的实际原生运行覆盖；两自构输入仅证明声明与结构合法、语义可区分，不能外推为这些分支运行通过。未发现需要修改公开题面或DATA的具体反例，因此无修订项。
