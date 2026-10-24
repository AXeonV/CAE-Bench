# RC6 环境修复实现独立审阅（阶段报告）

审阅范围是实际源码／回归测试／本地发行构建脚本；未修改这些源码、未调用模型、未更正成绩。需求账本见 dependency-audit.json 与 dependency-audit.md。以下结论以报告记录的文件SHA256为界；全容器执行证据尚待主任务提供，不把静态检查当作实际环境验收。

## 已确认的闭环方向

- release._snapshot 将既有 harbor/requirements.txt 与 harbor/task.toml 一并绑定，采用现有安全文件读取和文件摘要机制；无需改case协议或伪造数据回执。新增提取回归验证实际落盘内容与摘要，公开包混入私有环境配置仍拒绝。
- 非修复题 prepare_harbor 合并共享科学环境要求与题内要求，候选 environment 与独立 verifier tests 使用同一 effective requirements 字节；原有 SciPy 精确pin与范围要求可由pip求交。固定RC5的71份要求均仅是简单本地依赖声明，本次无相对嵌套requirements或URL路径语义被破坏证据。
- Docker构建在安装公共SDK及effective requirements后执行探针；候选context仍只包含公开agent.zip、依赖与环境探针，不复制tests隐藏数据。独立verifier模板继续单独构建，私有tests仅在其context进入。
- 探针包含5个真实Python模块导入、SciPy稀疏线性代数、h5py文件读写、Gmsh真实初始化／建模、C++链接运行、OpenMP runtime符号、HDF5开发库链接运行及MPI真实双进程，明显强于仅pip解析／import路径检查。
- build_bank.py 从已冻结本地RC5载荷硬链接构建，补回71个新环境文件。最终比较逻辑逐题限制唯一允许新增路径为 harbor/requirements.txt，并强制每个旧文件摘要、case/sample映射与所有82个原公开包保持一致，符合不改变题目／参考／评分的要求。

## 需要闭环的项目

1. **测试闭环 / P1（阶段未关闭）**：release-tests.log 为28 passed、1 skipped；harbor-tests.log 当前为30 passed、2 failed。两个失败是旧fixture仍期待空requirements和旧context文件集，必须更新为精确的新环境资产集合后重新通过；不能泛化放宽公开context不含隐藏材料的断言。
2. **两阶段真实容器消费 / P1（待实际证据）**：构建时探针不能替代每题全新候选容器＋独立network=none verifier的实际消费。最终82题均须固定公共包、包版本、镜像摘要和两阶段命令；不能共享候选安装副作用或只验证同一热容器。
3. **运行基底离线安装 / P1（设计待落地）**：交付基底镜像必须包含82个公共包要求的精确协议依赖版本，以及SciPy、全部系统能力和安装构建后端。离线安装各题包时若沿用pip默认build isolation，仍可能尝试网络拉取setuptools/wheel；应通过实际 --network none 安装验证（例如预置后端并使用 --no-build-isolation --no-deps），随后pip check和严格题目provider导入。只导入5个依赖不证明该题SDK已按正确绑定安装。
4. **能力措辞 / P2**：当前OpenMP小程序只调用 omp_get_max_threads，尚未实际执行parallel region；HDF5开发程序只调用H5open，真实文件I/O由h5py完成（通常使用wheel自带HDF5），未证明系统开发库的文件创建。建议增补parallel region与H5Fcreate/H5Fclose，或精确限定验收措辞。
5. **发行说明一致性 / P2**：mature release模板仍写“未包含求解器容器镜像”。若RC6新增科学运行基底镜像，需在最终README／catalog准确区别基底镜像、专用求解器镜像和模型执行器，避免让使用者误判实际附件；基底镜像的本地载入、task安装、断网判题及资源如何应用应有可照做步骤。
6. **基底镜像可分发性 / P2**：若将运行二进制镜像直接作为附件，应保留Debian及Python包的许可证／copyright材料或在说明中清楚指向镜像内部对应材料，不能把原题目许可账本误称为覆盖全部新二进制环境。记录镜像标签与不可变image ID／导出文件摘要，必要时分片恢复后实际 docker load 验证。

## 资格边界

通过环境探针只证明当前LinuxAMD64环境与声明能力可消费，不认证全部科学参考精度或异机时限。本次按用户指示不更正旧成绩，也不应为了环境验证追加收费模型trial。源码修复题不在当前82题发行范围，不能据本轮验证扩大声明到其专用环境。

## 审阅输入摘要

- `src/caeoj_tools/release.py`: `2e2ca91468092170db9568588037a3fd46aa6361f5e0021a84b054f64b933d95`
- `src/utils/prepare_harbor.py`: `b67263f43eb125871cecaaaeac53275f6eab1044b7572c15aa0bfcfcf291e528`
- `src/utils/harbor/environment/Dockerfile`: `929b850798359f06da023de94f594d1bddb6ed9d90f921a3d0c8b60387a9b0c5`
- `src/utils/harbor/environment/runtime-requirements.txt`: `c25255a20c8b14a7737a3a99ce194bfef34bcdb019d3fb962b9d84f21da07cb9`
- `src/utils/harbor/environment/check_environment.py`: `dd9b14ceaf15e8830f6d72bc718a1d4a3c7e7a20d26cc488f6aa780f1af16aab`
- `tests/test_release.py`: `8696b769325433dc62887fd465861e71eab4a8ac9c90287d573b15a78bb80994`
- `tests/test_harbor.py`: `12bc60cfd872332c107340c2c3d66b070c2f55b11451c6cbc407cba4448cf4ba`
- `runs/releases/rc6-authoring/build_bank.py`: `d702987d0373a67f931ebb7d6d0f5b6a34be7e791fb689fc187aa76d85733df0`


