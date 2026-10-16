# fuel-cell-energy 数据契约

入口problem.json及data_file引用的扁平HDF5，路径相对清单。顶层采用CONTRACT结构，physics恰含model、parameters；model=`electrochemistry-fuel-cell-energy-v1`，task可省略，出现须为`fuel-cell-energy`。禁止profile、contract_version、analysis、materials混用；不接受未列参数、条件、字段或位置。

## 物理定义与支持组合

等温氢氧燃料电池的各独立稳态工况，总反应H2+(1/2)O2→H2O，每mol H2转移2mol电子。Erev=E0+(RT/(2F))ln[(pH2/p*)√(pO2/p*)/aW]。几何面积电流J≥0，活化损失ηa=2RT/(ma F)asinh[J/(2j0a)]、ηc=2RT/(mc F)asinh[J/(2j0c)]，对应输入有效电子数的对称BV经验动力学；ma、mc不是总反应的热力学电子计数2。Vcell=Erev−ηa−ηc−J RΩ；单位几何面积电功P=J Vcell，向外热释放Q=J(Etn−Vcell)，因此P+Q=J Etn。E0、Etn与水活度的相态参考按输入一致给定，不能自动引入液态／气态水数据库或另加反应热。支持外电源强迫高电流，故Vcell、P可负，Q按公式带符号；不截零。无气体传输限制、燃料利用率修正、混合电位、双电层、温度场或水管理，提供的分压和交换电流已是该工况的有效值。

## 全局参数

parameters恰含下表全部项；各项只有value、unit，数值有限，布尔不能作数值，JSON整数要求不得用浮点数替代。全部无缺省。

| 参数 | 单位 | 含义与值域 |
|---|---|---|
| `temperature` | `K` | 恒定温度T>0 |
| `gas_constant` | `J/(mol.K)` | 输入明确给定气体常数R>0 |
| `faraday` | `C/mol` | 输入明确给定法拉第常数F>0 |
| `reference_pressure` | `Pa` | 活度采用的标准压力p*>0 |

## 位置、几何及身份

spatial_dimension=1，meshes、geometries均为空。entities表示真实有限对象，无虚构坐标；维度1仅为有限对象的存储标记，不增加空间方程。IDs为int64、非负、严格递增，身份仅在location内有效，字段N轴按IDs行序对应，不按ID数值作数组下标。

| location | kind、数量 | 完整语义 |
|---|---|---|
| `operating` | entities，1..128项 | 独立稳态工况，不是空间点或物理时间序列 |

## 时间、数组及重建

time_axes恰含state，其引用float64[1]=[0.0]，所有输入和输出均用state；0是稳态存储标记，不是物理初态。

场均float64，完整形状[T,N,*component_shape]。scalar为[1]、components=["value"]；components按表中shape行优先展平标签为c1..cL（L为分量总数）。

所有data只允许{"field":"逻辑字段名"}，禁止内联数值、option或数组。fields恰为实际被引用场；quantity等于data键名，键value例外等于该条件variable；逻辑字段名与array key自由且区分。字段必须在对应条件同location及上表规定时间轴，不能借相同数组长度配对其他身份。每字段均point，sampling显式，space=uniform、extrapolation=forbid；所有场time=constant。uniform表示各对象上给定值，不要求不同对象行相同，不作实体或观测点之间插值；连续物理解由方程求出，禁止把输入采样当内部解网格。

## 条件全集

### `operating`

role=`source`，variable=`operating_point`，operator=`operating`，location=`operating`；所引用字段均为time_axis=`state`（条件记录本身不含time_axis键）。恰一条，完整覆盖该位置。data恰含：

| 键 | 类型、单位及含义 |
|---|---|
| `hydrogen_pressure` | scalar [1]，`Pa`；氢气分压pH2>0 |
| `oxygen_pressure` | scalar [1]，`Pa`；氧气分压pO2>0 |
| `water_activity` | scalar [1]，`1`；产物水无量纲活度aW>0，由输入给定其相态参考 |
| `standard_voltage` | scalar [1]，`V`；此温度下给定标准可逆电池电压E0 |
| `thermoneutral_voltage` | scalar [1]，`V`；同一反应、温度和水相态的热中性电压Etn>0 |
| `current_density` | scalar [1]，`A/m2`；单位几何面积电流J≥0，正向消耗燃料；允许外电源强迫高电流 |
| `exchange_anode` | scalar [1]，`A/m2`；阳极有效交换电流密度j0a>0，已换算到几何面积 |
| `exchange_cathode` | scalar [1]，`A/m2`；阴极有效交换电流密度j0c>0，几何面积基准 |
| `effective_electrons_anode` | scalar [1]，`1`；对称BV动力学的有效电子数ma，精确整数1..4 |
| `effective_electrons_cathode` | scalar [1]，`1`；对称BV动力学的有效电子数mc，精确整数1..4 |
| `area_resistance` | scalar [1]，`Ohm.m2`；几何面积串联欧姆电阻RΩ≥0 |

## 输出

每个下列quantity至少出现一次，可重复请求；逻辑名及array key自由。全部float64、point、state轴，无sampling，分量规则同上。必须使用表中完整location及全部对象，不能新增输出位置、重排身份或省略分量。输出是各独立工况的稳态值，不是时间平均、单元平均或整体积分。

| quantity | 类型、单位、含义 | location |
|---|---|---|
| `reversible_voltage` | scalar [1]，`V`；由气体活度修正的Erev | `operating` |
| `cell_voltage` | scalar [1]，`V`；含活化与欧姆损失的端电压Vcell，可负 | `operating` |
| `electric_power` | scalar [1]，`W/m2`；单位几何面积向外输出电功率P=J Vcell，可负 | `operating` |
| `heat_release` | scalar [1]，`W/m2`；单位几何面积向外释放热Q=J(Etn−Vcell)，含可逆与不可逆热，可负 | `operating` |

结果HDF5只含输出array和必需IDs／时间轴，严格复制输入支持数组；不输出输入场、坐标、网格或额外数组。

## 接收限制



对象数量、参数及场值范围见各表；输入和输出场各≤2000000数值分量。正式数据还须独立核验本题模型及材料适用、给定条件相容、所请求观测存在、参考精度与预算内可达性。有限参数的极端条件仍须有稳定求值与预算内基准证据。声明检查不证明物理解、参考或数值准确性。不从目录、来源软件或隐藏配置补题意。
