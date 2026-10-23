# 19.1.2 OpenSees 独立最终后端审阅

日期：2026-10-23。按caeoj-configure-judge技能只读检查 `hysteretic-trial-state-repair`，只写本报告，未运行收费模型。物理参考、HF远端及考试材料审阅由相应专责记录承担，本次不重复认证。

## 结论

当前最终v3后端可验收，无阻断P1/P2发现。两个真实OpenSees材料.cpp被实际强制重编、链接到固定API driver；driver没有恢复、修正或替代材料状态。49文件真实源码闭包、正式10/10 Oracle、六探针及61路径只读检查相互支持。最终冻结资源为4CPU/4096MiB，不能称为8GiB；有限valid探针实测为2CPU/2GiB，与正式配置分开陈述。

## 公开要求到实际实现

| 要求 | 实际绑定与判断 |
|---|---|
| 只交两个.cpp | source-repair.json精确声明HystereticMaterial.cpp、HystereticSMMaterial.cpp，target为真实SRC/material/uniaxial源码；共享prepare要求精确普通文件集合，拒绝链接/额外/超限，每文件≤1048576字节，冻结并SHA绑定。 |
| 真实源码而非stub | public CMake显式编译19份真实上游.cpp及driver，包含两个材料、UniaxialMaterial、Matrix/Vector/ID、真实响应/Channel/Tagged存储等。driver仅提供OpenSees错误输出流全局集成，未提供伪造的材料、矩阵或构成关系实现。链接gc-sections剔除未使用工厂/解释器路径，不是以stub代替被测API。 |
| 增量依赖闭包 | 允许文件只有.cpp，不改header/类布局；强制删除两个实际.o与material_driver，旧依赖对象保留成熟构建。CMake真实目标和路径与rebuild_files完全对应，不存在header替换遗漏factory重编的ABI问题。删除前要求产物普通文件且非symlink、路径限定build_directory内。 |
| 固定driver调用双类 | driver分别直接构造HystereticMaterial与HystereticSMMaterial；统一execute实际执行history提交、多个不提交trial、committed+delta返回、接受、continuation、回滚、重置，六处直接调用getStrain/getStress/getTangent/getEnergy。 |
| 不纠正状态 | driver没有在返回前revert、缓存并恢复stress/tangent/energy、按阈值替换epsilon或重算功密度；只保存committed应变以按DATA生成返回目标。adapter按.17g序列化有效参数/步骤，解析六行四量、写结果；没有epsilon截断或后处理补答案。 |
| 可信原件检查/分类 | 原件先删除产物并构建，再以UID1000真实driver读取probe-input进行baseline_probe；失败RuntimeError为基础设施。候选语法失败SubmissionError→build_error，结构错误→invalid_submission，运行失败/超时按case未通过。输入/参考/评分故障先预检或抛基础设施，未计候选零分。 |
| 数值评分 | 10个实际reference/grading.json一致，direct_outputs完整绑定strain/stress/tangent_modulus/committed_work_density，pointwise/per_time/per_component。strain atol1e-19、rtol0；其余atol1e-6/1e-4/1e-8，rtol1e-10，与题面一致。每case全输出通过才计通过，分母保留全部10例及公开身份。 |
| 时限/资源 | 候选120秒、baseline构建min(60,120)=60秒、baseline probe60秒、10×(运行20+评价30)=500秒，最低740秒。judge-config自动预算300+10×55=850秒，staged实际保留共享1200秒。正式环境4CPU/4096MiB，Agent1800秒，镜像构建600秒；这些与候选120秒分别消费。 |

## 真实源码闭包与权限

source-closure-audit.json记录实际Ninja依赖48个源码/头文件，恰等于公开49文件减COPYRIGHT；全部实际镜像源码SHA匹配公开闭包。已读audit_source.py：从固定镜像ninja deps取真实依赖集，比较完整source树哈希字典，而不是只检查声明文件存在。pack_source.py固定归档权限644、root及确定时间戳，并保留COPYRIGHT。runtime基线ID `sha256:82d259b4ab35323722900047e9cab6cc2d4471fe2f4e7950ae33b9ae6f873c10`与runtime-images、闭包审计一致；不需要Index伪实现或无关完整仓库依赖。

