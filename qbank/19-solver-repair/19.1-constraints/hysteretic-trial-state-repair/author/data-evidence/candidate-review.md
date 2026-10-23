# hysteretic-trial-state-repair 独立考生审阅

## 模式、结论与独立性

先执行 statements 审阅，再执行 exam-materials 审阅。最终题面结论：本轮未发现未决问题。初版题面的一项运行接口冲突和一项非阻塞导航问题已在最终版本关闭，修订历史见下文。样例状态：01、02 全部公开输入、参考、评分及输出已检查，无缺失必需资产；数值核对均通过。

本审阅上下文此前仅接触另一题的公开材料与考生审阅技能。对本题仅 instruction.md、DATA.md、docs/CONTRACT.md 解释题意。data-manifest.json 仅读取 samples 映射确认身份，未追踪 pool；ZIP 仅读取 README/MANIFEST、中性 SDK 及已批准三文件和样例以核对字节。未读取 driver、solver/source、author、设计、隐藏 case 或参考生产材料，未编写完整 solver 或执行付费 benchmark。审阅未修改题目。

初次冻结 ZIP SHA256：82160e8b0412ec70050f66964484c16e777f43e6b71c7e346801fec896608928，与调用方给定值一致。README、MANIFEST 和 data-manifest 共同确认仅本轮 samples/01、02 的公开身份。审阅报告和中性核对证据存于本目录。

## statements 发现及关闭记录

### P2：运行接口的输出扩展名与协议冲突

位置：初版 instruction.md:9、DATA.md:50–52、CONTRACT.md:27；ZIP README 的命令已使用 result.h5。

触发反例：严格按题面执行 `run_case.py --input problem.json --output result.json`，将得到一个命名为 JSON 的路径；题目同时要求按 CONTRACT 输出 HDF5，并固定 `.h5` 扩展名。考生无法仅从三文件确定此入口是否有 JSON 例外，或命令示例是否陈旧；此处不能通过阅读驱动推断要求。

最小建议：题面运行示例改为 `--output result.h5`，与 DATA、CONTRACT、README 和公开样例一致。初次报告后交作者修订；最终版本有界复核已确认命令为 `--output result.h5`，本项关闭。

### P3：协议链接未指向包内位置（非阻塞）

位置：初版 instruction.md:5 的 ``CONTRACT.md（初版误指同目录）``。三文件审阅可以读取指定协议，且 ZIP README 指向 docs/CONTRACT.md，但题面该同目录链接没有对应公开资产。

最小建议：改为正确的仓库相对路径。此项是导航问题，不产生数学多解；最终版本已改为 `../../../../docs/CONTRACT.md`，解析到包内 docs/CONTRACT.md，本项关闭。

## statements 实际覆盖

- 输入是相互独立材料程序，program_ids、唯一 instant 时间、float64 的整数 count、有效前缀与严格零 padding、每类点数和正负侧对应，均可从 DATA:7–28 与 CONTRACT 的实体／数组规则确定。CONTRACT 另要求 IDs 递增，DATA 没有允许乱序的例外，二者可同时满足。
- DATA:32–46 给出全新材料、零初态、history 提交、trials 连续未提交、float64 返回目标、接受、continuation、回滚和 reset 的七步顺序。未提交试探不得污染已提交状态；不评价完整提交反向循环，pinching/beta 不要求考生重建任意滞回历史。
- DATA:42 明确用实际 float64 差而非原始 return_delta 判断，严格小于 EPS=2^-52 才恢复，等于阈值属于正常方向推进。恢复完整态且不保留微小目标应变，排除了只恢复应力或切线的部分实现。
- DATA:28、44 明确骨架分段线性、计分非零点远离折点至少 1e-7；零态切线使用正侧首段，非零微小应变使用其符号侧，故折点导数不需要额外约定。
- DATA:3、50–52 明确 stress/tangent/work_density 都为 Pa（功密度等于 J/m³），输出六检查点和四场，未提交 returned 的 getEnergy 仍是已提交功；跨折点也按实际提交离散梯形增量，不能用连续骨架积分替换。
- instruction:7 限制两个普通 .cpp 文件、替换路径和真实类接口，禁止驱动／构建／协议修改及替代模型；instruction:9、11–13 声明 GCC14.2/C++17/CMake/Ninja、构建120s、每输入20s、整输入全输出通过才计分及基础设施异常边界。最终 instruction:13 同时给出4个CPU、4GiB内存；总考生时限未另列。本轮不对真实执行资源达标作认证。

