# 独立考生审阅：扩散元件的电压贡献与热功率

## 范围与独立性

模式：`exam-materials`。独立上下文只接收白名单和审阅任务，未继承作者讨论。按 `caeoj-candidate-review` 技能，以考生读取和核对材料的视角审阅。解释性材料限 instruction.md、DATA.md、docs/CONTRACT.md；样例仅01、02各自的problem.json、input.h5、grading.json、reference.h5、result.h5。公开依据是任务明确白名单及zip内MANIFEST.json的 `public_samples: ["01","02"]`。

公开zip只读取条目名称、README.md、MANIFEST.json；未读取zip内其他载荷。未读取源码包、驱动实现、作者目录、其他case或设计/验收材料。工具仅用Python标准库、h5py、NumPy做JSON和HDF5解析以及公开公式代数核对，没有编写solver、运行可信驱动或调用收费模型。本报告是唯一写入文件。

## 材料版本（SHA-256）

| 实际材料 | SHA-256 |
|---|---|
| `qbank/19-solver-repair/19.4-observations/diffusion-element-heat-repair/instruction.md` | `213ae253355cb66b11e4875cf7f99dd6f9c30baf7c2988b01cac7fbe07450156` |
| `qbank/19-solver-repair/19.4-observations/diffusion-element-heat-repair/DATA.md` | `02b4ec9c4f1d4423e6b2905f364cd68ee1af211915ac490a305765328a00ebee` |
| `docs/CONTRACT.md` | `130d4416fd533812493780c8bc6afbc0a158de6800b59bbec14a852f3cf1c063` |
| `qbank/19-solver-repair/19.4-observations/diffusion-element-heat-repair/samples/01/input/problem.json` | `7c3d1659887fefdf92905110c1192b6d3a88b0e740f6abf466b2a20c83774c5a` |
| `qbank/19-solver-repair/19.4-observations/diffusion-element-heat-repair/samples/01/input/input.h5` | `7b1639d344348988d65ee902395201b98684455d487c8327e8b03b99e0942226` |
| `qbank/19-solver-repair/19.4-observations/diffusion-element-heat-repair/samples/01/reference/grading.json` | `aa17ccb64c3a7d8ae2ea5411dc87efd08f734d52672e29e8880d7924855aca56` |
| `qbank/19-solver-repair/19.4-observations/diffusion-element-heat-repair/samples/01/reference/reference.h5` | `493916db20e5ae07a45e8fdee0e108660e6612f6653b7bd9af235182dd45e2d8` |
| `qbank/19-solver-repair/19.4-observations/diffusion-element-heat-repair/samples/01/output/result.h5` | `493916db20e5ae07a45e8fdee0e108660e6612f6653b7bd9af235182dd45e2d8` |
| `qbank/19-solver-repair/19.4-observations/diffusion-element-heat-repair/samples/02/input/problem.json` | `7c3d1659887fefdf92905110c1192b6d3a88b0e740f6abf466b2a20c83774c5a` |
| `qbank/19-solver-repair/19.4-observations/diffusion-element-heat-repair/samples/02/input/input.h5` | `3b7d46774d5c64bf8bab8ec1e01644c21ca8fa7955cee5bcd785a339c8ec18f8` |
| `qbank/19-solver-repair/19.4-observations/diffusion-element-heat-repair/samples/02/reference/grading.json` | `aa17ccb64c3a7d8ae2ea5411dc87efd08f734d52672e29e8880d7924855aca56` |
| `qbank/19-solver-repair/19.4-observations/diffusion-element-heat-repair/samples/02/reference/reference.h5` | `9eaf5118a8e6a3e94cd1315736d39273afcdc16de3f3753fe08bb258df213b2a` |
| `qbank/19-solver-repair/19.4-observations/diffusion-element-heat-repair/samples/02/output/result.h5` | `9eaf5118a8e6a3e94cd1315736d39273afcdc16de3f3753fe08bb258df213b2a` |
| `dist/diffusion-element-heat-repair-agent.zip` | `c3854bbd256774446281fba4f8c0b1286730f466defc78a70d362f3ec00d5ee4` |
| `zip:README.md` | `a2a3a53c4991ced01d38727fef98c4e42dc083ef621c97b8dfe3d8749920d7ce` |
| `zip:MANIFEST.json` | `1d5d1438fb3374a4d3281f2b1c2bc55f1dfcc439ca23cd2bc8a10e42b3445919` |

## 题面与接口判断

题目明确要求修复两个既有子模型源码文件，而非提交结果计算程序；安装位置、替换映射、公开类和方法约束、文件类型和大小限制、构建入口及试运行方式均已给出。状态独立、单一时刻与状态ID轴的区分明确，不要求积分轨迹。

DATA完整定义了K、R、E、N范围、七个输入场、四个输出、位置/时间引用、分量顺序、dtype、单位及采样。线性分布的cell中心位置与表面端点、平均SoC的意义、OCV三次多项式及关闭扩散分支均明确。电流与分布允许独立，负扩散热及负总热不裁剪，避免根据放电符号反推状态。评分的逐分量比较公式、容差、按例计分、失败归属以及资源限制可从题面确定。