## 静态复核更新：探针与分发方案

主任务已将探针增强为实际OpenMP双线程parallel region、HDF5系统开发库H5Fcreate／close／reopen及MPI双rank Allreduce；已复读当前源码确认，原能力措辞P2关闭。新探针SHA256：`dd9b14ceaf15e8830f6d72bc718a1d4a3c7e7a20d26cc488f6aa780f1af16aab`。

RC6分发方案明确改为交付完整构建配方、固定要求与安装／预检脚本，不上传第三方运行基底镜像二进制；首次构建需要网络，构建后题目SDK安装和判题离线。因不交付二进制镜像，本阶段先前提出的镜像二进制许可／source义务扩张风险不再是发布阻碍。最终README必须反映这一具体边界，不能声称系统环境完全离线。

全82题离线安装、pip check、strict task provider与双阶段fresh容器的实际执行证据仍待复核。harbor-tests-fixed.log在本次检查时仍在运行，尚不计通过。


## 静态与产物复核更新：回归和71份环境补充

release-tests.log的28项通过、1项跳过与harbor-tests-fixed.log的32项通过、12个子测试已实际读到终态；原两条旧fixture断言闭环，P1测试项关闭。没有将早期失败日志删掉。

另独立核对实际RC6 catalog/qbank.zip/82个public ZIP，而不是只采信主任务比较脚本：82题所有旧文件的元数据、case/sample绑定保持不变；71份新增harbor/requirements.txt在实际qbank.zip中的LF归一化内容均与固定RC5源码1bfbc45一致，其余11题没有伪造额外题内环境文件。新增文件保留主机工作树原字节，部分CRLF与Git对象LF摘要不同；新RC6摘要均已逐项绑定，不把语义相同说成字节相同。82个public ZIP的实际字节摘要均与RC5相同。完整逐题证据见 implementation-artifact-checks.json。此检查不重算隐藏参考数值，也不认证参考精度。

两阶段fresh容器、离线pip安装/provider绑定及最终环境构建配方仍待实际执行／产物复核。


## 最终独立复核：通过，保留明确资格边界

已独立逐条读取最终 validation.json、164份原始stdout末行报告、164个实际CID文件及各题验证context，而非只采信汇总状态：82题×candidate/verifier各1个，164个CID互不重复，均由脚本固定network=none启动。每个context的公共包实际SHA与交付public ZIP一致；requirements字节与RC6实际qbank.zip内该题文件一致（无题内文件的11题为空），验证既有71份要求确实被消费。每个原始日志均包含“No broken requirements found.”，并完成离线装包、临时源码目录移除后从site-packages加载严格单题provider；模型和成绩更正调用均为0。完整证据见 independent-final-environment-review.json。

所有164个报告均返回相同预期Python模块版本及6项真实功能检查，包括SciPy稀疏求解、h5py读写、Gmsh初始化、OpenMP两线程、系统HDF5建文件重开、MPI双rank归约。实际验证镜像ID为 `sha256:bb901e49b30c78e2058d37fe18d5e1652b2bcfe07aa4e96b1998f26a131f3ae5`。

另独立核对负例脚本、原始stderr与落盘目录：PYTHONOPTIMIZE=1且卸载SciPy后，可信test.sh入口以非0退出，judge哨兵未执行，report.json/reward.txt均未产生。最终源码探针使用显式异常而非assert判定功能结果，源码与交付check_environment.py字节经换行归一化一致，负例记录的SHA与实际执行材料一致。final-regression.log为60 passed、1 skipped、12子测试，非旧失败日志。

交付Dockerfile的原生工具安装前缀与唯一共享源码模板一致，仅将基础image标签固定到runtime.json的digest；交付运行锁覆盖全部82公共SDK的精确依赖及共享SciPy要求。build_runtime.py、install_and_check.py和check_tasks.py组成可实际消费链；安装采用no-index/no-deps/no-build-isolation，删除临时解压源码后严格检查任务绑定。environment/README.md与发行README明确首次构建联网、无预建镜像二进制、构建后SDK安装／环境检查断网，与actual交付相符。

先前列出的发布相关P1已闭环，未发现需阻止本次环境修正版RC6发布的实现缺口。这里的通过限于环境／安装消费和冻结资产完整性：安装检查的2CPU／2GiB并不认证各题solver资源上限，未执行正式模型或校验科学参考精度；跨主机Debian仓库包可能随构建日期变化，需重新检查；源码修复题不在本次发行验证范围。按用户要求，任何旧成绩均未在此审阅中更正。

最终源码、交付环境材料与证据哈希见 implementation-review-sha256.json；此前阶段记录保留，以显示旧fixture和探针意见的闭环。
