# RC2 独立考生审阅：其他39题（原始公开快照）

模式：exam-materials。仅以 other-whitelist.json 中324个公开文件为输入；39题 instruction/DATA 均全文逐题阅读。各题CONTRACT全文内容相同，SHA一致后按同一协议审阅。未读取维护元数据、作者实现、隐藏case或隐藏reference，未写solver、运行模型或重新生产参考。

总计53个公开样例均检查实际JSON、H5、以及出现的MSH表示。全部324个SHA与白名单相符；所有样例输入/输出的key、dtype、shape、IDs、时间轴和Physical Groups匹配，数组均有限。**结构通过不能证明样例数值正确**。样例已有的公开reference/grading只按白名单读取。

## 明确缺陷

### F1 [P1] 35题未交代公开output是格式演示还是数值答案

11道PDE与24道CFD公开输出存在几乎统一的[−1,1]数值范围，但公开三文件没有“仅格式、随机值、非数值解、不可用于正确性判分”的说明。32题可仅由初值、边值、最大值原理或显式恒等式证伪；其余两道盖驱腔和圆管谱不因外观相似而直接判为错误。影响是考生可能用这些文件校验正确求解器，从而误以为公式、单位、采样或输出轴理解有误。

位置：例如 diffusion-sorption-1d 的 DATA.md:62 明确t=0等于初值，instruction.md:56却只称“公开输入输出样例”；其 samples/01/output/result.h5 的 concentration[0,314,0]=−0.9998777518381448，输入为0.002074830699712038。reaction-diffusion-2d DATA.md:62要求按细单元ID提取，样例已按ID对齐后仍错。incompressible-navier-stokes-2d DATA.md:68明确t=0保留预投影记录，样例亦不符。

最小建议：保留格式演示时，在instruction/DATA准确标明用途及不能用于数值正确性比较；若其用途是数值答案，应替换为经独立验证的答案。不能依赖考生不可见的作者元数据定义其身份。以下逐题表保留原版结论与反例，不把后续维护方解释反填为原题意。

### F2 [P1] 24个CFD任务的启动入口不完整

位置：全部 cc-* 的 instruction.md:8 只写读取problem.json及向“指定输出路径”写文件；约:20又写“入口遵守提交接口”，但instruction、DATA、CONTRACT均无solve.py文件要求、启动命令、参数名或输入/输出路径传递方法。CONTRACT的读写示例不是提交启动约定。

反例：同样满足文字的数据读写实现可以接受位置参数，也可以只接受--input/--output；评测器只能启动其中一种。物理和输出定义均完整仍不能保证提交可被启动。最小建议是在题面就地给出实际入口命令与参数。若考试另附统一启动说明，应让题面明确引用且该说明须在公开考试材料中；本审阅未获该说明，不自行假定。

## 逐题覆盖与原版结论

所有下列行都检查了任务、输入字段/条件、单位、轴、连续采样、输出、评分及资源声明；“结构通过”仅代表本报告列明的通用检查。全文件SHA、各数组shape/dtype/min/max、全部样例manifest、mesh统计和数值反例在 other-candidate-summary.json。

