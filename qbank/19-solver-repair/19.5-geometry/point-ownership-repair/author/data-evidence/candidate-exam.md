# point-ownership-repair 独立考生审阅（exam-materials）

结论：**本轮未发现未决问题**。样例状态：**已检查全部公开样例01、02及其全部输入依赖、承诺公开输出与参考**。三文件要求和已公开的14个查询相容。

冻结材料：`dist/point-ownership-repair-agent.zip`，SHA256 `5dae9c7e11e452550ad8b5c074bb9a92ec03a80d787511ed023053cbcc7fe158`；ZIP含45个文件，MANIFEST明确列出public_samples=[01,02]，44个被列资产的哈希全部匹配（MANIFEST自身另记录于archive-inventory.json）。包内三文件与statements工作树三文件逐字节相同。

| 解释性材料 | SHA256 |
|---|---|
| `qbank/19-solver-repair/19.5-geometry/point-ownership-repair/instruction.md` | `981ca344aabbe5c40902ebea2c92945ae1edf142c0b8707c0211b5bdff542bb3` |
| `qbank/19-solver-repair/19.5-geometry/point-ownership-repair/DATA.md` | `186545a6156cb954112f8b444e267b92c81cd4ca6b3c80af75deab237da58b65` |
| `docs/CONTRACT.md` | `130d4416fd533812493780c8bc6afbc0a158de6800b59bbec14a852f3cf1c063` |

## 独立性与检查边界

独立考生视角审阅；适用仓库根 AGENTS.md 和 caeoj-candidate-review 技能及其 workflow。解释性材料仅为三文件，没有读取作者材料、隐藏 cases/reference、真实 solver 归档内容、driver.cpp、CMakeLists.txt 或 run_case.py 实现；没有编写修复、运行真实求解器、调用收费模型。公开包中的实现资产只检查存在及字节哈希，不借实现补足题意。写入仅发生于 runs/candidate-review。

## 三文件自足性覆盖

- instruction 第1—2段明确修复真实 DOLFINx 入口，单普通 utils.h、1 MiB、真实替换路径、保留四参数并增第五参数默认 true；内部可重构，其余源码/driver/适配器/编译规则不可修改，禁止独立输出和硬编码。真实 API 修改边界清楚。
- DATA“网格与几何语义”明确 D=2/3、线性三角形/四面体、可附点元素、MSH 4.1、坐标及规模范围；MSH tag 为身份，不能按存储顺序恢复标签。闭单元含表面、边、顶点；非包含查询有至少 1e-5 m 距离，避免数值阈值语义争论。
- mode 必须是 JSON 整数 0/1/2（拒绝布尔和 0.0 等）；0 为 false 严格包含，1 为 true，2 省略第五参数且语义等于1。padding 是有限 0..5 m 数，不改变实际包含。
- 候选集为逐轴闭包围盒外扩 padding 的命中单元；包含优先。无包含时，模式1/2仅从候选集选择闭单元欧氏距离最小者，无候选为未归属。明确排除了全局最近回退。几何唯一性、最近/次近 1e-6 m 间隔、无重复或内部重叠均由数据保证，不要求考生从身份推断。
- 输入 node_ids 为全部节点递增 int64，probe_ids 为正且唯一递增 int64，坐标 float64[Q,D]，times 为 float64[1]=[0.0]；无额外场、条件或几何，声明完整。
- 输出仅 probe_ids、times、owned/cell_id/distance；三字段 float64[1,Q,1]，轴按输入身份排列。owned 是0/1，cell_id 是原MSH tag或-1，distance 是选中闭单元最短欧氏距离或-1；不复制node_ids或坐标。三字段精确quantity/unit/component/value_kind给出。
- owned/cell_id 精确比较；distance 逐值绝对+相对容差1e-8，所有查询和三字段全通过才计例通过，计分例等权。非有限/缺输出/运行/构建失败规则明确。20秒每例、240秒构建、4 CPU/8 GiB、单进程及排除范围明确；这些是可读要求，未据此认证真实运行资源。
- CONTRACT补足根dataset、dtype/shape、无属性、引用与MSH/输出身份规则，题面链接可解析；没有需要从SDK或作者侧材料补充的任务含义。

## 发现

