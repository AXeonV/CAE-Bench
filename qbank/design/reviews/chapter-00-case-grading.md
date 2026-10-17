# 第零章 case 判题测试实施记录

2026-10-17，在 PR20 的 `48e672c` 基础上新增 [case-grading-test](../../00-basic-tests/0.2-grading/case-grading-test/instruction.md)，稳定 ID 为 `caeoj-000004`。目标及范围见[规划](../chapter-00-case-grading-plan.md)，操作入口见[题目维护说明](../../00-basic-tests/0.2-grading/case-grading-test/README.md)。没有修改已有物理题的要求，也未新增观测输出请求或判题框架接口。

## 题面、审阅和数据

独立设计审阅与独立考试材料审阅均未发现未决问题；原始报告及材料 SHA 保存于本题 [design-review.md](../../00-basic-tests/0.2-grading/case-grading-test/author/data-evidence/design-review.md) 和 [candidate-review.md](../../00-basic-tests/0.2-grading/case-grading-test/author/data-evidence/candidate-review.md)。考生审阅仅使用三份公开说明和两个样例输入／完整输出，不读取隐藏数据或作者实现。

实际 HF 池包含 8 个独立输入：6 个测试 case、2 个公开样例，输入及来源轨迹无重叠。测试分别覆盖整场、x、y、xy、x/y 双检查及整场与测点组合；样例分别覆盖整场和稀疏双检查。所有输入均含 4 个节点、2 个一阶三角形和 3 个时刻，节点／单元 tag 非连续，节点 HDF5 行顺序与网格插入顺序不同。五个测点覆盖域内、共享对角线和外边界。

判题参考由确定的输入数据构造。生成器按手写角点权重制作测点参考，实际数据审计另外按矩形分片公式计算全部观测，并与参考逐项核对，不调用被测评价器生成期望值；审计结果见 [validation.json](../../00-basic-tests/0.2-grading/case-grading-test/author/data-evidence/validation.json)。全部 8 例的所有数组已核对；完整样例输出与输入逐项一致。输入值不是某个全局仿射场，因此能区分 P1 重建与未经规定的双线性重建。

## 工具与真实消费验证

- 新增 7 项测试、6 个子测试，覆盖全部正例、P1 独立已知值、未观察分量变化、缺分量、双项 AND 双向失败、整场捕获测点零空间扰动、tag／时间错配，以及无重叠制池和完整示例分离。
- 本题全套装配与严格核验通过；输入盘点覆盖 8 例，无缺文件。公开发布包含两个样例，私有 verifier 准备包含 6 例，存在可执行作者参考程序。
- 真实公开包在新虚拟环境普通安装，移走安装源码并切换工作目录后，以隔离 Python 运行两个样例的完整回传及判分，分别通过整场和稀疏双检查。
- 同一已安装公开工具以独立 CLI worker 对私有准备目录的 6 例执行参考程序并判分，全部 accepted。此处不等同于已运行 Linux 沙箱进程隔离。

全库最终回归（测试目录）：433 passed、5 skipped、1,323 subtests passed。跳过项是 Windows 平台的生命周期或链接检查；回归所需旧题数据按固定 HF 提交临时恢复，交付时再次清理。题面静态检查和公开材料链接检查通过。

## HF 发布

正式提交：[c1bc9417f2f4fceb8d654a2833a90f22a8e3b7f4](https://huggingface.co/datasets/jimzhouzzy2006/CAE-Bench-OJ/commit/c1bc9417f2f4fceb8d654a2833a90f22a8e3b7f4)。通过通用 upload 工具原子添加 57 个文件；重复上传返回 0 个文件，不改动已有题目。

按固定正式提交重新通过 HF 远程装配全套数据，摘要、参考预检及严格核验通过；另分别只选稀疏样例 02 和测试 case 05-two-checks，远程装配与严格核验通过。样例的完整 example 与稀疏参考分别存储。交付前清理原始载荷、本地装配、HF 缓存、临时安装、审阅解析依赖和发布包；Git 仅保留题目、制数／测试代码、选择与审阅证据。

## 未执行范围

本题属于可精确核对的基础设施测试，不认证任何 PDE 求解能力。10 秒为公开执行预算，未声称做过最大 N/T 性能校准。未运行实际 Linux Harbor 容器或 Agent benchmark；独立考生审阅不替代数值与运行验证。
