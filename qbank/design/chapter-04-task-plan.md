# 第四章有限逐题清单

编号固定；每题交付instruction、独立DATA、评分及运行配置，按节提交和独立审阅。

| 编号 | slug | 题名 | 主要能力 |
|---|---|---|---|
| 4.1.1 | `planar-kinematics` | 平面机构约束运动学 | 刚体关节与给定驱动确定运动 |
| 4.1.2 | `planar-inverse-dynamics` | 平面机构逆动力学 | 由给定运动恢复驱动转矩 |
| 4.2.1 | `planar-multibody` | 平面约束多体动力学 | 惯性、重力、关节与约束相容演化 |
| 4.2.2 | `spatial-free-rigid` | 空间自由刚体动力学 | 三维姿态、体坐标惯性与陀螺项 |
| 4.3.1 | `elastic-connectors` | 弹簧阻尼连接动力学 | 局部锚点连接力与转动耦合 |
| 4.3.2 | `prescribed-drive` | 给定运动驱动动力学 | 部分自由度驱动下的被动响应与驱动力 |
| 4.4.1 | `normal-contact` | 圆盘法向柔顺接触 | 多候选圆盘接触、单边性与有限接触时间 |
| 4.4.2 | `regularized-friction` | 圆盘正则化摩擦接触 | 接触切向速度、旋转与摩擦耗散 |
| 4.5.1 | `normal-impact` | 圆盘无摩擦瞬时碰撞 | 二体恢复律与动量跳跃 |
| 4.5.2 | `frictional-impact` | 圆盘摩擦瞬时碰撞 | 粘滑冲量截断与自旋变化 |
| 4.6.1 | `modal-flexible` | 固定参考系柔性体模态响应 | 耦合模态质量刚度阻尼与时域响应 |
| 4.6.2 | `translating-flexible` | 平移刚体与柔性模态耦合 | 浮动平移载体与柔性模态双向惯性反馈 |

接口复用通用entities、fields、conditions及HDF5；刚体／关节身份是离散标签，不使用伪坐标或运动网格。全部物理语义在逐题DATA展开。新增声明检查归共享`caeoj_ext.multibody`；核心只补通用entities表示；不改发布器或考生命令。