## exam-materials：全部公开样例核对

两例均 N=4、program_ids=[13,29,47,83]、times=[0.0]。01 四条程序均 Hysteretic、两侧各2点；02 均 HystereticSM、两侧各7点。每例前两条正向、后两条负向，history 有两步、continuation 两步、trials 为3或4步并可跨零，两例 return_delta 均为零。

使用 JSON/h5py/NumPy 中性读取，核对全部17输入场和4输出场的 quantity、unit、kind、component_shape、components、sampling、location、time_axis、dtype 及键集合。实际输入为 `(1,4,C)`，输出为 `(1,4,6)`；IDs/time 的形状和数值被正确复制。逐文件检查 HDF5 根级 dataset、无属性／分组／链接别名／外置／虚拟数据、允许压缩、有限值；检查整数 count、零 padding、正负骨架符号及范围、严格递增、正且非增段刚度、pinching/beta、全部操作应变范围、单向历史与continuation步距、计分点离折点距离，均通过。

全部公开 output 与 reference 字节相同，输入与输出／reference 在 ZIP 内与工作树逐字节一致，各 SHA 与 MANIFEST 一致。两份 grading.json 对全部四 quantity 的单位、逐点／逐时刻／逐分量规则及 atol/rtol 均与题面一致。

独立数值核对仅按公开单向线性骨架求各计分点应力与斜率，沿实际 history/continuation 步计算 `0.5*(sigma_old+sigma_new)*(epsilon_new-epsilon_old)` 累计功，按返回／接受／回滚／reset 协议构成六阶段预期值。没有模拟未计分的任意反向滞回、内部材料实现或完整 solver。所有4×6×4输出数值均在题面容差内。

| 样例 | 应变最大绝对误差 | 应力最大绝对误差 Pa | 切线最大绝对误差 Pa | 功密度最大绝对误差 Pa |
|---|---|---|---|---|
| 01 | 0 | 4.656612873e-10 | 2.980232239e-08 | 0 |
| 02 | 0 | 0 | 0 | 0 |

具体功密度反例：02 的 program_id=13 在 committed/returned/accepted 均为16810.16418358001 Pa，continued/rolled_back 均为185495.27887284776 Pa，reset 为0。跨零未提交试探未累计入 getEnergy；continued 的离散求和没有用连续积分替代。

## 实际材料与样例核对时 SHA256

路径相对仓库根；zip: 表示冻结包内条目。下表记录独立样例核对时读取的实际版本：此时输出命令已先行修复，链接和资源尚未补齐。初始冻结包的 instruction SHA 为493c477698509138faeb4273bf2fb6e660a171a5a7dbb527d85984862caa3ecc；下表中间版本与最终版本的区别单独保留，不将中间版本冒充初始冻结版本。最终修订见末尾有界复核。

