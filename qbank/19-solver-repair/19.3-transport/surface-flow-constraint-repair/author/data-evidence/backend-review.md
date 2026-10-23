# Cantera 19.3.2 / 19.3.4 独立后端配置与真实消费审阅

日期：2026-10-23。按caeoj-configure-judge技能只读审查，只写本报告，未运行收费Benchmark、未修改实现。两题均无共享框架变更；本次不代替全部物理参考、方法约束、HF远端或考试材料审阅。

## 结论

- **19.3.2 surface-flow-constraint-repair：当前后端可验收。** 真实FlowReactor.cpp与可信driver强制重编，实际加载新Cantera库；最终独立Harbor Oracle 9/9，匹配冻结版本及五种实际探针。未发现阻断P1/P2。
- **19.3.4 multisite-surface-concentration-repair：当前后端可验收。** 真实FlowReactor.cpp、SurfPhase.cpp及可信driver强制重编；直接属性和耦合管流均由真实库调用输出。最终独立Harbor Oracle 9/9，匹配冻结版本及五种实际探针。未发现阻断P1/P2。

此结论仅覆盖下列实际证据与当前版本，未以旧Oracle代替最终运行，也未外推全容器安全性或任意未来镜像重建。

## 两题共享的需求到消费者映射

| 要求 | 实际绑定与判断 |
|---|---|
| 精确源码提交 | .2仅FlowReactor.cpp；.4恰含FlowReactor.cpp和SurfPhase.cpp。真实target分别位于src/zeroD、src/thermo。每文件≤1048576字节；共享prepare拒绝额外文件/链接/超限，冻结提交并记录SHA。 |
| header/CPP依赖闭包 | 两题只允许.cpp，未变更公开头文件/类布局。CMake排除每个被替换.cpp的旧SCons .os，直接编译相同真实.cpp；其余成熟上游.os作为固定外部对象重新链接。不存在先前header替换题保留旧factory sizeof的ABI缺口；driver另强制重编。 |
| 强制重建 | .2声明4项产物，.4声明5项：各候选.cpp.o、真实版本libcantera_shared.so.3.1.0、driver.cpp.o及flow-driver。均位于各自build_directory；运行删除前要求普通文件且非symlink，避免把.so/.so.3符号链接当真实产物。baseline与candidate各自删除再构建。 |
| 固定链接/运行路径 | CMake链接本题cantera_repair目标、设置SOVERSION3；运行器LD_LIBRARY_PATH来自本题build/lib。实际ldd分别解析/opt/cantera1655-build/lib或/opt/cantera1996-build/lib的libcantera_shared.so.3，结合真实样例判分支持实际加载，不单靠链接声明推断。 |
| 源码与可信材料只读 | 基础#1872镜像已将cantera-source及原构建树root/go-w；本题runtime对新driver/CMake/build执行root/go-w。共享prepare仅交本题增量build给UID1000，编译后再冻结。实际UID1000查询覆盖替换源、非替换ThermoPhase.h、src/include、旧.os、全部新产物、driver/CMake源码，均不可写；隐藏/tests、logs/verifier、/probe不可读写。 |
| 失败分类 | 缺编译器时原件强制构建失败→RuntimeError基础设施；候选语法失败→SubmissionError/build_error零分；额外文件→invalid_submission。实际候选底层C++超时→timeout；输入/参考/评分配置由judge在候选前预载，坏配置/评分基础设施错误不计考生零分。两题未配置baseline_probe，不声称已注入验证任意动态运行时基础设施损坏。 |
| 时限/总预算 | 各题候选300秒，可信baseline min(60,300)=60秒；9×(执行60+独立评价30)=810秒，最低1170秒。judge-config实际自动预算700+9×95=1555秒，staged task.toml正好1555，覆盖前置构建及开销；Agent2400、镜像构建1500、4CPU/8192MB分别消费。 |

## 19.3.2 surface-flow-constraint-repair

### driver及评分

