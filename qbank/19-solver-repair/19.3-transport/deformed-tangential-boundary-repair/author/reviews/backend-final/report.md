# ASPECT6818 可信后端独立审阅

结论：**通过，最终Oracle与专属八项backend probes均完成独立绑定审计，未发现未决P0/P1/P2**。数据及参考独立审计见 `runs/data-review/repair22-aspect6818/report.md`。本次采用 caeoj-configure-judge 技能，读取workflow/current-backend及公开三文件，然后核查真实消费者与实际运行证据，未重新prepare活动题、未启动大build/模型或停止无关进程。

## 冻结对象与真实端到端

最终公开ZIP `9acb735ced6dcc52c86ffb187a5c7b3ae34e784713ba5b963f6d412e3e6b63ee`（40成员）、HF revision `eebdf355f381244b685814da1309e7d42296488f`。旧offline-v3继承bash ENTRYPOINT导致agent容器退出126的Oracle-v1保留为失败历史；没有将它解释成考生数值失败。生产offline-v4 ID `sha256:a87c3900fa03b34a57d65c4c1c2b9bc2d7de1354c200f1f939d927ca38d68ff5` 明确修正ENTRYPOINT/CMD，未改变原始ASPECT源码或baseline二进制；source.json已分别记录历史及生产角色。审阅者独立docker inspect确认v4前11层与v3精确相同，额外一层是1024零字节空tar的SHA；另在实际v4直接sha256sum确认baseline core/binary与独立资格摘要相同。image-identity.json保留真实镜像身份。

新 `runs/authoring/repair-22/repair22-aspect6818-oracle-v2.json` 为phase completed、returncode0，1个trial，exception_info=null，12/12 completed、12/12 passed、reward1.0。独立 `check_final.py` 对Oracle启动冻结快照内全部64个文件逐SHA核对当前prepared，全部一致；其中两个agent.zip均为上述SHA。12份input/problem.json、input.h5及reference/grading.json、reference.h5均逐SHA对题目录正式装配一致。实际trial全部12份result.h5逐key/完整数组与正式参考精确相等，非只检查report或reward。证据 `final-check.json` 的complete=true。

原件可信构建实际57.658秒，baseline健康probe0.920秒、ready；候选实际54.796秒。两次构建报告均明确删除unity_45_cxx.cxx.o与aspect-release。候选源码SHA eeb67502…，实际构建artifact SHA中程序为bdc6993c…，与已独立数值资格的reference二进制相同。

## 公开要求到消费者

|公开要求|配置、消费者及实际证据|
|---|---|
|只交core.cc≤1MiB，真实指定源码替换|harbor/source-repair.json白名单、target与max_source_bytes=1048576；source_repair.prepare检查目录精确集合、文件/非symlink和size；候选报告绑定source SHA|
|原件、候选可信重建，900秒预算|baseline_timeout_seconds=900、build_timeout_seconds=900；prepare调用remove_build_artifacts后降UID1000 cmake target aspect；实际两份构建报告及artifact摘要|
|60秒baseline健康|compile_source baseline_probe使用min(60,900)，真实原生ASPECT静态平行健康；实际ready0.920秒|
|每case60秒，评价30秒|judge-config，judge.execute传入60，独立评价worker subprocess.run(timeout=30)；实际Oracle report.limits一致，全部12case完成|
|4CPU、8GiB|harbor/task.toml继承prepared environment.cpus=4,memory_mb=8192；实际resource-corner-v4 cgroup cpu.max=400000 100000、memory.max=8589934592|
|总预算|base2100+12×(solve60+eval30+overhead5)=3240秒，prepared verifier.timeout_sec=3240；prepare additionally检查900+900+60+12×90=2940秒最低预算；真实Oracle全程约207秒|
|每点每时每分量、两项全过|各case reference/grading.json direct_outputs/pointwise/per_time/per_component；数量及单位、两套atol和rtol1e-5全量对题面；48个实际阈值变体与等号微型fixture见data-review|
|等权12case、公开2case也在分母|report total_cases12、completed12，public_cases明确01与02；judge总reward=score/len(cases)，没有排除送分case|
|基础设施错误不计考生0|prepare坏baseline/健康抛RuntimeError，candidate编译等抛SubmissionError；judge坏input/reference/config预检，评价超时/工具非预期错误raise RuntimeError；结构/数值失败score0。专属compiler/baseline-runtime实际infrastructure_error、syntax实际build_error、extra/symlink实际invalid_submission|
|降权、网络、只读保护|编译及运行setpriv reuid/regid1000、clear-groups、no-new-privs；prepare后build root所有不可写，源码/SDK/root父目录由镜像锁定，test.sh私有/tests与logs；valid实际428路径不可写、protected-include实际编译Permission denied|

