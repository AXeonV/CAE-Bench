# CAE Bench OJ MVP 任务计划书

目标：建立清晰的通用数据协议，再逐步完成“文字题目 → 编写求解程序 → 多测试点执行 → 逐点 0/1 判分”。工作区为 `C:\Users\Admin\Workspace\CAE-Bench-OJ`，Python 使用 `C:\Users\Admin\.conda\envs\expr\python.exe`。

## 1. 通用数据协议

正式规范为 [CONTRACT.md](CONTRACT.md)。

- Gmsh 生成网格，MSH 4.1 保留节点、单元、连接关系和 Physical Groups。
- NumPy NPZ 保存场及编号／时间数组，不重新定义数组序列化。
- JSON 声明文件引用、采样位置、字段单位与分量、参数、条件和输出要求。
- 实体 IDs 固定且递增；场统一保留时间、实体、分量轴。空间矢量／张量采用全局坐标，其他多分量量明确标签。
- 边界位置引用网格实体／组，条件类型和常量放 JSON，变化数值放 NPZ。初值、源项和材料场使用相同的数据引用方式。

协议允许多个网格、独立采样点和多个时间轴，不限制物理模型为某一类 CFD 方程。题目必须明确方程、支持范围、条件算子和离散输入的数学含义。固定网格以外的扩展须先定义清楚，再更新协议与校验规则。

## 2. 结构校验工具

元数据仅保留 `src/caeoj/problem.schema.json` 一个 Schema，不设版本注册和独立 Schema 子包。提供 `caeoj validate-input problem.json` 和 `caeoj validate-output --input problem.json --output result.npz`。检查清单结构、文件引用、数组 key、shape、dtype、分量、编号／时间轴和实体覆盖，返回 `valid/errors` JSON。

校验器不修改、转置、重排或纠正数据，不匹配等价网格，不检查物理方程、参数正负、守恒、条件相容性或答案误差。合法结构中的错误数值由判分器处理。SDK 仅协助读写与复制固定输出轴。

## 3. 本地 smoke：已完成

题目为原样回传输入场，不需要物理求解。统一启动方式：`python solve.py --input problem.json --output result.npz`。每例独立进程，独立判分器先校验输出再按默认误差阈值比较参考数值，每例 0/1 分。

12 个样例覆盖：1D 线网格、2D 三角／四边形网格、3D 四面体网格、混合单元、非连续 tag、规则划分与 binary MSH、多种 dtype、二维矢量、完整张量及组分、边界／单元／独立点场、时间序列。网格由真实 Gmsh API 生成，输入／输出数组使用真实 NPZ。

验收包括正确程序全部通过、结构错误被校验器报告、速度分量交换通过结构检查但被判错。判分在 `grading.py`，默认 `atol=1e-6`、`rtol=1e-5`；执行器不内置数值比较。本阶段不接入 Agent、Harbor，也不运行真实物理求解器。

## 4. 接入 Agent 与 Harbor：后续

开发材料提供文字题目、协议、公开样例、SDK 和校验命令。Agent 提交程序后冻结文件，判题逐例独立执行。隐藏测试和参考值不进入开发材料。

Harbor 适配只负责启动任务和汇总结果，需实际运行 Agent 和 verifier 完成验收，不以生成任务文件替代跑通。保留提交版本、逐例状态和分数即可，不建设额外调度平台或数据库。

## 5. 热传导题：完成题面和数据设计

已完成二维稳态热传导的[题面](../tasks/heat-conduction/instruction.md)和 [32 个解析测试点的数据设计](../tasks/heat-conduction/TEST-CASES.md)。后续继续设计和验证边界条件接口，再接入 Agent 评测。

## 6. 交付顺序

| 顺序 | 交付 | 状态或验收 |
|---|---|---|
| 1 | 通用协议、标准文件样例、结构校验器、SDK | 已实现，以 CONTRACT.md 为准 |
| 2 | 12 点本地回传 smoke、测试和报告 | 已实现，当前不接入 Agent |
| 3 | 热传导题面和测试数据 | 已完成题面和数据设计 |
| 4 | Harbor 适配及真实 Agent 验收 | 后续，实际跑通开发与判题流程 |

项目维持 `docs/`、`src/caeoj/`、`tasks/`、`tests/` 和 `runs/` 的简单结构。HDF5、可视化导出或更复杂数据形态只在具体需求出现后加入。
