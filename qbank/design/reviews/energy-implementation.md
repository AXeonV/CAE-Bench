# 2.2—2.4 能量与湍流实施记录

日期：2026-10-15。范围：保留规划2.2的12题，落实冻结清单2.3五题、2.4四题，共21题。公开目录为 `2.2-single-phase-energy`、`2.3-turbulent-flow`、`2.4-turbulent-energy`，每节README/COMMON/DATA及逐题instruction/DATA完整；examples/references/cases仅.gitkeep。

## 选择与缺口归属

| 需求 | 公开声明／拥有层 | 实施 |
|---|---|---|
| 层流热反馈、无黏/黏性气体、平均与统计目标 | physics.model显式14型号，不以task暗藏物理 | qbank/maintenance/protocols/FLUID-ENERGY.md、fluid_energy.MODELS |
| 物性随状态变化、Boussinesq与气体质量库存 | physics.parameters带单位固定标量 | 精确参数集合、单位/范围/物性端点可表示性检查、SDK物性助手 |
| 固定封闭域、机械与热边界 | conditions + element locations + fields | 复用既有结构；连通性、外边界覆盖、纯切向壁速、热锚检查 |
| 初态、连续源项、重建 | 条件typed-data、HDF5采样 | 必需变量、域覆盖、单位、正值、时间范围、piecewise_constant/constant或linear |
| 共同物理观测与统计 | outputs + 单元平均 + 显式统计时间参数 | 全部适用输出集合；离散等权、先空间平均再中央矩的SDK |

首版封闭域可以由移动壁/体力驱动强制对流、浮力驱动自然对流及组合，也适合封闭域湍流。没有借未定义开边界扩大范围；开口、周期、入口湍流生成、粗糙壁为明确后续扩展。为避免无黏稳态缺熵信息，该题限定平滑等熵并显式给等熵参考密度；无黏瞬态允许有限强度无真空激波。稳态热黏性题至少一个温度锚。2.3不含热流叙述或热观测。

同义结构复用，不改变Schema或通用容器：`physics.model`的新前缀是语义opt-in；旧输入不受该模块检查。拒绝未知前缀型号和CFD配置混用。根Agent负责geometry按需加载、validate-input接线、SDK公开导出、发布依赖及隔离验证。领域新函数为 check_fluid_energy(problem,errors)，错误类别E_FLUID；领域API为fluid_energy_properties、fluid_energy_condition_values、fluid_energy_statistics。

## 验证证据

- `.venv/bin/python -m unittest discover -s tests -p test_fluid_energy.py`：5个测试方法通过。临时目录生成14型号及全部允许二维分支的合法fixture，完整读/写/读取输出；不是题库数据。
- 非法项覆盖未知型号、混用、错/缺单位参数、零统计步长/热参数、缺/重叠边界、缺初态、非切向运动、错输出量、缺sampling、时间越界、额外条件键、温度范围和错误typed-data。
- 独立预期覆盖理想气体86100/(287*300)=1、cp=1004.5、温度比4的平方根物性倍率2；非均匀时间信号线性插值；三样本中央矩8/3、温度方差200/3、热流协方差40/3，不通过被测helper生成预期。
- `check_statements.py` 分别检查三节，12/5/4题链接与JSON静态检查通过；报告在runs/authoring/2.2、2.3、2.4。最终修订后由root复跑。

## 独立审阅与剩余限制

本记录不是独立审阅；实现作者未以自审代替考生审阅。根Agent将另派只读独立考生读取公开材料、修订后复核最终文件，并保留其实际记录。

预算与容差为分层设计目标（层流900秒，湍流1800秒、4CPU/8GiB），没有真实算例校准证据。未验证任何真实CFD求解器、物理准确性、稳态存在、马赫数、质量库存解、湍流模型误差或统计不确定度。RANS/URANS共同观测仍需未来独立多模型/实验或可信参考证明所选容差可达；协议检查与解析物性测试不能代替。未建设数据、未生成参考、未发布评测。

## 独立考生首轮意见的修订（2026-10-15）

根Agent转交独立 review_energy 的首轮缺陷，已落实如下。独立最终复核仍由原审阅者执行，本段仅记录作者修订。

1. 在 FLUID-ENERGY.md 明确黏性气体三维材料应力及耗散；二维平面应力仍采用1/3去迹系数，不能换成1/2。
2. URANS 原有U/k/length容易被误解为完整物理ensemble。现规范和2.3.3/2.4.2 instruction/DATA同步声明标准化建模初态：初始Reynolds应力2k/3 I，热URANS温度方差/速度温度协方差为0，模型专有状态从这些公共量初始化。目标是URANS平均演化工程近似，正式参考/容差须验证闭合和高阶初始化差异可容纳；没有隐含能谱或完整随机场。这是显式模型语义补足，不新增容器、字段或Schema；当前未发布配置与全部受影响题面同步更新，无旧真实数据可迁移。
3. 无黏稳态规范与两维题面明确请求观测唯一性保证，不要求猜未知涡量/环流分支，不能任选静止解。数据建设仍须提供此适定性证据。
4. 删除2.3 instruction中不适用的热条件；无黏instruction删除壁运动/热条件，明确固定域滑移绝热；所有三维DATA改为x/y/z完整分量。

修订没有改变读取容器或数值SDK，不新增镜像实现的测试。修订后重新运行本模块5组测试和三节静态检查，全部通过；真实物理/数值验证仍未执行。
