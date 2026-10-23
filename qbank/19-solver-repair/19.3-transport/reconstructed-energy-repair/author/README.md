# 维护与验收记录

SU2 issue2602 / PR2608，固定原件 `948a5ea9c72f0625a203b4d592b141e66dfa8b48`，参考 `610c66cae8ab1df82fcb8eb4b25b7decd91e45f0`。来源/API、原件完整源码及固定 MEL 摘要见 `data-evidence/source.json`；2530 个原始文件逐 SHA 核对无差异。仅替换真实 common.hpp；不混另一题壁热流修复。U-MUSCL 投影的代数整理不作为另一个物理缺陷宣传。

直接族使用真实 CConfig/CNSVariable 存储、reconstructPrimitives 和 compressibleConservatives。七个输入覆盖二维/三维、三种限幅、一阶、负压回退和平衡态。前四个阶段焓偏差工况原件丢失约 1000J/kg，修复独立增量误差至 5.82e-11；其余保留回归两版通过。真实参考由 `replay.py` 产生，不在公开驱动写物理答案。`audit_core.py` 另以 NumPy 批量仿射插值、独立热力学定义与 Roe 正性条件完整重算七例全部七个输出字段，均通过；逐字段差值见 `full-core-independent-audit.json`。该作者核查不进入运行驱动。

另外两个输入使用固定 14k 点壁函数网格，考察 CFL400/300 下实际 2100/2600 步收敛回归。最终作者参考 9/9 完整，原生两场由 `audit_flow.py` 独立审计：非壁节点 EOS 最大相对差 9.49e-7，包含 rho*k 的 SST 总能量状态恒等差 7.02e-7；壁 q=0，无穿透；外边界 inviscid 梯形通量的质量/能量相对净差约 3.07e-4/3.21e-4。开放边界粘性功、热扩散及离散积分误差未纳入该近似，不能将其称作精确 FV 守恒。壁阶段状态差约 0.13% 继续披露。

粗壁函数网格 Cf 相比外部 TMR 低 y+ SST-V 数据低约 20%，原始数据和清单保留。TMR 仅作为模型误差背景，不是本离散的物理标答。完整 CFD 得分明确属于指定离散设置的软件收敛稳定回归，不能包装成高精度一般湍流物理解。独立设计报告已审此边界。

资源历史：最初作者外层185秒超时，真实求解仍完成，记录在 `work/repair-22/su2-2602/historical-185s-timeout/`。最终08真实569.36秒；09在作者605秒观察超时后保持原进程继续至2599步，fresh HDF5/guard/grade通过，实际约791.48秒。恢复状态 `work/repair-22/su2-2602/recovery-09.json` 明确来源，未重启或截取错误前输出，也未复用旧 HDF5。据此公开/配置 case900 秒，源码完整构建仍 baseline120/candidate300，后续实际后端需再次验证。

正式冻结驱动的完整原件九例重放已完成，3/9。08 用时375.30秒后NaN退出1；09完整执行2600步，用时726.91秒，密度/能量RMS分别为−3.014/+1.302，未通过公开残量门槛，驱动拒绝合格输出。`baseline-cfd`归档完整历史/原生stdout与实际运行状态及所有native文件SHA；`baseline-replay.json`合并同一最终runtime的七直接族和两CFD记录。早期直接族runtime记录单独保留在`baseline-core-runtime-v1-replay.json`，其后仅七廉价直接族在最终runtime重放，没有重跑两完整CFD。

HF 正式 pool-v2 共九例，固定提交 `2afd2f16816b223a9cf9444ed7d63c547ebf7fad`；官方上传 46 文件，新空缓存固定提交装配 46 文件、changed=0、complete=true，strict 校验通过。全部九例输入和参考另经题内完整 checker 与结果契约检查；最新EOS版strict校验见`hf-final-eos-strict.json`。当前公开 ZIP SHA256 为 `00070750f53895a3cf21ae362e7636a9c7c807263aa59a44bd84ec2fda4fa3e2`，45 文件，样例 01/02 对应正式 01-unlimited/06-fallback。历史1915e539至f58整数检查增量见`contract-increment.json`；f58至当前EOS输入检查/公开精确容差增量见`eos-contract-increment.json`，仅五个包成员改变，instruction/source-driver/输入/参考/评分不变。

