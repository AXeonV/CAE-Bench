# 19.1.1 独立考生审阅：最终公开材料

- 模式：`exam-materials`。
- 题面结论：**本轮未发现未决问题**。
- 样例状态：**已检查**两份官方样例的全部输入、公开输出和公开 grading.json；限下述结构及声明检查，不代表数值参考认证。
- 独立性：只读协调方白名单三文件、samples/01 与 samples/02 的 input 全部文件、output/result.h5、reference/grading.json，以及公开 ZIP 的文件清单、README.md、MANIFEST.json。未读取作者材料、隐藏数据、规划、求解实现或 reference.h5 内容；未导入项目代码、未编写 solver、未修改公开材料。
- 日期：2026-10-23。未读取 Git 信息。中性解析使用 Python 标准库、h5py、NumPy。完整数组读取证据与 ZIP 清单见本目录 evidence.json，没有未读的大数组。

## 材料与 SHA256

| 文件 | SHA256 |
|---|---|
| `qbank/19-solver-repair/19.1-constraints/constrained-assembly-repair/instruction.md` | `6fcb40465a6ce87aab863b10250b4ed2fd6fe0a8697643cb76b357547b9aa3e8` |
| `qbank/19-solver-repair/19.1-constraints/constrained-assembly-repair/DATA.md` | `9a80eb966fe4b6b7c0061f12a33fda59ebbd36d1669cabbc680a169263d032b0` |
| `docs/CONTRACT.md` | `130d4416fd533812493780c8bc6afbc0a158de6800b59bbec14a852f3cf1c063` |
| `qbank/19-solver-repair/19.1-constraints/constrained-assembly-repair/samples/01/input/problem.json` | `6ea213a6551c6c709e7fae973a879c5004573afdba6e550a07df210f607a6abd` |
| `qbank/19-solver-repair/19.1-constraints/constrained-assembly-repair/samples/01/input/input.h5` | `52a369370518c9ff72c7e10ddebb33cd4cc48f64015411e7d07e004f2009d47c` |
| `qbank/19-solver-repair/19.1-constraints/constrained-assembly-repair/samples/01/output/result.h5` | `4704158bb4f68c48c698adfaebdda9d0935c26742bd05a0476c6be454fd9940a` |
| `qbank/19-solver-repair/19.1-constraints/constrained-assembly-repair/samples/01/reference/grading.json` | `afad5482d5c44bbdb15036b73220f340b487e9882944d3200ae2056cb65c4249` |
| `qbank/19-solver-repair/19.1-constraints/constrained-assembly-repair/samples/02/input/problem.json` | `55332f8ecf5e7165130d15be72e7f3d707acefafbe4ee4a0e2a81ed5dd2f899f` |
| `qbank/19-solver-repair/19.1-constraints/constrained-assembly-repair/samples/02/input/input.h5` | `a4187d6113a5e3c1d101d8b6d2fcdae3be9b4f7c5a9e5ecdd3c9ed6c81de7140` |
| `qbank/19-solver-repair/19.1-constraints/constrained-assembly-repair/samples/02/output/result.h5` | `c21d35ebe0c5d739922d039d6d4530bbbd4683bf2889d80e5498f68e0455b7f9` |
| `qbank/19-solver-repair/19.1-constraints/constrained-assembly-repair/samples/02/reference/grading.json` | `afad5482d5c44bbdb15036b73220f340b487e9882944d3200ae2056cb65c4249` |
| `dist/constrained-assembly-repair-agent.zip` | `767d89af2c3b33755367cbeae1d708c984f53e26eefc73f6eed4394accc74b36` |
| `ZIP:README.md` | `b46dd48c6d797efe5653fa848f80bc14035e45743f05cf86b1fc9ecd0ccc5d3f` |
| `ZIP:MANIFEST.json` | `508c67ef8e1e1e9d2d5b82fa15c4d89ba599fb01aed6c8bbd692c91c885b0b58` |

## 题面复核

instruction 增加固定源码版本 c6acd4e5a199f56052ba74b8e9d735a2157ba613 和唯一提交文件 1 MiB 上限，已移除上一轮 P3 可选意见涉及的维护验收句。DATA 和 CONTRACT 的实际 SHA256 与上一轮相同，前轮物理/数据语义结论仍适用。

重新核对了单文件替换、离线环境、独立编译、禁止替代入口、三种 action、位置回归保持方向、速度回归最小质量加权改动、瞬时物理加速度、双边约束、second 端点全局反力、固定体零加速度、实体身份和数组行、单位、必需输出、分量评分与资源上限。三文件足以定义这些要求，无需通过实现补题意。

具体反例交叉检查：交换链接端点会使 reaction 反号而不改变物体加速度，DATA 明确覆盖 second 固定的情况；质量 1、2 kg 两个活动体初始法向速度 3、0 m/s，速度回归目标唯一给出共同 1 m/s，排除算术平均；无约束分支明确省略 links、endpoints、length、reaction。均未发现符合三文件但要求不同答案的解释。

## 样例检查

