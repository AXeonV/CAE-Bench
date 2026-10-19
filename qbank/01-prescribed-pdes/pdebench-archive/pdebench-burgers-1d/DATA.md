# 归档 case 数据接口

输入目录含 problem.json、input.h5、source.json。problem.json 声明标准契约；source.json 保留固定来源版本、文件、行号、原始属性、字段映射和原始时间坐标，不含后续解场。

input.h5 的 point_ids 为从 0 起的原空间顺序，coordinates 为原 x-coordinate 按列排列；此处 point 表示归档坐标上的离散观测，不新增对原求解器点值/单元平均离散方式的断言。initial_times 取第一个有效时刻，times 取前 T 个原时间坐标；T 来自字段帧数。原文件多出的尾部时间坐标保留在 source.json，不为无数据时刻生成参考。

标量族保留字段 tensor；可压缩流保留 density、Vx、pressure。initial_<字段名> 为首帧，形状 [1,N,1]；reference.h5 的对应同名输出形状为 [T,N,1]。所有场及标准坐标数组以 float64 储存；float32 精确提升，float64 保持原值，无插值、滤波或重采样。字段单位标识 source_units_unspecified 表示本次不新增单位解释。

源属性与文件名分别保留；黏性等信息若冲突不静默合并，不用推测值填入 physics.parameters。当前 physics.model 标识来源族，conditions 为空，不补造来源未声明的边界配置。完整的物理求解题面可在后续正式评测建设时另行明确。

reference/grading.json、reference/reference.h5 为作者侧归档读取验收资产。固定来源身份和实际范围的无损核验记录在云端批次检查点保存。不得将结构核验或归档自比称为独立数值精度认证。
