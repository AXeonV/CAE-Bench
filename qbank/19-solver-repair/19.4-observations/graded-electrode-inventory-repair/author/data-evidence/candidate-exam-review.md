# 独立考生审阅：梯度电极锂库存公开考试材料

## 范围与独立性

模式：**exam-materials**。延续 statements 轮的三文件解释范围，仅新增公开身份清单、samples/01 与 02 的五项材料及发布 ZIP 的 README.md、MANIFEST.json。未读取驱动、转换器、源码、维护设计或隐藏数据；未从实现推断要求。data-manifest.json 仅用于确认 01/02 的 samples 身份，未追踪 pool 引用。ZIP 仅解读 README、MANIFEST；其他条目只读取清单中的名称和哈希。

题面结论：**本轮未发现未决问题**。样例状态：**已检查（01、02 全部授权输入、参考、评分声明与公开输出）**。公开样例足以按三文件独立解释；本轮没有发现材料矛盾或需要修订的歧义。

## 实际版本与公开依据

data-manifest.json 的 samples.01/02 与 ZIP MANIFEST.public_samples=[01,02] 共同确认公开身份。ZIP README 指向题面、DATA、CONTRACT、两样例和公开运行/判分命令；明确三文件为完整要求。清单列出的样例五项资产和三解释文件的 SHA256 均与本地实际材料一致。未验证 ZIP 内禁止读取的资产内容。

| 实际文件 | SHA256 |
|---|---|
| `qbank/19-solver-repair/19.4-observations/graded-electrode-inventory-repair/instruction.md` | `307ba428479c5f37ac596c5b1e795763cf5f8d055ef45c1506b1776f0b15e940` |
| `qbank/19-solver-repair/19.4-observations/graded-electrode-inventory-repair/DATA.md` | `8f6572303e5f40ad7fdf22a16842210e0d708526c52c7c732ce6683c9fe6b29e` |
| `docs/CONTRACT.md` | `130d4416fd533812493780c8bc6afbc0a158de6800b59bbec14a852f3cf1c063` |
| `qbank/19-solver-repair/19.4-observations/graded-electrode-inventory-repair/data-manifest.json` | `def2cb9f4549d0abbf43cadf9ca9846c285c1e1f4a0d29e3807fd1170d45baf9` |
| `qbank/19-solver-repair/19.4-observations/graded-electrode-inventory-repair/samples/01/input/problem.json` | `cb7404ba3294f12d24453429d0075eae646dbac2e21404ea9afbdf898bd83e9e` |
| `qbank/19-solver-repair/19.4-observations/graded-electrode-inventory-repair/samples/01/input/input.h5` | `3892d4ce72742c1ccae0d8c0ffb58b7cd5be12a1cf77483d1eb4104b32613598` |
| `qbank/19-solver-repair/19.4-observations/graded-electrode-inventory-repair/samples/01/reference/grading.json` | `82f74dc82150728982b99b34f5077c71b587a6c46d601223e19b5c2b1ac443a0` |
| `qbank/19-solver-repair/19.4-observations/graded-electrode-inventory-repair/samples/01/reference/reference.h5` | `8a392897036fcce2e0b46890029f2e77b4549f5183e43dddd76205c5013786a7` |
| `qbank/19-solver-repair/19.4-observations/graded-electrode-inventory-repair/samples/01/output/result.h5` | `8a392897036fcce2e0b46890029f2e77b4549f5183e43dddd76205c5013786a7` |
| `qbank/19-solver-repair/19.4-observations/graded-electrode-inventory-repair/samples/02/input/problem.json` | `ef07044d54c99a2fdfac1ef62c24dbe6a2172f8c14d3809e113b0f6365ecfb8a` |
| `qbank/19-solver-repair/19.4-observations/graded-electrode-inventory-repair/samples/02/input/input.h5` | `3e90d08f84121e30670ffd8050721644924c6bd105ad5f68f75a4ac7368ba8b9` |
| `qbank/19-solver-repair/19.4-observations/graded-electrode-inventory-repair/samples/02/reference/grading.json` | `82f74dc82150728982b99b34f5077c71b587a6c46d601223e19b5c2b1ac443a0` |
| `qbank/19-solver-repair/19.4-observations/graded-electrode-inventory-repair/samples/02/reference/reference.h5` | `9f32a4e2194a4ffbf76a6fcf00bc09a96a51ddfc57e73e86de72abd218ed6b7c` |
| `qbank/19-solver-repair/19.4-observations/graded-electrode-inventory-repair/samples/02/output/result.h5` | `9f32a4e2194a4ffbf76a6fcf00bc09a96a51ddfc57e73e86de72abd218ed6b7c` |
| ZIP sha256 | `6106589d8765bafed628400b412302bad3ad3c94fd240ae6ece5b52b9f7757bb` |
| ZIP README_SHA256 | `92ccd5e36aa062c273bf574e00da77f095f0fde036066605646e8044fe86159d` |
| ZIP MANIFEST_SHA256 | `9f4013683d2b93ff5eb9aa2d8b59868fcf1ef9866d26718eb71e74f35c86b97c` |

