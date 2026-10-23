# 实际数据独立审计：空间梁方向变换修复

结论：**通过（本轮实际输入、参考输出绑定和公开契约一致性）**。已检查全部10个计分case、40根梁，以及2个公开sample的8根重复梁。无资料缺口，无发现需修订项。结构、契约、物理关系的检查均完成；本结论不代替参考来源资格认证、真实求解器执行或资源实测。

## 范围、独立性与版本

按 caeoj-data-review 技能执行。审阅者已完成独立考生审阅，本阶段经协调方明确扩大白名单：三份公开文档、全部实际cases输入及依赖、对应reference判题配置和参考、2个samples完整公开输入/参考/输出、data-manifest.json、.data-assembly.json及其回执描述。三文档仍是唯一题意依据。未读取作者生成器、参考实现、求解源码、driver、设计报告，也未运行题目solver或付费benchmark。未修改正式数据、实现或回执。

基线提交 `940fa23777538be857eb18a3acc6b1b0d4ad67b7`；题目当时在未跟踪的19.2-operators目录中，故实际SHA作为审计版本证据。完整55文件路径/SHA清单保存在 [evidence.json](evidence.json)：三公开文档、data-manifest及装配回执5文件，10case×4文件，2sample×5文件。无未读大数组；本轮全部HDF5 dataset均完整读取。

| 解释文件 | SHA256 |
|---|---|
| instruction.md | 11bc5c792c1191dd02fb6170734b8dcfd5a95a76aaf20be087787535721cd637 |
| DATA.md | ea86ff1826a9038214f870e56262b96bc41c1b78a386fe85139f5cb0bd7d07c3 |
| docs/CONTRACT.md | 130d4416fd533812493780c8bc6afbc0a158de6800b59bbec14a852f3cf1c063 |

装配selection SHA256为 `d4a564f18b46558051df5060875e0a56fe564eb5892b990efec953f95ac1acf2`，固定revision为 `2ebfb364340fb0928dc2fd95d610aa2e1ebd4ed6`。独立复算全部描述原文摘要、case ID、complete标记、文件大小/SHA、回执绑定均吻合；样例01/02分别与计分case 01-aligned-public/02-oblique-public共享同一个case ID和描述摘要。

官方维护核验 `.venv/Scripts/python.exe -X utf8 -m caeoj_tools.cli data verify --task spatial-beam-transform-repair --strict` 返回valid=true、errors=[]，public_cases准确列出上述两项；没有刷新绑定或重新装配。inventory工具盘点12个输入，gaps=0（其not_evaluated不被当作本次审计结论）。初次调用系统Python缺少caeoj/caeoj_tools，改用项目.venv后两项检查成功。

## 全量输入与表示覆盖

完整元数据对照使用从最终DATA直接手写的13输入和5输出表，逐对象比较quantity、unit、array、dtype、kind、component_shape、components、location、time_axis、value_kind、sampling，未复用生成器表。JSON均为相同的合法模型声明：task/model固定、parameters={}、spatial_dimension=3、geometries/meshes={}、conditions=[]；无额外依赖文件。

| JSON/HDF5路径 | 文档依据 | 全量证据 |
|---|---|---|
| task/physics/geometries/meshes/conditions | DATA:3 | 12入口一致；无条件分支、无网格依赖 |
| locations.beams、beam_ids、time_axes、times | DATA:5、CONTRACT实体/时间节 | 每入口4个正int64严格递增ID=[11,27,43,89]，float64 times=[0] |
| fields.endpoints、section_axis | DATA:7、11–12、25 | [1,4,6]/[1,4,3]；完整端点范围、长度、轴模和正交投影下限通过 |
| fields.young_modulus/poisson_ratio/area/inertia_y/inertia_z/torsion_constant/shear_area_y/shear_area_z/density | DATA:13–21、27 | 全部[1,4,1] float64，单位和标量value标签准确；E/ν/A/I/J/Ay/Az/ρ逐值范围通过 |
| fields.body_acceleration/tip_load | DATA:22–23、27、29 | [1,4,3]/[1,4,6]，全局方向及M/L标签准确；全部加速度和载荷范围通过 |
| outputs.lhs_combined/lhs_separate | DATA:31、33–38、43 | [1,4,144]，144个row_i_col_j标签按行优先，归一化刚度单位N/m |
| outputs.rhs_combined/rhs_separate | DATA:29、31、39–40、43 | [1,4,12]，dof_0至dof_11顺序完整，单位N |
| outputs.tip_displacement | DATA:31、41、43 | [1,4,6]，ux/uy/uz/L_rx/L_ry/L_rz标签，单位m |

每个HDF5检查完整key集合、浮点有限性、dtype、完整shape；输出复制的ID/time逐值一致。根结构仅dataset，无属性、子组、软/外部链接、别名、外存储或虚拟dataset；压缩/过滤器在CONTRACT许可范围。不存在省略分量轴或用一维缓冲区替代矩阵的情况。

