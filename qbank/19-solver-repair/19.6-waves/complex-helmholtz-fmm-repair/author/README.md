# 复波数 Helmholtz 快速算子：维护入口

来源为bempp/bempp-cl issue20、PR45；基线84345ee9ee314c85750f045c7ad38090f5ea5f26，参考头2a353ef7cf73883fd761b400691dfb82cd7f614f，ExaFMMv0.1.0固定c9ad1980d50cb6ed5d01b2d5e65c7fce51bcfb05。本题只采用exafmm.py、fmm_assembler.py、helpers.py三文件的标量接口修复。完整273+98文件逐SHA核对，保留许可证；不把上游Maxwell变更纳入题目。范围及独立设计见qbank/design/repair22-bempp20-scope.md和runs/design-review/repair22-bempp20/。公开要求由instruction、DATA及CONTRACT拥有。

## 真实执行与参考资格

12份正式参考来自固定真实库：6份点势/目标梯度，6份P1曲面强形式单层、双层、超奇异算子及外部势。点参考逐值与闭式Green核和梯度核对；曲面用未修改原始库的稠密弱算子、独立P1质量矩阵逆及16/24阶独立三角势积分核查。独立依据只验收参考，不替代原生FMM生产标答。原生调用实测15.6–126.6秒；资源为4CPU/4GiB、每例至少8GiB可用临时磁盘，不能据正式数据推断所有合法输入的最坏时间。

缺陷版完整实际重放12例，仅4个非触发控制通过，其余8例失败。D盘不足时第12例在原生调用前被保护性拒绝；后在C盘以同镜像、驱动和输入SHA完成该例，保留两次原记录。只修前两文件而保留原helpers时，真实曲面例的三算子仍失败，外部势通过，证明第三修复点不是冗余。[原始重放索引](data-evidence/replays-final/index.json)保存实际命令、日志和身份。

第一轮dataset-v1将原生GiB预计算写入768MiB tmpfs，原生未报文件截断而产生错误。独立诊断后改足量真实磁盘，同镜像/源码/输入的点例误差由0.265降至4.1e-9；失败轮未发布。合格dataset-v2、完整源码与独立数学核查的原始证据见[资格索引](data-evidence/qualification-v2/index.json)。临时磁盘实际可用空间是运行前置条件，不声称Docker已强制存储配额。

## 最终公开包、数据与判题

最终ZIP为3b2f5344125bf5679bd026bef828bbe97a44c9a132cca97a5975a25ed8d319bf，共41成员。独立数据审计发现检查器遗漏拒绝非input.h5名称，现已修正；题面也明确根目录安装后进入题目录。原生源码、驱动、输入、参考未变。独立全量数据审阅覆盖12正式例、2样例、28磁盘变体及364阈值试验，含最终安装检查器的真实隔离核验。[数据审阅](reviews/data/report.md)、[最终身份](data-evidence/public-artifacts.json)保留细节。

最终包已在断网容器普通pip安装，移走SDK源码后仍从安装产物加载全部12例/2样例；两个样例实际运行原始库，均正确判缺陷0分。见[离线安装](data-evidence/offline-install-v2/result.json)。独立考生审阅及最终文档/检查器有界闭包见reviews/candidate和reviews/data。HF固定d4011e0522e1e9dcbc8f228624fe7b1c02063928，上传79项，全新缓存重新装配77项changed0/complete，strict通过；[取回回执](data-evidence/hf-d4011e/binding.json)与数值资格分别记录。

最终Oracle-v4实际12/12、exception_info=null。72份prepared材料逐SHA复验，3489个实际返回值逐位等于参考，两处实际消费ZIP均为最终3b2f。见[最终执行绑定](data-evidence/oracle-v4-3b2f/independent-binding.json)。原始库健康检查实际执行32源点势与梯度，24.263秒ready，未用只导入或语法检查代替。三份原始/候选pyc在可信构建中强制删除并实际重建；构建后源树、字节码、独立旧库环境只读。

最终8项真实后端探针通过，覆盖点/曲面调用、未来缓存时间戳、语法错误、额外文件、符号链接、原始编译/运行基础设施故障及实际Python候选超时；验证UID1000、隐藏文件不可读、外网拒绝和4CPU/4GiB。原始记录见[探针索引](data-evidence/backend-probes-v4/index.json)。最终使用独立审阅批准的每例subreaper共享judge，LF消费SHA5595500ff6c8612f4682f4eda0cdc6521c5af94343dcba6c825bb3555141180f。

## 阶段与历史边界

最终独立后端审阅通过，整题验收完成；见[独立终审](reviews/backend-final/report.md)及其233份原始材料索引。未运行新增收费模型Benchmark。旧241b包Oracle-v1、最终3b2f旧共享后端Oracle-v3及旧7探针各保留原身份。作者曾在旧任务尚占用目录时准备新任务，v2因目录锁失败于0 trials；72文件已逐SHA恢复，失败单列[setup-v2](data-evidence/harbor-setup-v2-failed)，不算考生成绩。后续准备必须等待已有任务退出或使用实际独立目录。