| 文件 | SHA256 |
|---|---|
| qbank/19-solver-repair/19.1-constraints/hysteretic-trial-state-repair/instruction.md | fc4f1b0fdeb377fd6affcfe8b12b4a11a6a0edce9b47b512312658043706d555 |
| qbank/19-solver-repair/19.1-constraints/hysteretic-trial-state-repair/DATA.md | 54d476fc8d62e3006e857455082bf2476c4d714e945108873accfb53f9c523ef |
| docs/CONTRACT.md | 130d4416fd533812493780c8bc6afbc0a158de6800b59bbec14a852f3cf1c063 |
| qbank/19-solver-repair/19.1-constraints/hysteretic-trial-state-repair/data-manifest.json | c314edae10f388f697e22ea659843728995beb423c3235b1e35de3d4b3c314d5 |
| zip:README.md | f34eab261e068446d7ee93f00d8d57fc7affd36b7cc33ef9059e03b01211453c |
| zip:MANIFEST.json | c415b8db40be3ca891a20fdd67b1db74c53702b80006f6b9fa5bc9b08a556d1d |
| zip:src/caeoj/sdk.py | 3ddf8f5a1b516eca67abae35a05a26dc1b7a8381a168d7d148ea22f2ecab9cba |
| qbank/19-solver-repair/19.1-constraints/hysteretic-trial-state-repair/samples/01/input/problem.json | 3188bfedc056f80dcd75f7eaaf7e7215e981619f93fb6755e129e9642d91a490 |
| qbank/19-solver-repair/19.1-constraints/hysteretic-trial-state-repair/samples/01/input/input.h5 | 1a66bba0d5768e6fbaf9231c3504150ca8dfb1683738d144366bd500f16c2555 |
| qbank/19-solver-repair/19.1-constraints/hysteretic-trial-state-repair/samples/01/reference/grading.json | 502076d1f44ae92b0656b034be3d6cb9d49b74fca89d4a239133e00b8fd85f91 |
| qbank/19-solver-repair/19.1-constraints/hysteretic-trial-state-repair/samples/01/reference/reference.h5 | e28dcd9e2de7b6712dc1f0ef8a6d52e807996421b22823cb778bfd4b3abe7be4 |
| qbank/19-solver-repair/19.1-constraints/hysteretic-trial-state-repair/samples/01/output/result.h5 | e28dcd9e2de7b6712dc1f0ef8a6d52e807996421b22823cb778bfd4b3abe7be4 |
| qbank/19-solver-repair/19.1-constraints/hysteretic-trial-state-repair/samples/02/input/problem.json | 3188bfedc056f80dcd75f7eaaf7e7215e981619f93fb6755e129e9642d91a490 |
| qbank/19-solver-repair/19.1-constraints/hysteretic-trial-state-repair/samples/02/input/input.h5 | 2385ed9952e968c22f5e0bdb406658c5bb8ee3ba6153015345cb1b098f868845 |
| qbank/19-solver-repair/19.1-constraints/hysteretic-trial-state-repair/samples/02/reference/grading.json | 502076d1f44ae92b0656b034be3d6cb9d49b74fca89d4a239133e00b8fd85f91 |
| qbank/19-solver-repair/19.1-constraints/hysteretic-trial-state-repair/samples/02/reference/reference.h5 | 824121ecc91ba1c149df180d75ead591483e8ddbd7c39fcfb36e9e03b57d49cf |
| qbank/19-solver-repair/19.1-constraints/hysteretic-trial-state-repair/samples/02/output/result.h5 | 824121ecc91ba1c149df180d75ead591483e8ddbd7c39fcfb36e9e03b57d49cf |

## 覆盖缺口与未执行验证

公开样例不覆盖非零 return_delta、严格阈值边界、history_count=0、Hysteretic 3点及 HystereticSM 2..6点／不等两侧点数；这些分支本轮仅审题意，不能用两样例数值核对宣称全部实现正确。试探中间响应和内部状态没有直接输出，仅由返回及后续行为间接约束。

未执行公开包安装、C++构建、真实材料驱动或实际修复，未验证资源实际达标、可信驱动语义、基线接口实现或隐藏数据／参考生产。中性 SDK 仅检查其保留数组、轴、单位的接口，未执行其依赖校验器。公开样例数值与结构一致不认证上述事项。


## 最终有界复核与关闭

最终 ZIP SHA256：ac438c25f7416d325897acb6b763642fc27e518af2e205035d30e53bd9bc16c9，与协调方最终冻结值一致。

最终 instruction.md SHA256：5045d7fa19c08ce613269a0ba9aba12083ce14f3157f011abe7e9bd37a861b17。
最终 ZIP MANIFEST.json SHA256：3c6dbc95af17190b497fc2c646f832d1e3798e73ece6cf0a2d18e8a5ea1d6e15。

重新完整阅读最终 instruction：输出示例为 result.h5；CONTRACT 相对链接为 ../../../../docs/CONTRACT.md，按题目目录向上四层到仓库根后进入 docs，正确；资源明确4个CPU、4GiB，构建120s、每输入20s。数学、操作、评分和修改边界没有新增待决要求。该检查依据实际公开文本，不以协调消息或私有配置补题意。

将全部 DATA、CONTRACT、data-manifest、样例 input/problem.json、input/input.h5、reference/grading.json、reference/reference.h5、output/result.h5 及 ZIP README/中性SDK 与样例核对时记录的 SHA 比较，全部未变；最终 ZIP 中允许资产与工作树逐字节相同，MANIFEST 的相应 SHA 全部匹配。变更局限于 instruction 与反映资产版本的 MANIFEST，无需重复已有样例数值核对或执行 Oracle。

最终结论：statements 与 exam-materials 均本轮未发现未决问题；01、02 全部已检查，无必需材料缺失。该结论仍受上列实际覆盖及未执行验证限制。

额外版本闭合：仅将最终 instruction 的协议链接、result.h5 及4CPU/4GiB资源前缀还原为初版内容，重构字节的 SHA256 恰为493c477698509138faeb4273bf2fb6e660a171a5a7dbb527d85984862caa3ecc，确认初版到最终版没有这三项之外的题面变更。