| 题目 | 公开样例状态与实际覆盖 | 原版结论 |
|---|---|---|
| smoke-test | 结构通过。01：二维网格节点、float64标量、单时刻；公开参考与输入回传一致。声明允许的int64/bool/张量/独立点分支在当前样例未出现。 | 未发现明确公开材料矛盾 |
| case-grading-test | 结构通过。01整场；02指定三角形P1测点、分开x/y检查；非连续节点tag与三帧非均匀时刻。完整输出与输入一致；公开稀疏参考未误当提交格式。 | 未发现明确公开材料矛盾 |
| darcy-flow-2d | 结构通过。01/02：128²原四边形平均输出、独立中心点系数双线性重建、四边非局部耦合；f=1/10。公开state含负值，正源与半平均边界不容许负解。 | F1明确反例 |
| heat-conduction-steady-2d | 结构通过。01全Dirichlet；02四种边界各一，源项及边界多项式components轴、整体归一化坐标和物理法向明确。01常数4，02线性1+x+y样例描述与值相符。纯Neumann/平均温度分支仅文档定义，未有公开样例。 | 未发现明确公开材料矛盾 |
| diffusion-sorption-1d | 结构通过。01/02：1024线单元、两个非局部边界、初值为两个常数、五时刻；t=0反例见下表。 | F1明确反例 |
| heat-conduction-transient-2d | 结构通过。01零场/全Dirichlet；02非零P1初态及四种边界、2401节点；t=0均精确回传。正时间精度及5秒资源未由本次无solver审阅证实。 | 未发现明确公开材料矛盾 |
| reaction-diffusion-1d | 结构通过。01/02：1024线单元、周期、ν=.5，r=1/10；初态分片常数，输出平均，t=0反例。 | F1明确反例 |
| reaction-diffusion-2d | 结构通过。01/02：512²完整初态、128²输出细单元子集、两字段/四边零通量；按ID查找初态后仍有t=0反例。 | F1明确反例 |
| advection-1d | 结构通过。01/02：1024线单元、周期、速度.4/2、五时刻；平均输出，t=0反例。 | F1明确反例 |
| shallow-water-2d | 结构通过。01/02：128²四边形，深度1/2、零动量、零梯度外推；熵条件和仅输出深度均明确；t=0反例且输出负水深。 | F1明确反例 |
| burgers-1d | 结构通过。01/02：1024线单元、周期、κ=.1/π与.001/π、五时刻；t=0反例。 | F1明确反例 |
| incompressible-navier-stokes-2d | 结构通过。01/02：512²中心points、双线性初态/强迫、零壁速fields与独立conditions时间轴；χf和连续投影定义充分；预投影t=0明确却与样例不符。 | F1明确反例 |
| compressible-navier-stokes-1d | 结构通过。01周期η=ζ=.01；02两端外推η=ζ=1e-8；密度/质量加权速度/守恒压力及一维vector分量x明确；三字段t=0均反例。 | F1明确反例 |
| compressible-navier-stokes-2d | 结构通过。01为128²/η=ζ=.01；02为512²/1e-8；双周期、完整四边形、守恒平均派生输出；三字段t=0反例。 | F1明确反例 |
| compressible-navier-stokes-3d | 结构通过。01为128³，02为64³，六面体、三周期、三分量速度、五时刻；守恒平均定义明确；三字段t=0反例。 | F1明确反例 |
| cc-1d-burgers-equation | 结构通过。201点含周期端点；终时.14π；输出u存在负值，且两端.42018/.59910不一致。初态可直接界定u≥4−π>0，黏性最大值原理保持下界。 | F1明确反例；另有F2 |
| cc-1d-diffusion | 结构通过。201点含端点，终时.0333；端点应为1，实际.934425/.443278；全场最小−.995420违反1≤u≤2。 | F1明确反例；另有F2 |
| cc-1d-euler-shock-tube | 结构通过。201内部点，终时.25；rho最小−.998161、比能E最小−.997141，均与正密度理想气体激波管相反。 | F1明确反例；另有F2 |
| cc-1d-linear-convection | 结构通过。201点含周期端点、终时10；u最小−.956152违反Gaussian正初态的对流扩散最大值原理。 | F1明确反例；另有F2 |
| cc-1d-nonlinear-convection | 结构通过。201点含端点、终时5；指定周期Kružkov右迹，两个端点实际.309487/−.977827不一致。该单点反例不单独证明全场NRMSE必超限。 | F1明确反例；另有F2 |
| cc-2d-burgers-equation | 结构通过。41²内部点、终时.027；u=v恒等式最大偏差1.927786；两字段还有<1的值，违反初边界最小值。 | F1明确反例；另有F2 |
| cc-2d-convection | 结构通过。41²内部点、终时.32；标量熵解后复制u=v，实际最大差1.928605，且值<1。 | F1明确反例；另有F2 |
| cc-2d-diffusion | 结构通过。41²内部点、终时.3777；u最小−.999670，违反1≤u≤2。 | F1明确反例；另有F2 |
| cc-2d-inviscid-burgers | 结构通过。41²内部点、终时.4；标量熵解后复制u=v，实际最大差1.986519，且值<1。 | F1明确反例；另有F2 |
| cc-2d-laplace-equation | 结构通过。41²内部点，稳态标记0；混合零Neumann与非负Dirichlet应p≥0，实际最小−.998072。 | F1明确反例；另有F2 |
| cc-2d-linear-convection | 结构通过。41²内部点、终时.5；平移矩形内2/外1/边1.5/顶点1.25定义明确；实际最小−.998112，不可能是任何规定分支。 | F1明确反例；另有F2 |
| cc-2d-navier-stokes-cavity | 结构通过。41²内部点、终时10；u/v/p、突启开边速度及压力加权消均值明确。输出各场约[−1,1]，本次没有独立数值证据确认其正确性。 | F1身份缺失；数值待核实，另有F2 |
| cc-2d-navier-stokes-channel | 结构通过。41²内部点、终时5；仅u、周期压力排除额外压降；正体力启动平行流应u≥0，实际最小−.999051。 | F1明确反例；另有F2 |
| cc-2d-poisson-equation | 结构通过。41²内部点、稳态0；唯一解因中心反对称满足p(1,.5)=0，ID2527实际−.796131。 | F1明确反例；另有F2 |
| cc-2d-steady-heat-equation | 结构通过。41²内部点、稳态0；固定背景20仅评分，实际T最小−.998438违反0≤T≤40。 | F1明确反例；另有F2 |
| cc-2d-unsteady-heat-equation | 结构通过。41²内部点、终时3；持续正源且初边界≥1，实际T最小−.997896违反T≥1；背景1定义明确。 | F1明确反例；另有F2 |
| cc-fully-developed-turbulent-channel-flow | 结构通过。201点含双壁、稳态0；最近壁距离与总Cess黏度明确；双壁应0，实际−.960233/.274394。 | F1明确反例；另有F2 |
| cc-lid-driven-cavity | 结构通过。41²内部点、终时.5；u/v/p、突启及压力加权消均值明确。输出各场约[−1,1]，本次没有独立数值证据确认其正确性。 | F1身份缺失；数值待核实，另有F2 |
| cc-flow-past-circular-cylinder | 结构通过。64×64圆环内部点、终时10；Cartesian坐标、径向Jacobian权重、ψ常数20、无滑移/外涡量明确；反射对称点ψ和应40，实际1.385774。 | F1明确反例；另有F2 |
| cc-1d-kdv-burgers-equation | 结构通过。201点含周期端点、终时10；三阶项符号、原区间初态周期延拓明确；端点.261998/−.051734不一致。单点反例不单独证明全场NRMSE必超限。 | F1明确反例；另有F2 |
| cc-2d-rayleigh-benard-convection | 结构通过。41²内部点、终时50；x-z到x-y映射、总浮力b、确定初态、压力消均值明确；b最小−.996554违反初边界0≤b≤1的最大值原理。 | F1明确反例；另有F2 |
| cc-2d-shear-flow-with-tracer | 结构通过。41²内部点、终时20；周期Helmholtz投影、tracer保留原剖面、压力消均值明确；s最小−.999867，初态剖面在[−.5,.5]，违反被动扩散最大值原理。 | F1明确反例；另有F2 |
| cc-pipe-flow-disk-evp | 结构通过。单entities ID7、无伪坐标、稳态0、权重1、s=.8298599572674159；最右物理谱实部与中心笛卡尔光滑明确定义。本次无独立谱计算，s数值待核实。 | F1身份缺失；数值待核实，另有F2 |
| cc-lane-emden-equation | 结构通过。201径向点含0/1、壳体积权重、正无节点基态；f存在负值且f(1)=−.8819687305578676而非0。 | F1明确反例；另有F2 |

