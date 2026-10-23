# 最近投影修复题：作者与验收材料

来源preCICE issue1304及PR1351，精确基线、归档和树摘要见data-evidence/source.json。公开归档保留原始完整库与许可证；真实完整库已编译，962个原始文件在基线镜像逐字节匹配固定归档，见pristine-baseline.json及独立source-image-check.json。题面、数据、真实编译判题与独立审阅已完成；本轮未调用收费考生模型。

## 能力与参考

可信C++driver构造真实mesh::Mesh，分别调用query::Index::findNearestProjection和findCellOrProjection。driver只从库返回的节点权重重建坐标与输入场，并报告其原生距离；不另搜最近点或修正权重。n设置为所有原语数量，使本题选择不受默认近邻候选截断影响。

来源PR比较边与最近顶点，三维还可能在面比全部顶点近时提前接受面，仍漏更近的独立边。实际上游原样反例的点(0,0,1)返回z=0的面、距离1；显式独立边在z=0.5，正确距离0.5。完整参考在原cpp签名内比较全部低维候选，不改Index.hpp；原样上游与作者补足分别记录，不能把上游合并状态当正确性证明。

正式reference生产者是真实preCICE库，author/independent.py只作独立闭单纯形验证：枚举非负重心坐标的活跃面，在其仿射包做正交投影并比较距离。完整节点轴权重、投影点、距离及三分量场均核查；恒等式和常数保持不单独充当最近选择的正确性证明。工况为依原缺陷机制新增的作者回归，不冒称原始耦合应用实验。

10例40查询覆盖2D/3D、单元内/外、顶点胜边、面/边/独立节点竞争、缺高维连接回退及nearest不使用体内部。真实完整参考10/10，原件3/10；最大绝对差1.56e-15，逐量误差与容差比例见reference-replay.json。完整实际数据及2样例经audit_data.py重读/独立几何核对，并检查13项合法/非法声明。其作者审计不替代独立数据审阅。

## 构建与数据复现

prepare_source.py固定归档并逐文件核对缓存树、构造最小cpp参考；prepare_runtime.py构建真实完整库及独立重链接修复目标。允许文件只含Index.cpp，固定上游对象来自该真实全库构建；CMake对Index和driver重编并重新链接版本库，可信判题在原件及候选两阶段强制删除声明产物，不能凭COPY时间戳使用旧对象。完整构建使用上游公开CMake选项关闭MPI/PETSc/Python actions；不使用替代查找实现或stub。

generate.py使用官方Gmsh写MSH4.1，replay.py通过真实低权限库执行生产reference，同时记录原始三输入资产SHA、序列化driver payload SHA及实际H5输出SHA。data pack/upload/assemble/verify均走官方流程。HF稳定IDcaeoj-190502、固定提交7147150c427dcc21434d930a1c76b58070d3334c已上传并完成新缓存组装；严格校验与最终回执另记录在data-evidence。

公开三文件及两样例独立考生审阅、全部10例与2样例的独立数据审阅均通过，见data-evidence/candidate-review.md及data-review.md。DATA明确mode.value必须是JSON整数，以消除1.0/0.0类型歧义；后端审阅另发现题面未写既有提交大小限制，现已明确1 MiB。两次澄清未改变数据、评分、SDK或求解器；最终版本的有界独立复核见bounded-public-change-review.md。保留旧考生报告原版本身份，不冒称全部重新考生审阅。

运行环境已补足普通离线pip安装所需SDK锁定依赖与构建wheel；实际断网普通pip install已通过，移走SDK源目录仍可运行两样例与评分，pip check无依赖缺口。该补足不改变求解器、评分或参考。实际安装使用澄清前b0caa版本；有界逐项差分证明最终包仅instruction及MANIFEST不同，SDK和所有样例字节相同。最终公开包SHA256为08223e23aeb1ab6cd9c01b53fd60fbb53dc4d4eacc29f04a6ba88d7d7e895a5c。

正式Harbor Oracle最终运行repair22-precice-oracle-v2：10/10、全部终态完成、exception_info=null，见oracle.json、oracle-trial.json、oracle-build-*及final-freeze.json。v1通过相同10例后，仅因公开限制澄清重装配v2；两次不是收费模型求解。七种真实后端探针覆盖有效修复及未来时间戳缓存、候选语法错误、额外文件、符号链接、缺编译器、可信SDK损坏和原生C++无限循环超时，全部通过；超时子进程结束为Z。有效探针实际cgroup为4 CPU/8 GiB、断网、UID1000，冻结源码/库/driver/原始对象不可写，隐藏目录不可读，ldd指向新链接真实库。正式Oracle没有另存cgroup快照，不把探针快照称作正式运行截图；未注入真实编译超时。

独立后端审阅通过，见backend-review.md及backend-review.json，另实际核对全部962源码、131个真实原始对象、六项判分阈值和非法输出；有限权限和网络探针不构成整个容器安全性证明。本题不认证MPI/GPU、默认候选截断、曲面高阶几何、动态网格或完整耦合应用。维护证据仅认证公开范围，真实参考生产、数学审计、后端运行和模型成绩分别陈述。
