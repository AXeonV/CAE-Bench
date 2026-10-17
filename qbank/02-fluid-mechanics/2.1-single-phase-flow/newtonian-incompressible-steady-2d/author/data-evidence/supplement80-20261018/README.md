# 第二批：80 个补充算例

本批在原 20 例之外增加 80 例。默认只入池；正式 data-manifest.json 的 cases／samples 不变。不调用 LLM 考生，不运行 Agent benchmark，不写 HF main。HF 起点、分支和实际固定提交以本目录交付索引为准。

## 覆盖与有意义的相似性

数值组共 64 例：57 个封闭多边形流、6 个零压跳周期流和1个非均匀形状流率通道。28 种封闭拓扑各安排单壁驱动与竞争驱动两例；浅宽几何分别用于封闭竞争驱动与流入／牵引流出。拓扑包含高腔、错层搁板、上下梳齿、沙漏、横向细颈、双窗口、多内岛、同心／偏心方环、细长障碍、阶梯、拱形、连通叶瓣、深支腔及交错挡板。成对工况改变壁面方向、驱动组合、黏性与惯性相对作用及涡流结构，保留它们是为了考查响应变化，而非仅换名称或坐标。

18 例使用整体刚体坐标旋转，给几何、速度、体加速度和观测坐标施加同一正交变换；标量和剪切率保持不变。Lethe 在原坐标系实际求解，参考按这个精确坐标变换转换。旋转不额外增加算例数量，既有拓扑／驱动差异仍是各例的主要区别。6 例额外提供较密输入网格，以覆盖读取、tag 关联与重新离散的规模；同一物理条件在粗细输入表示之间保持相同。

解析组 16 例分别为：单壁 Couette、反向双壁 Couette、顺向 Couette–Poiseuille、逆向带内部逆流组合、双端总牵引 Poiseuille、半通道对称、半通道滑移、倾斜 Couette 速度流入／总牵引流出、速度流入／储槽压力的塞流、流率塞流、竖向周期 Poiseuille、凹域均压静水、带孔点基准静水、倾斜储槽静水、同向运动壁的刚体输运，以及两个分别归一化入口的塞流。相似流型用于区分确有不同含义的边界、压力约束、通量符号和积分量。

难度标签为设计预期：5 例 easy、46 例 medium、29 例 hard。依据是几何连通、内孔／细颈、驱动竞争、惯性、坐标和输出语义；未经模型实测，不把标签当作已经测得的通过率或区分度。

## 参考出处与实际生产者

