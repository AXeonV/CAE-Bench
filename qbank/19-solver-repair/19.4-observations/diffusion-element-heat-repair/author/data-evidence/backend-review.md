# repair22 Python 源码修复后端独立审阅

日期：2026-10-23。只读审阅实现与材料，未修改代码，未运行收费 Benchmark，未把正式 Oracle、数据或装配文件的存在视为验证通过。本记录仅覆盖委派允许的文件；未核对新题 source-repair.json、task.toml、judge-config.json 和正式 grading.json，因此不确认它们的最终路径绑定、资源值或评分配置。

## 结论

现有后端能够表达并实际执行本题 Python 源文件替换。初审问题1、2、4及新增预算缺口已修复；问题3所要求的本题模块绑定、缓存强制重建、权限检查和真实执行证据已由6/6容器探针及独立Oracle 16/16补足，按下文实际范围关闭。未发现仍阻断本题这条后端通路的问题。结论不覆盖整个容器安全性、其他题目、HF远端或独立公开包安装。初审与增量条目保留作证据历史，最终状态见最后一节。

## 具体问题与最小建议

### 1. [P1] 可信基线只检查语法，不能识别可信运行时损坏

位置：`src/utils/harbor/tests/source_repair.py:78-85`、`public/CMakeLists.txt:7-9`、`src/utils/harbor/tests/judge.py:81-82`、`public/run_case.py:31-35`。

`prepare()` 在替换前删除声明产物并执行 baseline CMake；本题 CMake 只调用 `py_compile.compile()`。即使 PyBaMM 的导入依赖缺失、动态库加载失败，或可信 driver 自身不能执行，该 baseline 仍可成功。替换后的执行一旦失败，`judge.execute()` 直接记录候选 `runtime_error`、零分。runtime.Dockerfile 的一次 `import pybamm` 是镜像制作检查，既未调用真实子模型，也不在逐次可信 baseline 证据中。这与题面“可信原件故障单列基础设施错误”的承诺存在缺口。

最小建议：在引入候选前，用一份已校验的合法输入执行可信原件 driver/adapter 冒烟测试，只要求成功产生协议有效输出，不要求缺陷基线数值通过；失败抛基础设施错误，保留 stderr。可由共享后端提供明确的可信预检接口，避免依靠任意候选失败后的异常文本猜原因。补一例“语法编译成功但可信依赖/driver损坏”的分类探针。

### 2. [P1] 已有解包与 context 缓存可偏离通过 SHA 验证的上游归档

位置：`author/prepare_runtime.py:36-56`、`:60-68`。

脚本校验 base/fixed tar.gz 的 SHA，但已有 `work/base`、`work/fixed` 时跳过解包，已有 `context/source` 时跳过复制。镜像实际消费 context/source，Oracle 实际复制 work/fixed 中的文件。因此重复使用 work 目录时，先前修改过的源码能够进入镜像或 Oracle，而 source.json 仍记录正确归档 SHA 与固定提交。正式证据不能仅靠该脚本的 archive 校验推断实际源码身份。

最小建议：每次从已校验归档新建暂存源码树后原子替换，或验证整个已解包树和 context/source 的内容清单；至少对实际复制的 Oracle 文件、镜像源码树记录并核验哈希。用“改动旧 context/source 后重新执行 prepare”做一个实际回归验证。

### 3. [P2] 缺少源码 → pyc → 真实导入模块的执行绑定证据与回归

位置：`src/caeoj_tools/source_repair.py:47`、`src/utils/harbor/tests/source_repair.py:84-108`、`public/CMakeLists.txt:5-9`、`tests/test_harbor.py:82-133`。

目前后端删除显式 rebuild_files、编译候选并记录源码/产物 SHA，随后冻结 build 子树。对本题而言，若配置确实把两个 `*.cpython-314.pyc` 都列入 rebuild_files，则能排除这些旧缓存直接复用。问题在于本审阅范围内现有测试仅证明 C++ 配置的装配/拒绝；没有实际执行 Python 子模型或核对模块导入路径。CMake 的 cache tag 硬编码为 cpython-314，且 find_package(Python3) 的解释器与运行时 `python` 的一致性没有显式断言。构建成功及 pyc 哈希本身不证明 editable 安装最终加载了这些源码/缓存。

最小建议：在固定镜像做一次廉价实际后端探针，记录 `sys.executable`、`sys.implementation.cache_tag`、两个模块的 `__file__`/`__cached__`，并验证位置与替换目标、rebuild_files一致；提交一个有可观察数值影响的合法改动并执行真实 driver，再用未来时间戳旧 pyc 重复确认仍加载候选。使用 `importlib.util.cache_from_source` 生成缓存路径或明确断言运行时 tag，避免未来镜像升级时静默偏离。不能仅以 unit test 的 mock 构建替代该探针。