runtime.Dockerfile将source/driver/build去除group/world写权；prepare只在构建期chown增量build给UID1000，完成后冻结整个build。实际runtime-permissions.json记录固定verifier ID `sha256:7ec1adf31eef2e3008602898288943afaff4e03011c890501df242426f1e478c`，与runtime-images一致；UID/GID1000、groups=[]，61个路径全部write=false。范围含所有闭包文件、源码父目录、driver/CMake/probe-input、编译器、运行产物及其目录；阶段明确为candidate prepare前。valid另验证prepare后两个候选源及运行产物不可写、隐藏case/reference/log不可读。权限证据为os.access查询，未逐文件实际写入，不扩写全容器安全证明。

## 最终冻结v3与正式运行

重新计算 `runs/authoring/repair-22/repair22-opensees-harbor-oracle-v3.json` 中57项staged资产SHA，全部匹配当前文件；最终agent.zip实际SHA为 `ac438c25f7416d325897acb6b763642fc27e518af2e205035d30e53bd9bc16c9`。当前instruction、DATA、driver、CMake、adapter与冻结ZIP内容一致；当前共享source_repair.py、judge.py、本题source-repair.json与staged副本一致（仅归一化CRLF）。因此采用最终公开文本的v3，未用v1/v2替代。

原始job `runs/harbor/jobs/repair22-opensees-harbor-oracle-v3/hysteretic-trial-state-repair__q5ePk6L/` 的result.json明确oracle、separate verifier、reward1、exception=null；verifier/report.json complete=true、10/10。原始baseline stdout明确编译两个真实材料.o、重链接可执行文件；baseline构建约1.170秒、真实API预检0.0069秒、候选构建1.223秒均成功。verifier阶段约54.35秒，远低于实际1200秒。

Oracle、valid及当前generated两个源码SHA分别一致：HystereticMaterial为 `9b1b9f25d0e18b85345d0cab09c53a43a43b09aa9c1a2b37c20fe90106777ad1`，HystereticSMMaterial为 `53f001b8b9f8298ee4b92ba15f300d73daf19ee1bc7be3d841ec4426331c8d9c`。Oracle与valid的两个.o和可执行文件SHA全部一致；最终material_driver为 `9cd69cd704104aa41fb2fc31c751f6b0bc9acc87b1aa652d9e7d502eeffc3d99`。固定产物包含两个真实setTrialStrain符号，实际公开SM样例由低权限driver运行并经共享grade_case满分。这里是直接链接可执行文件，不需要套用其他题的动态库ldd证明形式。

## 六种实际探针及资源边界

六份 `runs/authoring/repair-22/opensees-probe-{valid,syntax,compiler,baseline-runtime,extra,symlink}.json` 与本题backend-probes.json逐项完全一致。已复读当前backend_probe.py：

- valid给两个对象与可执行产物设置2100年mtime，再真实prepare；旧/新可执行SHA不同。真实低权限执行样例02并判分，nm检查两个真实类符号，源/产物SHA与可信构建回执绑定。
- syntax→build_error，extra/symlink→invalid_submission；移走实际/usr/bin/c++后，即使旧产物完整，原件强制构建仍失败→基础设施；移走baseline真实输入后，driver预检失败→基础设施。两种原件故障没有误计候选错误。
- valid原始cgroup实测为cpu.max=`200000 100000`、memory.max=`2147483648`，即**2CPU/2GiB**；不能冒称4CPU/4GiB或8GiB的同次测量。它证明廉价探针在该资源下成功，并非正式资源限制的cgroup采样。
- 正式v3冻结task.toml为4CPU、4096MiB、separate/no-network，Harbor实际使用该冻结任务且无资源覆盖记录；本轮未独立采样已结束正式容器的cgroup。因此正式4CPU/4GiB配置与probe2CPU/2GiB实测分别记录，不伪称相同实测，也无需为缺失正式cgroup采样重新跑Oracle。

## 历史与未验证范围

v1/v2早期公开命令/链接/资源说明问题已由当前最终公开文本修正；本次只用冻结v3确认最终材料与执行一致，不把历史包成功运行倒推为当时题面已经清楚。材料数值与状态恢复的物理参考、方法约束及考生材料审阅另有职责，10/10不替代这些审查。

本次未重跑容器或收费模型；六探针没有注入候选构建超时、运行超时/后续case恢复、超限文件或全部非法数值/容差边界。共享执行器静态有进程组超时清理，但本题没有相应实际无限循环探针，不能借用其他题结果称为本题已实测。单网络连接失败、有限权限路径和闭包SHA不证明完整安全性或所有未来构建环境。当前没有由这些未覆盖范围引出的已观察实际故障，保持明确边界，不机械重复成熟框架全套测试。