## t=0严格反例（输入ID与输出ID已对齐）

索引使用HDF5零基索引；ID是实体身份。每个受影响瞬态题两份样例都已检查，以下列每例首个输出字段的最大偏差点；完整多字段证据在JSON。

| task/sample | field / index / ID | 应有值 | 实际值 |
|---|---|---|---|
| diffusion-sorption-1d/01 | concentration[0, 314, 0], ID=315 | 0.002074830699712038 | -0.9998777518381448 |
| diffusion-sorption-1d/02 | concentration[0, 761, 0], ID=762 | 0.1978023052215576 | -0.9997555247219294 |
| reaction-diffusion-1d/01 | state[0, 733, 0], ID=734 | 0.9875555038452148 | -0.9790069807110604 |
| reaction-diffusion-1d/02 | state[0, 514, 0], ID=515 | 0.9999861717224121 | -0.997160772849458 |
| reaction-diffusion-2d/01 | activator[0, 774, 0], ID=12826 | -3.263612270355225 | 0.962463905682597 |
| reaction-diffusion-2d/02 | activator[0, 13264, 0], ID=211778 | 3.496574878692627 | -0.7613252726070812 |
| advection-1d/01 | state[0, 0, 0], ID=1 | 0.8319239020347595 | -0.9944569562903867 |
| advection-1d/02 | state[0, 509, 0], ID=510 | 1.851911425590515 | -0.9943058772479541 |
| shallow-water-2d/01 | depth[0, 8384, 0], ID=8385 | 2 | -0.9625318784928867 |
| shallow-water-2d/02 | depth[0, 9144, 0], ID=9145 | 2 | -0.9990561082783362 |
| burgers-1d/01 | state[0, 522, 0], ID=523 | 0.8307957649230957 | -0.9892256731279956 |
| burgers-1d/02 | state[0, 527, 0], ID=528 | 1.854138970375061 | -0.9908169348356068 |
| incompressible-navier-stokes-2d/01 | velocity[0, 18996, 0], ID=18996 | -3.823428392410278 | 0.9833980421544724 |
| incompressible-navier-stokes-2d/02 | velocity[0, 259986, 1], ID=259986 | 2.555839538574219 | -0.9735831224534024 |
| compressible-navier-stokes-1d/01 | density[0, 656, 0], ID=657 | 16.96555709838867 | -0.9215460454355981 |
| compressible-navier-stokes-1d/02 | density[0, 782, 0], ID=783 | 5.219742774963379 | -0.9991159121446758 |
| compressible-navier-stokes-2d/01 | density[0, 3989, 0], ID=3990 | 1.617030024528503 | -0.9985111025473068 |
| compressible-navier-stokes-2d/02 | density[0, 188512, 0], ID=188513 | 1 | -0.9999931783898059 |
| compressible-navier-stokes-3d/01 | density[0, 1187108, 0], ID=1187109 | 0.1621056646108627 | -0.9947980266576839 |
| compressible-navier-stokes-3d/02 | density[0, 105093, 0], ID=105094 | 1 | -0.9999788527342734 |

