# 独立考生考试材料审阅：migration-soret-scaling-repair

模式：exam-materials。最终结论：**本轮未发现未决问题**；两例已公开样例的所有输入资产、全部参考输出数组和评分配置均已检查。三文件足以理解数学问题、修复职责、输出和评分要求；公开样例未出现与其冲突的内容。

本次保持前次独立盲审上下文，只增加公开ZIP中的MANIFEST/README、三文件、中性SDK和声明校验扩展、两例样例输入及公开reference。没有读取public/elmer-source.tar.gz、native_result.py、run_case.py内容，未读作者材料或隐藏cases/reference，未实现模块修复，未运行真实求解器或付费模型。只在当前runs审阅目录写入快照、检查脚本和证据。

## 冻结版本

公开包：dist/migration-soret-scaling-repair-agent.zip。

ZIP SHA256：`9a660158718cf8b451985e8b70d684774b0b042efae20a487ab481c9035e5ba7`，实际计算与指定冻结值一致。

MANIFEST列明public_samples=[01,02]，README指向这些公开样例。所有允许提取的37个资产均已提取；其中MANIFEST之外的36个资产SHA均与MANIFEST吻合。受限的三个public文件没有提取或读取，MANIFEST中列出的哈希不视为它们内容已验证。MANIFEST自身SHA：`ce810979025f6785e9ff1dca569b11793715b3ad46327f2ca59a4fc25c043741`。

下表绑定全部样例资产、三文件与关键工具版本；其他中性工具逐文件SHA记录在evidence.json。

| 公开资产（题目路径省略前缀） | SHA256 |
|---|---|
| README.md | f478f4b475ec04c21a9df7c0fc9dcd33bfe909dc5b4b3af8e81cdc9a88cb4652 |
| docs/CONTRACT.md | 130d4416fd533812493780c8bc6afbc0a158de6800b59bbec14a852f3cf1c063 |
| DATA.md | 099e93d85614463e91dfc69be52c68f9f2bd7ada09bb7d7235963cdbd433b578 |
| instruction.md | c273ff5c708efd7578852a06c565061205b3b28fd10a0bcf4f489f271cf4f8f6 |
| samples/01/input/input.h5 | 9ba8f125d93516d43897cf39a2a6fc5a89e60cd616023c9e9ff7dbb1a9f130af |
| samples/01/input/mesh.msh | 02865faea276e4c6f356d757cfe0fb8e2ff51a5f16ddf412b0f8498978d23a12 |
| samples/01/input/problem.json | 2959f17370a11d389dcb3802b461d0ef436f405e3b3ff3cf686ac46104f8768c |
| samples/01/reference/grading.json | c9f50df339371cd2a0e2e8dcbf887ba28b1c943f47351fbf34cd887385bc3912 |
| samples/01/reference/reference.h5 | 01f83ebbe5d62c00b8e99d43a9b9516c8cc99c2f330664f9d608f1f519eec487 |
| samples/02/input/input.h5 | 9ba8f125d93516d43897cf39a2a6fc5a89e60cd616023c9e9ff7dbb1a9f130af |
| samples/02/input/mesh.msh | 02865faea276e4c6f356d757cfe0fb8e2ff51a5f16ddf412b0f8498978d23a12 |
| samples/02/input/problem.json | b9df8a3c20dbf6523d8b585c4c379f529d0299e7fea34ccbe3728284d397491a |
| samples/02/reference/grading.json | c9f50df339371cd2a0e2e8dcbf887ba28b1c943f47351fbf34cd887385bc3912 |
| samples/02/reference/reference.h5 | 4fb2f460159c6cbdae721582c159da17b57842d0c77826c5e78a2d2b8e69b7ac |
| src/caeoj/sdk.py | 3ddf8f5a1b516eca67abae35a05a26dc1b7a8381a168d7d148ea22f2ecab9cba |
| src/caeoj_task_ext/transport.py | a3e3b030b70d14175e601d43cf84e518c0ad9d8ba161541ef571283833f4e25f |