### 4. [P2] 扩展后缀已支持 Python/Fortran，但维护能力说明仍声称限定 C++

位置：`src/caeoj_tools/source_repair.py:47`、`.agents/skills/caeoj-author-repair-question/references/backend.md:12`。

配置校验已经接受 `.py/.f/.f90/.F/.F90`，但后端指南仍写“限定 C++ 源／头文件替换”。现有测试也未覆盖这些新增允许项。维护者据文档会误判能力边界，或把当前语言扩展理解为任意语言运行服务。

最小建议：指南改为“限定声明源码替换、Linux CMake可信构建；Python需显式语法产物及导入绑定”，列明支持后缀；测试新增 `.py` 的有效配置和拒绝额外/路径型提交。Fortran 若只是预留而无实际需求，收窄为本次确有支持证据的后缀。

## 已核对的静态要求映射

| 公开要求 | 实现与本次判断 |
|---|---|
| 恰含两个普通提交文件，每个≤1 MiB | `prepare()` 比较文件名集合，逐文件拒绝链接和超限，冻结提交并记录 SHA；最终两个文件名及上限仍须核对题内配置。 |
| 原件失败基础设施、候选语法失败零分 | baseline 失败抛 RuntimeError，候选失败抛 SubmissionError，由 judge 的 ValueError 捕获转零分；构建分类链成立。可信运行故障见问题1。 |
| 忽略开发目录改动 | prepare_harbor 生成独立 verifier 镜像，指令明确仅传 `/app/submission`；不是复用 agent 可改源码树。实际 Harbor 传递行为仍需真实装配证明。 |
| 实际重建 | 两次 remove_build_artifacts 强制删除后再构建；基线构建完成仍缺声明产物时停止，避免候选承受基线故障。Python 产物清单和实际导入待问题3探针。 |
| 冻结源码与构建产物 | build.rglob 下非链接项统一 root:root、目录755/文件644或755；本题源码位于 build/source，pyc也在其下，因此都覆盖。可信 driver位于镜像默认root拥有的 `/opt/repair-driver`。需实际UID1000写入失败探针；链接项跳过不等于已证明其目标不可写。 |
| 真实子模型调用 | driver 显式调用 DiffusionElement/NoDiffusion 和 ThermalSubModel 的 get_coupled_variables，使用真实有限体积边界离散及 ParameterValues，未在 adapter 计算参考修正；静态满足调用设计，不确认 API 兼容或数值结果。 |
| 底层错误可诊断 | run_case 转发失败 driver 的 stderr；judge 保存 stdout/stderr；build 两阶段分别留日志。具备静态诊断链。 |
| 公开包隔离 | publish_dist 依赖 public-materials 显式路径及SHA，拒绝路径越界；Oracle装配仅进入solution目录，不由该路径进入agent ZIP。prepare_runtime 当前自动将 public 下所有普通文件登记为白名单，应在正式包检查实际清单。未执行独立解包安装，不能称公开包已可用。 |

## 正式绑定前所需证据

完成修复后执行一次实际镜像、实际后端和小型临时合法 fixture 即可验证框架；必须标注它不是正式数据校准。至少覆盖：有效候选真实驱动输出、错误语法/编译超时分类、可信运行时故障分类、未来时间戳缓存强制重建、UID1000不能改源码/pyc/driver、额外文件与链接拒绝。公开包独立普通安装后，从包外运行题面样例；检查系统动态库与 editable PyBaMM绑定。正式数据装配完成后另补全部case配置覆盖、Oracle判分、基线辨别力、资源及总预算实际消费；本报告不声称这些已经通过。

## 增量复核（2026-10-23）

新增获准读取题内 `harbor/source-repair.json`。确认其两个 target 位于 build/source 子树；上限为每文件1048576字节、候选构建60秒；runner为公开adapter的固定绝对路径；rebuild_files精确列出两个 cpython-314.pyc。这补足了初审配置路径绑定的待核对项，但不替代镜像执行证据。

### 已修复项

- **初审问题1：静态修复确认。** 共享配置接受维护端 `baseline_probe` 参数数组，不经过shell；prepare在引入候选前以UID1000执行并保存独立状态/stdout/stderr。新题配置真实调用固定driver的run，构造K=4、R=0、一个关闭扩散的非触发状态，检查输出名与有限数值；失败抛RuntimeError，不被judge的候选ValueError分支捕获。它可发现共同导入/驱动故障，未证明开启扩散的所有可信路径，也未包含JSON/HDF5 adapter自身的冒烟执行。此范围足以关闭初审所指“仅语法检查”的实现缺口；最终镜像故障分类探针仍待。
- **初审问题2：静态修复确认。** prepare_runtime新增verify_tree，针对已校验tar内全部常规文件计算SHA并比较实际base/fixed/context/source文件集合和内容，新增或变动普通文件会拒绝。仅允许5个明确文档链接被跳过或按目标内容精确复制，其余上游链接拒绝，实际树内符号链接也拒绝。Oracle随后从已校验fixed树复制；旧缓存不再能静默替换实际源码。委派方报告已实际验证重用缓存，本次未独立重跑该维护脚本。
- **初审问题4：文档修复确认。** backend.md已经同步C/C++、Fortran、Python后缀并明确“接受文件不等于该语言环境验证通过”，补充Python缓存tag、路径、重建与冻结要求。新增允许项/Probe配置的自动回归仍建议补齐，测试缺口归入问题3。

