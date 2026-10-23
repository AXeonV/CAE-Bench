# 维护记录

本题唯一历史来源为 idaholab/moose#30236，修复 PR30250。固定 parent `2f53071dc31d76ee1dfdbaaafe9ef34b7f2a33dd`，PR head `8cadd3769dd51e53d52d3c664c6d14342fd81999`，merge `7f915d0ff61581d60455f7f415fe842cfa58ca98`。原始完整归档 SHA256 为 `74d581cc49e262c96152865b0f5a3e9831bf262306b2c2766918c023d21e99a5`。来源只提供动机和原始回归；题内多晶粒、多项式、节点块、端点与稀疏身份是明确设计的新增检查，不能声称全部来自 issue。

允许替换真实 `GrandPotentialSinteringMaterial.C` 和 `.h`。上游 PR 为四个守恒系数增加 φ/φφ 导数，为固相最低浓度系数增加 η/ηη 导数；它仍缺少 `hs_c_min` 的 φ–η 混合导数。作者参考在这两个文件内补充混合属性声明与 `hs'(φ)·∂ceq/∂η`，其余沿用上游。因此 `generated/` 是“上游加作者混合项”的参考，不能称上游原样补丁。完整原件、PR 原样、作者参考分别实际重放。

真实执行使用官方 MOOSE 开发环境 digest `sha256:78d1470a041e789f0ecbfba507a890e03766c8983b09176da4f9eadaf4419149` 内的 GCC12.2.1、libMesh2025.04.02、PETSc3.23。真实原件 phase_field 应用及其依赖从源编译完成。源归档没有 `.git`，原生 prebuild 记录版本未知并忽略 versioner 的 HEAD 查询错误；这不是逻辑补丁，也不影响由固定归档摘要证明源码身份。运行时基线只继承这个未修原件，加入两个公开观察器；不从私有正确参考镜像反向覆盖目标文件来制作基线。两个观察器只读取 MOOSE 属性接口和实际 libMesh DOF 身份。PETSc 原生高精度 ASCII 输出提供首个残量和解析 Jacobian；不拿有限差分 Jacobian 替代目标输出。

公开协议统一 SI，PARABOLIC 分支不消费其他分支的 eV/K 常数。输入原样传给真实材料；适配器不换单位、不补导数、不裁剪结果。对逆能量响应 C/D 的值、一二阶导数使用输入定义的特征能量 `Ev=Va·kv`、`Es=Va·ks`；原单位 atol=`1e-10/Ei` J⁻¹、rtol=1e-10。原始 `hs=1−hv` 近纯相的浮点舍入保留，所有端点和近端点用例保留。早期未采用尺度的校准尝试不是候选成绩；正式逐例 grading 由 `policy.py` 显式生成，公开 instruction 给出相同规则。

当前数值证据：

- `data-evidence/reference-replay.json`：12 个输入全部用真实材料/内核/装配生成参考，并与独立解析多项式及线性形函数积分逐项核对通过。其 `native_input_sha256` 是精确 `case.i` 字节，不是输入 HDF5；`result_sha256` 是实际参考 HDF5。参考生产容器为 UID/GID1000、2CPU/4GiB、禁网；这些作者条件与正式配置的 4CPU/4GiB 分列。
- `audit_decimal.py` 与 `data-evidence/decimal-audit.json`：不导入驱动、补丁或解析导数实现；80 位 Decimal 数值微分公共值定义，并逐节点扰动、两点 Gauss 积分独立重建全部残量和矩阵条目。覆盖所有12输入、所有20输出及其全部分量，包括夹持端点、零项和混合项。最大容差比例小于0.000247；端点中央差分跨夹持边界，有限步长截断项保留在审计数字中。
- `data-evidence/data-audit.json`：核心 SDK 加显式本题扩展核验12输入、参考、逐例评分和2个样例，7种不合法输入被拒绝。此记录与最终普通安装的考试材料验证分列，后者见下文public-cli及独立审阅。
- `data-evidence/original-replay.json`：原样 `SinteringParabolic.i` 的真实两步瞬态回归在原件、原样 PR 和作者版本执行。该记录只证明实际执行和产物，不声称独立形貌正确性或 Exodiff gold 认证。

资源和接口由 `harbor/source-repair.json`、`harbor/task.toml`、`judge-config.json` 及逐例 HF grading 消费。两个可改头/源文件的直接包含关系已查：目标头只由其实现包含，因此强制删除材料 Unity 对象、libtool 对象、真实共享库和应用，重新编译并链接。最终未来时间戳、错误分类、隔离及动态加载的真实探针证据见下文backend-probes，不以依赖说明代替。