## 检查方法与完整覆盖

使用 Python 标准 JSON/ZIP、NumPy 2.4.6、h5py 3.16.0 编写中性检查，未导入项目代码。完整读取每个授权 HDF5 的所有 dataset 和全部数值，没有抽样或未读大数组。复核模型、参数数量/范围/单位、locations、times、IDs、输入/输出字段集、quantity、unit、分量标签、sampling、dtype、shape、有限性及数值范围。HDF5 检查根及 dataset 无属性、根下均为 dataset、无软/外链接、外部存储、虚拟 dataset 或不允许的压缩。

按 DATA 的 `j*R+i` 恢复每个状态 `[X,R]`，直接计算 `diff((i/R)^3)` 球壳权重、径向浓度、ε 加权体积平均、volume/cmax、A*L*mean(ε*radial) 及两极库存之和。对参考与公开输出的每一分量分别应用题面绝对/相对容差；验证各结果复制输入 IDs 与 times，且只含声明输出。公开 grading.json 的 quantity、单位、逐分量逐时刻规则及全部容差与题面一致。

| 样例 | Xn/Rn；Xp/Rp | 状态数 | 每份输出检查分量数 | 参考与 output 字节相同 | 最大误差/题面容差 |
|---|---|---|---|---|---|
| 01 | 5/6；7/4 | 6 | 114 | 是 | 2.4649212e-08 |
| 02 | 4/4；6/5 | 6 | 102 | 是 | 4.79401408e-08 |

两例均含 IDs `[3,17,47,81,251,901]`，验证了非连续实体身份。01 中 ε 与厚度位置浓度变化同时存在；02 的各状态 ε 沿厚度常数，仍含径向非均匀浓度。全部输入和输出状态、两电极、九类输出均检查，没有只检查总库存或单一标量。参考与公开输出共核对 432 个浮点分量。

## 反例与判别力

公开材料没有出现不同合法解释导致不同结果的反例；以下替代解释已由题面明确排除，并可被实际样例区分：

| 样例/电极 | 用径向算术平均替代球壳权重的最大浓度差 | 用厚度算术浓度平均替代 ε 加权平均的最大浓度差 |
|---|---|---|
| 01/n | 1713.69848849 mol/m³ | 315.191793469 mol/m³ |
| 01/p | 1312.65823045 mol/m³ | 307.671079621 mol/m³ |
| 02/n | 1643.86205824 mol/m³ | 3.63797880709e-12 mol/m³ |
| 02/p | 1543.78850616 mol/m³ | 3.63797880709e-12 mol/m³ |

02 的厚度算术与 ε 加权差仅为浮点舍入量，符合常数体积分数下应等价的要求；01 中差异显著，可识别忽略 ε–浓度相关性的计算。两例球壳与径向算术平均均显著不同。未发现单位、索引或输出字段与三文件冲突。

## 结论限制

本轮是公开材料一致性和样例公式复算，**不是数值参考认证**，不认证隐藏参考、求解器通用正确性或科学适用性。没有构建、没有执行可信驱动或任何 solver、没有检查隐藏数据、没有验证实际缓存重建/导入路径或资源达标、没有运行收费 Benchmark。ZIP README 的运行命令只做文本检查，未执行。

检查程序和逐文件/逐输出证据保存在同目录 `neutral_sample_check.py` 与 `evidence.json`，仅用于复核本次已授权的公开样例。