driver按输入species_order构建机制相，以名字设置A/B/I组分、真实TP/位点密度与反应倍率，真实调用FlowReactor、ReactorSurface、ReactorNet并关闭能量，固定IDA/入口稳态容差及步数。每行独立建相与反应器，沿输入z积分；结果直接调用massFraction(name)、getCoverages、pressure、density和speed。没有在输出阶段强制质量分数和为1、替换惰性物种残差、套解析转换率或按排序补偿物理解。三反应倍率是公开输入速率常数到固定机制常数的参数映射，不是输出修正。

5个输出由中性Python adapter切片并write_result；9个实际grading.json一致，direct_outputs以pointwise/per_time/per_component覆盖全部输出。质量分数/覆盖率atol3e-7、rtol1e-6，压力0.02/1e-8，密度/速度1e-8/1e-7，均与公开要求一致。原始最终Oracle评价确实加载这些实际配置，并非author模板参与运行。

### 最终运行和绑定

正式job `repair22-cantera1655-oracle-final/surface-flow-constraint-repair__KQPcBJy` 原始result.json记录oracle、separate verifier、reward1、exception=null；verifier报告complete、9/9。归档oracle.json全部cases与原始逐项一致。实际baseline重建9.54秒、候选7.71秒；verifier阶段约48.83秒，均在真实限额内。

冻结清单 `runs/authoring/repair-22/repair22-cantera1655-oracle-final.json` 的52项资产重新计算SHA，全部匹配当前staged文件。实际agent.zip SHA为 `79ace2ad25027a9bd9c45af41846ebacb7f7665e0e5572b3d7b2ff672b6fd8bc`；当前public driver/CMake/adapter/mechanism与ZIP内容一致，共享source_repair.py/judge.py和题内配置与staged副本一致（仅归一化CRLF）。

当前author/generated、Oracle及valid的FlowReactor.cpp SHA均为 `664295cce24bec8e4b1af8ab928fa9091c00d5d965dae633908a594607aee6e9`。Oracle与valid的全部4项产物SHA一致，真实新库为 `c2967411f0e2659a4f4042642bbf8682857f19a0142a277c1bf02b2c6f8a1f08`。原始baseline stdout明确逐项重编FlowReactor.cpp、重链接库、重编driver、重链接执行文件；不是缓存无事可做。

## 19.3.4 multisite-surface-concentration-repair

### driver及评分

与.2相同的真实管流调用外，driver在进入管流前实际调用setCoverages或setCoveragesNoNorm，再直接读取getConcentrations、density、getFwdRatesOfProgress。随后调用公开指定的setCoverages重新归一化作为入口猜值，才运行管流；最终surface_concentrations再从真实SurfPhase读取。该两阶段接口顺序与DATA一致，没有将direct状态和final状态混为一谈，也未在driver手算n0×theta/占位数、进度率或质量面密度。输出后没有强制归一化，更没有绕过真实SurfPhase来补多占位转换。

9个输出由adapter纯切片返回。9个实际grading.json一致，除.2五quantity外，surface_concentration同时绑定direct/final浓度，surface_mass_density、reaction_progress_rate完整绑定。追加atol/rtol分别1e-13/1e-6、1e-12/1e-8、1e-12/1e-8，匹配题面；共享quantity与输出对象名分别绑定，没有漏评分direct或final字段。

### 最终运行和绑定

正式job `repair22-cantera1996-oracle-final/multisite-surface-concentration__4jQPzpu` 原始result.json记录oracle、separate verifier、reward1、exception=null；verifier报告complete、9/9。归档全部cases与原始逐项一致。实际baseline重建10.85秒、候选8.28秒，verifier约51.21秒，均在真实限额内。

最终冻结清单53项资产SHA全部匹配；agent.zip实际SHA为 `753ea2594085887485c2b9917daabd54560d6b335c1d5933593b69dafe0bbb4e`。当前公开driver/CMake/adapter/mechanism与冻结ZIP内容一致，共享执行代码及题内配置与staged匹配。