### 新发现：[P2] 总 verifier 预算检查遗漏 baseline_probe

位置：`src/utils/prepare_harbor.py:137-141`、`src/utils/harbor/tests/source_repair.py`中baseline-probe调用。

新增probe可独立执行最多 `min(60, build_timeout_seconds)` 秒，但prepare_harbor的minimum仍为“候选构建上限 + 60秒基线构建 + 全部case执行/评价”。对于当前60秒构建上限，允许的前置阶段最坏时间已从120秒增为180秒，现有检查却没有增加。配置在旧minimum处会被接受，实际可能被外层verifier截止中断。此处是共享预算消费者遗漏；不表示当前新题最终外层配置必然不足，本次未获准读取其task.toml和judge-config。

最小建议：配置了baseline_probe时，将其实际超时 `min(60, build_timeout_seconds)` 加入minimum；补预算等号及少1秒拒绝测试。基线build也可用同一实际min值减少计算重复；保留独立I/O和判分开销余量。

### 仍待执行的证据

问题3继续开放：最终镜像内两个模块`__file__`/`__cached__`和运行解释器cache_tag、未来时间戳缓存强制重建、候选真实数值影响、UID1000写入拒绝、可信运行故障分类、候选语法失败及最终Oracle装配执行仍需实际探针。固定driver的代码路径检查不能替代这些结果。

委派方报告真实PyBaMM加只读固定源码overlay的参考修复16/16、缺陷基线3/16，证据位于 `work/repair-22/pybamm-5859/dataset/*-report.json`。这是有价值的数值与辨别力进展；本次未独立读取该日志，不将其表述为最终镜像、可信后端或Oracle已通过。

## 第二次增量复核：预算与离线 SDK（2026-10-23）

**预算缺口静态修复确认。** prepare_harbor.py现于存在baseline_probe时增加 `min(60, build_timeout_seconds)`，与运行器实际probe timeout一致。上一轮新增P2预算遗漏关闭其实现部分，最终总预算/I/O余量及真实完成证据仍待。

**共享库路径泛化静态确认。** judge与compile_source均从配置build_directory派生lib路径，已移除judge中Chrono专用路径。本题因此使用 `/opt/pybamm-build/lib`；所需系统库是否存在及实际加载仍由镜像探针证明。

新增获准读取 `author/prepare_offline_sdk.py`，离线准备边界如下：

- Docker多阶段仅复制捐赠SDK镜像的 `/usr/local/lib/python3.14/site-packages/` 与明确的 `libgmsh.so.4.15`，未复制其 `/tests`、reference、submission、logs或源代码目录。公共driver从本题public文件复制，未另外引入参考计算器。该路径边界可静态确认，不能据此断言被复制依赖目录内部绝无额外资产。
- setuptools/wheel来自指定本地安装分发，要求WHEEL声明py3-none-any，排除pyc/__pycache__和包含..的记录，用标准wheel pack重打包。报告区分“本地安装分发重打包”与下载wheel原字节，并记录wheel哈希、捐赠SDK/求解器基线/结果镜像ID；没有把它们冒称为原始上游wheel或物理参考。
- 镜像启用PIP_NO_INDEX与本地wheel目录，构建时真实import pybamm/numpy/h5py/jsonschema/gmsh并检查gmshInitialize符号，较只验证Python包装器更有区分力。该脚本未执行题内子模型或候选重建，因此不足以关闭问题3。

**问题3的补充边界：site-packages为整体覆盖。** .pth、editable finder及sitecustomize也可能随整体目录进入镜像，亦可能覆盖同名分发；仅打印pybamm.__file__未断言它来自固定build/source。建议记录捐赠SDK包清单与重叠项，在最终镜像明确assert两个子模型模块实际路径、缓存路径和解释器cache_tag均与source-repair配置一致。当前可复用镜像ID提供身份线索，但未证明所有被复制依赖的公开资产边界；不要把“未COPY /tests”扩写为整个镜像私有材料隔离证明。此建议并入既有P2实际绑定/公开包探针缺口，不新增未经证实的泄漏结论。