## SHA覆盖

下表为原始题面与DATA的SHA256；全部39份CONTRACT的SHA256为 `130d4416fd533812493780c8bc6afbc0a158de6800b59bbec14a852f3cf1c063`。324个文件的完整逐文件SHA均保存在JSON，不截短。

| task | instruction SHA256 | DATA SHA256 |
|---|---|---|
| smoke-test | `5db2a8b566d920a2fac546e6f2fe79aec958aa2ecf753d3cfa63be5deac9794e` | `51a8607a52b9173f6816d9615422d4635d727385af03ee715bda01f884325b15` |
| case-grading-test | `a574efe46353c2a9e63bdd7b3c3fe49e2bece4312768c79a62644328b7126474` | `47f6241a891866d6eab7801c7da6bea2f98c3e4ea1896a44de47019b4150211c` |
| darcy-flow-2d | `9036da63f1ff7bdf1e98ab630d8df7506431136988e628b32dcd74309214c11e` | `0b9d78fe743716bd90600b2f038c657ae15392548f271b18d7a65235d6a39ec2` |
| heat-conduction-steady-2d | `e8cc26fad2386b1eae3096ea24e266cea9177d33463a2c3f2878e87eaba78537` | `0ebddc4d16fd6f2c4e9580867cdf6885f88f467ab848f2d39dbb69c7e7fb2061` |
| diffusion-sorption-1d | `a06303c03116ce860131cc22d72f69ed140610d66daea229a75df5fe63cb0d97` | `a891d70ccf780fbffb3d23656dcf42e4ecbfd14e2c0a2b6078c0ce81e50f224b` |
| heat-conduction-transient-2d | `b828e787cafac7f9a0a90b4159c690d954068321ffccf98deaa864f76c081be6` | `8b8e8eaae4373ba80dfc0e0357b491bed4890b91e550c2c74dd46dcd1cae692c` |
| reaction-diffusion-1d | `8114570a83cebceeed43d3eede4be6cd2aaf12f25c15427959fb828f07d31299` | `6d1c350ecd002c0886e74208f740d7b1fa4e51ad7ded05e8d1d9f6e3c21b760f` |
| reaction-diffusion-2d | `61e9dccf791c6e47805fc771958376ed1425ddac501808f969593befd8f20e12` | `37d727851940d721a40fe4cf7007dbbce91d4c34ca8f729369e953aedc228ddb` |
| advection-1d | `e6cfe317424bf400fcf3b3db388c0db13a3a166ff070b2bb7d7440159382ed0a` | `8531cf967d5208907ccedb8758c2ca98d354174282c8d3a34388cc66bdaac3bf` |
| shallow-water-2d | `35ce496f2b044e31640de0e00c41e9f046d1e2b6bff5078a154869c71f07ab77` | `2dd9fe46fcfcfb5325fea0d856e09bdf5a32d143a30ea1567c477a527d665d71` |
| burgers-1d | `67591209cc81d6db73471647728c8cc367c6e21cfce8e27b701b320e013a10ed` | `63bec17ceb291bad00d348519adc960b7512a41281e643ee1c794f8d84e4468f` |
| incompressible-navier-stokes-2d | `2d09f401d62dad47322c3d6ba3b5f62b5a2c5a165d2debbb79879a757eaebf86` | `c5d70e638f7412ac9dcb6d629743fd74da261453ec1bf20114c7564b382e3b73` |
| compressible-navier-stokes-1d | `65e48635454ffdfbb11d436737e634892765d54709ccbc197db8afa153ffc64a` | `377906b0f16c12d0a72465adef1d8c579028bb1507c1403b778eae5a3c98fef3` |
| compressible-navier-stokes-2d | `3894daa72d941385f8dd2afd683e8e63cf88cd054d719677bc86fe93a0c13203` | `1d6c12880de18f433a864e059954d38a13de4488be247b61f436a3eb703e0c65` |
| compressible-navier-stokes-3d | `f4d3cde4c48d4cb8eecdcc1182cf06abdc3c84259be04c5b26ad89eb26000fb8` | `cd1013f6f6b6bdb46f33b38dcfb3e86fb7b10004241ab7681e7128794a4f6824` |
| cc-1d-burgers-equation | `43b88d4bb3db659a2b75ed998f4a2ee09ebabea9186479c5ca9eb5f0bedfe002` | `c4757d08649ca5e6677e977a35e9eaed5fcba4dd4842d035cb5aba629c1effb6` |
| cc-1d-diffusion | `0c4467090e1e5fbdaf419994a3449f0dc11ec154642689440c37816b9f8e854e` | `fcc916fce23cf82b4d74c58807542bba83785127f07779aed59f85a3331655cc` |
| cc-1d-euler-shock-tube | `852f2bfd1c2e1b85ff8444f2bf24f4ba3679d9ad9452dadebe1b6173f0330f24` | `5bf5ba925302ceca722f3b17d9874a333ca83f3594c245b9653ffc0acef2900f` |
| cc-1d-linear-convection | `7dcb395e2e0ef8f3c40985495bcc792d03b9926fe675a033b70fd2771352eb4d` | `c15409d2290291e31c81d8b91b31fc4a42bbeac120c7f22b17a30c74424e6252` |
| cc-1d-nonlinear-convection | `c5d270d05a030653118d8de22931b9db19a37a237a8e21c987b91487a5fde231` | `9c8c4359d6473a5c9dcab329cd112c1f91f13d23b6e978b7533a5c1f45a6c215` |
| cc-2d-burgers-equation | `3899041d074e781cb77f84e9929df84fd5f3cb84f90e3cc069d8a6f1c18a0606` | `6986bb1b468ed8bf345b05cda793cef58c72d426a9e348dcd302dfc713271971` |
| cc-2d-convection | `a21c1be3b535bcef3f5c85128f398cc63426ab94b1f0555d82e534d6356f2db2` | `9a1d30d15c07a5a88931f96fc487efe4476a5430efeccc1b51e0f9a54bf0f069` |
| cc-2d-diffusion | `e24cc6663dfff9b090eeceeb382c8dd8961ad1fc9f914546fbf4eb9022a2cca9` | `1e20b41aa64ccdac0f9126620eb835ad6602251e91421547d0607701fb145085` |
| cc-2d-inviscid-burgers | `6994678103a865bc8a423d3694539c4d5987702191ee412ea6fb1a6b0b8aa321` | `8b6d89871c54a997005a464eb900e910a025538986a17d1bb04255def5565082` |
| cc-2d-laplace-equation | `0b78e746fbbd865639df856958ad5643b295d00c4e049cb290fa8e92c50a1453` | `1b61b3b12abbf0bd6908204edc68f7e577e47d5f64911c85701379a67f345210` |
| cc-2d-linear-convection | `6d3144360380e08ed47af8b8b2c148e9925a39295538a2fcfab0e39836a7fda6` | `bb0034c16b97b3bbd462116178036cee74e8caf8954b6a7756e1a9a399b20b55` |
| cc-2d-navier-stokes-cavity | `1ef16a788deeb579efdbbe166a6e3b56c7272e56ce638e163e7cc84a7e9fef9a` | `40bb2eb77158e3ee05561c5b7e1769fa5898ba732a9cc43777ca049256827fd3` |
| cc-2d-navier-stokes-channel | `15d68145b40f2ee8d240929509c3f89186b3659e0ffe542dfff134aace837a66` | `893a170598e251795fa7d9cf9ad99e5f30d445920c053a31f360fc9b0790e9d0` |
| cc-2d-poisson-equation | `bc1c316acafb58c1dd557638e78647d903f8cbfa1afced073b57e5c63e368e81` | `0566aecb5253a4f09a943dec9be1f97084319c617241c283a83ac7ab7dc1f15a` |
| cc-2d-steady-heat-equation | `70b6b8441c7c0ec6052c5788b4bc0be3c2d63fc4152858e0fc7c71fd00fa5790` | `c314a5d11e8e1470f4733f845b83d6bb74dd037ae30cef39d33d79433ae3daf6` |
| cc-2d-unsteady-heat-equation | `714ef884747b1937c6317d930096d1bf2f5611ac8231f96d4d8c7b159463ce27` | `8e92668b19e74b15797b68504dfd8b876c5ba6260e74f84b767fd8c697678645` |
| cc-fully-developed-turbulent-channel-flow | `059baaa3851ac482f55bb5d2d3f6c52fc6af204188c050ec4f09b34ecccbc057` | `543aae19b43781a8a3a5597fde502f7e6632f3cd4281ea393f0a282cee92f916` |
| cc-lid-driven-cavity | `724a542a2fbcb44c27b51cb60140ad579e1dca8930806eefc87a2fa7a6a14874` | `ed23c0a6df04c00ff1555f4af252b1863523f349e0b768a43187401beca5fa05` |
| cc-flow-past-circular-cylinder | `ba1993e49f6610b4336ff270c5260c6c9d7ca09cc44035b0b2a4d6cbd438a3d2` | `3e033270a728e58bb090920dffff9ff799ad5e2354c3ee2050897414f7d57e87` |
| cc-1d-kdv-burgers-equation | `c3877212c12f45391034c26c9dccb7bc00f1a9d386149f9a5dbe5cc69acff5b9` | `639cae20cd3af28fc76e6ebc02acb87ee258c34da65ee1598725f815646f9950` |
| cc-2d-rayleigh-benard-convection | `db3312992979ac8bfa5cc8830f9ad9d9c9dc8213f3849397a5d5c4978613e127` | `677d347b9a60e3d5aa9ce25bb58d4dadacdcdfadd91676dc9ca671bd2b22242a` |
| cc-2d-shear-flow-with-tracer | `86d12617d8fb0a043a270a6f83dac17ec9c5020e10fc06039b41d4995c75ba19` | `56567199939a10c3537e1a7775f72e746d7be9d510c7323a1bc35a14e1da598b` |
| cc-pipe-flow-disk-evp | `85f006f4abbaf143cd2b446408c9b14447d3646f3ef7e16b3e9940f9d3dd0abe` | `565680b12e0529bd9b57ca51f655cf8455e217cb1bbde30bd9c782d9b1ab7f7c` |
| cc-lane-emden-equation | `6607a40772ee517d1c32e4cdf1a539b9a8f61d18b8010cfbcb13edc23d296ca4` | `796f9d2e02f8ada7340b6b85ece63b2796a74e351c8a0d7fca361013167a3a81` |

## 待核实

两道CFD盖驱腔和圆管谱样例尚无独立数值证明；不将统计外观当作错误证明。全部题目的实际墙钟/内存可达性、隐藏参考精度和隐藏判分一致性，本次未运行solver且无权读取隐藏材料，故不能认证；这不构成已确认缺陷。heat-conduction-transient-2d样例02的正时间精度同样未经独立求解认证。

## 可选改善

smoke-test当前公开样例仅float64标量，增加bool/int64/张量/独立点可以更充分演示声明的范围。稳态热传导的纯Neumann与域积分平均温度分支可另给样例。两项均非题意阻断：现有文字已说明相应语义。
