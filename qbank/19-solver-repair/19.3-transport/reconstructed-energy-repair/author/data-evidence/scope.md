# 19.3.5 可压缩流重构能量一致性

固定来源su2code/SU2 issue2602→PR2608。baseline `948a5ea9c72f0625a203b4d592b141e66dfa8b48`，reference `610c66cae8ab1df82fcb8eb4b25b7decd91e45f0`，merge `74e30cf9c3521c55f471ca50b2b6a8d0e99f9fd0`；两题不同基线和独立修复，不预混另一题补丁。API原始metadata/files和原始源码归档在work/repair-22/su2-2602。

本题保留来源实质：SIMD MUSCL重构先使用梯度更新T/u/p，再用EOS重算rho；焓必须在节点已有状态上与温度和速度的增量一致，不能擅自丢弃壁模型/非线性迭代中既存的保守能量信息。只替换SU2_CFD/include/numerics_simd/flow/convection/common.hpp，不混入PR回归预期、别的题补丁或数值调参作为修复。另一个UMUSCL表达式变更代数等价，记录但不冒充独立缺陷。

计划联合两种真实入口：实际模板reconstructPrimitives与compressibleConservatives的直接状态调用，以及完整SU2_CFD的可压缩SST绝热平板收敛流场。直接调用涵盖2D/3D、两侧状态、梯度/限幅/一阶回退、MUSCL开关及壁模型迭代阶段的T-H非平衡存储（明确不是最终气体热平衡态）。参考必须真正编译该头文件产生；驱动只存储输入并调用真实SU2，不在驱动重算缺失能量。

完整CFD从上游实际14k点平板case固定输入/mesh版本出发，保持M0.2/Re5e6/SST/绝热标准壁函数。必须检查真实残差收敛、后续迭代稳定和全场，而非把10步regression预期作物理答案。独立核查至少含直接状态热力学增量恒等、EOS/守恒变量转换，真实流场质量/动量/能量平衡、壁面无穿透、Cf及速度剖面，与独立通量路径及网格/迭代收敛对照；TMR CFL3D/FUN3D SST数据用于外部物理合理性校核，并明确其低y+参考与本题wallfunction网格并非相同离散，不能直接当全场标答或无依据设容差。实际来源NASA已迁移tmbwg.github.io/turbmodels，下载原data并保留SHA。

工况族围绕节点迭代能量偏差、重构梯度和物理可接受性、壁面第一层及CFL、来流/Re/输出位置，必须保留通过直接检查但完整CFD仍错误的检出能力。是否保留全部变体及资源限时取决于真实重放；不得仅增加相同case数量充覆盖。

## 当前可行性进度（不能作为验收）

真实原版源完整离线Meson构建已完成，外部MEL固定原preconfigure指定46205ab019e5224559091375a6d71aabae6bc5b9；禁用MPI/OMP/AD/CGNS/TECIO，仅正常CPU求解器。build-baseline.log为实际逐TU日志，source未改。下文记录真实原/修重放和独立核查，正式全池及后端尚待完成。

真实构建历史：首轮编译至FSI CFlowTractionInterface.cpp时，其../../../Common相对include在原Meson搜索路径失败。未修改source，第二轮仅追加cpp_args=-I/opt/su2-source/SU2_CFD/src/interfaces，使原include通过搜索路径定位原Common头文件。build-baseline-v1.log保留首轮失败，当前build-baseline.log保留重试；不将无关构建修复计入候选补丁。

## 实际原型与评价分层（2026-10-23）

原/修两版完整真实编译及模板CNSVariable入口已完成。两侧已有焓偏差分别+1000/-500J/kg时，原件重构丢失相应信息，独立增量恒等误差-1000/+500；修复误差≤5.82e-11J/kg。driver使用真实CConfig/CNSVariable存储、真实reconstructPrimitives及compressibleConservatives，仅装填梯度/状态。

完整14k点上游平板原件1171步NaN并error exit1；仅common.hpp源修复的参考2000步exit0，rho残差-14.49、energy残差-8.99，额外100步延续稳定。非wall节点EOS关系在VTK6位输出误差内≤9.49e-7；绝热q=0。壁模型节点的T/rho/P并非同时重置的平衡态，最多0.13%差异必须按迭代存储语义解释，不能强制最终壁面采样全满足同一热平衡恒等。