正式数据已通过官方 pack、上传与独立新缓存固定取回：HF commit `e3180f4f7c955107dbba20247d7756cdd95a8785`，池61文件、装配58消费文件 complete=true，严格 verify 有效，原始回执为 `data-evidence/hf-assembly.json`。两个样例同时是正式计分 case，工具明确报告 public_cases，不暗减分母。公开源码包逐条审计25078文件、22,299,660字节，SHA256 `1ba9047d2fed89afc71e3ecf0c934629b9afaad45dbe79ef9272753930f948b7`；公开 ZIP 为 `04563d1ff3576d2ee759f620f3f8ae3d73dfb40a7aacab75912ccefde57e26cc`。`prepare_source.py` 可从固定 PR 文件逐字节重现已冻结作者两文件，`target-source-versions.json` 分列原件、原样 PR 和作者参考摘要。下载缓存因容量搬至C，`download-cache-reserve.json` 记录恢复路径和不变摘要；没有移动题内源码或证据。

`data-evidence/runtime.json` 记录最终真实基线运行镜像，既有依赖由锁定 Linux wheel 和 Rocky RPM 离线安装。系统 `/usr/local/bin/python` 是执行绝对虚拟环境路径的只读包装器，避免 venv 外软链接丢失 prefix；Docker 最终 SHELL 保留显式 PATH，清除原开发镜像 ENTRYPOINT，保证普通安装与 Harbor 生命周期。`public-cli.json` 记录公开 ZIP 经标准 `pip install .` 安装后、移出源码目录、UID/GID1000清空附加组及清理环境实际执行两样例共8条CLI：输入/输出验证及原生执行成功，缺陷原件两样例数值均为0分，这是应检出的结果，不是修复版成绩。模块确从 venv site-packages 导入，NumPy2.4.6/h5py3.16.0/Gmsh4.15.2/jsonschema4.26.0 与公开锁定依赖一致。

`data-evidence/backend-probes.json` 与 `backend-raw/` 保留固定 verifier image `f2994588faffcc22d2d5c0d50170dc181c3acbd08dfbf40597fc87bd6a1a785b` 上8种实际探针：future-mtime有效修复、语法错误、缺编译器、原件运行时缺失、原件SDK缺失、额外文件、软链接及超限。有效修复强制重编四个实际产物，真实新库摘要不同、ldd指向原生库且nm含目标类方法，低UID样例02得1分；有限路径不可写、私有目录不可读、一次网络连接被拒绝，并实际采到4CPU/4GiB cgroup。该权限/网络检查不外推为全容器安全证明。runtime缺失在真实原件重建之后注入，避免把应用作为重建产物缺失误称运行探针失败。v1首次权限查询用Path.exists查私有目录触发PermissionError是作者探针错误；保留失败日志，修成os.path.exists后v2八模式全部通过。原件真实重编65–147秒低于300秒。此固定镜像内的旧judge不被这八项直接调用；其源码构建后端、公开ZIP和评分策略身份保留，不能把探针伪称正式Harbor job。

唯一正式 Oracle 为 `repair22-moose30236-harbor-oracle-v1`，原始 job/trial、完整逐例报告、两次构建和健康日志、实际结果及冻结文件SHA已归档 `data-evidence/harbor-oracle-v1/`。新prepared judge SHA为 `5595500ff6c8612f4682f4eda0cdc6521c5af94343dcba6c825bb3555141180f`，正式12/12、complete=true、trial无exception、returncode0；原件151.10秒、候选151.97秒、真实健康6.64秒。正式配置4CPU/4GiB，单次构建300秒，逐输入30秒、评价30秒；实际cgroup证据来自上述固定verifier有效探针，不冒称已单独采样退休后的正式容器。未运行付费模型。

整题验收完成。最终独立设计复核、盲考生题面及考试材料、全数据与题内后端终审均通过，归档于[reviews](reviews/data-final/report.md)。独立审阅重新按公开值定义实施80位微分与逐节点两点Gauss积分，覆盖12正式例、2样例的20输出全分量；75个独立合法/非法/阈值变体有效，36份原生raw的材料CSV/真实DOF/首残量/hand-coded Jacobian重新提取吻合，全部25078源文件与固定归档、公开闭包及真实native镜像三方核对。正式12份返回H5与参考逐数组完全一致。新增临时容器又实际重跑普通安装的两样例8条CLI，site-packages身份有效，原件0分保持应有缺陷含义。见[数据终审](reviews/data-final/report.md)、[后端终审](reviews/backend-final/report.md)、[最终设计](reviews/design-final/final-followup.md)及[考生审阅](reviews/candidate-final/REPORT.md)。

最终绑定见[data-evidence/final-freeze.json](data-evidence/final-freeze.json)。八探针固定f299内的旧judge身份与正式559550的新共享入口明确分列；有界复用依据是源码构建后端、最终ZIP与策略完全相同，而新共享入口已有独立审阅及新正式12/12实际执行。没有重命名旧记录、冒充重新采样已退出容器或追加收费模型。