1915e539版六种有限后端探针已通过；`backend-contract-increment.json`保留旧身份并证明新prepared仅两份agent.zip改变，可信执行器/配置/source-driver/所有数据与评分文件均同。死循环探针首次在作者注入时把上游UTF8 BOM移至文件中间，导致合成探针编译失败；原始记录保存在`runtime-timeout-bom-setup-failure`，不归因于后端。修正注入只在合成候选读取时移除开头BOM后，实际原件/候选强制重编完成，真实模板函数死循环被超时终止，PID128状态Z。

f58版已在真实base容器断网普通pip安装，证据见`offline-install-final`。`repair22-su22602-oracle-v1`的verifier完整9/9，原件61.93秒/候选76.25秒强制重编，两完整CFD实际411.71/473.83秒。Harbor随后恢复sidecar allow-all策略时docker compose返回3221225794，trial exception非空；`oracle-v1-f58-infrastructure-exception`原字节保留该异常与完整数值结果，不将其称作干净成功。

独立全数据审计107变体仅发现输入rho=p/(RT)声明漏检，现SDK只验证不修改密度，DATA明确逐项绝对1e-12kg/m3加相对1e-12容差，不检查或抹除已有阶段焓偏差。最终独立107原变体和60增量全部通过，全部11正式/样例参考grade1；七个精确payload由独立审阅者另调用真实/cache/driver-fixed保留raw JSON，七输出字段差均0。原审计脚本/数学/原生数据在`data-evidence/reviews/data-evidence`字节归档；报告权威原文在`data-evidence/reviews/data/.../source.txt`及`archive.json`，不改其原身份。

000707版在真实base容器断网普通pip安装，安装后site-packages消费九正式输入、两样例与参考契约，并拒绝iterations浮点和1%EOS错误，见`offline-install-eos-final`。`backend-eos-increment.json`证明prepared仅两份agent.zip改变；旧有限探针保留旧身份，不能称为新包实际执行。最终`repair22-su22602-oracle-v2`已干净完成9/9，returncode0、exceptionnull；原件39.002秒、候选43.876秒、健康0.677秒，两完整CFD实际254.938/430.626秒。原始runner/trial/verifier/build与52文件冻结SHA归档于`oracle-v2-000707`。独立逐值核对9实际H5共139,575值与参考完全一致；1TU、两静态库、solver与driver共5产物及源码SHA完整绑定。

直接模板与完整 CFD 分层资格、字段及物理定义在公开 DATA 中明确；作者核查见 `full-cfd-08-audit.json`、`full-cfd-09-audit.json`。独立设计通过 `runs/design-review/repair22-su22602/report.md`；最终公开题面与考试材料分别通过 `runs/candidate-review/repair22-su22602-statements/report.md`、`runs/candidate-review/repair22-su22602-exam/report.md`，归档在`data-evidence`。最终全数据审阅已通过；最终新包Oracle与后端增量、公开EOS有界盲考生复核均已通过，本题验收完成。`generate.py`、`replay.py`、`audit_flow.py` 是维护入口，`harbor/source-repair.json` 与 `grading-template.json` 唯一维护运行和数值配置。

权威原字节报告及SHA索引为[data-evidence/reviews/index.json](data-evidence/reviews/index.json)。最终执行未额外采cgroup；实际资源与隔离实测保留最初1915探针身份，并已逐SHA核对相同task.toml、执行器及全部运行配置的有界复用，不能冒称v2重新实测。旧f58收尾异常完整保留。