| 样例 | 实际材料及结果 |
|---|---|
| 01 | action=4；body_ids=[7,27]、link_ids=[103]；first 固定、second 活动；长度1 m，活动体位置(0.6,-0.8,0)，速度(1.6,1.2,0)，重力(0,-9.81,0)。输入位置距离和法向速度残差均为0，质量加权约束系统条件数1。输出仅 acceleration、reaction、body_ids、link_ids、times，固定体加速度零。 |
| 02 | action=1；两个物体、一个固定体、一条链接；零重力/外力/速度；初始距离/目标长=1/0.9，在[0.8,1.2]内。输出仅 position、body_ids、times，没有无关 link_ids 或 reaction，符合按输出位置复制身份规则。 |

对全部输入和输出执行：准确 key 集合、dtype/shape、时间轴、递增非负 IDs、端点实际 ID 引用、有限值、固定体速度/外力零、质量/长度/坐标/速度/力范围、根层 dataset、无属性/子组/软链接/外部存储/虚拟 dataset、允许压缩、输出身份与时间逐值复制。检查全部通过。全部字段元数据及单位按三文件人工核对；输入 sampling 一致，输出无 sampling。

两例 grading.json 都采用 direct_outputs、pointwise/per_time/per_component。加速度 atol=0.01、反力 atol=0.05、两者 rtol=0.0005；位置及速度 atol/rtol 均1e-8，与题面一致。配置引用的相对 reference.h5 在 ZIP 清单中均存在；未读取参考数组或调用评分器。

## 公开包检查

README 指向正确三文件、public 源码/驱动及官方样例，安装、运行和评分示例与题面路径一致，并说明固定环境提供编译和驱动。清单包含三文件、基线源码压缩包、CMakeLists、driver.cpp、run_case.py、两例完整输入/输出/grading/reference 和共享运行工具。

ZIP 没有重复文件名；除 MANIFEST.json 自身外，文件清单与 MANIFEST.files 键集合完全一致；public_samples 为01、02。MANIFEST 对三文件及全部本地白名单样例资产的 SHA256 声明均与本地实际文件相符。

未读取白名单外 ZIP 成员正文。以上仅证明文件清单完整性及已授权本地资产与声明的一致性，不能等同 ZIP 全成员实际字节/CRC校验、嵌套源码包可构建、依赖可安装或 Linux 可运行。

## 问题与严重度

本轮未发现 P0/P1/P2/P3 未决问题。上一轮 P3 可选编辑意见已修复。两例未演示 action=2、second固定、无约束、多约束；这是样例覆盖限制，题面没有承诺这些样例且已经完整定义相应语义，不作为材料缺失。

## 未验证项

- 未认证公开输出或参考数值精度。结构合法、状态相容和条件数通过，不证明答案正确。
- 未执行 Chrono、编译修复、驱动或评分器；未验证1800秒开发、300秒增量编译、10秒单例及CPU/内存预算达标。
- 未验证离线镜像、预配置构建目录、源码版本与构建配置一致、源码裁剪可构建、驱动转换正确、安装依赖齐全和实际公开工具链独立可运行。
- 未读取 reference.h5 内容、隐藏数据或作者实现；未检查正式case覆盖和参考校准。
- ZIP仅按白名单读取，未复核所有成员实际内容或嵌套源码压缩包。

本结论仅适用于表中SHA256版本。公开文本和已纳入样例未见妨碍考生确定任务、接口或观测的矛盾，不宣告数值参考校准、修复可行性或预算验收完成。

## 收尾版本适用性复核（2026-10-23）

依协调方要求，仅复核末尾空白清理后的版本及重建 ZIP，没有重跑数值或全套审阅。通过把当前 instruction 原始字节末尾加回一个 LF（0x0A），重建出的 SHA256 恰为上一版 `6fcb40465a6ce87aab863b10250b4ed2fd6fe0a8697643cb76b357547b9aa3e8`；由此确认本次差异只有删除末尾一个多余换行，原3805字节变为3804字节，题意未变。DATA、CONTRACT 及前轮两例全部已授权输入、公开输出、grading.json 的实际 SHA256 均未变。

重建 ZIP 的41项文件清单、README 全文字节、public_samples=[01,02]均与前轮一致。MANIFEST.files 键集合与 ZIP 清单仍完全对应；其文件哈希声明唯一变化为 instruction.md，正确指向当前实际哈希。两例清单与全部授权样例资产哈希仍与前轮及 MANIFEST 一致。MANIFEST 的 assembly 标识未变。

| 当前材料 | SHA256 |
|---|---|
| instruction.md | `37fa63a5b95eb23311b4f428e40cac13eff50415f1f8df21d3439a08b003a915` |
| dist/constrained-assembly-repair-agent.zip | `f5b43ea6d3496ba99ff6c724b20667b2daf2d75c714954c7f1d718e2c8228861` |
| ZIP:MANIFEST.json | `ade0f124b40e2aff360df76c65d76d7876d98e2d5325a17b87b45e09ecf93572` |
| ZIP:README.md（未变） | `b46dd48c6d797efe5653fa848f80bc14035e45743f05cf86b1fc9ecd0ccc5d3f` |

原结论适用于以上当前版本：本轮未发现未决问题，样例已按原报告范围检查。原覆盖边界及未验证项全部保留；本次未读取新增 .gitattributes、驱动或其他白名单外正文，未验证参考精度与预算，未认证 ZIP 全成员实际字节。复核机器记录见同目录 final-version-audit.json。
