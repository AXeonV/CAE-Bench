# 复波数 Helmholtz 快速算子修复：独立考生审阅

## 结论与范围

- 模式：`exam-materials`；依照 `caeoj-candidate-review` 技能独立执行。没有读取 author、隐藏 cases、私有参考、设计报告、历史讨论或维护规范，没有接收作者数学结果，没有实现 solver。
- 题面结论：**本轮未发现未决问题**。仅凭 instruction.md、DATA.md 和 CONTRACT.md，可确定任务、两种输入分支、数学对象、观测、输出、提交限制、误差与资源。
- 样例状态：**已检查**。01、02 的全部 manifest、输入数组、公开参考数组、评分 JSON，以及 02 的全部网格节点/三角面已读取。未用结构检查代替参考数值认证。
- 当前包 SHA256：`241b6bad4d344139e034dd798638a0cb62d0a364ae28c9b999a41a7bb9e18e27`，与协调方指定版本一致。
- 材料版本见 `materials-sha256.json`；完整逐数组统计及清单见 `sample-checks.json`，安装产物 CLI 结果见 `cli-checks.json`。
- 审阅时基线提交为 `b59daab1e0c795264bae805aa5a5a5b439132aad`；白名单范围内 instruction.md、public/driver.py 已有工作树修改，public-materials.json 未跟踪。本报告以实际文件SHA256为准，未修改任何题目材料。

## 实际材料与独立性

解释性材料仅为题目 instruction.md、DATA.md 和 docs/CONTRACT.md。样例公开依据为明确任务白名单以及包 MANIFEST.json 的 `public_samples: ["01", "02"]`，公开参考由各样例 grading.json 的 `reference.h5` 引用并实际包含在包内。

运行工具检查覆盖白名单 public/driver.py、public/run_case.py、public/CMakeLists.txt、public-materials.json，以及 ZIP 的 manifest、安装声明、SDK 和声明扩展。工具只用于接口核对和中性加载，未用于补充物理要求。两份源码压缩包只核对包成员及 SHA256，没有展开阅读求解源码。未阅读包 README.md、docs/GRADING.md 等额外说明来补题意。

ZIP 全部成员哈希均与自身 MANIFEST.json 一致，且没有 manifest 以外的额外成员（MANIFEST.json 本身除外）。工作区白名单的同名材料与 ZIP 完全一致；public-materials.json 所列三项运行工具及两项原始来源压缩包哈希均对应包内版本。SHA 文件记录了每个实际白名单材料的路径、哈希与包内匹配状态，以及包成员完整哈希表。

## 题面及接口覆盖

| 检查项 | 公开依据与判断 |
| --- | --- |
| 点模式数量、身份与单位 | DATA operation=0 明确源32–512、目标1–24、间距和坐标上限；IDs 各表独立，strength 的复分量/形状明确；核与目标梯度公式确定方向和 `1/m`、`1/m2` 单位。跨表相同ID不会删除源目标作用。 |
| 两条调用路径 | instruction 与 DATA 明确 fmm 与 local 分别来自真实接口，不可相互覆盖；固定展开阶、ncrit 和 dense_evaluation=False，局部接口对给定点对求值。 |
| 曲面输入与法向 | DATA operation=1 明确18–100节点、32–196面、MSH 4.1 ASCII、一阶三角面、凸闭合拓扑、面绕序决定外向法线；无另行猜测或翻转法向的自由。网格标签与库自由度身份不同。 |
| 密度和积分对象 | 密度是实际平面三角网上的连续P1系数，按重心坐标重建，不是隐含光滑曲面函数采样。S、D、V、K、W 的符号与跳跃项约定明确。 |
| 超奇异算子 | DATA 给出 W 的P1弱式及 `M^-1 A φ` 强形式；这是有限维弱泛函的质量矩阵表示，不能作为尖角节点的连续经典点值。即便将同一节点系数解释为连续点值会遇到尖角问题，题面也已经排除该解释。 |
| 输出 | 点模式4项、曲面模式5项，位置、单位、复/梯度分量顺序及 `[1,N,C]` 均可确定；输出IDs与时间轴必须按CONTRACT复制，仅写当前模式的所需字段。 |
| 固定离散语义 | regular=6、singular=8、Numba双精度、连续P1及 strong_form 均明确；不能靠重网格/提高积分阶更换评价对象。 |
| 提交 | 恰好3个普通源码文件及每个1MiB上限、无额外文件/子目录/链接、替换位置、真实接口与快速路径要求均明确。 |
| 评分与资源 | 每一实/虚/梯度分量逐项 `1e-6+1e-5*abs(reference)`，每例全过才通过，按通过例数比例；CPU/内存/编译/执行/评分预算及环境错误分类明确。 |
| 本地消费路径 | 运行Python、源码根、构建根、字节码删除和重建命令、独立磁盘工作目录和至少8GiB临时空间均有说明。固定工具与这些声明一致。 |

