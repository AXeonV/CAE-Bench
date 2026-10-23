# 独立考试材料审阅：空间梁方向变换修复

模式：exam-materials。题面结论：**本轮未发现未决问题**。公开样例状态：**已检查**；01、02所需实际输入、承诺参考及示例输出均齐全。无资料缺口。该结论不外推到隐藏数据、源码修复正确性或资源达标。

先完成 `../repair22-kratos-statements/report.md` 的三文件审阅，再读取白名单内实际公开资产。解释性资料仍限三文件；未读取实现、驱动、源码归档、作者材料、设计报告及隐藏case。未从样例反推新增题意。只使用 Python 标准库、NumPy 2.4.1、h5py 3.16.0 作中性解析及数值观察；没有运行公开包代码、完整solver或付费benchmark。

## 公开身份、版本及覆盖

公开依据：本题 data-manifest.json 的 samples 将01/02列为公开样例；dist/spatial-beam-transform-repair-agent.zip 的 MANIFEST.json 明列 public_samples=[01,02]，README.md 指向公开samples。仅读取ZIP根README.md和MANIFEST.json，未读取ZIP内代码或源码。MANIFEST中出现的其他文件名及SHA不视为读取授权。

完整实际文件/SHA256清单保存在 `evidence.json`：三公开文档、本题data-manifest、每例 input/problem.json、input/input.h5、reference/grading.json、reference/reference.h5、output/result.h5，共14个本地文件；另记录ZIP README/MANIFEST各自内容SHA。三文档SHA同 statements 报告；每例5个文件的SHA均与ZIP MANIFEST吻合。基线提交及工作树情况同 statements 报告。元数据检查确认无几何/网格或其他输入依赖。

两个样例的全部JSON、全部HDF5数组均完整读取，无未读的大数组。每例4根梁，ID=[11,27,43,89]；所有输入shape为[1,4,C]，时间=[0.0]，输出5场及ID/time的dtype、shape、有限值、身份关联正确。检查HDF5根dataset、无属性/子组/软外链/别名/外存储/虚拟dataset、允许过滤器。JSON的对象、轴、分量顺序、数量、单位及采样声明可由三文件确定。两个problem.json字节相同，其逐梁数值来自各自input.h5。

## 数值观察与结果

复现命令：`python runs/candidate-review/repair22-kratos-exam/inspect_public.py`。脚本只读白名单资产并写本审阅目录的evidence，不产生或替代提交源码。

- 所有输入数值满足DATA声明范围；样例01为全局x轴梁；样例02含x轴、xy斜向和一般三维斜向梁，参考轴投影定义能唯一恢复右手局部基。
- 每例 reference.h5 与 output/result.h5 全部数组逐值相同；combined与separate矩阵和力逐值相同。grading的三个quantity、单位、逐分量/逐时刻pointwise规则及atol/rtol与题面一致。
- 完整12×12归一化矩阵的最大对称误差≤2.981e-8 N/m，6个刚体模态相对残差≤2.878e-17，数值秩6，未出现超舍入误差的负特征值。
- 从公开S和R还原物理局部矩阵，仅观察自由端柔度块。其轴向L/EA、扭转L/GJ、两弯曲对角L³/(3EI)+L/(GA)、转角L/(EI)、平面交叉柔度±L²/(2EI)与公开材料、轴配对及右手符号一致；整块最大误差/最大参考幅度≤1.102e-13。此处没有读取参考实现或构造替代12×12求解器。
- 用公开Knorm后6×6块与 p_body,tip+tip_load 重新求解，8根梁的tip_displacement最大绝对差均为0；因此样例的转角归一化、夹持分块及输入集中载荷分量可以直接解释。
- 依据DATA的一致节点体力/端矩公式检查rhs，全部通过。但本轮8根梁的body_acceleration均为0，故该项只验证零体力，不覆盖非零ρAb、非零端矩及体载荷下FE响应。具体未覆盖反例为R=I、L=2、ρA=6、b=(0,1,0)应产生y力[6,6] N和绕z归一化矩[+1,−1] N；现有样例不能检出漏乘密度或端矩反号。这是样例覆盖限制，三文件已完整定义，未据此判题面有缺陷。

## 未执行与结论边界

未执行源码解压、构建、补丁实现、3个Kratos API真实调用、公开CLI/driver、容器启动、180秒编译/15秒逐例/8GiB内存实测；未验证隐藏case、pool来源或参考生成过程。数值观察不等于对参考实现的全面认证。未增设算法、语言、精度或连续梁精确解要求。

本轮没有必须修订或待核实的考试材料问题。可选的后续覆盖改进是公开一个非零体加速度例；这不阻止当前材料独立理解及做题。
