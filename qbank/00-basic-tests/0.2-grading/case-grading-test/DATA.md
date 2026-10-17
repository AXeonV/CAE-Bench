# 数据定义

本题是二维节点速度场回传任务。任务、评分与资源见 [instruction.md](instruction.md)；文件结构、数组轴和引用规则见 [CONTRACT.md](../../../../docs/CONTRACT.md)。下文完整规定本题合法输入与输出。

## 输入

每例包含 `problem.json`、其 `data_file` 引用的 HDF5 和 `meshes.main.file` 引用的 Gmsh MSH 4.1 网格；文件名以清单为准，路径相对 problem.json 所在目录。

- `task` 为 `case-grading-test`，`spatial_dimension` 为 2；`geometries` 为空。
- `main` 网格的所有二维单元是一阶三节点三角形，节点坐标位于 z=0 平面，x、y 单位为 m。节点／单元 tag 是身份，不是连续行号；网格节点插入顺序也不定义 HDF5 行顺序。
- `locations.nodes` 为 `kind: mesh`、`mesh: main`、`entity: node`，其 `ids` 指向 `node_ids`。该 int64[N] 数组逐项列出网格全部节点 tag，唯一、正数、严格递增，可非连续；N≤1,000。
- `time_axes.response` 指向 `times`：float64[T]、有限、非负且严格递增，单位 s，1≤T≤100。它列出全部需回传的时刻；无需求解或生成中间时刻。
- `fields.velocity` 和 `outputs.velocity` 的描述完全相同，见下表。`conditions` 为空；没有其他场、参数、边界条件或可选物理声明。场表示输入已给定的目标数据，不涉及初态、初猜或控制方程。

| 描述键 | 值 |
|---|---|
| array / quantity | velocity / velocity |
| location / time_axis | nodes / response |
| dtype / kind | float64 / vector |
| component_shape / components | [2] / ["x", "y"] |
| unit / value_kind | m/s / point |

HDF5 恰含 `node_ids`、`times`、`velocity` 三个数组。`velocity` 为有限 float64[T,N,2]；第一轴对应 times，第二轴逐行对应 node_ids，最后一轴为全局 Cartesian x、y 速度分量。长度为 1 的轴也保留。不允许额外数组。

## 输出

结果 HDF5 恰含相同 key：`node_ids`、`times`、`velocity`。IDs 和时间轴原值、原 dtype、原顺序复制；`velocity` 保留 float64[T,N,2]，目标值为输入同 key 的全部值。不得省略未观察的分量或时刻，不添加测点值、积分量、评分结果或其他 key。

## 样例与参考

公开样例位于 `samples/<编号>/input/`，完整正确提交示例位于 `output/result.h5`。样例 `reference/` 内的判题材料供公开判分工具使用，可包含整场或稀疏参考；稀疏参考不是合法提交文件，不能复制它代替完整结果。

本题所有测点值由评分器按题面规定从完整节点场提取；输入不携带观测请求，也不要求考生读取测点文件。字段、时间及完整提交要求不会随选中的评价检查改变。