CONTRACT规定了根组dataset、严格轴复制、不得重排或广播、bool底层枚举和相对路径等，DATA的entities位置与其4.5节一致。输出结果文件由可信驱动生成，与候选仅提交两个源码文件的职责分工没有冲突。未发现需要依赖作者材料补足的任务、观测或评价定义。

## 两个公开样例：已检查

全部JSON和全部HDF5数据均已读取；不存在只检查头部或未读大数组的情况。两例problem.json相同，K=8、R=0、E=1、N=12。

| 字段/轴 | 实际dtype与shape（两例相同） | 含义核对 |
|---|---|---|
| state_ids | int64[12] | `[11,25,41,59,79,101,125,151,179,209,241,275]`，严格递增且不连续 |
| times | float64[1] | `[0.0]`，时间轴instant |
| current、average_soc、element_heat、reversible_heat | float64[1,12,1] | scalar/value，states/instant；element_heat在E=1时使用scalar |
| diffusion_enabled | bool[1,12,1] | HDF5枚举，signed int8底层，FALSE=0/TRUE=1 |
| soc_profile | float64[1,12,8] | cell_0…cell_7对应ξ=(j+1/2)/8 |
| ocv_coefficients | float64[1,12,4] | c0、c1、c2、c3，单位V |
| 四个输出 | float64[1,12,1] | surface_soc、diffusion_overpotential、irreversible_heat、total_heat |

输入根组恰为两轴加七输入；reference与result根组均恰为两轴加四输出。每个输出文件IDs与times的dtype、shape、值和顺序均与本例输入一致。六个HDF5文件均为扁平具名dataset，无属性、子组、软/外部链接、dataset别名、外部存储或虚拟dataset；全部数值有限，实际未压缩。元数据字段、采样、components、quantity和unit与DATA一致，data_file及grading的reference相对引用均能解析到白名单实际文件。

01：12个状态均开启扩散，电流为正、分布斜率为负；线性分布最大重建残差5.56e-17、平均残差0，两个端点总范围约[0.123074,0.830371]。OCV导数在[0,1]上的最小值约0.526115 V。02：12个状态均关闭扩散，profile严格常值且等于average_soc，端点范围约[0.280486,0.747850]；OCV导数最小值约0.362961 V。两例系数、电流、其他热源和可逆热范围符合DATA。

仅用公开定义，从线性profile核对表面值，再核对OCV差及两项热功率。01的reference与result相对公开公式最大绝对差分别为：surface_soc 5.56e-17，diffusion_overpotential 4.45e-16 V，irreversible_heat与total_heat各1.07e-14 W；均远低于题面容差。02四个量的最大绝对差均为0，包含负总热而未裁剪。每例reference.h5与output/result.h5的SHA也完全相同。该代数核对是公开样例一致性检查，不是子模型实现验证或隐藏数据参考认证。

grading.json两例相同：direct_outputs、pointwise/per_time/per_component，四种quantity的单位和atol/rtol与题面一致；参考文件均存在。

## 公开包核对

README指出三文档、样例、public源码/可信驱动位置，说明安装与样例运行/评分命令。MANIFEST任务名正确，公开样例恰为01和02。zip条目集合恰为MANIFEST.files键集合再加MANIFEST.json；无清单遗漏条目或清单虚列路径。

清单列有三文档、样例两套各五文件，以及题面承诺的public/CMakeLists.txt、public/driver.py、public/run_case.py、public/pybamm-source.tar.gz；还列有共享安装与协议/评分工具。所有白名单内本地三文档和十个样例文件的实测SHA与MANIFEST逐项一致。README自身内容SHA与MANIFEST一致。按白名单约束，未读取zip中三文档、样例二进制或源码等载荷，因此“清单对应当前本地版本”不等于逐字节认证zip内全部载荷。

## 发现、覆盖缺口与结论

未发现明确材料缺失、字段/轴冲突或阻断考生理解的未决问题；本轮无必须修订项。题面结论：**本轮未发现未决问题**。公开样例状态：**01与02均已检查**。考试材料范围内可只凭三文档确定任务、读取输入和核对公开输出；承诺的工具/源码资产在公开包清单中齐全。

样例仅覆盖K=8、R=0、开启扩散放电且负斜率与关闭扩散两分支，没有样例实证覆盖多RC、其他K/N、充电/反向电流、正斜率、零电流或同case混合开关；这些情形的语义已由DATA定义，此处是样例覆盖边界，不是题面歧义。

未验证：源码包完整性与可构建性、共享SDK/校验器/评分器或可信驱动实现、固定镜像安装、真实子模型调用及构建冻结隔离、隐藏case、正式成绩、数值求解精度/性能与资源预算。未将样例结构或公开公式一致性外推为这些范围已通过。
