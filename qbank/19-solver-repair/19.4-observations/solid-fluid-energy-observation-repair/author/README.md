# 固流能量观测能力维护记录

本题对应 idaholab/moose#22074 与 PR#22075，稳定ID `caeoj-190406`。公开接口、单位、评分及资源由题面/DATA和实际配置拥有；此处只记录来源、制作与验收事实。

来源为真实新增能力：固定父提交 `03cebc8ae93747c437f53c9905f9a7322f154211` 中没有目标 `.C/.h`、没有两个注册类型。参考是固定PR head `b72cbaf771ac9eeb14b7c1ce7447f5235c9e7491` 两个新增源文件，未添加作者逻辑补丁。`target-source-versions.json` 绑定它们的真实SHA；`prepare_source.py` 验证或从固定上游下载，绝不制造空白基线。源问题为固流能量观察缺项，不声称修了既有能量方程。

真实2022父源码与相应gitlink固定PETSc3.16.6、libMesh、MetaPhysicL/TIMPI等依赖完成原生构建。旧版与新libMesh直接组合的API失败已保留工作日志，最后采用匹配依赖，不改上游框架逻辑。`pinned-dependency-archives.json` 给出各真实源归属、提交、URL、长度和SHA；`dependencies.Dockerfile`/`native-base.Dockerfile` 给出实际构建。`build_runtime.py --rebuild-native` 可显式重建，默认验证已实际构建的固定镜像，避免无意重复大型编译。SDK系统Python3.11离线环境从固定30236运行时复用；MOOSE/libMesh/PETSc使用真实2022基线。两组库的同SONAME通过明确旧库搜索前缀消歧，不能只凭环境变量名假定加载旧库。

公开 `moose-source.tar.gz` 包含20456个固定上游真实文件、20,487,421字节，SHA `728715cd2cebd2618a30f7bab222544ab3c9662feb1136e38f7cd747ad9a5cd9`。制作时顺序读取原始209,573,649字节archive并核对SHA `a4b242257c81f7b33055a260d722f77830629b3f70a53869a824787316f92dc8`，每个保留文件又与实际native-built source逐字节核对。保留源码、许可证及必要内部普通文件链接，排除文档/gold及列出的二进制媒体；不是作者精简重写。完整逐文件绑定在source-closure证据。公开材料不含参考修复。

原始PR的q1q1.i与q2q1.i完整原样重放均返回0，稳态能量残差分别约1.0e-15W与-5.92e-14W。`original-inputs/` 保留原件，`observation-prototype.json` 保存输入SHA、原生CSV与结果。初态原例PP默认未执行给出的零不能解释为真实初态源为零。正式题输入是作者依据真实能力设计的新实验，不冒称issue原始全部历程。正式瞬态显式加入真实动量时间导数、固体热时间导数及流体INSAD热时间导数，隐式Euler，避免仅添generic热导数却漏掉SUPG强残量的瞬态状态。

正式12个参考全部由固定真实上游参考镜像运行生成，12/12原生返回0；真正未新增接口的父版本12/12均未知类型失败（0/12）。这是缺能力复现，不能把基线健康问题记成候选错误。`reference-replay.json` 的native_input_sha256指真实MOOSE case.i UTF-8字节，result_sha256指规范reference/<case>/reference.h5原字节；不是input.h5摘要。初次显式程序因ParsedPostprocessor零常数配置缺必需pp_names失败的开发记录单独保留；随后用真实Receiver(default=0)声明无Robin显式族，最终输入与参考已重新完整重放。