4CPU8GiB实际边界资源例含128个探针、9帧、二维refinement6，使用固定原生ASPECT修复程序和公开runner、UID1000，28.649秒成功，memory.peak=296771584。此证据核对所测边界输入，未将其当成所有连续参数范围的严格最坏耗时证明。

## 共享进程清理与公开安装

prepared judge.py实际LF SHA `5595500ff6c8612f4682f4eda0cdc6521c5af94343dcba6c825bb3555141180f`；与当前共享源按prepare归一化规则逐字节相同，匹配 `runs/configure-judge/repair22-mpi-cleanup/report.md` 的独立审阅冻结对象，可有界复用其subreaper、doublefork/setsid、同UID无关sentinel存活、超时/早退后代回收与基础设施清理错误分类结论。本题额外真实native timeout probe注入ASPECT约束函数无限循环，以3秒小预算进入相同execute超时路径；返回后原生PID133含zombie彻底不存在，无关同UID sentinel仍存活。它不宣称实际等待60秒或制造不可杀D状态。

审阅者从最终ZIP普通pip构建安装到独立target，非editable。随后python -I显式仅加入安装target，caeoj与题内extension实际来自已安装目录，两公开样例完整grade=1。installation.json记录实际导入位置。真实Linux SDK及ldd依赖不可写和网络封锁由专属valid probe提供实际证据，未用Windows独立安装代替。

## 专属八项probes最终证据

`work/repair-22/aspect-6818/backend-probe-evidence-v4` 八项均complete/exit0/passed。审阅者check_probes.py逐份读取stdout JSON、对应*-state.json及*-raw/verifier/build原始报告/日志，确保嵌入reports与实际raw逐JSON一致。专属上下文agent.zip、source_repair.py、source-repair.json、judge.py、judge-config.json、selection.json与最终prepared全部逐字节相同，probe镜像 `sha256:4827bd3fbbefb93a7cbd6dd692296a3271f97f8412db9408b858bada0fb3b9c4` FROM实际offline-v4，未对活动目录prepare。probe-check.json complete=true、pending=[]。

valid把已有对象及程序mtime设置未来，仍实际删除并重新编译：baseline/candidate原始stdout都有unity45对象编译及程序链接，候选绑定和built_artifacts摘要正确；两公开sample真实grade=1。实际UID1000，network denied，cgroup4CPU/8GiB，构建memory.peak=3255836672 bytes；428个source/SDK/ldd依赖及父目录检查无可写，/tests、/logs/verifier、/probe均不可读。protected-include候选直接包含/tests/source-repair.json，编译真实Permission denied并归为build_error，原始candidate-stderr保留。

syntax→build_error；禁用编译器→infrastructure_error/Trusted baseline build failed；禁用baseline健康脚本→infrastructure_error/Trusted baseline runtime probe failed；extra/symlink→invalid_submission。旧入口126和最初resource-corner作者工作目录权限失败保留其历史边界；最终采用修正后的v4真实UID1000成功资源例，不将旧权限失败计作题内数值失败。

审阅者另开只读专属生产v4容器，以UID1000遍历source/build/SDK全部18160路径及关键父目录，os.access(W_OK)全部false。证据permission_probe.py与independent-permissions.json；只读检查没有编译、求解、修改镜像或清理无关容器。最终check_final.py再次核验64个冻结文件与12份实际H5仍完全一致。没有未决待项；本结论只覆盖本次冻结题与允许范围，不是付费Agent benchmark成绩。
