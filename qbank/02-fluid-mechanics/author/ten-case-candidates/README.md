# 第二章十例候选参考建设

本批在 `cases/chapter-02-ten-reference-candidates` 工作，基线是
`1740d71a86bcb9260b3b3fdde7feb6ab28ed2735`。目标为第二章除2.1.1、2.1.3
外63题各补足10例。HF仅只读核对固定提交
`d46b17a03d444646157e1e2fe4b4f00587dc5d89`；该提交没有目标题目的池。

用户要求先设计全部工况，再计算参考；本阶段不做数值验证、交叉验证、
HF上传、正式选样或模型评测。旧FOAMBench任务保持停止。
随后用户明确选择：继续寻找现成求解器，未匹配的题暂缓，不能扩展物理模块。

## 设计材料

- [CATALOG.md](CATALOG.md)：63题的逐题索引。
- [COVERAGE.md](COVERAGE.md)：逐题覆盖矩阵索引；设计分配不等于已实现。
- [ALL-CASES.md](ALL-CASES.md)：630项设计的可读列表。
- [SOURCE-RESEARCH.md](SOURCE-RESEARCH.md)：已定位实现、匹配限制和待查闭合。
- [index.json](index.json)：文档指纹、来源索引和状态。
- 各题 `author/chapter02-ten-20261020/design.json`：每例的意图、有效差异、
  全部SI参数、几何构造、初边值、源、物理时间、观测、生产者匹配风险及待办。
- [scenarios.py](scenarios.py)：物理实验草案，不是求解器，不生成答案。
- [build_designs.py](build_designs.py)：确定性生成设计清单。
- [detailed_design.py](detailed_design.py)：逐例数值实验定义，不是PDE求解器。
- [freeze_designs.py](freeze_designs.py)和[design-freeze.json](design-freeze.json)：设计完整性、逐题重复实验检查与固定文本摘要。
- [EXECUTION.md](EXECUTION.md)和[execution-summary.json](execution-summary.json)：最近一次收集的实际执行状态；不从设计文件中的执行前状态推断当前进度。

630项均已有详细数值实验定义，仍不能表述为630个实际输入包或630份参考。
根据全面覆盖要求，2.1工况已从十个闭腔实验调整为入口、牵引、周期、
滑移/对称、流量、分布源和初态的组合；先前20个闭腔配置不再作为本批十例选择。
其中2.1.2、2.1.4共6项保留完整闭腔工况。设计检查只说明数值定义、
单位、参数集合、初态/时间类型与覆盖分配完整，且没有完全相同的物理定义。
它不证明非线性求解状态、无回流、全湿、稳定性、精度或资源限制已满足。

## 计算规则

先完成全部可执行工况的设计冻结；明确暂缓条目不能混入执行队列。
不自行编写求解器或改变现成求解器的物理模块。可制作原生输入、边界条件配置、
网格与HDF5转换器；实际生产者必须有版本、固定镜像及源码定位。
文献明确给出解析关系时，可按技能规定求值；须明确区别公式生产者和原文数值求解器。

计算目录与旧FOAMBench目录隔离。只将脚本、设计、轻量索引和摘要留Git；
原生网格、完整场、日志、执行记录及输入参考载荷保存在Titan。
成功执行与输出存在不等于数值准确。结果必须标记 `unvalidated_candidate`，
不得在没有相应证据时报告稳态收敛、精度通过或适用于正式测试。

已接通的生产入口：

- [native_closed_cavity.py](native_closed_cavity.py)：未修改的OpenCFD icoFoam，6个瞬态闭腔。
- [polytropic_reference.py](polytropic_reference.py)：文献静水平衡公式、固定势与质量归一化，20项。
- [native_euler_transient.py](native_euler_transient.py)：未修改的rhoCentralFoam，18个无外源Euler瞬态；2个加速度源工况仍待原生源项匹配。
- [native_gas_film.py](native_gas_film.py)：未修改的Elmer ReynoldsSolver，可压缩等温气膜10项。

这些入口是输入/输出适配器及原生配置，结果均为未验证候选参考。其余条目仍须匹配和装配。
不能把“找到了候选模块但适配未完成”说成“没有现成求解器”；具体闭合缺口与普通待执行工作在实际执行索引中分开记录。

在保留题面、DATA、grading-template和本目录的快照根目录中生成并冻结设计：

```powershell
python qbank/02-fluid-mechanics/author/ten-case-candidates/build_designs.py
python qbank/02-fluid-mechanics/author/ten-case-candidates/freeze_designs.py
```

生产脚本统一接受`--root <独立计算目录> --snapshot <冻结快照根目录>`，在Titan现有caeoj Python环境执行。
闭腔入口额外要求`--execute`；Euler与气膜可用`--limit`限制任务数。执行前检查主机、父级cgroup和已有任务的实际资源。
已有status.json的条目不会自动重启；失败后的修复须先核实容器结束状态、保留旧配置/日志，再只重做必要步骤。
运行[execution_report.py](execution_report.py)收集真实载荷状态与摘要；它只检查文件存在与摘要一致性，不做数值验证。
