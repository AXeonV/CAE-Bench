# 第十七章实现、审阅与配置证据

日期2026-10-16。基线a12c2ae，启动工作树干净。范围为7节12题的规划、题面、自包含DATA、共享扩展、评测配置和独立考生审阅；未授权正式数据、参考或发布，未向数据目录写载荷。第17章先前只有总体方向，新增有限范围与依据见章规划及逐题清单。所有题采用明确的一维连续体模型，未宣称完成任意三维多物理场能力。

## 归属及公开接口

- qbank/17-multiphysics逐题仅以instruction、DATA、docs/CONTRACT为题意阅读集合。无COMMON、共享DATA、源码阅读或注册要求。
- qbank/extensions/caeoj_ext/multiphysics为可复用continuum声明检查，models.json仅存公开类型、单位、参数和支持组合；不含数值求解、参考或章号分派。
- qbank/extensions/caeoj_bundle/runtime.json显式绑定12题及模型名字空间。复用physics、points、entities、fields、conditions、多时间轴和quantity评分，未改核心、CONTRACT、Schema、发布器或Harbor实现。
- qbank/maintenance/authoring/multiphysics.py维护题目定义和展开源；审阅修订同时回写源。公开包不包含该维护文件或tests。
- 支持常量的稳态题及只接受显式field的瞬态／复相量题分别声明。domain为真实物理观测坐标，left/right是实际端面对象；不使用伪坐标。乱序坐标不改变ID行序。复数统一峰值exp(+i omega t)、[real,imag]。

## 独立考生审阅

三位单独subagent只获真实实现任务及各题instruction、DATA和CONTRACT路径，明确只读，禁止隐藏数据、代码、规划和维护材料。实际覆盖全部12题、24份逐题文件和1份公共CONTRACT。初审与修订后复核的文件SHA256由审阅者返回，最终25文件均与当前文件匹配，见[版本清单](chapter-17-review-manifest.json)。

| 审阅者 | 覆盖 | 反例尝试与闭合 |
|---|---|---|
| review_fluid_thermal | 17.1—17.2，4题 | 刚壁声速后附加壁位移、压力／活塞外力反号、绝对／表压、温升／绝对温度、两端热约束与自由膨胀、热容重复乘密度、遗漏反向热反馈，均由明确方程排除；补因果弱解与初边角点解释，清理模式／实体模板 |
| review_electric | 17.3—17.4，4题 | 正负电压、加载阶梯／线性、牵引力／应力、D与端电荷、负e、e=0、无外负载、正负时间相位／RMS均可确定；修正压电area误用液柱活塞面积说明，清理T0、E、eta和无关物理模板 |
| review_magnetic_porous | 17.5—17.7，4题 | H的+y与外法向、磁弹性四边界、Biot有效储存与三维模量换算、孔压基准、三场反馈、热电流符号、只返回导热热流或乘面积均有明确排除；将磁固u(0)=0前移到物理定义，清理材料与适用条件模板 |

最终复核三组均通过，未发现仍需猜测的公开契约问题。通过仅限三文件可确定性，不是无缺陷保证，也未实现或验证数值求解器。

## 维护验证及实际消费点

以当前基线的caeoj_tools.grading_policy.task_policy、caeoj.grading_policy.resolve_policy、caeoj.grading.grade_arrays和src/utils/prepare_harbor.py.task_config核对配置；未将JSON存在视为生效证据。

| 公开要求 | 实际生效配置／消费者 | 本轮证据 |
|---|---|---|
| 每quantity逐值atol/rtol，全部时间／位置／实虚分量AND，无偏置 | grading.json v2按quantity及unit绑定真实逻辑字段，实际array key由清单获取 | 12题分别以不同逻辑名／array名加载，独立列出的公开阈值核对；0与非零参考、等号与紧邻越界均测试 |
| 每例0/1，总通过比例 | 共享Harbor judge正常退出、结构与grade后汇总通过数/例数 | 既有judge回归通过；新题无正式实例，不启动正式汇总 |
| 坏输出考生失败、坏参考基础设施错误 | grade_arrays结构检查 | 删除输出字段score=0；删除参考字段score=null |
| 360s或480s逐例墙钟，输出无独立字节限额 | judge-config timeout_seconds与max_output_bytes=null；共享judge读取 | 新配置值与公开题面独立核对；共享运行器超时／错误回归通过，未运行新题数值程序 |
| 2CPU、4096MB、0GPU、Linux、agent3600/build1800 | 各题harbor/task.toml与模板实际合并 | 12题实际task_config读取，核对结果；未声称macOS执行Linux cgroup限额 |
| separate/no-network verifier及总预算 | 模板与配置base300、per_case_overhead60 | 用临时N=3验证max(1200,300+N*(timeout+60))；正式N由数据阶段确定 |
| 一次普通安装、CLI/SDK自动契约 | runtime_materials最小闭包、已安装provider | 12题合并装配独立普通安装，移开源目录、清除PYTHONPATH、换/private/tmp、Python -I逐题检查；详见[机器摘要](chapter-17-validation.json) |

专项8组测试覆盖12题真实HDF5声明与SDK回写、非连续ID／乱序坐标、同值跨端口ID、无端点采样、字段／常量差异、零初态、时间覆盖、错重建、单位与复数布局、缺多参数／条件／输出、未知绑定、耦合参数、Joule反馈和正温度接收条件。反例变体依最终文档选择，公开评分阈值另行列出，不仅调用生成器反推预期。

七节check_statements静态检查通过；最终全仓320项回归通过（52.043s）。首个系统python调用因缺h5py未能启动测试，随后使用项目既有.venv完成验证，未改用户环境或掩盖失败。回归命令：`.venv/bin/python -m unittest discover -s tests`；日志runs/chapter-17-regression.log。专项命令：`.venv/bin/python -m unittest discover -s tests -p test_multiphysics_contract.py`。逐节静态命令见skill，输出在runs/authoring/chapter-17/<section>/static.json。

## 后续条件

没有正式输入、公开样例、隐藏cases或独立参考；未运行数值求解器、Agent benchmark或发布。临时零结果仅做协议和评分机制探针，不能充当物理真值。正式prepare仍要求真实数据／参考和有效公开包，本轮不绕过该门槛。

需后续制作有意义变化的实际算例、独立参考与误差证据，核验初边值兼容、解唯一性、材料／小扰动适用、全域接收限制；然后校准精度与时间／内存预算，冻结实例数，在Linux AMD64目标容器验证系统依赖与禁网verifier，最后审计公开材料并发布。参数正性与接口通过不等于无量纲极端范围都可在预算内求准。完整三维、大变形、非线性磁滞等方向见章规划，不作为本版已完成能力。

独立安装实况：Python3.14.6、macOS26.3 arm64；实际导入来自临时venv的site-packages。十二题逆序／正序合计24次加载，逐次执行info、validate-input、validate-output、显式grading的grade及SDK写回，坏单位拒绝、移走必需扩展后退出码2。测试装配ID为`22cef3f45da33cb3388755bf575b48fdfa638b7b41d6973ed3134598b3425118`。独立安装脚本与执行日志位于runs/authoring/chapter-17/check_install.py和install-check/，仅为本地临时验证材料，不是正式公开样例或发布包。

最终维护核查：12个稳定task与逐题清单、题面和DATA目录一一对应；7节全部有交付，无以几何或来源名重复拆题；共享CONTRACT未变；12题全部显式绑定同一受控物理扩展，未增加阅读或安装步骤。版本清单25个SHA256均核对。阶段提交均为中文commit，仅纳入本轮文件。
