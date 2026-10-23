# 最终 PML 外端边界有界盲审

结论：**本轮未发现未决问题**。本轮只读最终公开三文件及公开 ZIP，检查声学 PML 外端定义和既往两问题的关闭状态；未读作者结果、隐藏数据或求解实现。此前9cd版本报告及其材料身份保持不变，本文件补充最新22aa版本的限定结论。

## 版本与范围

最终 `dist/parallel-pml-reduction-repair-agent.zip` 自核完整原始文件 SHA256：`22aa0bcf168c9cabd7853ec8a63e2498838968fb53aa996034cb3e48108144d7`。44个ZIP成员，44个唯一名称，无增加、删除；与既往 `9cd9a7479aaa7973194bfd5099e97fbc60f40c8133cddcce8b2e7552f54c3f39` 的逐成员SHA清单相比，仅本题DATA.md和MANIFEST.json变化。全部44项原始解压字节SHA见 terminal-materials.json。MANIFEST全部成员SHA正确，覆盖43个非MANIFEST成员。工作树三文件与最终ZIP逐字节SHA一致。

因此 instruction、CONTRACT、公开SDK/CLI、运行工具、求解源码压缩包及两例公开输入/参考/输出/评分等42项未变；不重复运行此前的样例结构/评分检查。本轮也不重新解释旧参考的物理正确性。

## 边界定义检查

最终DATA「声学边界和C-PML」已明确分支：无PML时四壁为chi齐次Neumann；有PML时每个试件上下各三行、仅z方向PML，左右仍为齐次Neumann，z=0及800外终端为chi=0齐次Dirichlet截断，并将保存chi旧值、chi_t、chi_tt置零。内部接口z=3h及800−3h按连续谱元/MPI装配传播。PML厚度、方向、剖面、初始记忆变量、固定原生时间离散和残余反射观测亦已就地给出。

该定义不要求从模板或私有实现猜测外边界。左右Neumann和上下零Dirichlet在角点可以同时满足，不形成相互矛盾的非零约束；边界试件与零初始场也相容。无PML分支的刚性壁面与有PML分支的外端截断已明确区分，不把两者误认为同一边界。不从修订文本推断实际源码/驱动已经实现此条件，本轮只判断公开任务是否明确。

## 既往问题关闭状态

DATA输出仍仅为wave_response加times/probe_ids，明确不重复点坐标，与未变CONTRACT和固定接口一致；原输出支持数组冲突保持关闭。instruction仍明确从包根安装后cd至题目录，再运行public/run_case.py和samples相对路径；原路径问题保持关闭。本次边界修订不改变这两项。

## 限定

未编译、未调用原生Fortran/MPI或候选修复、未量测资源、未独立认证公开参考与最终边界声明的数值一致性。本次盲审不授予native执行、参考精度或资源预算验收。
