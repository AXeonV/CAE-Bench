# 独立考生审阅：19.3.2 与 19.3.4

## 范围与执行顺序

按 caeoj-candidate-review 先完成两题 statements 阅读并形成独立结论，再进入 exam-materials。解释题意只用两题各自 instruction.md、DATA.md 以及 docs/CONTRACT.md；没有用其他题、实现或作者记录补题意。CONTRACT 与本审阅上下文已读版本 SHA 相同。

exam-materials 的公开依据为各题 data-manifest.json 的 samples 01/02 与最终 ZIP 的 MANIFEST/README。没有跟随 manifest 中其他 case/pool 路径。实际打开各样例 problem.json、input.h5、grading.json、reference.h5、result.h5，并完整读取全部数组、全部行/分量。ZIP 只读 README/MANIFEST 和同样十个样例文件做身份比对；没有读取源码、driver、run_case、机制、SDK 实现、作者/设计/来源材料或隐藏 case。没有修改任务材料、编写提交求解器、运行真实库构建或付费 benchmark。

|题目|statements 结论|exam-materials 结论|样例状态|
|---|---|---|---|
|19.3.2 surface-flow-constraint-repair|本轮未发现未决问题|本轮未发现未决问题|01/02 全部数组已检查|
|19.3.4 multisite-surface-concentration-repair|本轮未发现未决问题|本轮未发现未决问题|01/02 全部数组已检查|

## Statements：逐题结论

### 19.3.2 表面反应管流物种约束修复

instruction 的物种身份、同摩尔质量/热性质、恒温稳态/无摩擦/定截面、表面准稳态、质量守恒及排序不变性与 DATA 一致。DATA 完整给出六种排序到名字的映射、名字固定的输入输出顺序、入口与轴向观测距离、所有反应计量/速率/浓度/覆盖/常数及单位。每行新建独立轨迹，不能把一行末态当另一行初态；时间 [0] 只是标签。

具体反例核对：将 species_order 从 ABI 改成 IBA，不允许重排输入的 A/B/I 组分或输出；表面 θ 不能作为真实浓度直接代入 q；零 ka 或 kc 应无净 A→B 转化；表面初猜不是自由入口物理状态。S/AS 均单占位，因此 C=n0θ；这些要求均可从本题三文件确定。等摩尔质量气体下质量分数数值等于摩尔分数，但仍须按所声明输出含义报告。

提交只允许 FlowReactor.cpp，可信运行器写结果、强制可信重编译，禁止后处理归一化掩盖守恒缺陷，边界可确定。评分的逐点容差、例内全通过、等权及失败规则完整；60秒/例、300秒重编译、4 CPU/8 GiB 有明确文字。构建和样例命令形式明确，未实测是否能执行。

可选清理：DATA 首个字段说明中的「两个选择字段…coverage_mode（若本题有）」及末段「多占位题如下定义」带有跨题模板痕迹。该题表格明确不含 coverage_mode/initial_coverages，单占位初猜也明确，不导致两种合法解释；建议删去无关分句，作为编辑优化，不列阻断问题。

### 19.3.4 多占位表面浓度与耦合管流修复

本题自身三文件完整给出 AS 占2个位点、反应 A+2S→AS 及逆解吸/转化、速率单位 m^5/(kmol^2*s)、C=n0θ/s 与 AS 的 2Pt+O 组成。真实浓度、表面质量面密度和反应进度率之间能作量纲与守恒核对，无需借助另一题。

具体反例核对：coverage_mode=1、θ和=1.2 时，直接输出不得先把和缩回1；AS 浓度必须除2，q1必须使用 C_S²。direct_rates 是直接状态三条不可逆反应的正向进度率；不是先达到准稳态的净物种生成率。direct_concentrations 是给定初始覆盖属性，surface_concentrations 是最终管流准稳态属性，两者可不同。直接求值后归一化作求稳态猜值，不能把未归一化属性状态当最终管流物理覆盖。这些路径均在本题 DATA 明确。

