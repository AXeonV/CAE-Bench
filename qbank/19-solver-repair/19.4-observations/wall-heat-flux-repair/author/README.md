# 维护与验收记录

来源为 SU2 issue2347 / PR2394，固定原件与参考提交、原始 API、完整源码及 MEL 摘要见 `data-evidence/source.json`。仅应用不可压缩壁面弱残差、法向距离 helper、原生热流报告三个真实文件；不混用另一 SU2 题的基线，也不承诺该 PR 的压缩流分支。完整原件及 MEL 共 2479 个原始文件逐 SHA 核对，无差异。

`generate.py` 制作 10 个独立输入，包括四个非正交导热、四个真实非零对流和两个规定热流回归。Gmsh 4.1 节点/边身份及积分位置完整声明。`public/run_case.py` 只转换网格和边界、调用真实 INC_NAVIER_STOKES，再抽取原生 CSV 和历史热率；不采用 HEAT_EQUATION，不计算补偿热流。`independent.py` 以导热解析解和含轴向导热的平滑入口对流扩散解核查所有参考，另从实际场估计开放边界能量通量。该估计有导数截断误差，不冒称精确离散守恒。

正式作者参考 10/10 均正常收敛且独立审计 passed；原件 3/10。`data-evidence/reference-replay.json` 和 `baseline-replay.json` 保留逐例数值。倾斜粗/细两个对流输入，boundary-only 与 report-only 均 0/2，记录分别为 `boundary-only-replay.json`、`report-only-replay.json`。正交对流是三种不完整版本均通过的保留回归，不能将其单独称为缺陷检出。静止线性导热也不能单独检出仅修边界的版本。

HF 固定提交 `00ce8b1176746fe7aa3ccf9e1c184402ec805121`；官方上传回执 61 文件，随后新空缓存固定提交装配完整 62 文件，strict valid。样例 01/02 分别复用正式 01/07，身份由清单显式声明。数据未因后续构建预算校准而改变。

真实 header 编译依赖闭包共 62 TU，必须连同两静态库和 SU2_CFD 全部强制删除重建。作者先前独立测量约 102.8 秒，参考并发完整重建编译约 350 秒；两种环境结果均保留。首正式 Oracle `repair22-su22347-oracle-v1` 在可信原件 300 秒预算内仅完成 33/65 步即 build_timeout，Harbor 随后报告 RewardFileNotFound，属于基础设施失败，未进入候选评分。原始材料位于 `runs/harbor/jobs/repair22-su22347-oracle-v1/wall-heat-flux-repair__Xme6j2t/verifier/build/`。现校准为 baseline600 / candidate900 秒、verifier base2200，公开候选预算同步。

`repair22-su22347-oracle-v2` 对638026版已完成 10/10，Harbor returncode=0、exception_info=null。真实原件强制重编 244.53 秒，候选 236.48 秒；两次均完整删除重建 65 个产物，候选源码及产物 SHA 与归档绑定。`data-evidence/oracle-v2` 保存原始 verifier、trial 与 runner；68 个冻结 task 文件逐 SHA 与启动快照一致。638026版六种有限后端探针均通过，归档在`backend-probes-v1`：额外文件、原件编译失败、原件运行失败、候选语法失败、未来时间戳仍重建且逐SHA绑定/UID1000权限/禁外网、真实候选C++死循环超时及原生PID终止至Z。该有限检查不外推为穷尽安全证明。

独立数据审计发现初次作者制数未保留已清理的原生临时CSV。现以`observe_native.py`仅观察临时目录及subprocess输出，对全部十个正式输入再次调用同一固定镜像与未改公开驱动。全部输出字段与冻结reference误差严格为0；每例config、mesh、inlet、restart/surface/history CSV和stdout/stderr保存在`retained-native-formal-replay.tar.gz`，命令、PID与文件SHA在`retained-native-replay.json`。`retained-native-image-binding.json`核对完整2479文件（仅覆写已声明三修复），实际静态exe/两库与Oracle-v2字节相同。此为第二次精确正式输入重放，不将其冒称初次production原始CSV。

独立审计79个变体集中发现iterations浮点类型、非零流入口端点不连续、triangle区域类型三个SDK漏检分支。均已修正：严格JSON整数；声明`geometry:true`读取真实网格类型/坐标，拒绝非一阶quad/line，核查活动流动两入口端点连续而静止忽略。全量有效输入和负例见`integer-metadata-audit.json`、`contract-branches-audit.json`。新ZIP为`d041bdf1db275794789a233b138bbc029deb768f22971a9787c0b9316156df8d`；`contract-increment.json`证明只有checker与三份运行时/包清单衍生元数据改变，公开三文件/source-driver/样例全同。新包已在真实base容器断网普通pip安装，以安装后site-packages SDK完整消费十正式输入、两样例与参考并拒绝iterations浮点，证据在`offline-install-final`。旧638026公开包、Oracle及上述探针身份保留；旧Oracle不充作新包验证，最终有界复核与新Oracle证据分别保留。

独立设计通过 `runs/design-review/repair22-su22347/report.md`；公开题面和考试材料分别通过 `runs/candidate-review/repair22-su22347-statements/report.md`、`runs/candidate-review/repair22-su22347-exam/report.md`，最终 ZIP `638026c8158d232aea0100c0a37d117a9face22fe5e6f55dc982aebd2cf3ae78` 的预算句增量已独立复核通过。报告归档在 `data-evidence/candidate-statements-review.md`、`candidate-exam-review.md`。最终审阅状态与权威原字节报告以data-evidence/reviews/index.json及下述记录为准。

最终d041版完整独立全数据审计已通过：79变体、全部12输入的实际geometry消费及参考评分通过，三个历史SDK分支保留发现并关闭。后端独立有限审阅无配置/消费阻断，原文按SHA版本归档在`data-evidence/reviews/<kind>/<SHA>/source.txt`，`archive.json`记录原路径/字节SHA，不改报告正文身份；历史便捷MD副本不代替该原文。

最终`repair22-su22347-oracle-v3`已实际clean10/10，Harbor返回0且exception_info=null。原件145.98秒/候选142.19秒，完整62TU与两静态库/实际CFD共65产物强制重建，三源码SHA绑定generated，全部68冻结task文件与启动快照相同。原始trial/verifier/build/runner/watch及归档元数据在`oracle-v3-d041`。最新strict见`hf-final-d041-strict.json`。最终新执行证据交root与独立后端收束，不在本维护材料自行计中央完成数。

重建入口：先按 `baseline.Dockerfile` 使用公开源码/MEL 及离线 Meson1.8.3 wheel 构建原件；`runtime.Dockerfile` 仅加可信 CMake→原生 Ninja 适配及只读权限。`prepare_runtime.py --output WORK --docker DOCKER` 核对完整原件并创建参考替换上下文；原件/参考真实制数由 `replay.py` 执行。判题配置唯一归属 `harbor/source-repair.json`，数值判据归 `grading-template.json`，不复制共享执行器。

最终验收完成：公开题面与DATA、设计／盲考生、全量数据、实际参考和缺陷重放、固定HF取回、普通离线安装、可信编译与实际评分、最终d041正式Oracle及独立后端增量均已闭环。原字节权威审阅索引为[data-evidence/reviews/index.json](data-evidence/reviews/index.json)，最终后端报告为[66dd6d33e7da](data-evidence/reviews/backend/66dd6d33e7da/source.txt)。旧版本探针与失败历史保持其原身份。