FlowReactor源码SHA与.2相同；SurfPhase.cpp的当前generated/Oracle/valid SHA均为 `6219c3a49bb045baddee630339248cf49fe008050fa6073f44766eaf51f70300`。Oracle与valid全部5项产物SHA一致，真实新库为 `9f9b492c041435386e5a9a27695fdd9fbe0939cfce8f1b0093a550c22e429307`。原始baseline stdout明确2个真实.cpp及driver均编译、库和执行文件均重新链接。

## 两题探针与基线来源范围

每题author/backend_probe.py已复读。两题author/data-evidence/backend-probes.json的5项均与 `work/repair-22/cantera-{1655,1996}/probe-{valid,syntax,extra,baseline-compiler,runtime-timeout}.json` 原始JSON逐项一致：

- valid将全部4/5项产物mtime设到2100年，再真实prepare、judge.execute及grade_case公开样例满分。文件/产物SHA与可信build报告逐项核对，ldd确认新库路径。
- syntax→build_error，extra→invalid_submission，缺g++→可信baseline基础设施失败；不是把任意非零编译退出都当候选错误。
- runtime-timeout实际在候选FlowReactor::evalDae中插入PID marker与C++无限循环。真实driver进入候选实现后被3秒探针时限终止，judge返回timeout，记录PID退出或僵尸；共享执行器使用killpg清理进程组。它不是对外层Python sleep做的假超时。
- 两题valid均为UID1000，全部查询路径不可写，隐藏父目录不可读；cgroup cpu.max=400000/100000、memory.max=8589934592匹配4CPU/8GiB；一次外部socket失败。权限证据是os.access查询，不冒称逐路径写入测试或全系统安全证明。

两题pristine-baseline.json均记录1284个原始archive常规文件、changed_or_missing为空，同一source_tree_manifest SHA `04f68e6e0bec93facf87536c57e5ee533a19474d1ee773b1631a12e1f87a02f3`，并记录各自base/reference镜像ID。已读prepare_runtime.py：先核对公开archive SHA，再对共享父镜像内archive所列每个真实源码文件逐一核对，之后制作本题CMake与driver上下文；没有在本题镜像预先复制其他题修复头。继承成熟原始SCons对象而重编指定.cpp的设计与此相符。

该1284文件检查证明归档列出的源文件一致，不是整个镜像文件清单审计，也不单独证明每个保留.os的全部编译历史。当前有真实原件强制构建、全题Oracle、hash/加载证据支撑所用通路，未发现固定对象与本题源码相冲突的实际问题。

另核对固定.os来源：`two-temperature-state-repair/author/runtime.Dockerfile`保留固定archive解包后的真实SCons完整构建命令，`work/repair-22/cantera-1872/build.log`包含实际mpicxx编译原始FlowReactor.os等过程；`offline-sdk-build-final.log`保留成熟父镜像制作。两题继承该父镜像的原始SCons对象，再由本题CMake排除被替换对象，未把#1872 CMake新增对象目录混入GLOB的build/src/*.os。该来源证据与1284文件原样校验相互补充，而不是只验证要替换的一两份.cpp。

## 未验证范围

本次未重新运行镜像/Oracle，没有因已有成功证据再付费或重复全套。未独立注入候选编译超时、链接/动态依赖损坏、超限文件、symlink、超时后后续case恢复或所有非法数值/容差边界；这些不被包装为本轮通过。两题没有配置baseline runtime probe，故可信编译器失败分类已验证，任意仅在运行期暴露的基础设施故障分类未获同等覆盖。当前真实运行已验证依赖可用，不据这一未注入范围宣称存在实际候选误判。

方法约束中禁止硬编码/替代程序需独立源码审查，9/9不证明方法合规；reference各108状态、HF固定assembly/strict及考试材料可由对应专责记录交付，本次不重复认证。ldd、有限路径权限、单次网络连接和PID清理均只按实际范围解读，不外推任意恶意候选、其他题或全容器安全性。
