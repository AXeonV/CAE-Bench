# case-grading-test 独立考生审阅

## 范围与结论

- 模式：exam-materials。独立新上下文，只从协调方获得任务、公开白名单和审阅边界；未继承作者方案或预设问题。
- 题面结论：本轮未发现未决问题。仅凭 instruction.md、DATA.md、CONTRACT.md，可以确定读取接口、完整输出、身份对应、时间与分量轴、数值目标、评分和资源约束。
- 样例状态：两个获准公开样例的输入与完整输出已检查，全部数组逐项精确一致，未见与三文档的冲突。
- 此结论只覆盖明确授权的公开三文档及样例 input/problem.json、input/input.h5、input/mesh.msh、output/result.h5。未读 reference/、隐藏 cases、生成器、求解实现、规划或维护文档。技能及其工作流仅作为通用审阅方法，不用来补题意。
- 基线提交：48e672c0dda191f59fb24e3c916fc4bd557fcb72。审阅时题目目录为未跟踪文件，故以下实际文件 SHA256 才是本轮材料版本依据。

## 实际材料与 SHA256

三文档由协调方作为唯一解释性材料授权；01/02 样例由协调方明确确认公开，未从目录名称自行推定公开范围。

| 文件 | SHA256 |
|---|---|
| `qbank/00-basic-tests/0.2-grading/case-grading-test/instruction.md` | `a574efe46353c2a9e63bdd7b3c3fe49e2bece4312768c79a62644328b7126474` |
| `qbank/00-basic-tests/0.2-grading/case-grading-test/DATA.md` | `47f6241a891866d6eab7801c7da6bea2f98c3e4ea1896a44de47019b4150211c` |
| `docs/CONTRACT.md` | `130d4416fd533812493780c8bc6afbc0a158de6800b59bbec14a852f3cf1c063` |
| `work/ch0-case-grading/source-final/samples/01/input/problem.json` | `b0c9798ce823de7d4e17977e8d96860944554327037d95e6844fa4ad41ada9f2` |
| `work/ch0-case-grading/source-final/samples/01/input/input.h5` | `062419dfa97d254bad5aada7457b4079fd23d1f26181cb5a947a837c6c9e7f0b` |
| `work/ch0-case-grading/source-final/samples/01/input/mesh.msh` | `3a4b414fe2eb2a5095c87cc7273ff33c4e863d4d0a12be6d56eea45e8246d37e` |
| `work/ch0-case-grading/source-final/samples/01/output/result.h5` | `1802fe01c2bcebf735ade5f99cbbc2b3b837dacf569b8fd91238f5be5ae8c084` |
| `work/ch0-case-grading/source-final/samples/02/input/problem.json` | `b0c9798ce823de7d4e17977e8d96860944554327037d95e6844fa4ad41ada9f2` |
| `work/ch0-case-grading/source-final/samples/02/input/input.h5` | `7b4f132e5797f67b85a0fd854b4042657342e0dd935be6ae3e72add024211941` |
| `work/ch0-case-grading/source-final/samples/02/input/mesh.msh` | `b093300dec8b5feb3e55b1109f63371745ff559ad7925603b8d41040c23f31fe` |
| `work/ch0-case-grading/source-final/samples/02/output/result.h5` | `39878713b17f3849701a063eed4ac8916eb1151acc2ade32585ff2807f7f09cb` |

## 任务到提交的覆盖

| 环节 | 核对结果 |
|---|---|
| 任务与建模自由 | 明确是输入二维节点速度场完整回传，无 PDE、初态或控制方程；不需解读隐藏观测请求。 |
| 清单与文件引用 | task、data_file、main 网格、nodes location、response 时间轴及唯一 velocity 描述明确；相对路径的基准及路径限制由 CONTRACT 定义。 |
| 身份与轴 | IDs 必须取全部网格节点并按 tag 递增；网格插入顺序不能决定行顺序。时间为输入列出时刻，分量固定 x/y，完整 shape 为 [T,N,2]，单例轴保留。 |
| 数据、单位和重建 | IDs int64，时间和速度 float64、有限；坐标 m、时间 s、速度 m/s。只回传离散值；测点为三角形 P1，精确列出时刻，无时间插值。 |
| 输出契约 | 恰含 node_ids、times、velocity；IDs/时间的 dtype、shape、值、顺序固定，速度目标为全部输入值；额外 key 或省略未评分分量均非法。 |
| 评分 | 先校验完整契约；每例选中整场或测点中的一个或多个检查，全过 1 分，否则 0 分；每标量绝对容差 1e-10，无相对或平均容差。 |
| 资源和启动 | python solve.py --input problem.json --output result.h5；Linux AMD64、无 GPU，10 秒含启动与读写；N≤1000、1≤T≤100，未设本题专用 CPU/内存配额。 |

检验过的反例：把 tag 当行号、按网格插入顺序重排行、交换 x/y、漏掉未选中分量、只写测点值、压掉长度为 1 的轴、在两个给定时刻间插值、读取稀疏参考并把它当提交。三文档均能明确排除；“未选中数据无额外数值判据”也与“正确目标是完整回传”区分清楚。

## 样例中性解析与实际覆盖

解析脚本为 inspect_samples.py，证据为 sample-evidence.json。使用标准 json、h5py 3.16.0、NumPy 2.4.6，未导入项目 SDK 或判题实现。对两个样例读取了全部输入/输出数组，未跳过数组区间。

| 样例 | 网格 | IDs / 时间 | 速度与输出 |
|---|---|
| 01 | MSH 4.1 ASCII，z=0；4 节点，2 个非退化 P1 三角形 | IDs=[7,13,42,91]；times=[0,0.51,1.31] | float64[3,4,2]，全部有限，输出 24 个速度值与输入逐项精确一致 |
| 02 | MSH 4.1 ASCII，z=0；4 节点，2 个非退化 P1 三角形 | IDs=[7,13,42,91]；times=[0,0.52,1.32] | float64[3,4,2]，全部有限，输出 24 个速度值与输入逐项精确一致 |

两个网格的节点插入顺序均为 [42,7,91,13]，与 HDF5 顺序不同；节点集合精确相同。检查了清单重复键和非标准数值、所用元数据、引用路径、节点/单元连接及三角形面积，HDF5 恰含三个根 dataset、无属性/组/软链接/外链/别名/虚拟 dataset/外部存储，过滤器只允许标准无损类型，dtype/shape/有序性/有限性均符合声明。

## 问题与未验证项

- 明确缺陷：无。待核实的题意或输入输出问题：无。
- 未查看 reference/ 下公开判分材料，未调用本地 grade 命令，因此不确认该目录是否完整或本地判分材料与已声明规则一致；这属于协调方明确排除的访问范围，不通过其他材料间接推断。
- 未运行完整 solver 或 Linux 沙箱，不认证 10 秒资源执行链、SDK/校验器/评分器实现、正式公开包装配、隐藏 case 覆盖或参考数值正确性。
- 样例实际覆盖 T=3、N=4、非连续 tag 和插入顺序差异；未实证覆盖 T=1、最大 N/T 或其他 HDF5 存储布局，但这些接口分支的公开定义已审阅。
- 由于任务只是 echo，本次全部速度值一致的检查可直接验证公开完整输出的目标；不把该结果外推为任何未见评分配置的正确性证明。
