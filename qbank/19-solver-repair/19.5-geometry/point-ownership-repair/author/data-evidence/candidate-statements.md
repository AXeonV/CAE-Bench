# point-ownership-repair 独立考生审阅（statements）

结论：**本轮未发现未决问题**。样例状态：本模式未纳入；公开样例另以 exam-materials 独立记录。

基线提交：`df9eefb00cd3c485e17e233d07837294028c742c`。审阅实际工作树文件，版本以下列 SHA256 为准，不用提交号替代文件版本。日期：2026-10-23。

| 允许解释性材料 | SHA256 |
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
