# Basic 81–110 题面迁移设计记录

本批固定按 basic JSON 插入顺序保留 shallowWaterWithSquareBump、Cavity、Cylinder 各十题。仅交付中文题面、逐题 DATA 与轻量来源记录，不制作网格、HDF5、参考、判题配置或运行器。独立设计／考生审阅由上级任务统一协调，本记录不冒称已通过。

已逐族读完整 prompt，逐题提取初始深度、驱动速度与黏度；核读全部条件、材料、几何、setFields 和物理时刻配置。复用实际通用 physics/conditions 协议，未往 CFD profile 添加未知键。输入采用 Gmsh 实体身份与 HDF5 显式场，输出采用给定单元面积平均值。

## 改编与冲突

- 浅水：所有题保留0.001m中央方形床突起、0.001m2/s左边界流量、.01m右边界水深、旋转与滑移。除variant1外原setFields中的突起初态未随prompt调整；公开以平自由面与均匀速度精确关系覆盖遗留值，不隐藏冲突。hTotal是派生量，不另解。采用公开静水路径给出床台阶解释；尚无数值参考验证此选择与原离散结果的差别。
- 腔流：使用缩放后0.1m边长，保留k–epsilon而非以低雷诺数擅改层流。去除不被模型消费的omega与nuTilda。源nut=0属于派生字段存储初始化，不迁移成公开独立物理初态。明确标准系数与低／高y+壁函数含义；压力由源第0单元归零改为全域面积均值零，避免编号依赖。输出机械静压Pa（取rho=1 kg/m3），动量方程显式包含各向同性湍流应力；来源运动学压力需作对应转换。
- 圆柱：从几何配置补全x∈[−5,5]、y∈[−1.5,2.5]、原点半径1m孔。基础constant nu作为Cross的nu0，不覆盖广义牛顿模型；nuInf=10大于nu0保持不变，公开说明剪切增稠。端面为二维实现痕迹，去除厚度2m。
- 求解器名称、PISO/PIMPLE、离散网格数和内部时间步不迁移成物理或算法要求；输出间隔转成秒，资源未校准不伪造限制。

## 壁函数依据

