# #1872 双温状态关系修复：最终独立考生审阅

## 结论与范围

模式：exam-materials。题面结论：**本轮未发现未决问题**。样例状态：**已检查**，两份已明确公开的输入、评分配置、参考输出和公开输出均已完整读取和逐元素复核。

审阅独立沿用考生视角，只用 instruction.md、DATA.md、docs/CONTRACT.md 解释题意；data-manifest.json 仅用于确认 samples 01/02 的公开身份，没有跟随其中其他 case/pool 路径。包内只读取 README.md 和 MANIFEST.json 校验材料身份及入口，没有读取源码、driver、run_case、构建文件、作者/设计/来源记录或隐藏数据。两份 problem.json 均未引用额外 YAML 依赖，因此没有读取 YAML。未修改公开材料。

最终 instruction 仅在原构建/样例命令处改为 `/opt/cantera-source/build` 和 `samples/01/input/problem.json`；DATA 与 CONTRACT SHA 和上轮复核完全相同。构建路径被一致用于环境声明和 cmake 命令，样例命令现在直接指向公开 JSON；库头文件提交边界和可信运行器写结果的职责一致。前轮 DATA 写结果责任 P2 仍关闭。

没有执行真实库构建、可信驱动或正式判分程序，没有检查隐藏数据，没有运行付费 benchmark。数值检查是公开数据的中性独立复算，不证明库内实际 setter/getter 调用链、资源达标或隐藏数值参考正确。

## 实际材料版本

下表为实际读取文件 SHA256。公开包仅检查 MANIFEST 中声明的三文档及十个样例文件 SHA 与工作树相等，没有读取 ZIP 内这些文件正文；README 的样例入口也与最终 instruction 一致。MANIFEST 不是实际库功能或编译正确性的证明。

|文件（仓库相对路径）|SHA256|
|---|---|
|qbank/19-solver-repair/19.3-transport/two-temperature-state-repair/instruction.md|0a7874f0d8cf083ed15e6970542ae4ebcc9a8eac2052d8642e2bd7ba2492f074|
|qbank/19-solver-repair/19.3-transport/two-temperature-state-repair/DATA.md|96e4fd3b7a761e283a667c0bfe5c9185ba11abe41411e0fa912bdb365c3a2591|
|docs/CONTRACT.md|130d4416fd533812493780c8bc6afbc0a158de6800b59bbec14a852f3cf1c063|
|qbank/19-solver-repair/19.3-transport/two-temperature-state-repair/data-manifest.json|df5f871e0a4c929ffb6797ef008007d7c22d241ece5bce2755025c576948adb6|
|dist/two-temperature-state-repair-agent.zip::MANIFEST.json|67ca1f5e69363bd1138c6d22f3d0fa1fa9c3d99c6dfbc3967035a09e56e89a0a|
|dist/two-temperature-state-repair-agent.zip::README.md|bf8f0c444dd20c4646f3a36d88998b5cc1a4948fce933bdd06b2bbac511c639d|
|qbank/19-solver-repair/19.3-transport/two-temperature-state-repair/samples/01/input/problem.json|99c7a0ad65fb2e2b6a5550889b71572e653a1ce4cfc3559c1724ca89ffc651c9|
|qbank/19-solver-repair/19.3-transport/two-temperature-state-repair/samples/01/input/input.h5|f898e3e1dd45b1d2007ff55d5288b5bfebb41002849aebc2ce86cc4a35ef545c|
|qbank/19-solver-repair/19.3-transport/two-temperature-state-repair/samples/01/reference/grading.json|17a3b9d1d4610b33650cf31d461c589fc58dd89a6773816f85c7e6d513ac905a|
|qbank/19-solver-repair/19.3-transport/two-temperature-state-repair/samples/01/reference/reference.h5|4dab59878523f077f7bba6ec65fa5446d374ed60c33a792c9a03eaa2dc4618a4|
|qbank/19-solver-repair/19.3-transport/two-temperature-state-repair/samples/01/output/result.h5|4dab59878523f077f7bba6ec65fa5446d374ed60c33a792c9a03eaa2dc4618a4|
|qbank/19-solver-repair/19.3-transport/two-temperature-state-repair/samples/02/input/problem.json|99c7a0ad65fb2e2b6a5550889b71572e653a1ce4cfc3559c1724ca89ffc651c9|
|qbank/19-solver-repair/19.3-transport/two-temperature-state-repair/samples/02/input/input.h5|7eadd2dcfbc5cbb9bc04306899681f06d5808929a2419fc08b7df44c402d12f4|
|qbank/19-solver-repair/19.3-transport/two-temperature-state-repair/samples/02/reference/grading.json|17a3b9d1d4610b33650cf31d461c589fc58dd89a6773816f85c7e6d513ac905a|
|qbank/19-solver-repair/19.3-transport/two-temperature-state-repair/samples/02/reference/reference.h5|45c2b4e42e8f0ab00cabc6db790565fc1780a221f841595ab37dcf274f9ab2ee|
|qbank/19-solver-repair/19.3-transport/two-temperature-state-repair/samples/02/output/result.h5|45c2b4e42e8f0ab00cabc6db790565fc1780a221f841595ab37dcf274f9ab2ee|