严格区分计分资格：核心状态重构输出（含rhoE转换）有独立精确物理增量依据；同一指定网格/离散设置的完整CFD流场输出可作为实际收敛/稳定性软件回归，参考由真实固定修复SU2生产，需同时核查残差及延续稳定。当前粗wallfunction网格Cf比独立TMR低y+ SST-V数据低19.5..23.7%，因此该Cf不得标为高精度物理reference、不得以NASA曲线当本离散的标答；若最终要求高精度物理Cf/全场，将先增加独立支持。外部20%偏差与未做全物理验收均原样记录。正式题面和评分须清楚命名该指定离散回归，不宣称已验证一般湍流物理解。

真实header依赖仅CNumericsSIMD.cpp，参考强制删该对象、两静态库及CFD后49.4s；实际模板driver另编译。拟baseline120s、candidate300s，正式判题中真实强制重编与加载证明仍待完成。

## 拟冻结的计分边界

拟设8至10个等权独立case：约6个直接重构问题族（2D/3D、限幅路径、MUSCL关闭、物理失败回退、壁模型阶段H缺陷及梯度变化），每case若干独立边；另2至3个完整CFD指定离散稳定回归（保留原14k壁函数网格，参数变化在真实验证后确定）。直接输出为两侧T/u/p/rho/H及真实库转换后的rho/rho*u/rhoE，独立增量/状态依据可精确核验。CFD输出为原网格节点的保守量以及壁面Cf，明确属于给定离散设置和库接口的收敛回归，不称为NASA高精度物理量；NASA数据只留作者作为误差背景，不能包装进reference资格。CFD必须真实完成给定迭代并满足公开残差、有限性和延续稳定条件，不能输出十步历史或由driver直接拼装场。

该定位有意考察算法修复保持实际求解器稳定，而不是要求考生校准SST/壁函数。若独立设计认为固定离散回归仍不能作所列评分，需要在正式题面前调整评分边界，不能隐瞒20%外部Cf偏差。当前已证实原/修差异及可运行性，尚未宣称整个数据池/形式后端/所有物理工况已验收。

增补真实7族模板重放证据reconstruction-family-audit.json：2D/3D、NONE/edge/point limiter四个含阶段H偏差的问题原件误差1000J/kg，修复最大5.82e-11；MUSCLoff、负压回退两版完整原样返回，平衡态回归两版通过，所有保守量转换均独立精确核查。驱动仍调用真实库函数。

真实完整场另做外边界独立梯形通量抽查boundary-flow-audit.json：质量净差相对throughflow约3.07e-4，inviscid能量通量净差约3.21e-4；wall无穿透、q=0。报告Cf积分转壁剪切约14.042N/m，外边界inviscid流向动量净差-14.486N/m，差约.444N/m。该检查受6位VTK、粗壁网格边界积分及开放边界遗漏粘性功/热扩散影响，不等价于精确FV离散守恒证明，也不能消除NASA Cf差20%的外部偏差。它仅补足稳定回归的物理合理性证据，不升级为一般高精度RANS物理解。


## 正式制数与资源校准增量

独立设计审阅时原范围卡 SHA256 `c51eb2068ebe955d63d69899f773a56a63328d99e9edb711bf891578a5054cb1` 的完整字节另归档 author/data-evidence/design-scope-v1.md。能力和提交文件范围不变。

正式9参考齐备。完整CFD 08真实2100步、569.36秒，09保持同一原进程继续至2600步约791.48秒（作者605秒观察超时及恢复状态保留），最终正常输出及全部guard/grade通过；据此case预算900秒。两场非wall RANS总能量恒等包括rho*k，独立误差7.02e-7；这不消除已披露壁阶段及NASA Cf差异。源强制编译预算仍base120/candidate300，实际后端待消费验证。原/修核心七族正式对照已完成；完整原件正式冻结入口重放尚待运行，原上游平板NaN失败保留。
