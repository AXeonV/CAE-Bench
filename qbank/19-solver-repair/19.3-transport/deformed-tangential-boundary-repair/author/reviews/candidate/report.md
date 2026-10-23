# 独立盲考生审阅：变形边界切向约束修复

模式：exam-materials。结论：**本轮未发现未决问题**。公开样例状态：**已检查**（两例全部数组、公开输出/参考及评分；未运行原生 ASPECT）。此结论不证明隐藏数据、参考精度或实际编译/求解资源达标。

## 独立性与版本

只以指定公开 ZIP 内 instruction.md、DATA.md、docs/CONTRACT.md 为解释材料。阅读技能及 workflow 仅为审阅流程；公开 SDK 只用于中性加载、支持轴复制、校验和评分。没有阅读作者材料、隐藏 cases、生成器、既有设计/审阅/数值记录、public/run_case.py、baseline_probe.py 或 aspect-source.tar.gz 中的求解源码，没有通过实现补充物理定义，没有编写 solver、启动付费模型或覆盖 prepared。

ZIP 实算 SHA256：`9acb735ced6dcc52c86ffb187a5c7b3ae34e784713ba5b963f6d412e3e6b63ee`，与指定期望相同。解包到 `C:/Users/Jim Zhou/.codex/tmp/aspect6818-final-candidate-9acb735c`。仓库写入仅限本报告目录；不读取仓库工作树实现/提交状态来解释公开材料。成员清单不表示逐项阅读，源码压缩包只记录其原始成员字节 SHA。

三文件 SHA256（原始 ZIP 解压字节，未做换行转换）：

| 文件 | raw SHA256 |
|---|---|
| instruction.md | c7266803e4caaf79b40f0adf5f1082b8622cafe2076613175546c0705ef54f64 |
| DATA.md | b5288eb1c0628105dc91e9fe084f937a3738eb0b63b92753ca04bca66c26e091 |
| docs/CONTRACT.md | 130d4416fd533812493780c8bc6afbc0a158de6800b59bbec14a852f3cf1c063 |

## 从输入到交付的覆盖

- 模型：常密度、常黏度、零重力、定温不可压缩线性 Stokes，DATA 给出动量/连续性方程与黏性应变定义；无材料惯性，各要求时刻在当前域求解。
- 几何/运动：parallel 2D/3D 的初始盒、上下当前平面及侧壁完整速度明示；wedge 只有上壁变形，底壁不动并给抛物线驱动；annulus 是固定原点圆环，内圆完整旋转速度、外圆切向零法向。内部网格平滑由指定库承担，未要求内部仿射。
- 材料速度与网格速度：题面直接定义 u·n=0、零切向黏性牵引并区分 w，不会默认为 (u−w)·n=0。法向来自当前物理边界。边角由相邻相容条件共同约束；wedge 底端抛物线归零。
- 初时刻：盒 t=0 是已经求解的矩形 Stokes 状态，非未求解初始化。annulus 的专节明确静态圆环与 [0]；通用时间段中“t=0是矩形初始域”按盒族上下文解释，不构成需要外部知识才能决定的另一几何。
- 观测：固定 Cartesian/Eulerian 内点，坐标不动；原生 point values / Use natural coordinates=false；全时域/全部要求时刻域内及距边界下界。压力为当前 top 平均零，2D 边长、3D 面积，圆环 top 为外圆。
- 参数/数组：三族准确 model 字符串、D 约束、必需/禁止族键、单位和数值范围均明示；refinement 整数及各族范围，dt/end_time 关系与帧数上界，变形幅度与网格不反转保证已覆盖。无网格文件、无 fields/conditions；probes ID/坐标、times 与两输出均明确。
- 输出：velocity [T,N,D]、pressure [T,N,1]，全部 float64，固定 ID 和时间顺序；输出只复制 probe_ids/times，不复制坐标。每个数组数量/轴/分量/单位都可仅凭三文件确定。
- 方法/交付/资源：只提交≤1MiB core.cc 替换指定路径，保留 API 与实际求解；block AMG，排除 GMG/自由表面/其他几何；开发构建与运行命令，4 CPU/8GiB、编译900秒/每例60秒均在题面。输出直接来自可信原生后处理，六位有效数字说明无隐藏重采样责任。
- 评分：全部点/时刻/分量逐点比较，速度与压力同时通过，等权例平均。rtol=1e-5，各族 atol 明确；公开两例 grading 与平行盒/圆环阈值一致。

