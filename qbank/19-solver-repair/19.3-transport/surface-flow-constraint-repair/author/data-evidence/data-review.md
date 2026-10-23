# 19.3.2 / 19.3.4 最终独立实际数据审计

## 结论与范围

按 caeoj-data-review 执行。本轮允许正式输入/参考和来源证据，数学预期仍仅从各题最终 instruction.md、DATA.md 与 docs/CONTRACT.md 独立确定。上一轮 public-only 考生审阅报告未修改，也未将本轮隐藏材料追溯算入其范围。

|题目|实际输入覆盖|结果|公开样例状态|
|---|---|---|---|
|19.3.2 surface-flow-constraint-repair|9正式case=108状态；2sample=24重复公开状态|**通过**|01/02所有输入、参考、公开输出数组均已检查|
|19.3.4 multisite-surface-concentration-repair|9正式case=108状态；2sample=24重复公开状态|**通过**|01/02所有输入、参考、公开输出数组均已检查|

合计读取22份实际输入HDF5、26份结果HDF5（正式参考18份、样例参考4份、公开输出4份），全部数组/行/分量已读取，没有未读大数组部分。共216个正式状态，连样例重复读取为264个状态。全部实际输入与参考均在本轮审阅；未将作者 fixture 计作实际数据。样例01/02与各题正式01/02共享case ID，作为送分样例身份已保留。

没有读取 driver、参考修复源、solver、reference.patch、机制源或作者设计记录。允许的JSON来源证据只用于核对身份、生产范围、版本、运行记录及其绑定。没有运行真实求解器/库构建、没有写参考生成器、没有改题或重装配数据、没有运行付费模型。只在 runs 下建立中性检查、临时变体与发布SDK副本。

## 版本与实际文件摘要

完整逐文件SHA256位于同目录 file-sha256.json，覆盖最终三文档、两个ZIP、manifest、全部实际输入/评分/参考/公开输出、装配回执及实际读取的来源JSON。evidence.json 保留全部实际文件列表与逐case数值指标，source-binding.json保留来源链。下表列解释材料及包版本：

|文件|SHA256|
|---|---|
|docs/CONTRACT.md|130d4416fd533812493780c8bc6afbc0a158de6800b59bbec14a852f3cf1c063|
|dist/surface-flow-constraint-repair-agent.zip|79ace2ad25027a9bd9c45af41846ebacb7f7665e0e5572b3d7b2ff672b6fd8bc|
|qbank/19-solver-repair/19.3-transport/surface-flow-constraint-repair/instruction.md|8bb769e257aa54fa0daf73cea9cfb58b8c5d08c6e043103bb2b149d5b9794809|
|qbank/19-solver-repair/19.3-transport/surface-flow-constraint-repair/DATA.md|0d3b42fc578be4fc061a25b095bda25269d93081fba524055f365f3e1dc042e4|
|dist/multisite-surface-concentration-repair-agent.zip|753ea2594085887485c2b9917daabd54560d6b335c1d5933593b69dafe0bbb4e|
|qbank/19-solver-repair/19.3-transport/multisite-surface-concentration-repair/instruction.md|9fd781e7c93b2e5a7e89ab8ceb3b1fce31aa34567b83edef9d6327fdcb3bdf59|
|qbank/19-solver-repair/19.3-transport/multisite-surface-concentration-repair/DATA.md|d725e47b658f90446d1c2df3e78fda3365f24118ad27f3aeef0ffd3e81b10f9b|

## 结构、字段和实际消费链

对照 DATA 的两个字段表，逐项覆盖 JSON 的 task/physics.model/parameters、spatial_dimension、空 geometries/meshes/conditions、entities location、instant time axis、全部必需输入输出字段。每字段的 array/quantity/unit/location/time_axis/dtype/kind/component_shape/components/value_kind，以及全部输入 sampling，都与最终DATA一致。没有靠维护实现补定义。所有正式case和样例均使用同一声明分支；19.3.4额外包含 initial_coverages、coverage_mode 与四类直接/最终表面输出，不能缺省成零。

全部 HDF5 检查根层结构、有限性、完整shape/dtype、ID非负严格递增、时间[0]、键集合和输出轴原样复制。输入范围逐元素核对；变量为实际单位值，组分按名字A/B/I、表面按S/AS、反应率按adsorption/desorption/conversion，无排序暗换。19.3.4直接未归一化覆盖符合自身范围，不按概率裁剪。完整输出与完整参考按同一输出契约检查，本批没有稀疏参考。

两题分别从最终发布ZIP提取src下的协议SDK/题目契约插件，置于独立子进程的PYTHONPATH；工作目录在审计runs中，未使用仓库src替代发布SDK。SDK实际导入路径记录在各题 -sdk.json。两题分别完成70/79项检查：各13次实际材料加载（9正式input+reference、2sample各reference/output），其余为57/66个独立选择的合法/非法变体，无预期不符。