本轮没有明确缺陷或待核实的题意歧义。上述结论针对公开要求的可确定性，不是参考实现、隐藏数据、真实源码回归和资源上限的认证。

## 公开资产与证据

读取了包内README、MANIFEST、pyproject、全部样例problem.json、source.msh、input.h5、reference/grading.json、reference/reference.h5、output/result.h5；中性SDK/校验/评分器及任务扩展在包内snapshot上执行。已显式查看ownership声明检查扩展，它不执行查询包含/归属判定；没有把扩展的检查范围当作合法几何全部保证的证明。

所有45文件的路径与SHA256见 [archive-inventory.json](archive-inventory.json)。白名单快照仅包含中性工具、三文件及两组公开样例等允许资产；没有解开源码归档或复制driver/CMake/run_case。全部样例数组的dtype、shape、值及逐查询独立几何核对见 [sample-evidence.json](sample-evidence.json)，不存在未读大数组切片。

| 样例 | 完整输入 | 独立数学核对 | 公开输出/参考与中性检查 |
|---|---|---|---|
| 01 | D3、mode0、padding0，四面体顶点(0,0,0),(1,0,0),(0,1,0),(0,0,1)，原单元tag31；节点存储顺序58,24,7,41，身份数组7,24,41,58；Q7 | 用x/y/z>=0且x+y+z<=1核对全部查询；内部、外表面、边、顶点归属31；(0.5,0.5,0.5)虽命中bbox但严格模式未归属，其余域外点均未归属 | owned=[1,0,0,1,1,1,0]，cell_id=[31,-1,-1,31,31,31,-1]，无归属distance=-1，包含距离数学上0且公开约0..4e-20；在明确容差内。input、output、reference校验各通过，grade accepted/score1 |
| 02 | D2、mode1、padding0.25，三角形顶点(0,0),(2,0),(0,1)，原tag31；节点存储顺序24,7,41，身份数组7,24,41；Q7 | 用x/y>=0且x/2+y<=1判断包含，以三条闭线段投影独立算域外距离；扩展bbox为[-.25,2.25]×[-.25,1.25]；(3,3)无候选故未归属 | owned=[1,1,1,1,1,1,0]，cell_id=[31,31,31,31,31,31,-1]；距离约[0,.6260990336999411,.360555127546399,.223606797749979,0,0,-1]，逐值吻合；input、output、reference校验各通过，grade accepted/score1 |

两例probe_ids均为[3,22,41,60,79,98,117]、times=[0.0]。input只有node_ids/probe_ids/probe_coordinates/times；output与reference只有probe_ids/times及三个float64[1,7,1]字段，根与dataset无属性。公开output与对应reference每个数组精确相同。样例MSH含允许的类型15点元素以及唯一顶维单元，节点tag与坐标关联已逐一读出；没有把点元素tag当成输出cell_id。

8项CLI检查全部退出0，完整命令参数、stdout、stderr见 [neutral-checks.json](neutral-checks.json)。执行使用本机Python3.11.9以及包内src（显式PYTHONPATH，工作目录为snapshot），依赖实测numpy2.4.1、h5py3.16.0、gmsh4.15.2、jsonschema4.26.0；未安装锁定环境，pyproject声明numpy2.4.6，因此不声称完成整个锁定环境安装验证。该差异没有阻碍本轮中性校验或简单独立数学核对。

## 覆盖缺口与未执行内容

两个公开样例都是单单元，分别mode0和mode1，没有mode2默认调用、多单元候选竞争、包含优先于其他候选、候选局部最近与全局最近不同的数值实证，也没有刚好位于扩展bbox边界的样例。三文件已清晰定义这些行为，因此这些是样例实证覆盖缺口，未上升为题意缺陷。本轮没有检查隐藏数据是否覆盖这些分支。

未读取或运行真实DOLFINx源码、driver、构建规则及run_case；未提交/编译utils.h；没有认证真实C++API可编译、可信重建隔离、旧版失败现象、修复后回归、候选构建240秒或单例20秒/内存限制。源码和许可证/依赖归档的存在及哈希匹配不代表其内容已审计。未做完整公开包安装或依赖获取验证。以上限制不影响本轮对任务自足性和全部已公开样例的结论。