## 两个独立合法输入及竞争语义尝试

完整人工构造清单及数组见 semantic-probes.json；仅做契约加载，无求解。这些不是隐藏题、prepared 或数值参考。

1. **3D parallel**：width=height=depth=1 m，rate_x=0.1/s，rate_y=−0.1/s，velocity_x=0.4 m/s，velocity_y=0.2 m/s，dt=end_time=0.5 s，probes=(0.5,0.5,0.5)，times=[0,0.5]，refinement=1；其余密度/黏度/温度取1/1/300。变形上界0.1≤0.8。合法 SDK load 通过。在 t=0.5，上下法向平行(−0.05,0.05,1)，侧壁材料速度为(0.4,0.2,0.01)，恰满足零法向。竞争解释“材料速度等于网格速度”给出该水平位置 w_z=0，而 u_z=0.01 且水平分量非零；DATA 明确排除此解释，无需借助实现。
2. **2D wedge**：width=height=1 m，rate_x=0.1/s，peak_velocity=0.5 m/s，dt=end_time=0.5 s，probe=(0.5,0.5)，times=[0,0.5]，refinement=1；其余公共参数同上。顶壁端点变形0.025≤0.3，probe 严格内部，SDK load 通过。尝试“以初始法向”和“以当前法向”两种解读：当前顶壁 t=0.5 坡率0.05，故应有 u_y=0.05u_x；若沿初始水平顶壁则错误施加 u_y=0，三文件明确选择前者。再尝试网格跟随 probe：即使内部平滑不仿射，固定物理坐标与 Cartesian 指令均排除将它推进到任何 X(t) 的解读；无需从代码获取网格坐标映射。

这两类反例均被公开文字消歧，没有同时合法而产生不同输出的解释。静态圆环专节也充分排除了把运动边界规则强行应用到圆环的解读。此为题意检查，不是完整数学存在唯一性证明。

## 全部公开样例的实际检查

样例01是2D parallel：N=15，T=5，times=[0,0.25,0.5,0.75,1]。输入为 probe_coordinates float64[15,2]、probe_ids int64[15]、times float64[5]；输出和参考均为 pressure float64[5,15,1]、velocity float64[5,15,2]、probe_ids int64[15]、times float64[5]。

样例02是静态2D annulus：N=36，T=1，times=[0]。输入为 probe_coordinates float64[36,2]、probe_ids int64[36]、times float64[1]；输出和参考均为 pressure float64[1,36,1]、velocity float64[1,36,2]、probe_ids int64[36]、times float64[1]。

六个 HDF5 文件全部根 dataset 的全部元素实际读取（无切片遗漏），所有值有限；完整值、shape、dtype、原始数组 SHA 见 evidence.json。SDK load_problem/load_result 成功；write_result 将公开结果字段中性回写到临时文件，所有字段与支持轴逐值/类型/shape 保持一致；两例输出和参考全部数组也逐值相同。两例 validate-input 各通过；各自公开输出、参考、SDK roundtrip 共6次 validate-output 均通过，scope=task-contract。两次公开输出实际 grade 均 accepted/score=1。仅将每例 pressure[0,0,0] 增加1e-3的结构合法副本作为负对照，均 wrong_answer/score=0；仅速度正确不能通过。实际命令/退出码/完整 stdout/stderr 均保留在 evidence.json。

检查的是公开文件自洽与实际工具消费链；公开输出=参考及工具判满分不证明数值真值。未从公开结果拟合或实现 solver。

## 未执行的部分与结论边界

未解压或阅读 ASPECT 源码，未定位补丁或构建 core.cc，未执行 cmake/native ASPECT/原生 point values，未验证4 CPU/8GiB内900秒重建及60秒各族运行，未认证 refinement/当前几何对原生输出的精度影响，未运行隐藏案例。公开样例没有3D或wedge实例，这两分支本轮只检查三文件定义及人工合法输入中性加载；不把此范围扩展成原生运行认证。未发现实质问题，因此没有修改建议或阻断项。

