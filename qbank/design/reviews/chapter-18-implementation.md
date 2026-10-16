# 第十八章实现、审阅和验证记录

2026-10-16，基线7321575，启动工作树干净。章规划此前仅有总体方向，作者先细化7节10题完整有限清单，再分两批实施全部题面、自包含DATA、必要共享扩展、评测配置与独立考生审阅。未生成正式数据、参考或发布，未推送／合并。选择及边界见章规划与逐题清单。

## 实现归属和契约

逐题位于qbank/18-system-multidomain；每题只依赖本题instruction、DATA和docs/CONTRACT。所有参数、符号、条件、IDs、数组分量、时钟和评分就地定义，无COMMON、共享DATA或源码阅读要求。

共享systems.networks位于qbank/extensions/caeoj_ext/systems；注册只由已装配可信provider提供，模型标识不动态导入代码。新增字段全部复用通用physics、entities、fields、conditions和多时间轴，未修改核心、CONTRACT、Schema、发布器、评分框架或Harbor实现。通用core不导入物理模块。扩展只检查声明，没有数值求解器或参考。

实体分为nodes、edges或systems。拓扑是edge_properties.endpoints的int64实际节点ID，不是行号，允许非连续ID、并联、有环和反向支路；拒绝自环及不连通图。端点双分量代表真实支路两端端口，不是伪坐标或空间平均。incidence辅助按声明ID行序组装尾端正矩阵，兼容大／小端int64，手算矩阵回归独立核对。

qbank/maintenance/authoring/systems.py为维护源，展开逐题题面／DATA及配置；审阅修订同时回写源，重新生成后与审阅最终版本匹配。维护文件、tests、隐藏数据和参考不进入公开闭包。考生保持一次普通安装、统一CLI与caeoj.sdk，不选扩展、不注册模型。

## 独立考生审阅与修订

三位单独subagent收到真实任务“仅依据三文件实现覆盖整个公开问题族的可复用求解器”，只获指定题目instruction、DATA和CONTRACT路径，明确只读，禁止维护记录、实现及隐藏数据。覆盖全章10题的20份逐题文件及1份CONTRACT。初审后修订，再对最终版本复核，21个SHA256实际匹配，见[最终版本清单](chapter-18-review-manifest.json)。

| 审阅者 | 覆盖 | 反例尝试与修订闭合 |
|---|---|---|
| review18_mechanical_hydraulic | 18.1—18.2，4题 | 变比n=2时反力矩不能等大反向；死区内阻尼不能关闭；负液压压差须反流，表压不得加大气压；管路首端Q(l)不能取反，不能用集总阻力替代PDE。删除分布管路的“初态由算例改变”泛用措辞，与固定零初态一致 |
| review18_networks | 18.3—18.5，3题 | 绝对压力平方关系、质量关联矩阵符号、导热反向热率、有效面积不能重复乘发射率、二极管对asinh关系、电势参考地不能任意改选节点；明确load相邻时间采样点、data键对应引用值，删除无关角度及fixture维护文字 |
| review18_cross_control | 18.6—18.7，3题 | B omega²进入指定热节点但负载功不进入；内部泄漏不能重复扣；控制先算U_k再递推z_{k+1}；最后时钟重算U_N。删除不存在的endpoints和initial条件模板，非热电机R0明确为固定电阻 |

三组最终复核通过，未发现仍需猜测的公开语义。通过只限实际三文件可确定性，不是无缺陷证明；审阅者没有实现求解器，没有核验数值参考或预算。

## 配置到实际消费者的映射

本轮直接核对当前src/caeoj_tools/grading_policy.py、caeoj.grading_policy.resolve_policy、caeoj.grading.grade_arrays、src/utils/prepare_harbor.py.task_config、共享Harbor judge与模板，未把配置存在当作生效证据。

