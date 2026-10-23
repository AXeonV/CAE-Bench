# 维护状态与参考依据

作者实现、制数、HF 固定回取、正式 Harbor Oracle及独立全数据/后端审阅均已完成。独立设计、公开题面与全部公开考试材料已通过，原文分别为 data-evidence/design-review.md、candidate-statements.md、candidate-exam.md。

固定来源为 ElmerCSC/elmerfem issue870 / PR872，基线 a3f108c8580efd649e84b35842cd92a06c834331，修复 head cd35f9d23145519973ed66c62661a0298105bf3a。仅允许真实 fem/src/modules/AdvectionDiffusion.F90；reference 应用完整上游两个密度处理修改，无作者逻辑补丁。prepare_source.py 验证档案、模块散列和上游精确补丁；pack_source.py 产生必要真实源码闭包并保留许可证，完整文件清单见 source-closure.json。公开源码包已从头配置并编译真实 Core、ElmerGrid 和三个模块。

四个原始上游复现分别在基线/修复版本原样执行，记录见 original-replay.json；退出码零本身不能证明原生 norm 检验通过。另行添加原生 Output File 形成全节点诊断，明确区别于原始不改文件重放；original-full-field.json 包含对解析解的核对。keyword-consumption.json 通过非默认温度/电势变量及错误绑定反例验证实际关键词消费；公开驱动采用有效的非默认绑定。

参考生产调用实际 HeatSolve、StatCurrentSolve、AdvectionDiffusion，由原生 ASCII3 输出转换 HDF5。输入参数与节点顺序只转换，不补偿密度或修正数值。连续迁移解为 u=u0+(uL−u0)expm1(−a s)/expm1(−a)，a=zeΔφ/(kBT)，a=0 时取线性极限。Soret 解 u=u0−(DT/D)ΔT s。标准 Galerkin 在均匀网格上给相邻差比 r=(1−a/(2ny))/(1+a/(2ny))，等价 a_eff=2ny·atanh(a/(2ny))；将 a 换成 a_eff 可独立核对离散节点解。该推导不读取 Elmer 装配实现。真实求解器生产参考，连续及离散解析路径负责独立验证；基线/修复差异仅负责检出性。

正式十二例覆盖四个机制/单位交叉格、正负驱动、低/高/单位密度、零可选项、零浓度边界及稀疏标签。两组物理等价单位配对明确保留，其余材料并非上游原始输入，来源标注见 cases.json。reference-replay.json 与 defect-replay.json 分别记录实际重放、哈希语义和判题，修复版12/12，基线6/12；错误的相对质量迁移、绝对质量Soret三例各被检出，两种原本正常组合全部保留。convergence.json 的 ny=100/200/400 真二维网格重放显示连续误差相邻比4.00010、3.99994，全部节点同时满足独立离散解误差界。生产实际重放使用2CPU/2GiB离线容器，正式题目配置4CPU/4GiB，两个条件分别陈述。

官方 HF upload 提交 4148aa0822f399d96b7d6aca9e24764dcca9b7af，上传73文件。新缓存固定提交官方组装70文件、changed=0、complete=true；hf-upload.json、hf-fixed-assembly.json 是从保留完整终端记录的 raw.log 提取的末尾工具 JSON，原记录未覆盖。elmer-870-hf-strict.json 为正式 strict 核验 valid=true。两个公开样例明确与计分case复用。独立考生和数据审阅时公开 ZIP SHA256 为 9a660158718cf8b451985e8b70d684774b0b042efae20a487ab481c9035e5ba7；public-install.json 证明断网安装及两样例真实基线运行成功、得分均0。data-audit.json 记录独立安装公开严格SDK后12case全量读取/参考自判以及20非法变体拒绝。

backend-probe.json 与七份原始 elmer-870-probe-*.json 验证有效修复、语法错误、缺编译器、缺实际ElmerSolver、缺SDK、额外文件、链接提交。有效修复先把预处理缓存、对象和模块时间设至2100年，真实可信后端仍移除三者并重建；模块SHA改变，真实模块导出符号存在，UID1000运行公开样例通过。缺编译器/求解器/SDK归基础设施错误；syntax归候选编译错误，额外/链接归非法提交。探针2CPU/2GiB，网络只验证一次IPv4 TCP连接拒绝，不外推所有网络协议。UID/GID1000、清空补充组的源/库/驱动/SDK只读及隐藏输入参考不可读证据见探针和runtime-permissions.json；其固定镜像身份、执行命令及范围均有记录。runtime-images.json 固定生产runtime/reference和探针verifier镜像，baseline真实image ID以该inspect记录为准，Docker构建config摘要不是image ID。

正式 Harbor Oracle job repair22-elmer-harbor-oracle-v1 已结束，12/12、reward=1、exception_info=null；原始job、trial、verifier报告及构建报告分别归档 harbor-job-result.json、harbor-trial-result.json、harbor-verifier-report.json、harbor-build-*。harbor-oracle-v1.json 保存冻结prepared task全部文件SHA与实际命令、PID和阶段。final-configs.json 保存最终source-repair、judge及task配置字节SHA；正式4CPU/4096MiB由实际配置给出，未另采样formal容器cgroup，不冒称有该采样。此为真实Harbor生命周期证据，与手工探针分别陈述。

流程为 prepare_source.py、pack_source.py、generate.py、build_runtime.py、build_reference.py、replay.py（reference 后 defect）、convergence.py，随后官方 data pack/upload/fixed-commit assemble/strict verify、公开 ZIP 独立安装与样例执行、七模式可信后端探针和正式 Harbor Oracle。独立考生、全数据及后端报告已归档；原数值生产、公开材料、后端运行和模型成绩分别陈述。本轮未调用收费考生模型。

最终后端独立审阅通过，见backend-review.md/json、source-image-check.json及threshold-check.json。审阅者实际逐一核对2468源码文件和真实模块链接，并运行六项判分阈值/非法输出检查。全数据独立审计通过，见data-review.md及independent-data-evidence.json，完整12case与2sample的实际数组、独立离散节点数学、24项合法/非法变体、原生ASCII3转换和固定HF回取均已核查。

独立后端审阅发现题面漏写既有1 MiB提交上限，已补明。最终ZIP为79ea2a0562e2028a11685cec8cde8361b259ef09bdbcb60f180c178341116921；与上述已审公开包40条逐项比较，仅instruction和MANIFEST改变，其余38条相同，见public-version-diff.json。原考生/数据报告保留原包身份，结合该有界澄清复核覆盖最终公开版本，不冒称全部重新盲审。最终Harbor-v2重新绑定该包，12/12、completed=12、exception=null，见harbor-oracle-v2.json、harbor-v2-*.json；v1记录保留历史版本。formal-version-binding.json证明两次prepared冻结清单仅两份ZIP改变，评分/源码/数据/执行器未变。

限制：没有注入真实无限循环求解或编译超时；探针网络检查有限，不能外推整个容器安全性。失败日志只留stdout/stderr末尾各2000字符，不从尾部臆造完整失败栈。数值范围仅公开的二维条带、常密度及规定有限元，不认证任意非等温电迁移、非线性扩散、瞬态、MPI或工业多物理应用。
