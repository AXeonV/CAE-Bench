# 多孔介质声明扩展维护说明

本文件仅供维护方使用，不进入考生包。题意与输入输出的唯一公开依据仍为每题 instruction、DATA 和通用 CONTRACT。

`caeoj_ext.porous` 实现共享能力 `porous.flow_transport`，由 `caeoj_bundle/runtime.json` 的可信模型选择器及题目表绑定；模型目录保存在同包 models.json。无需修改核心 Schema、SDK、发布器或判题器。SDK 仍以 load_problem／read_field／write_result 读写标准数组。

检查范围为参数与单位、类型、时间和 sampling、材料声明范围、节点／单元支撑、边界覆盖与重叠、裂隙线与基质身份关联、输出 quantity／位置及规模。不会计算流场、投影初态、归一化参数、检查 PDE／守恒或更改答案；网格质量与真实物理解适用性在正式数据阶段验证。

不同孔隙模型共享存储结构，但不会按算子名称猜变量：records 列出本模型全部 role／variable／operator／data。材料张量为完整全局矩阵；条件引用不得跨 location 隐式配对；压力水头、机械压力、相绝对压力各由逐题 DATA 定义。t0 状态和梯度通量按初态重建，是否要求自然边界立即匹配在 DATA 直接说明。

作者模板为 `qbank/maintenance/authoring/build_porous.py`，仅展开文档、配置和内部模型目录，不生成算例或参考。运行后应检查已审阅文件是否改变。测试入口为 `tests/test_porous_contract.py` 与 `tests/porous_fixture.py`，所有网格／HDF5 为临时工具载荷。

评分统一使用 grading.json v2 的 quantity／unit 绑定；每题题面逐项列出相同逐值阈值。执行资源从本题 judge-config 与 harbor/task.toml 合并；最终 verifier 总预算依实际案例数计算，不因没有数据而虚构 N。正式阈值与资源可达性、独立参考、Linux 容器限制实测和发布仍需后续证据。