| instruction要求 | 配置／实际消费 | 本轮验证与限制 |
|---|---|---|
| 全quantity逐时间／对象／分量atol+rtol，等号接受，无偏置／重排 | grading.json v2，按quantity+unit绑定实际逻辑字段及array key | 10题以不同逻辑名和array名实际加载；另列公开阈值比对，0与非零参考的边界及nextafter越界执行 |
| 每例0/1，最终通过有效例比例 | 共享judge与grade_arrays、汇总 | 坏输出score=0、坏参考score=null；共享judge回归覆盖失败分类。本轮没有正式案例汇总 |
| 逐例180/240/300/480/600秒（按题） | judge-config.timeout_seconds | 实际task_config读取并与独立公开期望核对；未执行新题数值程序校准时限 |
| 无独立输出字节限额 | max_output_bytes=null | 核对实际配置消费者；输出仍受声明规模和总体内存约束 |
| 2CPU/4096MB/0GPU/Linux，agent3600、build1800 | 各题harbor/task.toml与模板合并 | 逐题解析并核对生效结果；macOS工具测试不证明Linux cgroup限制 |
| separate/no-network verifier，总预算按真实例数 | 模板及base300+N*(timeout+60)，至少1200秒 | 临时N=3实际合并；正式N未绑定，不制造样例绕过prepare |
| 自动加载完整声明，一次安装、稳定CLI/SDK | runtime_materials闭包、已安装caeoj_bundle | 独立普通安装、移走源目录、换目录与交替读取见机器摘要；未发布包 |

## 验证范围

十组新增专项覆盖10题真实HDF5的CLI前置声明与SDK回写；手算有向关联矩阵；非连续ID、ID跨表同值、环／并联／反向、非法节点引用、自环／不连通、大小端int64、错误元件单位／正性／变比、表压负值与绝对压力正性、支路双端顺序、两腔顺序、缺多字段／条件／输出、字段位置长度相同却不同身份、未知绑定、load线性与control前值保持、控制末点覆盖、重复quantity等。文档允许／禁止边界独立选取，不仅从生成器清单反推合法性。

专项命令：`.venv/bin/python -m unittest discover -s tests -p test_systems_contract.py`。全仓命令：`.venv/bin/python -m unittest discover -s tests`，日志runs/chapter-18-regression.log。七节check_statements按skill入口逐节运行，报告runs/authoring/chapter-18/<section>/static.json。普通安装验证脚本runs/authoring/chapter-18/check_install.py；它只在runs生成协议fixture和临时装配，未向examples、samples、cases、reference写载荷，也未发布评测。

最终计数、平台、安装装配ID及执行结果见[机器摘要](chapter-18-validation.json)。协议fixture与零结果只验证结构和机制，不能作为物理参考。资源加载、评分执行与独立安装分别提供有限证据。

## 后续未决事项

正式数据／独立参考未生成，没有数值求解器运行、Agent benchmark或评测发布。后续须制作拓扑、元件、初态、源时程、非线性及控制饱和有意义变化的实际算例；核验全程正压／正温度、可变容腔体积、无空化／小扰动等逐题接收条件、方程适用与观测唯一性，建立独立参考误差证据并校准容差／资源。

声明正性不证明整个无界时间尺度或刚性参数族都能在同一预算求准。正式实例数与参考绑定、完整公开样例、Linux AMD64目标容器依赖和禁网verifier、发布审计尚待后续；实际prepare依旧要求真实数据和有效公开包，不绕过门槛。通用DAE、理想开关、非等温／临界气流、空化、通用协同仿真和自主控制设计等后续能力不作为本版交付。

最终执行证据：七节静态通过；10组专项与全仓330项回归通过（53.938s）。普通安装测试平台为macOS26.3 arm64／Python3.14.6，实际导入来自临时venv的site-packages，装配源目录已移开，清除PYTHONPATH并以Python -I从/private/tmp执行。十题正反序20次交替读取，每次运行info、validate-input、validate-output、显式grading的grade与SDK写回；坏单位拒绝，移走必需扩展后返回工具错误／退出码2。未测试Linux AMD64容器或离线安装。测试装配ID：`ced7f8efd610430eef98f251b2c00be923458614f141cddf5ebc9f1568f41165`。

最终维护核查：10个稳定task与规划、题面和DATA一一对应，7节没有遗漏；跨节能力分别为变比、死区、集总非线性、分布传播、气体质量、辐射、二极管、电机热反馈、双腔液压反馈与数字采样，未按来源或几何重复填题。公共CONTRACT未变，21个最终审阅哈希一致，生成源再次运行保持交付可重现。仅纳入本轮文件，中文阶段提交，最终工作树干净。