未发现两种操作的单位、目标/源身份、法向、静态轴、P1离散观测或输出集合存在冲突。

## 全部样例与工具验证

两例经 ZIP 自带 SDK `load_problem` 和 `load_result` 完整加载，通过题目声明扩展及通用契约。各HDF5根组/数据集无属性，全部数组完整读取而非抽样，shape/dtype/有限性/引用/IDs时间一致性已检查。JSON 完整字段及数组最小值、最大值、元素数保存在 sample-checks.json。

| 项目 | 样例01 | 样例02 |
| --- | --- | --- |
| 操作 | 点相互作用 | 曲面算子 |
| 规模 | 64源、7目标 | 18节点、32三角面、12目标 |
| 输入数组 | source_coordinates、source_ids、strength、target_coordinates、target_ids、times，全部 | density、node_ids、target_coordinates、target_ids、times，全部 |
| 公开参考 | fmm/local potential `[1,7,2]`、gradient `[1,7,6]`，target_ids、times | 三种boundary `[1,18,2]`、两种potential `[1,12,2]`，node_ids、target_ids、times |
| 几何检查 | 最小源间距0.0835878m；最小源目标距离2.33791m；源AABB对角线2.44332m | 最小面面积0.337350m²；最短边0.800131m；体积3.91961m³；AABB对角线3.53811m |
| 目标与法向 | 所有点分离约束满足 | 每个目标在外部，最短面距离2.20479m；最大外向支撑面偏移仅1.11e-16m（舍入量级） |

02 的整个网格经过中性网格解析：全部节点均使用、标签对应、闭合反向共享边、连通及凸外向约束由已检查的包内声明扩展实际执行；另独立计算面积、边长、体积、面支撑平面和目标至三角面距离。未读取大数组遗漏部分：无。

离线安装在本审阅私有目录执行，使用现有 `.venv` 的依赖：

```text
python -m pip install --no-index --no-build-isolation --no-deps --target <本审阅目录>/installed .
```

从 ZIP 解包根构建并安装成功，产物版本 `0.3.0+bundle.2f7e9be7d855752c`。随后从安装产物（不是仓库 src）分别执行两例的 `info`、`validate-input`、`validate-output` 和 `grade`；8次均退出0。info 实际加载对应 `task.complex-helmholtz-fmm-repair`；validate 返回 `scope: task-contract`。grade 将公开参考作为候选自比较，两例均 accepted/score=1；这只证明配置可加载、公开参考满足输出契约与评价消费链可用，不证明答案物理数值正确。

## 发现与可选优化

没有明确缺陷或待核实的题意/接口问题。

**C1，可选操作说明优化（非阻塞）**：instruction.md 安装段先给考试包根目录 `pip install .`，随后使用 `public/run_case.py` 和 `samples/01/...` 的题目目录相对路径。具体反例是在包根目录直接连续执行这两个示例，根目录没有 `public/run_case.py`，会先遇到文件路径错误。包 manifest 和题面所在位置足以定位题目目录，不妨碍确定任务；建议在运行示例前补一行切换到题目目录的命令，或使用完整包内相对路径。此项没有扩大成运行库缺失或数值故障。

## 未执行与结论边界

- 没有在Linux判题镜像执行 `/opt/bempp-env/bin/python`、真实Bempp/ExaFMM、CMake重编译或实际源码修复，因此不认证原件故障复现、真实调用成功或600秒/4GiB预算。
- 离线安装验证复用现有依赖且关闭构建隔离；没有宣称验证全新空环境中不带选项的 `pip install .`。包内没有依赖wheel仓库，题面运行环境预置依赖是否齐备不在本次Windows验证范围。
- 没有自主重新计算或认证参考答案精度，没有运行收费考生、隐藏测试或参考实现，没有判断能力设计与来源独立性。
- 结论只针对所记录SHA256的公开材料、样例契约和中性工具链；材料版本变化后需针对影响面复核。