| case | 梁数 | 非零体加速度梁数 | 非零端力梁数 | 非零端矩梁数 |
|---|---:|---:|---:|---:|
| 01-aligned-public | 4 | 0 | 4 | 4 |
| 02-oblique-public | 4 | 0 | 4 | 4 |
| 03-spatial-mixed | 4 | 0 | 4 | 4 |
| 04-axial | 4 | 0 | 4 | 0 |
| 05-torsion | 4 | 0 | 0 | 4 |
| 06-shear-bending | 4 | 0 | 4 | 4 |
| 07-uniform-body-force | 4 | 4 | 0 | 0 |
| 08-symmetric-section | 4 | 0 | 4 | 4 |
| 09-negative-direction | 4 | 0 | 4 | 4 |
| 10-section-roll | 4 | 0 | 4 | 4 |

40根中27根Iyy≠Izz、13根Iyy=Izz，40根Ay≠Az，涵盖坐标对齐、平面斜向、一般三维和反向梁以及截面转角。密度逐例取值和方向细节见 [bindings-coverage.json](bindings-coverage.json)。公开2sample均b=0的缺口，在实际case07的4根非零b梁中得到数值检查。

## 输出、物理关系及评分绑定

全部10case与2sample的reference/grading.json均采用完整direct_outputs，reference.h5引用存在；3个quantity的单位、逐时刻/逐分量pointwise规则、atol/rtol与instruction:11完全一致。不是稀疏参考。2sample各自output/result.h5与参考全数组逐值一致，SHA匹配公开ZIP清单。计分case未承诺独立output/result.h5，本审计没有将参考自身比较当成数值证明。

中性NumPy检查按公开S和R恢复物理局部算子，逐梁检查完整矩阵对称性、6个刚体模态、数值秩6和半正定性，再观察自由端6×6柔度的轴向EA、扭转GJ、EIzz/GAy及EIyy/GAz配对、±L²/(2EI)转角耦合。全部通过。最大矩阵对称绝对误差5.961e-8 N/m，最大刚体相对残差4.952e-17，最大柔度误差/最大参考幅度3.042e-13。

依据DATA:29独立计算w=ρAb、一致节点力和端矩，再用R及S变换；40根全部rhs符合，最大绝对误差7.106e-14 N。case07 ID27为具体非零端矩证据：ρ=4598.8235261965965 kg/m³、A=0.004922544406294135 m²、b=(1.7656370168681743,2.0612037001416823,2.7074929150670783) m/s²；输出两个节点归一化平移力均约(23.9822023323,27.9968100536,36.7751934753) N，根端归一化矩(2.81969562235,4.89895205191,−5.56836067028) N，自由端矩为相反数。该观察可区分漏乘密度、错误截面方向或一致端矩反号。

combined/separate矩阵及力逐值一致。依据DATA:43，用combined自由端块与body-tip+tip_load独立重解后，全部40根及8根样例重复梁的tip最大绝对差为0。未以连续梁的均布载荷公式取代指定有限元响应，也未读取任何参考生成实现。上述检查提供物理关系证据，不被称为来源认证或完整数值参考资格证明。

## 从最终DATA独立选取的契约变体

仅在本审计目录fixtures修改副本。正式SDK来自发布ZIP的src/caeoj、caeoj_bundle、caeoj_task_ext，复制供运行而不阅读实现；新子进程以该src优先的PYTHONPATH调用CLI，未载入或运行题目solver。复现脚本 [check_sdk.py](check_sdk.py) 与完整诊断 [sdk-evidence.json](sdk-evidence.json) 留存。

正式SDK对12实际输入、12完整参考及2公开示例输出的26次validate-input/output均通过。未运行参考对自身判分并将它冒充数值认证。

独立5个合法变体均接受：非零b=(1,−2,3)并保留原非零tip_load、Ay=1e-5A下界、ν=0、b各分量=−20边界、替换为[100,200,400,800]的无物理意义合法ID。独立16个非法变体均以退出码1拒绝：参考轴与梁平行、零梁长、ρ=99、b=20.01、M/L=10000.1、Ay=2A、Az=1e-6A、ν=.451、ID含0、density改float32、times=[1]、输出缺rhs_separate、错误physics.model、density错误单位、lhs分量标签反序、添加conditions记录。预期均来自DATA/CONTRACT，不取自生成器。该组变体同时检查“合法不误拒”和“非法不放行”，不宣称穷尽所有边界组合。

## 缺口及结论边界

无本范围必需文件缺失，无未检查数组。实际资料没有非零b与非零tip_load同时作用的数值case；合法混合载荷副本已通过契约解析，但未运行solver产生此副本参考。未对参数全部极端组合做数值校准，未验证构建、真实3API调用及CPU/内存/时间限制。

装配描述origin为prepared-input，本阶段未获准读取作者生产者记录或参考求解源码，也未审计上游物理参考出处；不能据本轮结构、关系和摘要检查宣称来源建设或数值参考资格已全面认证。若需此认证，应由来源建设环节提供/审查独立生产者与精度证据。当前实际数据与已公开定义一致，故本轮数据审计通过。