- 64 例几何／驱动由作者设计，不冒称文献工况复现。参考生产者为上游 [Lethe](https://github.com/chaos-polymtl/lethe/tree/9bf70a921d86ed2fd8ccf5e5d4642d11ab4f7cf0) 的 lethe-fluid，实际使用 Q2 速度／Q1 压力、稳态 Newton 求解；源码版本、二进制摘要、网格、配置、执行日志、非线性残差、资源记录及原始场关联保存在维护归档。
- 平行板公式来自 MIT 2.25 [Couette & Poiseuille Flows](https://ocw.mit.edu/courses/2-25-advanced-fluid-mechanics-fall-2013/1a114d602956fa0dd328155f9b45f93d_MIT2_25F13_Couet_and_Pois.pdf)，PDF 第 1 页的平面 Couette／Poiseuille 速度公式。采用单向流的线性叠加、半域对称限制，以及与压梯等价的恒定体加速度；压力周期时没有隐藏压跳。共动塞流是 Couette 两壁同速的极限情形。
- 静水公式来自 MIT Unified Fluids [Lecture 2 Notes](https://web.mit.edu/16.unified/www/archives2006-2007/FALL/fluids/Fluids_Lectures/f02.pdf)，第 1 页式 (1)、(2)，第 2–3 页静水载荷。对常密度、常加速度作积分并按输入的点／面积平均基准平移；旋转及分源相加不改变该物理关系。
- 解析参考是上述公式的实际求值，不是数值求解器输出。应力、剪切率和积分观测按本题 DATA 从同一有出处的速度／压力计算。总牵引使用完整对称黏性应力；有限通道端部用解析解真实满足的牵引，未把充分发展 Poiseuille 静压误当成零切向牵引出口。只有塞流／静水使用 pressure_outlet。

数值组请求多点速度、压力、密度、动力黏度、剪切率；不能将这些结果称作已验证连续全场。解析组同时请求节点点值、单元平均、域平均、边界平均牵引与按单位厚度积分的载荷、体积／质量流率。

内部逐档 samples.npz 的 xy／velocity 已转换到 case 全局坐标，pressure 已转换到物理 Pa 并遵守所声明基准；velocity_gradient 额外保留生产者原坐标系的3×3速度梯度，不是题目请求的输出。对有旋转的例子，取其前2×2块 G 后，全局梯度为 R G Rᵀ；R 由该例 coordinate_rotation_radians 确定。shear_rate 使用旋转不变的对称梯度范数。不要将保留的原坐标梯度直接当作全局梯度。

流率通道实际使用两个不同的正分段权重，由全入口线长归一化为 0.1 m2/s；输入还覆盖 rate 的 uniform 场形式。该例在上游 Lethe 中选择 power-law 的 n=1、K=0.08，物理上严格等于常运动黏度0.08的牛顿流体，目的是调用上游完整对称应力组装器；公开材料仍声明 Newtonian。出口为零总牵引，不借用软件的静压出口近似。入口由现成弱 Dirichlet 边界施加，另检查罚参数敏感性、实际流率、自然出口应力与网格变化。过大罚参数的失败原型保留为退役证据，不计入合格求解；初始浅腔成员也不进入最终80例。

## 验证边界

使用 caeoj-data-review 流程审计全部实际输入与完整输出，覆盖 DATA 中全部边界 operator、source、9 类输出、三种空间采样、两种压力表示、点／均值／自然压力约束、三角形／四边形／混合单元和非连续 tag。覆盖这些分支不等于覆盖所有合法参数、几何或条件的笛卡尔积。

数值网格验收要求最后两档的所有请求速度、压力、剪切率分量差异均小于对应题面容差的 25%；保留所有已运行档次。资源记录为实际原生求解的 CPU 绑定、墙钟和峰值 RSS，不把 OpenFOAM 交叉计算当作考生资源认证；输入转换／采样脚本与依赖亦留存，可重放。

8 个代表性复杂工况另用上游 OpenFOAM Foundation incompressibleFluid 实际计算，并与 Lethe 比较；2 个周期工况另对照公开平行板公式。独立比较范围只包含这些例子，不将其扩展成“全部64例均由另一求解器验证”。解析组作实际边界重建、守恒、压力约束与 8／16 阶积分复核，这些属于公式／转换一致性检查，不是独立数值生产者。

全部 case 使用现有 direct_outputs 与题面原有容差；实际检查完整提交正例和按各请求 quantity 构造的错误输出反例。上传后从固定提交重新获取、严格装配并重放消费链；具体结论和局限见交付摘要。

## 重新生产

脚本位于本题 author/。在固定生产者的 Linux 环境安装 gmsh、numpy、h5py，并指定 Lethe 可执行文件。先运行 4／8／16 档，再读取 numerical-validation.json 中 accepted=false 的别名，依次加密至 32、必要时 48；不得仅凭退出码认为已通过：

```sh
python supplement80.py run "$RUN" --levels 4 8 16 --workers 8 --solver "$LETHE"
python supplement80.py convert "$RUN" "$SOURCE" grading-template.json
python supplement80.py run "$RUN" --levels 32 --names <待加密别名> --solver "$LETHE"
python supplement80.py convert "$RUN" "$SOURCE" grading-template.json
python analytic80.py "$SOURCE" grading-template.json "$RUN/analytic-validation.json"
```

本批实际各例／各档集合见冻结 numerical-validation.json；精确重放时按该集合分档传入 --names，已有成功档次会被复用。输入网格密度、坐标转换、材料及工况全部由 supplement80.py 固定定义；原始参数不靠本机路径或未归档状态推断。

OpenFOAM 复现通过 run_openfoam80.sh，使用环境变量 OPENFOAM_BASHRC、PYTHON 和可选 MPI_BIN 指定对应固定安装，传入 source、输出目录、--levels 16 24 32、--workers 8、--initial-level 16、--linear-relative .02 和已交付的8个别名；额外加密档按比较记录重放。已有上游转换器直接读取最终契约输入，不读取 Lethe 场或迭代初猜。check_analytic80.py 另在新目录以16阶积分重新制作解析参考并核对8阶结果。

维护 SDK 的源码环境需设置 PYTHONPATH=src:qbank/extensions（PowerShell 使用分号）；audit80.py 对源树或隔离装配树执行全部契约、几何／边界、正反例检查。获取与装配复用现有数据池工具，详细证据获取沿用 evidence_archive.py --index 本目录的 archive-index.json；不改变旧批次的默认索引。