变体预期在调用SDK前按DATA确定：所有连续标量范围的上下端点、选择字段端点、N=1/32、I=0.05应接受；范围外/N=0/33、负组分/错误总和、NaN、错误整数dtype/shape、重复/负ID、时间非0、缺字段/未知参数/错误quantity/unit/components/sampling/model应拒绝。多占位另检查mode1覆盖和低于/高于1、和=0.5/1.5、AS>1的合法状态，以及mode0未归一化、错误mode、非法覆盖范围应拒绝。输出缺量/额外key/改轴/float32拒绝。SDK未纠正数值或重排数组。

另用每个发布ZIP的 CLI grade 独立子进程实际消费全部18份正式reference及4份公开result，22次均exit0；完整报告在 zip-grading.json。逐份grading.json的direct_outputs/reference定位、全部quantity、单位、逐点/时间/分量规则及atol/rtol均与题面相符，没有引入额外判据。该步骤只验证评价消费链，不用于自证物理正确。

维护侧 `data verify --strict` 两题均valid=true、errors=[]。没有刷新绑定或改变文件来取得通过；装配回执每个文件size/SHA、嵌入原始描述SHA、manifest case ID/描述绑定、角色范围逐项重算相符。固定HF装配版本分别为：

- 19.3.2：3dc6f98310bbb04871ac5c51d5dcdd544fa2687a。
- 19.3.4：cba8ad7fefc4db50636b37976cbba18ebc3e90ea。

本轮为本地固定装配核验，没有重新访问HF服务器，不能据此报告远端实时状态。

## 独立数学与物理核对

从DATA直接列元素/位点矩阵：气相A/B/I各一个O；S是Pt，AS为s个Pt加一个O；S占1个位点、AS占s个位点，单占位s=1，多占位s=2。对三反应 A+sS→AS、AS→A+sS、AS→B+sS，逐项核对O、Pt、表面位点守恒，全部残差为0。准稳态q1=q2+q3时气相总摩尔/质量源为0；不把直接非平衡属性观测误当准稳态。

等摩尔质量15.999、恒温、无摩擦、零净气相质量源给出恒定P/rho/u，rho=15.999P/(RT)，R=8314.46261815324。实际全部参考和公开输出都逐点核对该关系、Y和、惰性I不变、A+B不变、覆盖和。表面真实浓度取 n0θ/s，绝不将覆盖或质量分数直接当真实浓度。

准稳态令K=s*ka*c*XA*n0^(s−1)/(kd+kc)，c=P/(RT)，则θAS/(1−θAS)^s=K。独立计算该0..1内的根，核对每个最终覆盖分量。所有非零反应轨迹进一步检查：

`z = s*u*c/(a*kc*n0) * integral[XA_out, XA_in] 1/theta_AS(x) dx`。

以log(x)变量做中性积分，使用公开XA±题面容差给出单调端点包围，而非只检查终点平衡。零ka/kc/z极限直接检查XA不变。没有实现完整ODE/库替代solver。所有实际参考/公开输出均通过；逐case最大等效XA误差/容差见下表。该误差比是局部残差指标，实际通过依据为端点区间包围。

19.3.4全部直接状态另独立算C=[n0θS,n0θAS/2]、面密度=C·[195.084,406.167]，以及q1=ka*(cXA)*C_S²、q2=kd*C_AS、q3=kc*C_AS；最终表面浓度用最终覆盖单独核对。所有分量在公开容差内。正式08-pressure-scale的一个参考XA约−1.15813e−15，属于远低于3e−7绝对容差的积分尾差；没有将其当成合法输入负组分。积分验证以物理正值端点区间包围，避免对负尾差取对数，未对参考改值。

## 逐case实际覆盖

所有case均12行；下表只列正式case，样例01/02已另逐文件校验并与同身份正式case绑定。

|题目/case|排序集合|零ka行|零kc行|轴向距离范围m|最大等效XA误差/容差|
|---|---|---:|---:|---|---:|
|surface-flow-constraint-repair/01-reacting-last-public|0,1,2,3,4,5|0|0|[8.340167792338945e-05, 0.11641723851097209]|0.00101532|
|surface-flow-constraint-repair/02-inert-last-public|0,2|0|0|[0.0001466019720486962, 0.02634353813617975]|0.001071334|
|surface-flow-constraint-repair/03-zero-adsorption|0,1,2,3,4,5|12|0|[0.01, 0.01]|0|
|surface-flow-constraint-repair/04-zero-conversion|0,1,2,3,4,5|0|12|[0.01, 0.01]|0|
|surface-flow-constraint-repair/05-product-rich|0,1,2,3,4,5|0|0|[9.228025347486803e-05, 0.008645598065082118]|0.001001539|
|surface-flow-constraint-repair/06-trace-substrate|0,1,2,3,4,5|0|0|[0.00023031663612485667, 0.024169898628610912]|5.236875e-05|
|surface-flow-constraint-repair/07-site-density|0,1,2,3,4,5|0|0|[0.00023170413986434247, 0.011047954174176642]|0.002220359|
|surface-flow-constraint-repair/08-pressure-scale|0,1,2,3,4,5|0|0|[0.00024438476877863737, 0.04766417954174807]|0.001346257|
|surface-flow-constraint-repair/09-kinetic-regimes|0,1,2,3,4,5|0|0|[0.0017381593639399359, 0.03404061248549883]|0.001952888|
|multisite-surface-concentration-repair/01-reacting-last-public|0,1,2,3,4,5|0|0|[0.0002889899168393876, 0.050211026156641664]|0.001111389|
|multisite-surface-concentration-repair/02-inert-last-public|0,2|0|0|[0.0007534122254702309, 0.14053109541206982]|0.001959607|
|multisite-surface-concentration-repair/03-zero-adsorption|0,1,2,3,4,5|12|0|[0.01, 0.01]|0|
|multisite-surface-concentration-repair/04-zero-conversion|0,1,2,3,4,5|0|12|[0.01, 0.01]|0|
|multisite-surface-concentration-repair/05-product-rich|0,1,2,3,4,5|0|0|[2.896649517891217e-05, 0.010917451666062951]|0.002285563|
|multisite-surface-concentration-repair/06-trace-substrate|0,1,2,3,4,5|0|0|[2.0812011362703885e-07, 7.662908415737622e-05]|2.372258e-05|
|multisite-surface-concentration-repair/07-site-density|0,1,2,3,4,5|0|0|[0.00044830846618583615, 0.011226456343504684]|0.002514468|
|multisite-surface-concentration-repair/08-pressure-scale|0,1,2,3,4,5|0|0|[1.9109121264677505e-05, 0.2693148380350355]|0.003401715|
|multisite-surface-concentration-repair/09-kinetic-regimes|0,1,2,3,4,5|0|0|[4.279766816297676e-05, 0.036773162153411164]|0.00170659|