提交 SurfPhase.cpp 和 FlowReactor.cpp 的边界、固定机制、可信写回及重编译职责一致。全部九项输出、分量、单位、评分及与19.3.2相同的资源文字完整。未发现必须打开 driver 才能消除的题意遗漏。

## Exam-materials：中性检查方法

用 NumPy/h5py 直接读取 JSON/HDF5，没有导入项目实现。检查全部输入范围、field 名称、quantity/unit、dtype/shape、components、sampling、模型/参数/空几何/空条件、实体和时间轴、HDF5 根层结构与输出键集合。输出轴与输入完全一致。评分文件 direct_outputs 的全部 quantity、单位和逐点/逐时间/逐分量规则逐一对照 instruction；没有用评分工具实现补定义。

独立物理核对不实现库替代程序：同摩尔质量、恒温、零总气相质量源和无摩擦使 P、rho、u 沿轴向不变，rho=15.999 P/(RT)。气相 I 不变、A+B 不变、质量分数和为1；覆盖和为1。令 s 为 AS 占位数，c=P/(RT)、K=s ka c XA n0^(s−1)/(kd+kc)，准稳态满足 θAS/(1−θAS)^s=K。单占位 θAS=K/(1+K)，双占位取0至1内的稳定正根。

对每个公开最终 XA，检查它是否满足单调轴向积分恒等式

`z = s*u*c/(a*kc*n0) * integral[XA_out, XA_in] (1/theta_AS(x)) dx`。

使用 log(x) 变量做中性数值积分，分别将公开 XA 加减其声明容差作为端点，确认给定 z 落在对应单调区间内。此法直接验证整条轨迹的积分约束，没有写完整 solver，也没有只用端点准稳态冒充轴向演化检查。质量守恒检查补充固定另外两个物种值。

多占位直接属性独立计算：C=[n0θS,n0θAS/2]，面密度=C·[195.084,406.167]，q=[ka*(c XA)*C_S²,kd*C_AS,kc*C_AS]；最终表面浓度另按最终覆盖计算。所有单位采用 DATA 指定的 kmol、m、s、kg 常数。

## 样例覆盖与检查结果

|题目/样例|状态数|排序|多占位直接接口|轴向积分等效 XA 误差/容差最大值|
|---|---:|---|---|---:|
|surface-flow-constraint-repair/01|12|0,1,2,3,4,5|不适用|0.00101532|
|surface-flow-constraint-repair/02|12|0,2|不适用|0.001071334|
|multisite-surface-concentration-repair/01|12|0,1,2,3,4,5|{'0': 6, '1': 6}|0.001111389|
|multisite-surface-concentration-repair/02|12|0,2|{'0': 6, '1': 6}|0.001959607|

两题各24状态、合计48状态。每题01覆盖全部六种排序，02覆盖排序0与2；输入状态不是成对相同物理条件的六种排序，因而不声称公开样例直接证明排序置换实现正确。独立公式不依赖排序，所有行均符合按名字解释的物理约束。两题均有非零入口B和惰性I。

19.3.4 每个样例 coverage_mode=0/1 各6行；未归一化行覆盖和小于1与大于1的状态，且部分 AS 覆盖大于1，合法地检验未裁剪接口。所有直接浓度、面密度、三个速率分量及最终表面浓度均与独立公式在公开容差内一致。两题四组公开 result.h5 与各自 reference.h5 全数组相同，但仍另做上述物理/积分核对，没有以双方相同代替审阅。

全部结构/声明、评分、公开包身份、守恒、准稳态、积分和直接属性检查通过，无未决数值反例。逐字段最大绝对误差、容差比和实际覆盖清单保存在 evidence.json；可复跑的中性检查为 check_public_samples.py。积分端点校验的等效 XA 容差比最大约0.00196，所有状态远小于1。

