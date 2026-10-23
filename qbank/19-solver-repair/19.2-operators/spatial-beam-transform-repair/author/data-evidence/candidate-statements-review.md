# 独立考生审阅：空间梁方向变换修复

模式：statements。结论：**本轮未发现未决问题**。样例状态：本模式未纳入；实际公开样例另见 `../repair22-kratos-exam/report.md`。

审阅者为独立 subagent，仅收到真实任务、检查主题和白名单，未读取作者讨论、设计报告、实现、源码归档、驱动或隐藏数据。阅读技能及其 workflow 后，仅用 instruction.md、DATA.md、docs/CONTRACT.md 解释题意。未编写提交 solver，未调用付费 benchmark，未修改公开材料。

基线提交 `940fa23777538be857eb18a3acc6b1b0d4ad67b7`。题目所在 `qbank/19-solver-repair/19.2-operators/` 在审阅时为未跟踪目录，因此以下实际字节 SHA256 是复用结论的依据，不能由提交号代替。

| 文件 | SHA256 |
|---|---|
| qbank/19-solver-repair/19.2-operators/spatial-beam-transform-repair/instruction.md | 11bc5c792c1191dd02fb6170734b8dcfd5a95a76aaf20be087787535721cd637 |
| qbank/19-solver-repair/19.2-operators/spatial-beam-transform-repair/DATA.md | ea86ff1826a9038214f870e56262b96bc41c1b78a386fe85139f5cb0bd7d07c3 |
| docs/CONTRACT.md | 130d4416fd533812493780c8bc6afbc0a158de6800b59bbec14a852f3cf1c063 |

## 按考生读取流程检查

1. **任务与模型。** instruction:3–7 明确真实 Kratos 两节点三维线性 Timoshenko 单元、各梁独立、零初始位移转角、静力小变形、保留单元积分和材料响应。它要求修复既有单元，而非自由选取另一个离散模型；无须凭“线性 Timoshenko”自行选择全积分或减缩积分实现。
2. **输入与身份。** DATA:3–23 定义所有字段、dtype、shape、实体编号、时间和分量，空网格/几何/conditions 有明确意义。CONTRACT 的 entities 及 components 可直接表达此有限维对象，不依赖网格节点编号猜测顺序。
3. **轴与符号。** DATA:25 定义根至自由端的 t，截面参考轴投影为 y，z=t×y，R 的行和变换方向明确。DATA:29、31 固定全局右手转角及力矩。输入保证参考轴不退化。
4. **截面与材料。** DATA:16–20、27 明确 Iyy=∫z²dA、Izz=∫y²dA；y 横移由 EIzz/GAy 控制，z 横移由 EIyy/GAz 控制。J 是单独输入，不能默认等于 Iyy+Izz。G、密度和范围完整。
5. **载荷。** DATA:22–23、29 明确 b 是全局加速度而非线载荷，w=ρAb；给出两个节点一致力和端矩符号。rhs 不含 tip_load，tip_load 的后3项是全局力矩除以 L。初始零状态消除残差符号或内力状态的不确定性。
6. **归一化与响应。** DATA:31 的 q=S d、p=S^-T f、Knorm=S^-T K S^-1 维数及虚功一致。DATA:43 明确根端前6分量固定，自由端从 combined 后6×6块与 body-tip+tip_load 求解；有限元响应定义无需从连续梁解反推。
7. **输出、评分、提交。** DATA:33–43 指定5个完整数组、按行优先矩阵、全局分量、ID/time复制、combined/separate与3个API的对应。instruction:7–13 指定唯一替换文件、允许范围、冻结增量编译、禁止事项、按case全部数值通过、逐分量容差和资源限制。

## 具体歧义反例尝试

以下是已被公开文字排除的不同解释，不是未决缺陷。

- 取 t=(1,0,0)、a=(0,0,1)：DATA:25 唯一给出局部 y=(0,0,1)、z=(0,-1,0)，不能再由外力方向选择 y。各向异性截面下误选 y 会交换弯曲响应，但不构成题面歧义。
- 令 Iyy≠Izz 且 Ay≠Az，施加局部 y 端力：DATA:27 已排除用 EIyy 或 GAz 解释 y 挠度。
- 令 L=2 m、物理端矩 Mz=8 N·m：tip_load 的 mz_over_L=4 N，q 的 Lθz 是2θz m；若只缩放位移、保持物理力矩不变则虚功差一倍，DATA:31 明确排除。
- 令 b=(0,1,0)、ρA=6 kg/m、L=2 m 且 R=I：局部两端 y 力各6 N，绕z物理矩分别+2、−2 N·m，归一化矩为+1、−1 N；DATA:29 排除漏乘密度、反向端矩或把 tip_load 加进 rhs 的解释。
- 有体载荷时用连续梁公式代替单元方程：DATA:43 把目标固定为指定矩阵块的有限元响应，没有要求额外满足某种连续梁解。未将任意连续梁模型作为新的评分要求。

无必须修订项；无待作者补充的题意事实。未检查代码/API实现是否兑现声明、编译和运行耗时、真实镜像依赖、隐藏数据数值正确性；本结论不认证这些事项。