委派方报告前两次独立Oracle分别因外部HTTPS依赖安装和gmsh共享库缺失而属于基础设施失败；第三次 `repair22-ecm-oracle-v4` 当时仍运行。本次仅静态复核脚本，未观察其容器结果，不将运行中状态或修复脚本存在视为最终Oracle成功，亦未触发收费模型。

## 最终证据复核（2026-10-23）

本轮实际读取 `runs/authoring/repair-22/ecm-backend-probes-v2/report.json`、本题author/backend_probe.py、归档backend-probes.json/oracle.json，以及Oracle v4原始result.json、verifier/build三份report。归档探针与原始报告内容一致；Oracle摘要与原始结果的通过状态一致。

### 版本与真实绑定

当前共享source_repair.py、judge.py和题内source-repair.json，与 `runs/harbor/tasks/diffusion-element-heat-repair/tests/` 对应装配文件逐字比较（仅归一化CRLF）一致。当前配置指向offline-sdk基线，包含gmshInitialize断言；Oracle的baseline-probe日志命令与之匹配，结果ready。

Oracle候选源码哈希与当前author/generated两个文件实际SHA完全一致：diffusion_element为 `ec81979d3b93655fac046b3a71ad0df46311a3b6db2c0f396aedf6b7ea58b95f`，thermal为 `bc7722064926f68a1f8b08c90132e219b3fc6d1c4fdfd2ceb2c6aff5a90762d8`。探针也使用相同两份源码并将运行UID1000导入后的文件/pyc哈希与该次可信构建报告绑定。不同运行的pyc哈希不同不表示源码漂移：py_compile默认缓存包含源文件时间信息，证据要求是每次运行的导入pyc与同次构建哈希一致。

本轮没有重新构建镜像；版本关联来自当前装配比较、真实运行命令、Oracle源码哈希、实际导入路径及任务结果记录。记录不包含探针镜像全部文件的完整哈希清单，因此不把它扩写为任意未来重打镜像的认证。

### 已闭合的执行证据

- valid探针给两个旧pyc设置2100年的未来mtime，再调用真实prepare；两者被删除重建，旧/新产物哈希均不同。随后真实judge.execute运行公开样例，grade_case断言满分成功。这个passed并非仅由外层退出码推断，脚本内有真实执行与判分断言。
- UID1000导入两个真实子模型，断言绝对`__file__`与`__cached__`匹配题内target/rebuild_files，cache_tag为cpython-314；源/pyc SHA与同次构建报告一致。因此关闭“SDK整体覆盖导致实际模块来源未明”的本题绑定缺口。
- 权限探针在UID1000查询os.access：submission、driver及两个源/pyc均不可写；/tests、cases、reference、logs/verifier、/probe不可读写。结合已审冻结代码，这补足了限定路径的只读检查。它是访问权限查询，未实际逐路径执行写入系统调用，也不证明全文件系统隔离。
- syntax返回build_error，extra与symlink返回invalid_submission。禁用可信numpy初始化代码后，baseline probe失败且明确被RuntimeError分支归为infrastructure_error，未被候选失败分支接纳；补足问题1的故障分类探针。
- 候选thermal模块加入import期间的无限循环，实际写出自身PID marker；judge.execute在5秒探针限额返回timeout，检查该PID已退出或为僵尸。结合共享执行器killpg代码，证明这次真实候选导入超时被清理；没有另行验证任意恶意脱离进程组的后台程序。
- valid记录cgroup cpu.max=`400000 100000`、memory.max=`8589934592`，对应4核与8GiB；单个外部socket连接失败。仅支持这次容器资源值和该网络尝试，不能外推完整网络策略安全性。

独立Oracle `repair22-ecm-oracle-v4` 的result.json明确 `verifier_environment_mode: separate`、oracle agent、reward=1.0、exception_info=null；verifier报告complete，16/16通过，包含两个公开样例的身份记录。baseline重建0.067秒、baseline真实probe1.553秒、候选重建0.070秒均成功；逐例实际执行约1.68至3.31秒，实际verifier阶段约58秒。这证明当前实际Oracle装配的可信构建、真实adapter/driver和全部16例判分链已经运行通过；不把成功运行时间当成所有候选最坏资源校准。

### 当前未决范围

本次独立后端审阅没有仍阻断该题Python后端链的P1/P2实现问题。初审问题3按上述具体探针范围关闭；无需为了形式重复同批探针。维护建议仍包括给共享配置新增项保留自动回归、独立公开ZIP普通安装验证，以及若要求覆盖候选编译超时/超限文件/后续case恢复，可补对应探针；6种现有模式未覆盖这些场景，不将它们冒称为已验证。未独立审计全部评分容差数值、所有正式输入/参考的物理正确性、依赖目录完整私有资产清单，亦未访问HF远端。前两次基础设施失败继续保留为失败历史，未据此给考生记错。本审阅未触发收费模型。