覆盖缺口：四个样例均未含零吸附、零转化或 z=0；参数也未穷尽声明上下界。19.3.2没有独立直接表面属性输出；这是题目范围，不是遗漏。未读取机制，无法核验真实库热性质、反应定义是否逐字符合文档；未运行编译/驱动，无法证明方法要求满足、真实 API 消费链可用、超时/内存达标或隐藏数据/参考精度。这些缺口不改变本轮公开材料结论。

## 实际版本与 SHA256

最终两 ZIP 的完整 SHA 与协调方给定值相同；MANIFEST 所列三文档及十个样例 SHA 均与实际文件相符，ZIP 内同样样例字节也逐项核对。README/命令入口与三文件提交职责一致。以下为实际读取/校验的白名单材料；没有把清单内其他文件身份扩展为阅读许可。

|路径（仓库相对）|SHA256|
|---|---|
|docs/CONTRACT.md|130d4416fd533812493780c8bc6afbc0a158de6800b59bbec14a852f3cf1c063|
|dist/surface-flow-constraint-repair-agent.zip|79ace2ad25027a9bd9c45af41846ebacb7f7665e0e5572b3d7b2ff672b6fd8bc|
|dist/surface-flow-constraint-repair-agent.zip::MANIFEST.json|8d54d814e786f404b0495be56f8ba11b26063a218fe42d3e64b7fcf8f2e4f4e4|
|dist/surface-flow-constraint-repair-agent.zip::README.md|62ef2e477495c12efe0b10dc3ef79a6665256417d034951b25b03e6fcb9da17a|
|qbank/19-solver-repair/19.3-transport/surface-flow-constraint-repair/instruction.md|8bb769e257aa54fa0daf73cea9cfb58b8c5d08c6e043103bb2b149d5b9794809|
|qbank/19-solver-repair/19.3-transport/surface-flow-constraint-repair/DATA.md|0d3b42fc578be4fc061a25b095bda25269d93081fba524055f365f3e1dc042e4|
|qbank/19-solver-repair/19.3-transport/surface-flow-constraint-repair/data-manifest.json|1b3e4ed8d6e1ff60d9d8042665c5742b451b5045090ebacdbd218dc15e09399b|
|qbank/19-solver-repair/19.3-transport/surface-flow-constraint-repair/samples/01/input/problem.json|c12f0a9991a6cc964a34140e572975dfacd720edd38179fa857be0680dfa39b5|
|qbank/19-solver-repair/19.3-transport/surface-flow-constraint-repair/samples/01/input/input.h5|423c32a3f9845d22afb8065ec703d1a82c2faf2971620c8c5795d9856439063f|
|qbank/19-solver-repair/19.3-transport/surface-flow-constraint-repair/samples/01/reference/grading.json|4381ba105b26af238cd2e7d86bbe7b475534c16285be1f9329a10d7828d11d60|
|qbank/19-solver-repair/19.3-transport/surface-flow-constraint-repair/samples/01/reference/reference.h5|f9643ecac400210378e4f32874ba3205ea057a5c0e421248717023a32f2046e0|
|qbank/19-solver-repair/19.3-transport/surface-flow-constraint-repair/samples/01/output/result.h5|f9643ecac400210378e4f32874ba3205ea057a5c0e421248717023a32f2046e0|
|qbank/19-solver-repair/19.3-transport/surface-flow-constraint-repair/samples/02/input/problem.json|c12f0a9991a6cc964a34140e572975dfacd720edd38179fa857be0680dfa39b5|
|qbank/19-solver-repair/19.3-transport/surface-flow-constraint-repair/samples/02/input/input.h5|82db8664f32f8a74f60d6401823e7f0c422128a0ecd32797d203934203c68d9c|
|qbank/19-solver-repair/19.3-transport/surface-flow-constraint-repair/samples/02/reference/grading.json|4381ba105b26af238cd2e7d86bbe7b475534c16285be1f9329a10d7828d11d60|
|qbank/19-solver-repair/19.3-transport/surface-flow-constraint-repair/samples/02/reference/reference.h5|19a8fa92f161dccd537d655f78525b0c6ce545d8e048080579df2d77423dba87|
|qbank/19-solver-repair/19.3-transport/surface-flow-constraint-repair/samples/02/output/result.h5|19a8fa92f161dccd537d655f78525b0c6ce545d8e048080579df2d77423dba87|
|dist/multisite-surface-concentration-repair-agent.zip|753ea2594085887485c2b9917daabd54560d6b335c1d5933593b69dafe0bbb4e|
|dist/multisite-surface-concentration-repair-agent.zip::MANIFEST.json|225d366b85e3d6fc5a579f3c5f32b1c5e0b5b9eee632cd8a6f676825ccb55850|
|dist/multisite-surface-concentration-repair-agent.zip::README.md|0c0a77557351c01b44fde69d1f2da73a019e135e22ade45efd79da1ac073d421|
|qbank/19-solver-repair/19.3-transport/multisite-surface-concentration-repair/instruction.md|9fd781e7c93b2e5a7e89ab8ceb3b1fce31aa34567b83edef9d6327fdcb3bdf59|
|qbank/19-solver-repair/19.3-transport/multisite-surface-concentration-repair/DATA.md|d725e47b658f90446d1c2df3e78fda3365f24118ad27f3aeef0ffd3e81b10f9b|
|qbank/19-solver-repair/19.3-transport/multisite-surface-concentration-repair/data-manifest.json|0f58e36171c2da1b242cd340067e619e7cca09970b0a62b5f3ed80387abb41d7|
|qbank/19-solver-repair/19.3-transport/multisite-surface-concentration-repair/samples/01/input/problem.json|555671d8dd1dc80d28de339edac727f97761218069544a7b23b0ded080e5cd90|
|qbank/19-solver-repair/19.3-transport/multisite-surface-concentration-repair/samples/01/input/input.h5|4095fc109aef8342dc54c17bfae837469f82c7d05b3af485986999604b1b6423|
|qbank/19-solver-repair/19.3-transport/multisite-surface-concentration-repair/samples/01/reference/grading.json|d0a3a4dd2e13f16d1b998691763226aeeca76463bd2462a43ac72ceab7000f3b|
|qbank/19-solver-repair/19.3-transport/multisite-surface-concentration-repair/samples/01/reference/reference.h5|dc68eeb9be6f40aaf7419091220cf798118317aa8f62702cff021623b6d22339|
|qbank/19-solver-repair/19.3-transport/multisite-surface-concentration-repair/samples/01/output/result.h5|dc68eeb9be6f40aaf7419091220cf798118317aa8f62702cff021623b6d22339|
|qbank/19-solver-repair/19.3-transport/multisite-surface-concentration-repair/samples/02/input/problem.json|555671d8dd1dc80d28de339edac727f97761218069544a7b23b0ded080e5cd90|
|qbank/19-solver-repair/19.3-transport/multisite-surface-concentration-repair/samples/02/input/input.h5|d71d41ab5f6ee77b915fd2f9fb84cc820b884208c7787541c9979891516e94d9|
|qbank/19-solver-repair/19.3-transport/multisite-surface-concentration-repair/samples/02/reference/grading.json|d0a3a4dd2e13f16d1b998691763226aeeca76463bd2462a43ac72ceab7000f3b|
|qbank/19-solver-repair/19.3-transport/multisite-surface-concentration-repair/samples/02/reference/reference.h5|349857846ede2827f79b4d7d2e41ee6802f87e33dbe02dd80e8d8bd64bd6276f|
|qbank/19-solver-repair/19.3-transport/multisite-surface-concentration-repair/samples/02/output/result.h5|349857846ede2827f79b4d7d2e41ee6802f87e33dbe02dd80e8d8bd64bd6276f|