## 覆盖与检查结果

两例都完整读取problem.json、input.h5、mesh.msh、grading.json、reference.h5，不是抽样读取。完整数组检查通过包内中性load_problem/load_result完成；按其提供的全部节点坐标、连通和组检查矩形与身份，按节点tag映射比较所有输出值。

- 两例共用W=1e-4 m、L=1e-3 m、nx=1、ny=400网格，802个节点、400个体QUAD4、上下各1条边和左右各400条边，满足公开范围。微小浮点坐标差按公开均匀网格语义处理，没有误认为额外网格层。
- 输入包含且只包含node_ids、bottom_ids、right_ids、top_ids、left_ids、times，IDs为int64、时间float64[1]=[0]；所有身份引用、边界组覆盖与顺序均通过检查。
- 两参考均恰含node_ids、times、concentration、temperature、potential。身份和时间与输入逐值一致；三场全部为float64[1,802,1]且有限，未漏内部节点，没有额外边界IDs数组。
- 样例01为Relative Mass电迁移：ρ=1200 kg/m3、D=1e-9 m2/s、z=1、DT=0、T=298.15 K、φ从0到0.05 V、Y从1到0。浓度范围[0,1]，驱动力和单位均满足DATA。
- 样例02为Absolute Mass Soret：ρ=1000 kg/m3、D=1e-9 m2/s、DT=5e-12 kg/(m.s.K)、z=0，T从300到400 K、φ=0，底端c=1 kg/m3、顶端零总通量。平衡顶端c=0.5 kg/m3，物理范围及DT/D/ρ约束满足DATA。
- 两份grading.json的四类量容差均与instruction一致，pointwise/per_time/per_component检查覆盖三个场802个值。
- 使用快照内src作为PYTHONPATH分别执行官方validate-input、validate-output、grade，各两次共六次均退出0。grade以公开reference本身作为既有公开输出验证，accepted/score=1仅证明配置消费链自洽，不能单独证明数值正确。

## 独立数学核对

仅从三文件、公开输入和坐标推导，不读取求解器实现。

温度和电势应是端点值的线性插值。样例01等温、线性电势下，横向常数的QUAD4标准Galerkin退化为均匀一维线性单元节点递推。令a=zeΔφ/(kBT)、n=400、r=(1-a/(2n))/(1+a/(2n))，节点序号j的浓度为u0+(un-u0)(r^j-1)/(r^n-1)。用expm1/log1p评价该既有公开参考的全部节点，避免以连续指数曲线替代离散解。此为有限范围的样例验算，未编写修复或完整求解器。

样例02零总通量给c=c_bottom-(DT/D)(T-T_bottom)，在本线性网格场上也是规定离散的精确节点剖面。

| 样例 | 浓度最大绝对差 | 温度最大绝对差 / K | 电势最大绝对差 / V |
|---|---:|---:|---:|
| 01 | 2.23709939e-13 | 2.42380338e-10 | 1.96058447e-14 |
| 02 | 1.30162547e-12 | 2.75576895e-10 | 0 |

以上全部小于题面容差。数学核对覆盖全部已公开样例输出，既检查边界也检查所有内部节点。

## 问题与限制

未发现新的歧义、缺失样例资产或声明/样例不一致。前次statements中的F1（输出场与支撑数组混淆）已在本ZIP的DATA SHA099e93...版本关闭，当前两例输出也符合五key要求。

样例覆盖是电迁移Relative Mass和Soret Absolute Mass两种组合，不覆盖其他单位/模式组合、负DT、负z或零驱动力全部变体；不把有限公开样例当作全域数值认证。本轮没有检验真实源码打包内部、构建、驱动映射和20秒/180秒预算，不评价隐藏测试。不能将六次结构/自评分通过外推为真实候选修复可通过。

详细可重现证据：check_assets.py、evidence.json；快照仅包含允许资产，路径snapshot/。全部写入发生在runs/candidate-review/repair22-elmer-exam/。
