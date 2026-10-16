# 第十三章实现与审阅记录

## 归属与接口

十三题全部以本题 instruction、DATA、CONTRACT 定义要求，不依赖维护规范或共享 DATA。标准 Gmsh、HDF5、网格位置、aggregate 与类型化条件足以表达本次范围，未扩展通用存储。

实现为共享 `caeoj_ext.porous` 和内部 models.json；可信 provider 以逐模型 selectors 和逐题 tasks 绑定，公开 files 仅核心及所需扩展。使用 `physics.model` 显式声明材料能力，任务 slug 不代替模型；公开工具支持省略单题 task，但必须与安装的唯一题目一致。独立核心、SDK 主接口、Schema、发布器与 judge 无改动。

`build_porous.py` 是维护模板，仅展开文档／配置，不是 solver 或案例制作器。模型、场名与 HDF5 key 分开；条件表固定 operator 字面值、数据键和 quantity。全矩阵物性、节点 P1、单元／边常数、线性时间历史及原始请求轴均由逐题 DATA 定义。

## 独立审阅及修订

考生审阅者以 fork_turns=none 启动，未提供作者结论或实现。A 覆盖13.1—13.2五题，B覆盖13.3—13.4四题，C覆盖13.5—13.6四题；均完整读取本组双文件与 CONTRACT，随后复核修订。没有正式数据，未声称完成真实数据审计。

| 问题 | 修订与最终证据 |
|---|---|
| 条件标题未明确等于 operator | 总则明确逐字使用标题，所有 data 键、role、variable、location 就地给出 |
| 边界和 source 按角色笼统称为分片常数 | 改按 location 分类：节点 P1，element 常数；given_flux 不被体源总则覆盖 |
| 双连续体同边施加两套状态与节点不共享矛盾 | 不共享限定同一未知量，不同连续体可用相同节点；双连续体合法反例回归通过 |
| 正性与张量范围不足 | ρ、μ 显式为正，全部渗透张量全局对称正定、对称分量完全一致并给谱范围 |
| 请求 t0 时初态、自然条件与通量定义不清 | 状态边界与初态相容；初始代数量和梯度通量直接从初态重建，t>t0 才施加自然通量及界面流量连续；孔隙初压取有限右极限 |
| 不存在的 fractures／mean 与稳态模板信息 | 输出段只保留本题位置，删无关裂隙例外与压力偏移提示；孔隙壁面采用明确线段位置 |
| 不可压缩相质量通量禁止等价单位转换 | 允许按各相真实密度转换，要求质量和源项一致；可压缩题不得用恒定参考密度替代状态密度 |
| 单题装配接受同扩展其他模型的省略 task 输入 | 按可信唯一 task 核对模型；独立维护探针遍历十三模型，仅本题接受，其余十二返回 E_POROUS |

修订回写维护模板，避免重建恢复旧定义。具体声明测试不替代物理解、守恒或网格质量；这些属于数据／参考阶段证据。三组考生与独立维护核查在各自检查范围内无剩余确认缺陷。

## 评分与资源映射

每题 instruction 的 quantity、unit、atol、rtol 表逐项对应 grading.json v2 的 pointwise／per_time／per_component 规则。无隐式压力对齐或额外评分常数；全部输出都请求且必须通过。临时比较载荷覆盖零参考绝对边界和非零参考相对边界，边界等号接受、超出拒绝；坏参考属于基础设施错误。

judge-config 的 timeout_seconds 为单例墙钟，max_output_bytes=null 不另设字节限额，stage=provisional；Harbor 补充仅资源，4 CPU、4096 MB、生成3600 s、构建1800 s。verifier 总预算按真实N计算 max(模板预算,300+N×(单例时限+60))，测试用临时N验证消费公式，不宣称已经绑定正式N。两相／非线性／输运900 s，线性稳态300 s，孔隙瞬态1200 s。

## 验证范围

六节静态文件／JSON／链接检查；十三模型临时 MSH4.1 ASCII、HDF5 与 SDK 往返；关键非法声明和十类畸形结构无 traceback；全部策略边界、资源真实合并、严格单题与多题运行闭包。普通 wheel 安装使用用户项目 Python 环境、独立目标目录，移开源码、清除 PYTHONPATH 并以 Python -I 换目录运行十三模型；必要工具及 models.json 均从安装目录加载。验证摘要与文件散列另存本目录。

本章没有制作正式案例／参考，没有运行 solver benchmark 或 Harbor Agent，也未发布正式评测 ZIP。回归中的临时包与数组只验证接口和工具行为。目标 Docker／MPI／硬限制、参考连续精度、当前误差与资源设计目标的可达性后续验证。

## 范围查证

采用现有格式与工具，无新二进制编码器。领域方向与量纲核对参考官方资料：[PFLOTRAN Richards 模式](https://documentation.pflotran.org/theory_guide/mode_richards.html)用于核查水头／饱和与 Darcy 通量的身份；[PFLOTRAN 不混溶模式](https://www.pflotran.org/documentation/theory_guide/mode_immis.html)用于核查各相质量储集；[DuMuX 混合维耦合](https://dumux.org/docs/doxygen/master/group___facet_coupling.html)用于核查线／体域归属。本题的简化响应、交换系数与边界组合由逐题 DATA 精确定义，并不要求复现这些软件的默认模型或离散。