独立参考核验覆盖全部12例和所有输出条目：8显式场采用独立多项式/精确阶次Gauss积分；4耦合场逐单元真实PointValueSampler内部点重建Q1/Q2形函数，再独立积分两相能量、对流功率、固体源和真实外壁Robin。重建前减已知Tref减少梯度消减误差，能量积分再加回Tref，不改变实际native结果。最大显式能量差7.46e-8J、功率差1.19e-8W；耦合能量差5.46e-12J、对流功率差1.99e-12W。稳态及每个Euler步的全局能量残差也通过1e-5W核查。旧NodalValueSampler在QUAD9几何/FIRST变量无DOF中点重复前值的行为未用于审计、未越界修框架。这里只独立认证实际求得FE场上的能量观察和离散收支，不外推连续温度/速度解的独立认证。`independent-audit.json` 给出逐例全量值与误差。

核心SDK、明确任务扩展、参考自评分、两公开样例均通过；7个坏输入（RZ旋流/ζ填充、浮点整数元数据、零密度、错误单位、错误实验身份、非零初始时间）被拒。数据使用官方pack/selection/local assemble/strict通过；官方HF已上传61文件并固定commit `cadbdde490008f7709698216c5980c17bc6bdca9`；全新C缓存的固定取回/strict由Hidden持久流水线执行，真实完成回执独立保存，不能把local回执当HF证明。2个公开样例同时属于计分集合，角色重叠由case ID和摘要明确绑定。

实际后端复用通用source_repair，不引入逐题框架。新源文件由原生make首次扫描并进入既有postprocessors_Unity对象，强制重建清除的四个artifact在原件已存在，不列不存在的新独立.o。固定verifier的valid探针已真实通过：futuremtime四artifact仍删除、原件16.62s及健康0.77s、候选17.37s；两个新类型computeQpIntegral符号同时存在于真实Unity.o与库，输出库SHA改变。低UID1000/GID1000/groups=[]运行两样例共8条普通安装公开CLI全部成功、数值score1，依赖来自实际site-packages。私有tests/reference/logs不可读、共享源/依赖/驱动/二进制不可写、单次外连被network-none拒、cgroup实际4CPU/4GiB。八种模式已全部通过：valid、syntax、compiler、baseline-runtime、baseline-sdk、extra、symlink、oversize；分类分别为成功、候选build_error、三类infrastructure_error和三类invalid_submission。49个原始文件保存在无损backend-raw.tar.gz及逐文件SHA清单，实际探针条件固定4CPU/4GiB。公开8条CLI来自正常离线pip安装后的site-packages，另有public-installation.json低UID路径和版本查询补证。

最终公开ZIP候选SHA `307d4652af831c8ccaa15ba8ef509caa2d4786a7cbd56d89479510838537b0f2`，43文件、2样例。纯设计最终审阅与全新独立考生公开材料审阅已通过；独立全数据/后端审阅及正式Harbor Oracle尚待完成，不计最终验收。正式Harbor与固定verifier手工探针证据将分别标识，不混称官方job；题内`.gitattributes`保护冻结字节，Git索引SHA在主整合提交时另核验。

最终HF固定cadbdde490008f7709698216c5980c17bc6bdca9，61上传文件，全新C缓存58项装配及strict通过。唯一正式Oracle repair22-moose22074-harbor-oracle-v1真实12/12、exception_info=null；65份prepared文件逐SHA相符，12份实际返回HDF5全部7数组逐值等于参考。正式原件22.203秒、候选18.687秒、健康0.897秒，与手工探针测量分列。完整真实trial/build/case日志、输出与原始字节摘要见[data-evidence/harbor-oracle-v1](data-evidence/harbor-oracle-v1/binding.json)。

独立终审从公开定义另写单项式反导数及物理坐标Q1/Q2重建，核验全部12输入/2样例、35个变体、全部时刻五积分与Euler能量账；20456原始/公开/实际built源码及HF58文件全SHA闭合。见[数据终审](reviews/data-final/report.md)、[后端终审](reviews/backend-final/report.md)及[最终冻结](data-evidence/final-freeze.json)。正式退休容器cgroup未单独采样，资源实采来自同配置固定手工探针；两者不混称。本轮未新增收费模型Benchmark。
