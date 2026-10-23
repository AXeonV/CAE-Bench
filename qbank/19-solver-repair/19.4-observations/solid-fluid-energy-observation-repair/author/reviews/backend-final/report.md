# MOOSE 22074 题内后端终审

结论：通过。依 configure-judge workflow/current-backend 建立公开要求→实际配置→原始执行证据映射，结合本次fresh全量数学数据审阅。仅写本审阅目录；未prepare覆盖任务、重启Oracle、重建大原生环境或调用付费模型。

## 固定源及闭包

`artifacts.py` 独立流式加载真实原归档 SHA `a4b242257c81f7b33055a260d722f77830629b3f70a53869a824787316f92dc8`、公开 `moose-source.tar.gz` SHA `728715cd2cebd2618a30f7bab222544ab3c9662feb1136e38f7cd747ad9a5cd9`。20456成员全部逐文件验证；其中原归档20058普通文件、398符号链接完整递归解析并比较实际内容。不是抽样或只信作者summary。

`built_source.py` 又在真实 `caeoj-moose22074-runtime:base` 镜像中，对 `/opt/moose-source-2022` 的上述20456文件全部SHA独立比较，零差异；目标新增C/h实际均不存在。镜像内现有编译产物和完整NS/HC原生库由真实构建日志及正式baseline强制重编证实。基线为2022父提交 `03cebc8ae93747c437f53c9905f9a7322f154211`，参考只增加PR head `b72cbaf771ac9eeb14b7c1ce7447f5235c9e7491` 的两文件，SHA分别 `eaa829c1f6d38e962036c9c698f7e738c2871f23e739ed53ef1a6d17cb007825` 和 `15dc968c33f85c73c20e0cfdb2ed3e3d310c1198bb2489853a668c534c92a59a`，与正式候选build报告一致。

该任务是补全真实缺失观测接口。12条原件原始日志逐条核验均为unknown/unregistered object；健康检查证明基线已有温度积分/能量等能力可运行，不能将缺接口称作原有PDE方程bug，也不能声称未修复基线已完成公开数值题。

## 评分与执行映射

|公开要求|实际配置/消费者|验证|
|---|---|---|
|五输出、全部时刻、逐值绝对+相对容差|12个reference/grading.json，direct_outputs、pointwise/per_time/per_component，atol1e−5/rtol1e−9，J/J/W/W/W|已装配真实SDK完整加载；fresh35变体中五量内/外阈值及等号核查|
|非有限值/缺支持数组失败|CONTRACT输出check_result→PreparedCase.evaluate|NaN/缺times/错ID/float32/展平/多initial_time均invalid_output|
|每例全部通过得1、12例等权含样例|共享judge汇总score/total_cases|正式12/12，complete=true、completed_cases=12、reward=1.0|
|恰两完整源码，每文件≤1MiB|prepared source-repair.json replacements/max_source_bytes|真实extra、symlink、oversize探针均invalid_submission|
|原件/候选各300秒真实编译|source-repair.json baseline_timeout_seconds/build_timeout_seconds；source_repair.py setpriv cmake→原生make|真实syntax为build_error；compiler基础设施故障为infrastructure_error；正式baseline22.203s/candidate18.687s|
|发现两新增文件并注册普通/AD接口|原生make发现新C/h→postprocessors_Unity；目标库与NS应用链接|manual valid的Unity发现、两个注册符号及原始build日志；4现存artifact强制重建；正式候选全12分支运行|
|基线健康错误不计考生错|baseline_probe及共享judge基础设施分支|真实baseline-runtime/baseline-sdk两故障均infrastructure_error；正式health ready，0.897s|
|每例60秒求解|judge-config timeout_seconds=60；共享运行器受限子进程|正式12例完整结束；未追加超时native求解|
|4CPU/4GiB与低权限/隔离|prepared task.toml环境4/4096；setpriv低UID/GID、clear-groups、只读保护|manual真实cpu.max=400000 100000，memory.max=4294967296，UID/GID1000/groups=[]，私有不可读，源码/库/driver/工具不可写，网络访问被拒|
|外层预算|agent2400s；verifier base900+12×(求解60+评价60+开销5)=2400s，prepared实际timeout_sec=2400|足够容纳原件300+候选300、健康检查、逐例预算和开销；正式job约138秒完成|

8模式manual probe原始文件49成员归档SHA `4b3d9c70c5ab60d0ed2fa331b8c0e2f5291c7088f8ab3733e29c4f30f2806525`；native/field/build原始210成员归档SHA `c66af7f8b3b407eb240c9d452e09a57653d997969ce9f3e5b1043adfec81879f`。本次独立逐成员SHA和尺寸全部验证。manual valid原件16.62s、候选17.37s是该manual运行实测，不与正式22.203s/18.687s混淆。

正式容器的cgroup未单独采样，manual固定镜像/相同4CPU4GiB设置的实采证据不表述成formal实采。资源配置消费者与正式执行已核验；本审阅没有额外运行资源耗尽测试。共享subreaper的独立审阅由协调方另行汇总，不扩张到本题审阅结论。

## 普通安装、发布绑定与正式生命周期

公开ZIP SHA `307d4652af831c8ccaa15ba8ef509caa2d4786a7cbd56d89479510838537b0f2` 已独立验证，43文件、两样例，无作者/隐藏case泄漏。普通pip安装在真实固定verifier镜像site-packages；先前8条真实公开CLI命令（两样例各validate-input/run_case/validate-output/grade）全部返回0且score1。本次另外在该普通安装镜像只读挂载下运行fresh12+2数据、数学及35变体，未将editable开发环境当作安装证据。

HF固定commit `cadbdde490008f7709698216c5980c17bc6bdca9` 的assembly receipt实际58文件逐SHA/尺寸与当前题目一致，strict有效。prepared `runs/harbor/tasks/solid-fluid-energy-observation-repair` 中 frozen-run声明的65文件逐SHA全一致，包含两份307d ZIP、12输入及reference、执行器、评分及候选。没有重新prepare正在运行任务。

唯一正式job `repair22-moose22074-harbor-oracle-v1` 已终态：1完成、0错误、0重试；trial `solid-fluid-energy-observation-r__bk64Vb2` exception_info=null；verifier score12/12、全部accepted、reward1.0。本审阅逐个真实result.h5读取全部7数组，包括支持量，12例每数组逐值精确等于正式reference；不是只信reward或作者摘要。原始reference-replay的每个result.csv五观测也独立与HDF5逐值精确比较。可核查 `artifacts.json` 中结果摘要、trial/job结果SHA和build证据。

本题实际数据、公开安装、可信构建及正式Oracle均完成。未发现阻断问题。方法约束仍是人工源码要求，不以文本相似度冒充证明；真实参考为原样上游PR两新增文件。
