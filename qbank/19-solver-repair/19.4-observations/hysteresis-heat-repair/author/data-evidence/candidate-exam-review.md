# hysteresis-heat-repair 最终独立考生审阅

## 范围、独立性与结论

模式：exam-materials。题面结论：本轮未发现未决问题。样例状态：01、02 的已确认公开输入、参考、评分声明和公开输出均已检查，无必需资产缺失。样例可按公开公式解释，全部输出在题面容差内。

审阅者沿用此前仅接触公开三文件的独立考生上下文，本次重新核对实际内容版本。仅三文件承担题意解释；data-manifest.json 只确认 samples/01、02 身份，未追踪 pool 或其他 case。公开包仅读取 README、MANIFEST、中性 SDK，以及本次白名单内三文件与两样例用于字节核对。未读 author、driver、solver/source、参考生产、设计记录或隐藏数据，未运行完整 solver、构建或付费 benchmark，未修改题目。

公开包实际 SHA256：63c61fdbcdd152098dafaf6f67ad78b82e4fe85e40d24267060f0659b633a66e，与调用方冻结值一致。README/MANIFEST 声明 public_samples=[01,02]；三文件和两样例在工作树与包内逐字节相同，样例 SHA 亦与包 MANIFEST 一致。

## 实际材料 SHA256

路径以仓库根为起点；zip: 表示包内条目。仅读取这些条目的内容，MANIFEST 列出的其他资产不因列名而纳入审阅。

| 文件 | SHA256 |
|---|---|
| qbank/19-solver-repair/19.4-observations/hysteresis-heat-repair/instruction.md | ca86fb7865ea5360cbf8d2ca7a2b6c1d4bf0db816947a5ad6dc096797aa25600 |
| qbank/19-solver-repair/19.4-observations/hysteresis-heat-repair/DATA.md | 2e77b479eb5109d206b7ce949ce7a5b8a2b5834bc829d04facef74ca5d573028 |
| docs/CONTRACT.md | 130d4416fd533812493780c8bc6afbc0a158de6800b59bbec14a852f3cf1c063 |
| qbank/19-solver-repair/19.4-observations/hysteresis-heat-repair/data-manifest.json | 94568587c81c5b81f46d6c93343117a021f8238c5f711af6461ef7dd8b690d41 |
| zip:README.md | b8d9e5d8e8d70687e9b7884eba057377f8b6774d6d8786dd131b7232c7274e44 |
| zip:MANIFEST.json | bd5f1ea35fee4acaf986239bd0b6b213ede8baf64d6fadb59c46565cffe3d030 |
| zip:src/caeoj/sdk.py | 3ddf8f5a1b516eca67abae35a05a26dc1b7a8381a168d7d148ea22f2ecab9cba |
| qbank/19-solver-repair/19.4-observations/hysteresis-heat-repair/samples/01/input/input.h5 | bcf298500ce885dc8b74d171f5b4a4ce8f12040a1188eb77799a5e5ca1d2a616 |
| qbank/19-solver-repair/19.4-observations/hysteresis-heat-repair/samples/01/input/problem.json | 48fc524c68707828e65a5d39edab96caf3055c9a5a8126b63392dc5faa968323 |
| qbank/19-solver-repair/19.4-observations/hysteresis-heat-repair/samples/01/output/result.h5 | 511ce86b60e51c86148139610999c6deea1bd6ee9eea7b4ba09ac1da9d09e576 |
| qbank/19-solver-repair/19.4-observations/hysteresis-heat-repair/samples/01/reference/grading.json | 9cf2a661148a32127ddb6c4a88656c9f63e96fef688770ed7515dd66a7f93487 |
| qbank/19-solver-repair/19.4-observations/hysteresis-heat-repair/samples/01/reference/reference.h5 | 511ce86b60e51c86148139610999c6deea1bd6ee9eea7b4ba09ac1da9d09e576 |
| qbank/19-solver-repair/19.4-observations/hysteresis-heat-repair/samples/02/input/input.h5 | 5cccfc3a43df284efcd3a7b5784c4bb88a557fa9bb8a2e9e38e0848867ee30a3 |
| qbank/19-solver-repair/19.4-observations/hysteresis-heat-repair/samples/02/input/problem.json | 47d4b900eb5c7852c3dbd9396f4cdaa723f594fbb48a0b3dc55ff6b8cf5aa6fc |
| qbank/19-solver-repair/19.4-observations/hysteresis-heat-repair/samples/02/output/result.h5 | 1a215cbc645b3bc44f2468ee1fb0f30cc69046a50d54ddc2cef43d37ea5d77c3 |
| qbank/19-solver-repair/19.4-observations/hysteresis-heat-repair/samples/02/reference/grading.json | 9cf2a661148a32127ddb6c4a88656c9f63e96fef688770ed7515dd66a7f93487 |
| qbank/19-solver-repair/19.4-observations/hysteresis-heat-repair/samples/02/reference/reference.h5 | 1a215cbc645b3bc44f2468ee1fb0f30cc69046a50d54ddc2cef43d37ea5d77c3 |