用于核对源码专有名的主来源为 [OpenFOAM 10 epsilonWallFunction](https://github.com/OpenFOAM/OpenFOAM-10/blob/master/src/MomentumTransportModels/momentumTransportModels/derivedFvPatchFields/wallFunctions/epsilonWallFunctions/epsilonWallFunction/epsilonWallFunctionFvPatchScalarField.C)。本题公开给出其分支公式和角单元贡献解释，不要求考生读源码。原始FOAMBench来源身份以总任务核准仓库为准，commit和源key逐题固定。

## 覆盖清单

| 题号 | 源key | 参数（带单位） |
|---|---|---|
| 2.12.81 | shallowWaterWithSquareBump/7 | gravity=9.81 m/s2; rotation_rate=7.292e-05 1/s; initial_surface=0.07 m; inlet_flux=0.001 m2/s; outlet_depth=0.01 m; bump_height=0.001 m; start_time=0 s; end_time=100 s |
| 2.12.82 | shallowWaterWithSquareBump/6 | gravity=9.81 m/s2; rotation_rate=7.292e-05 1/s; initial_surface=0.06 m; inlet_flux=0.001 m2/s; outlet_depth=0.01 m; bump_height=0.001 m; start_time=0 s; end_time=100 s |
| 2.12.83 | shallowWaterWithSquareBump/3 | gravity=9.81 m/s2; rotation_rate=7.292e-05 1/s; initial_surface=0.03 m; inlet_flux=0.001 m2/s; outlet_depth=0.01 m; bump_height=0.001 m; start_time=0 s; end_time=100 s |
| 2.12.84 | shallowWaterWithSquareBump/5 | gravity=9.81 m/s2; rotation_rate=7.292e-05 1/s; initial_surface=0.05 m; inlet_flux=0.001 m2/s; outlet_depth=0.01 m; bump_height=0.001 m; start_time=0 s; end_time=100 s |
| 2.12.85 | shallowWaterWithSquareBump/2 | gravity=9.81 m/s2; rotation_rate=7.292e-05 1/s; initial_surface=0.02 m; inlet_flux=0.001 m2/s; outlet_depth=0.01 m; bump_height=0.001 m; start_time=0 s; end_time=100 s |
| 2.12.86 | shallowWaterWithSquareBump/4 | gravity=9.81 m/s2; rotation_rate=7.292e-05 1/s; initial_surface=0.04 m; inlet_flux=0.001 m2/s; outlet_depth=0.01 m; bump_height=0.001 m; start_time=0 s; end_time=100 s |
| 2.12.87 | shallowWaterWithSquareBump/1 | gravity=9.81 m/s2; rotation_rate=7.292e-05 1/s; initial_surface=0.01 m; inlet_flux=0.001 m2/s; outlet_depth=0.01 m; bump_height=0.001 m; start_time=0 s; end_time=100 s |
| 2.12.88 | shallowWaterWithSquareBump/9 | gravity=9.81 m/s2; rotation_rate=7.292e-05 1/s; initial_surface=0.09 m; inlet_flux=0.001 m2/s; outlet_depth=0.01 m; bump_height=0.001 m; start_time=0 s; end_time=100 s |
| 2.12.89 | shallowWaterWithSquareBump/10 | gravity=9.81 m/s2; rotation_rate=7.292e-05 1/s; initial_surface=0.1 m; inlet_flux=0.001 m2/s; outlet_depth=0.01 m; bump_height=0.001 m; start_time=0 s; end_time=100 s |
| 2.12.90 | shallowWaterWithSquareBump/8 | gravity=9.81 m/s2; rotation_rate=7.292e-05 1/s; initial_surface=0.08 m; inlet_flux=0.001 m2/s; outlet_depth=0.01 m; bump_height=0.001 m; start_time=0 s; end_time=100 s |
| 2.12.91 | Cavity/7 | density=1 kg/m3; nu=0.001 m2/s; drive_speed=2.0 m/s; start_time=0 s; end_time=10 s; Cmu=0.09 1; C1=1.44 1; C2=1.92 1; sigma_k=1 1; sigma_epsilon=1.3 1; kappa=0.41 1; E=9.8 1 |
| 2.12.92 | Cavity/6 | density=1 kg/m3; nu=0.0001 m2/s; drive_speed=2.0 m/s; start_time=0 s; end_time=10 s; Cmu=0.09 1; C1=1.44 1; C2=1.92 1; sigma_k=1 1; sigma_epsilon=1.3 1; kappa=0.41 1; E=9.8 1 |
| 2.12.93 | Cavity/3 | density=1 kg/m3; nu=0.0001 m2/s; drive_speed=1.5 m/s; start_time=0 s; end_time=10 s; Cmu=0.09 1; C1=1.44 1; C2=1.92 1; sigma_k=1 1; sigma_epsilon=1.3 1; kappa=0.41 1; E=9.8 1 |
| 2.12.94 | Cavity/5 | density=1 kg/m3; nu=1e-05 m2/s; drive_speed=2.0 m/s; start_time=0 s; end_time=10 s; Cmu=0.09 1; C1=1.44 1; C2=1.92 1; sigma_k=1 1; sigma_epsilon=1.3 1; kappa=0.41 1; E=9.8 1 |
| 2.12.95 | Cavity/2 | density=1 kg/m3; nu=1e-05 m2/s; drive_speed=1.5 m/s; start_time=0 s; end_time=10 s; Cmu=0.09 1; C1=1.44 1; C2=1.92 1; sigma_k=1 1; sigma_epsilon=1.3 1; kappa=0.41 1; E=9.8 1 |
| 2.12.96 | Cavity/4 | density=1 kg/m3; nu=0.001 m2/s; drive_speed=1.5 m/s; start_time=0 s; end_time=10 s; Cmu=0.09 1; C1=1.44 1; C2=1.92 1; sigma_k=1 1; sigma_epsilon=1.3 1; kappa=0.41 1; E=9.8 1 |
| 2.12.97 | Cavity/1 | density=1 kg/m3; nu=1e-05 m2/s; drive_speed=1.0 m/s; start_time=0 s; end_time=10 s; Cmu=0.09 1; C1=1.44 1; C2=1.92 1; sigma_k=1 1; sigma_epsilon=1.3 1; kappa=0.41 1; E=9.8 1 |
| 2.12.98 | Cavity/9 | density=1 kg/m3; nu=0.0001 m2/s; drive_speed=3.0 m/s; start_time=0 s; end_time=10 s; Cmu=0.09 1; C1=1.44 1; C2=1.92 1; sigma_k=1 1; sigma_epsilon=1.3 1; kappa=0.41 1; E=9.8 1 |
| 2.12.99 | Cavity/10 | density=1 kg/m3; nu=0.001 m2/s; drive_speed=3.0 m/s; start_time=0 s; end_time=10 s; Cmu=0.09 1; C1=1.44 1; C2=1.92 1; sigma_k=1 1; sigma_epsilon=1.3 1; kappa=0.41 1; E=9.8 1 |
| 2.12.100 | Cavity/8 | density=1 kg/m3; nu=1e-05 m2/s; drive_speed=3.0 m/s; start_time=0 s; end_time=10 s; Cmu=0.09 1; C1=1.44 1; C2=1.92 1; sigma_k=1 1; sigma_epsilon=1.3 1; kappa=0.41 1; E=9.8 1 |
| 2.12.101 | Cylinder/7 | density=1 kg/m3; nu=0.1 m2/s; drive_speed=2.0 m/s; start_time=0 s; end_time=0.5 s; nuInf=10 m2/s; cross_time=0.4 s; cross_exponent=3 1 |
| 2.12.102 | Cylinder/6 | density=1 kg/m3; nu=0.01 m2/s; drive_speed=2.0 m/s; start_time=0 s; end_time=0.5 s; nuInf=10 m2/s; cross_time=0.4 s; cross_exponent=3 1 |
| 2.12.103 | Cylinder/3 | density=1 kg/m3; nu=0.01 m2/s; drive_speed=1.5 m/s; start_time=0 s; end_time=0.5 s; nuInf=10 m2/s; cross_time=0.4 s; cross_exponent=3 1 |
| 2.12.104 | Cylinder/5 | density=1 kg/m3; nu=0.001 m2/s; drive_speed=2.0 m/s; start_time=0 s; end_time=0.5 s; nuInf=10 m2/s; cross_time=0.4 s; cross_exponent=3 1 |
| 2.12.105 | Cylinder/2 | density=1 kg/m3; nu=0.001 m2/s; drive_speed=1.5 m/s; start_time=0 s; end_time=0.5 s; nuInf=10 m2/s; cross_time=0.4 s; cross_exponent=3 1 |
| 2.12.106 | Cylinder/4 | density=1 kg/m3; nu=0.1 m2/s; drive_speed=1.5 m/s; start_time=0 s; end_time=0.5 s; nuInf=10 m2/s; cross_time=0.4 s; cross_exponent=3 1 |
| 2.12.107 | Cylinder/1 | density=1 kg/m3; nu=0.01 m2/s; drive_speed=1.0 m/s; start_time=0 s; end_time=0.5 s; nuInf=10 m2/s; cross_time=0.4 s; cross_exponent=3 1 |
| 2.12.108 | Cylinder/9 | density=1 kg/m3; nu=0.01 m2/s; drive_speed=3.0 m/s; start_time=0 s; end_time=0.5 s; nuInf=10 m2/s; cross_time=0.4 s; cross_exponent=3 1 |
| 2.12.109 | Cylinder/10 | density=1 kg/m3; nu=0.1 m2/s; drive_speed=3.0 m/s; start_time=0 s; end_time=0.5 s; nuInf=10 m2/s; cross_time=0.4 s; cross_exponent=3 1 |
| 2.12.110 | Cylinder/8 | density=1 kg/m3; nu=0.001 m2/s; drive_speed=3.0 m/s; start_time=0 s; end_time=0.5 s; nuInf=10 m2/s; cross_time=0.4 s; cross_exponent=3 1 |

## 已执行核查与边界

30题双文件与30条source记录均存在；逐题核对编号、源key、源prompt SHA-256、仓库URL及120条本地链接，JSON片段均可解析。对每族配置全键哈希分组，确认几何、物理边界、模型及时间配置在族内一致，变化范围为本清单保留的深度或速度/黏度。节静态检查通过（扫描题量随其他并行批次增加，结果见runs/foambench-import/static-basic-c.json）。统一提交入口、相对路径解析、退出码、日志、预冻结依赖和逐例无网络要求已逐题写入题面。

上述仅证明文档结构、链接及源差异覆盖；未产生实际数据或fixture，未执行数值求解、物理专用校验器、独立公开包安装或评分/资源校准，不代表数值正确或评测可运行。独立审阅由总任务接续。