实际覆盖混合反应、惰性最后排序、零吸附、零转化、富产物、痕量底物、位点密度变化、压力尺度和动力学区间；不是只核对样例。所有实际标量最小/最大值保存在evidence.json各case ranges；多占位每case还保留mode计数和覆盖和，能核对归一化/未归一化两条分支。没有将case数或六种排序出现本身当成实现排序不变性的充分证明；本轮逐行物理核对不依赖species_order。

## 来源、生产者及绑定审计

cases.json明确这些工况是作者构造的回归工况、由Cantera issue1655/1996启发，不伪称上游实验。source.json分别定位Cantera官方仓库/issue/PR、v3.1.0及固定commit 6e0027548cf295bd478b8acfe34816f2db6dd58b、源码归档SHA；明确必要上游片段回移并附加本地气相总源修复，不冒充整个上游PR原样实现。这里审计记录是否如实定位和限定范围，未访问上游或读取修复源码来认证其实现。

reference-replay记录实际Cantera FlowReactor/ReactorNet，19.3.4包含真实SurfPhase/kinetics直接观测。逐case将其output_sha256与实际reference.h5原字节SHA绑定，9/9匹配；再核oracle.input_assets的problem.json/input.h5逐文件SHA与实际输入一致，assets的grading/reference SHA与实际文件一致，避免把只对一个旧工况的回放记录用于当前输入。本批未使用或发现需要解释为payload的input_sha字段；使用的是oracle.input_assets明确的逐文件摘要，没有猜摘要定义。

source.reference_source_sha256与oracle-build-report.sources_sha256相同；build报告记录成功构建、对象/库/driver产物摘要及旧产物清除。reference-replay的镜像与pristine-baseline.reference_image一致；两题完整reference回放均9/9记录通过。按来源资格，实际生产者是已定位版本且有明确修复范围的Cantera源码实现，不是临时自制解析/数值程序。独立验证依据为本轮从DATA推导的准稳态消元/轴向积分及直接属性公式，和生产者记录分开陈述。

不完整修复回放也已读取：19.3.2 baseline与upstream-subset均3/9；19.3.4 baseline0/9、flow-only0/9、surface-only3/9、upstream-subset3/9。记录支持本题并非只看Y归一化或只修一端即可通过；本轮未重新执行这些修复，也未借此反向调整题目容差。详见source-binding.json。

作者data-audit.json的逐case checks/contract/reference_grade作为既有验证证据单独核对存在及覆盖9case，并未拿其数字替代本轮独立数学检查。未将不存在的示例文件名atom-site-balance.json判成资料缺口；元素/位点核对已在本轮直接从DATA完成。

## 验证边界与交付证据

两题分别通过结构/契约、实际公开SDK正反变体、评分消费、全实际参考的独立物理/积分核对及现存生产记录绑定。未发现影响消费的未定义分支、输入越界、公开输出缺量或参考/输入错绑，结论为通过。

仍未重新执行真实库、读实现或证明其方法要求；构建/耗时来自既有记录而非本轮实测，不将本轮结果报告成资源达标或正式benchmark成绩。没有重取原始镜像/源码归档来验证文件摘要对应的内容，没有重新测试远端HF；这些是明确边界，不是用接口验证代替数值审计。

本目录主要证据：file-sha256.json（所有实际文件版本）、evidence.json（全数组/范围/逐case物理结果）、source-binding.json（来源与生产者绑定）、两个data-verify.json、两个题目-sdk.json（发布SDK实际材料与独立变体）、zip-grading.json（22次实际评分消费）。所有辅助脚本仅操作允许材料/临时副本；上一轮候选报告读取边界保持不变。