## 题面与数据消费检查

- instruction:7–13 与 DATA:19–31、39–43 给出局部状态、J 按电极体积计、直接相加、输入电流符号、工作和平衡 OCP、single 零滞回项、负热不裁剪、单位与几何积分。其他场固定零与非零 J 并存是明确的局部热模型测试，不需构造完整 DFN 或温度轨迹。
- instruction:19–27 明确库内修改责任、指定函数链与原有观测、单文件路径、可信输入转换和输出责任；不能用独立输出程序替代修复。instruction:31–33 明确全输出／全状态要求、量纲容差、case 等权、时限与资源。
- DATA:7–11、15、35 与 CONTRACT 的实体／时间／场和输出规则足以解释状态身份及分量。两样例均 N=6，IDs=[7,31,88,201,449,801]，times=[0.0]，P_n=P_p=1，pairs=1；01 两极 mask=1，02 两极 mask=0。
- 逐字段核对了全部 JSON 输入／输出元数据、quantity、单位、sampling、shape、dtype、字段全集，全部与 DATA 一致。输入 18 个场各为 [1,6,1] float64，实体 IDs 为 [6] int64，时间为 [1] float64；输出五场及 IDs／时间齐全、无额外 key。
- 使用 h5py 读取两例全部输入、公开输出及参考数组，未截取大数组。检查根级 dataset、无属性／组／软链／外链／别名／外置或虚拟数据、允许压缩、有限数值、递增身份、固定轴和各输入范围；均通过。02 single 相的工作／平衡 OCP 数值一致。
- 两份 grading.json 与题面量纲容差、逐点逐时刻逐分量检查相符。公开 output 与 reference 的数值及文件字节均一致。

## 独立数值核对

仅从公开输入使用 NumPy 代入 DATA:39–43：每极按相求 J[eta+T entropy+active*(U-U_eq)]，再计算厚度、面积、pairs 和实际 volume 组合。single 项明确置零；不是调用作者参考或库实现。以下为全部 6 状态的最大绝对误差。

| 样例 | heat_negative (W/m³) | heat_positive (W/m³) | area_heat (W/m²) | cell_heat (W) | volume_heat (W/m³) |
|---|---|---|---|---|---|
| 01 | 1.8189894e-12 | 7.27595761e-12 | 1.11022302e-16 | 3.46944695e-18 | 5.68434189e-14 |
| 02 | 2.27373675e-13 | 4.54747351e-13 | 2.22044605e-16 | 1.38777878e-17 | 3.41060513e-13 |

具体反例核对：02 的首状态负极热为 -177.5043847360232 W/m³，公开输出保留负值，因此不能非负裁剪。01 的首状态为 heat_negative=2369.709683998627、heat_positive=797.3185943634177 W/m³，组合得到 area_heat=0.22375230860161102 W/m²、cell_heat=0.006683084924150697 W、volume_heat=148.05395352055737 W/m³；实际 volume 被明确使用。给定熵项和 OCP 差值均可从实际输入直接读取，无需反推完整电池状态。

## 问题与缺口

本轮没有需修订或待核实的公开题意／样例问题。样例 01 覆盖两极单相滞回，02 覆盖关闭滞回及负瞬时热；两例不覆盖双相、混合 mask、pairs>1 或边界极值，这属于公开样例覆盖范围，不表示任务定义缺失。

本轮未执行公开包安装、可信构建或真实库导入／观测链，未验证 driver 与源码实现、独立包实际运行、资源实际达标、隐藏 case、源码修复正确性或参考生产来源。SDK 仅检查中性读写接口声明保留数组、轴和单位，不把 SDK 或其依赖作为额外题意来源；未执行其校验器。上述未执行项目不由本次题面和样例数值核对认证。