## 实际 ZIP 全部成员

下表与 evidence.json 来自 zipfile.namelist()，没有使用仓库其他版本。SHA 为各成员原始解压字节 SHA256。

| 成员 | 字节 | SHA256 |
|---|---:|---|
| LICENSE | 11558 | 1eb85fc97224598dad1852b5d6483bbcf0aa8608790dcc657a5a2a761ae9c8c6 |
| MANIFEST.json | 5208 | 7603703fc09303365a7f6305056f2edc47a64fa8008c2290a4231af2107c6f55 |
| README.md | 1638 | 5d291a3c39acc085e5d3f8cb3ca8fbf2d0bd32edc10afd07747ffefb91be656b |
| docs/CONTRACT.md | 31847 | 130d4416fd533812493780c8bc6afbc0a158de6800b59bbec14a852f3cf1c063 |
| docs/GRADING.md | 13807 | 78c402c0f3a4428f45aec81c86868666c7a2cab1ffe24248b30ca982e1796df8 |
| pyproject.toml | 613 | 84a4ff044d466594f2bbfd5fa6b5f8e23918c579fe626e758d8e8899796babbd |
| qbank/19-solver-repair/19.3-transport/deformed-tangential-boundary-repair/DATA.md | 5448 | b5288eb1c0628105dc91e9fe084f937a3738eb0b63b92753ca04bca66c26e091 |
| qbank/19-solver-repair/19.3-transport/deformed-tangential-boundary-repair/instruction.md | 2574 | c7266803e4caaf79b40f0adf5f1082b8622cafe2076613175546c0705ef54f64 |
| qbank/19-solver-repair/19.3-transport/deformed-tangential-boundary-repair/public/aspect-source.tar.gz | 1641221 | fb58b7d5d6026472166cd70ef26d0b9d8ff8362c03d86357c225c58b9dac3030 |
| qbank/19-solver-repair/19.3-transport/deformed-tangential-boundary-repair/public/baseline_probe.py | 958 | 4cc0762fcdd14407255e621bbb595857be0cafffef7bde986a191028fb8587bd |
| qbank/19-solver-repair/19.3-transport/deformed-tangential-boundary-repair/public/run_case.py | 7152 | 263c0b506e21ae3ea8f37cb60876cb9130b11dd7ccc8c5fa85e57545bf521763 |
| qbank/19-solver-repair/19.3-transport/deformed-tangential-boundary-repair/samples/01/input/input.h5 | 2448 | d1f8d4a3e7e9bc6022fb74650278ae87e88156c2c124f203b0dcc815e9a22216 |
| qbank/19-solver-repair/19.3-transport/deformed-tangential-boundary-repair/samples/01/input/problem.json | 1959 | 3c70877c3ca709c4a5de41636d9e7e5d9c4120c32a9d09ab128e10c7c983df05 |
| qbank/19-solver-repair/19.3-transport/deformed-tangential-boundary-repair/samples/01/output/result.h5 | 4368 | 928fba8dad0c4e0767109ef7833111afc52dcb02f6268f562d436b123683cd8c |
| qbank/19-solver-repair/19.3-transport/deformed-tangential-boundary-repair/samples/01/reference/grading.json | 771 | 42bd430f67aceed79f4708153b5b65b865adde254d2720fd5ceed2c2dc89c06f |
| qbank/19-solver-repair/19.3-transport/deformed-tangential-boundary-repair/samples/01/reference/reference.h5 | 4368 | 928fba8dad0c4e0767109ef7833111afc52dcb02f6268f562d436b123683cd8c |
| qbank/19-solver-repair/19.3-transport/deformed-tangential-boundary-repair/samples/02/input/input.h5 | 2920 | 210d105d5d9f403bf8b15867c6c03698252e22a25b003e6dd0e8526a8cfdd85d |
| qbank/19-solver-repair/19.3-transport/deformed-tangential-boundary-repair/samples/02/input/problem.json | 1899 | 08648164da88d3e8cefab0953883e0c204f8f5f14766c2b6a9f36cf2839c5956 |
| qbank/19-solver-repair/19.3-transport/deformed-tangential-boundary-repair/samples/02/output/result.h5 | 4368 | 0388dbdd5fe391ea1346760b86ff86073f0f0d2734983787f6082282c9869e41 |
| qbank/19-solver-repair/19.3-transport/deformed-tangential-boundary-repair/samples/02/reference/grading.json | 771 | 42bd430f67aceed79f4708153b5b65b865adde254d2720fd5ceed2c2dc89c06f |
| qbank/19-solver-repair/19.3-transport/deformed-tangential-boundary-repair/samples/02/reference/reference.h5 | 4368 | 0388dbdd5fe391ea1346760b86ff86073f0f0d2734983787f6082282c9869e41 |
| src/caeoj/__init__.py | 116 | 93f28b174ae1899c1d4b21395111f3379f5540903b7fb093a5976068235e3a8b |
| src/caeoj/__main__.py | 51 | 482b8693e2fe6dbd732e3d7961e03827d3efa187bad11d29da188be580ebbeea |
| src/caeoj/case-grading.schema.json | 669 | 68d579a08c5a7b0adde10315053787344d2f37c8350ef5a878eea76311ecc558 |
| src/caeoj/case_grading.py | 16231 | 441388ecf1517aadc3577a6b8b3c2d738de2e14542e0928649ecdcab0019855e |
| src/caeoj/cli.py | 3196 | 5c0ee356b10aad84569d17d47ee25f3256bc64b48461f6e7cc05ffe616d9ea40 |
| src/caeoj/grading.schema.json | 9530 | d17c8cca6bf2938a5d7f3cb52942643e9034090c6806dd000cecaa804dd91c72 |
| src/caeoj/grading_metrics.py | 10551 | 9878c58ac2231f612a5e493ad2282c672ecc498b50ef1bd10dbc7d0bb345f529 |
| src/caeoj/grading_policy.py | 9663 | f5785d0555b2119268b94586d04f9073e2ecbc316f30325615e9e0a92b6f50c9 |
| src/caeoj/mesh_geometry.py | 6486 | cf1ac007cafe58849a612ebb3c0a7308a8c9d2d230e6d6f3c7f38110e79fc15c |
| src/caeoj/problem.schema.json | 11590 | 0763e789f64c52cfdb0cd20ae06309ffe19e2d007780271a61421eac24d20cb6 |
| src/caeoj/public-runtime.json | 474 | f71df3dfdf1d3f2cfbf625d2d12ef63f94e7fb3e0f5b3a47a000e56aff4d43a7 |
| src/caeoj/runtime.py | 10561 | f1e35d8d89caa9c4fb3f4b10f450b0f92b26b0312ecab6e6140a5b7946e73329 |
| src/caeoj/sdk.py | 4782 | 3ddf8f5a1b516eca67abae35a05a26dc1b7a8381a168d7d148ea22f2ecab9cba |
| src/caeoj/storage.py | 4065 | 7de5005e11a0fb01ed9adde18b2f01410b897194510be7eb64454429c8a47ce5 |
| src/caeoj/validation.py | 26037 | 60fa0b4d0763e60a758710417a8559666e2d97a693237e4d6fa9726f77fa07fa |
| src/caeoj_bundle/__init__.py | 42 | 01afef244b55a3e53d48b0c86ea965839ab01765c60fe236afa3d66017e3afc4 |
| src/caeoj_bundle/runtime.json | 2183 | 8c8ae374aa431a4778842f4364754dbe1fe9c656b3e1988ae587ac13203530f7 |
| src/caeoj_task_ext/__init__.py | 36 | 0cb3c4c4a6b572aa9f44eeb934fc573804c2312a3b9c74073d5668f1479a0ad4 |
| src/caeoj_task_ext/deformed_tangential.py | 5327 | 48dba5b62f2752730bea9286326d1eb8bfd08cf7428bc8148e6f3c21b46ee2c8 |