## 输入、接口及评分核对

两样例各 N=12，共24个独立状态。JSON 的 task/model、空参数/几何/网格/条件、entities IDs、瞬时轴、全部输入输出字段的单位、分量、dtype、shape 和 sampling 与 DATA 相符。读取全部 HDF5 数组，未跳过大数组；输入全有限且在声明范围，IDs 非负严格递增，输出 IDs/时间值、顺序、dtype 与输入一致。输入和输出 key 集合正确，所有四项输出的每个状态及三个浓度分量都已比较。HDF5 根层扁平、无属性/外部链接/虚拟数据，所见压缩在允许范围。

两份 grading.json 都是 direct_outputs 指向本地 reference.h5，policy v2 覆盖 pressure/electron_pressure/density/molar_concentration；逐点、逐时间、逐分量比较，rtol=1e-10，atol 依次为1e-7、1e-7、1e-12、1e-14，单位与题面一致。评分文件没有覆盖这四项的宽松规则。每样例 public result 与 reference 的 SHA 相同，但仍分别与独立物理复算比较，没有以两者彼此相同代替数值检查。

## 中性复算方法及结果

只依公开定义使用 R=8314.46261815324 J/(kmol K)，物种摩尔质量 [31.998,15.999,0.0005485799088728283] kg/kmol。令 W 为摩尔分数加权摩尔质量，A(Te)=(1-Xe)T+Xe Te。mode0 从给定密度得到总浓度 c=rho/W，修改 Te 后 c 不变；mode1 初态 c=P/[R A(Te)]，修改电子温度后再施加同一总压，最终 c=P/[R A(Te2)]。最终计算 rho=cW，P=cR A(Te2)，Pe=c Xe R Te2，物种浓度 ck=cXk。

这些公式仅用于审阅公开样例，不提供提交 solver，也不据输出反推定义。逐行复算相当于每个状态重新初始化，不存在跨行累计。初态和中间状态由公开调用顺序确定，但只有最终状态有公开输出；没有观测库实际中间状态。

|样例|实际覆盖|reference 和 public output 相对独立复算的最大绝对误差|
|---|---|---|
|01|12行全部mode0；T=Te=300 K，Te2从300至100000 K，X=[0.5,0,0.5]，rho=0.6415 kg/m³|四项全部为0|
|02|12行全部mode1；T=Te=Te2，组分变化，总压100至5e6 Pa|P 9.31323e-10 Pa；Pe 1.16415e-10 Pa；rho 1.77636e-15 kg/m³；浓度5.55112e-17 kmol/m³|

两样例全部满足公开容差。02最大“误差/允许误差”约2.133e-6，远小于1。完整逐项误差和初/终状态复算值见 evidence.json；检查脚本 check_public_samples.py 使用 NumPy 2.4.1、h5py 3.16.0，没有导入项目实现。

01直接展示固定密度修改 Te2 时，总压/电子分压变化而实际各物种浓度不变；例如末行总压约1.6718661e7 Pa，超过 mode1 的输入压力上限不构成问题，该上限约束的是 mode1 constraint_value。02展示等温压力路径，初/终密度一致且 P=给定总压。电子质量按公开非零常数计入。

## 覆盖缺口与保留结论

公开样例没有覆盖 mode1 的非等温电子温度变更、Te2低于T、零电子或mode0中非零O组分；这不构成题意歧义或公开样例数值错误，也不据此推断隐藏数据覆盖。三文件仍清楚定义这些范围和回归极限。

本轮未发现明确缺陷或待核实的公开材料矛盾。保留前轮对双温重粒子/电子身份、初态与最终状态约束、独立行、单位/浓度、提交边界、评分与资源文字完整性的结论。实际源码 API 分派、YAML 的库内解析、构建命令可执行性、公开包完整消费链、隐藏数据、参考生成来源和资源实测仍不在本轮验证结论内。
