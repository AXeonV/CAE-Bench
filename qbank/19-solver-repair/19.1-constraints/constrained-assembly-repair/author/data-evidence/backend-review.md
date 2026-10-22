# 最终更新结论（取代下文首轮复核的保留项）

原三项 P2 现均关闭。最终 source_repair.py 在 pristine baseline 前及候选替换后分别调用 remove_build_artifacts，删除相同 object/so；原件真实重编译和链接成功后才接触候选。新增compiler探针保留完整缓存但移走/usr/bin/c++，得到 infrastructure_error，覆盖并关闭首轮复核的缓存no-op反例。

独立解析 backend-probes-final/report.json：9/9通过；九份stdout逐项与汇总报告一致、九份stderr均为空。模式为 valid/syntax/baseline/compiler/extra/symlink/compile-timeout/runtime-timeout/generic。最终valid仍覆盖未来object/so时间戳、库hash改变、ldd断言和样例grade=1；候选编译1.970794032秒，新库SHA为ed17d4c41b0a58bbbec12113a4d49c71387fa285d94d94f170bff58a43b5e303，与oracle摘要一致。

最终版本的执行证据以 backend-probes-final 九项报告为准；下文旧 backend-probes 八项仅属首轮历史证据，不用于覆盖后续源码改动。oracle20/20、编译1.67秒及单例最大1.02秒仍属此前独立verifier的摘要；未据此声称新增基线强制重建后的20例已再次执行。

下文评分绑定和覆盖边界继续成立：20个manifest及20个grading逐一核查通过；没有读取隐藏reference.h5；库冻结的探针仅针对列出的路径os.access，未构成所有父目录/链接终点或主动setsid逃逸的完整对抗证明。普通solve.py探针通过freeze/execute/grade，不是完整普通Harbor任务端到端回归。未重跑容器、未调用模型。

最终改动及九项报告哈希：

```text
src/utils/harbor/tests/source_repair.py d2aef316bd98cadf49c159f1f0b93a8143ae7256265629a06d0f88090084196d
qbank/19-solver-repair/19.1-constraints/constrained-assembly-repair/author/backend_probe.py 47d674ac6c2e51775990c29394f845638cd77cfa9181496f0b935826a33d34ae
qbank/19-solver-repair/19.1-constraints/constrained-assembly-repair/author/verify_backend.py 1cbea2c05ff78f52a8edb1315f94454487a40195db742a733daffe9a99f2f50a
runs/benchmarks/chrono-846-repair/backend-probes-final/report.json 3219bdbc4662efdab535f7f4bdcd64ff3389398d3b505bdb0fe93d074813b1d2
runs/benchmarks/chrono-846-repair/backend-probes-final/baseline-stdout.log 0626ac6ea88159a58e283eaf1cf03e24f914f1485538b0c062674f03da38ce4b
runs/benchmarks/chrono-846-repair/backend-probes-final/compile-timeout-stdout.log 532af7648afc309684792563e6810c0b9666f9494aa0ed2a671f970bccca3d3c
runs/benchmarks/chrono-846-repair/backend-probes-final/compiler-stdout.log 1ba761882547e6e4554ceeada73d1e055c0da4306e388f5bba78d74799ce587c
runs/benchmarks/chrono-846-repair/backend-probes-final/extra-stdout.log 9debf54e9b0657504dd5dcc11bfb7352218abf398a117d91cf389d9fc3ddbe86
runs/benchmarks/chrono-846-repair/backend-probes-final/generic-stdout.log 446d6cbb3234b37352c0aa039f907df23fcb99778aae263bfd5876c2ce7f3faf
runs/benchmarks/chrono-846-repair/backend-probes-final/runtime-timeout-stdout.log f394cf6627a9c59199b7efa2c843f550b5a85a33553c9b4c9f66fc9a53ff34cf
runs/benchmarks/chrono-846-repair/backend-probes-final/symlink-stdout.log a25384ad2f825eeac90ceb749949baf5947ffa647b414d099a0cd2b9adb183fb
runs/benchmarks/chrono-846-repair/backend-probes-final/syntax-stdout.log 9328ef405e9987bd9c7bba4798947ec5f7a3fb28d601460fe5d9c798342e7300
runs/benchmarks/chrono-846-repair/backend-probes-final/valid-stdout.log c1a49d198113868d6ef2888407e7b965d885ebb0b964dee07b312ee09634ea88
runs/benchmarks/chrono-846-repair/backend-probes-final/baseline-stderr.log e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
runs/benchmarks/chrono-846-repair/backend-probes-final/compile-timeout-stderr.log e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
runs/benchmarks/chrono-846-repair/backend-probes-final/compiler-stderr.log e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
runs/benchmarks/chrono-846-repair/backend-probes-final/extra-stderr.log e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
runs/benchmarks/chrono-846-repair/backend-probes-final/generic-stderr.log e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
runs/benchmarks/chrono-846-repair/backend-probes-final/runtime-timeout-stderr.log e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
runs/benchmarks/chrono-846-repair/backend-probes-final/symlink-stderr.log e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
runs/benchmarks/chrono-846-repair/backend-probes-final/syntax-stderr.log e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
runs/benchmarks/chrono-846-repair/backend-probes-final/valid-stderr.log e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

---

以下为首轮复核记录；其保留P2已由上述最终更新关闭。

# 源码修复后端最终独立复核

日期：2026-10-23。只读取指定白名单及本次扩展范围；不读隐藏 reference.h5 或参考修复 C++，未调用 Docker/WSL 服务或收费模型。复核依据为当前源码、已有真实容器探针日志和 oracle 摘要，不等于重新执行全部测试。

## 结论

原三项 P2 中，源码大小上限和发布 README 接口已关闭；可信构建错误分类已改善，但下述缓存场景仍未关闭。真实执行证据对主要通道有明确支持，未发现评分容差与公开要求不一致。

**保留 P2：pristine baseline 预检仍可能只检查缓存。** `src/utils/harbor/tests/source_repair.py` 在删除 `rebuild_files` 前调用 baseline compile_source；此时完整缓存可使 CMake/Ninja 不执行原始 translation unit 的编译和链接。触发：固定镜像已有 object/so，但可信编译器或某个未触发依赖扫描的构建必需资源丢失；baseline no-op 成功，随后强制删除 object/so 的候选构建失败，被归入 SubmissionError(build_error)，全部 case 零分。现有 baseline 探针删 build.ninja，证明配置损坏能被识别，但没有覆盖上述缓存场景。最小建议：在写入候选前对 pristine baseline 同样删除指定 object/so，真实重编译与链接成功后再替换候选并再次删除；适当保持基线预算与总预算匹配。

## 三项 P2 复核

- 源码大小：instruction.md 明确“提交文件不得超过 1 MiB”，配置为 1048576，backend 按字节执行，关闭。
- README：publisher 的 source_repair 分支给出可信 run_case.py 命令，collect_materials 按配置选分支；普通 solve.py README 保留，关闭。未读取最终 ZIP，本结论为生成器代码层复核。
- 错误分类：baseline 失败改抛 RuntimeError，judge 只捕获 ValueError，因此不写考生完成 reward；syntax 探针产生 build_error，baseline 探针产生 infrastructure_error。上述实际分支成立，但缓存编译链缺口仍保留。

## 运行证据与覆盖边界

| 声明 | 独立核查到的证据 | 结论与范围 |
|---|---|---|
| 八个真实容器探针通过 | report 为 8/8；逐一解析8份 stdout 与 aggregate 对应项一致，8份 stderr 均空；verify_backend.py 以 docker run --rm --network none --cpus 4 --memory 8g 执行 | 支持 valid/syntax/baseline/extra/symlink/compile-timeout/runtime-timeout/generic 八模式 |
| 真实重编译 | valid 在未来 object/so mtime 下调用 backend；源码现在精确 unlink 两个 rebuild_files；旧库 SHA 24abfe…，新库 ed17d4…，新 object/so hash 已记录 | 修复此前时间戳跳过重建缺口；新库 hash 与 oracle 摘要一致 |
| 驱动使用新库 | 探针检查 ldd 指向 /opt/chrono-build/lib/libChrono_core.so，并经 run_case.py 得到样例 score=1；runtime-timeout 由修改入口为死循环产生 | 支持真实 API 经替换库执行。LD_DEBUG 子进程输出被 run_case 捕获，原始 loader trace 未存档；ldd 原文也只由断言证明 |
| UID与私有拒读 | unprivileged Python 显示 euid1000；/tests/cases、/tests/reference、/logs/verifier 不可读，实际读取 /tests/source-repair.json 得 PermissionError；编译命令有 setpriv UID/GID1000 | 支持所测路径。没有从真实 C++ 进程内直接记录 euid，但源码驱动调用继承 UID 且无提权入口 |
| 冻结 | os.access 检查提交、库文件、库目录、驱动、替换源均不可写；代码构建后 root chown/chmod | 支持被测文件与库目录；未直接尝试写/rename，也未遍历所有父目录、runner目录、软链接终点。不能将此描述为完整对抗性不可变证明 |
| 4CPU/8GiB/无网络 | cpu.max=400000 100000，memory.max=8589934592，network none命令及socket失败 | 支持该探针容器资源和网络配置；不能据此外推每个未来评测环境 |
| 编译超时与后代清理 | compile_source 使用真实 shell→sleep 子进程，0.2秒超时，子进程消失或僵尸；源码 killpg | 支持进程组清理机制。该探针直接测 compile_source helper，没有经 prepare 的 build_timeout→全case报告链 |
| 执行超时与后代清理 | 真实候选 AssemblyAnalysis 死循环，经 judge.execute 超时；扫描driver只允许消失/僵尸 | 支持真实 driver 后代终止；未测试候选主动 setsid 逃离进程组 |
| 普通solve.py兼容 | 删除 source-repair.json 后实际 freeze/execute，复制公开样例结果，grade_case score=1 | 支持通用执行路径；不是完整普通任务 Harbor artifact传输+judge.main端到端回归 |
| Oracle20/20与时长 | author/data-evidence/oracle.json：score=20/20、complete=true、候选编译1.671966657秒、单例最大1.018403754秒；新库hash与valid一致 | 支持该摘要陈述。白名单未给对应原始verifier report，只能核对摘要内部与探针交叉一致，无法重算其 report_sha256 |

## 公开要求到实际评分绑定

本次以只读脚本逐一解析20个 cases/*/problem.json 和同名 reference/*/grading.json，未读 HDF5 数值。15例 action4、2例 action1、3例 action2。每例恰有一个 direct_outputs check。输出集合按action和是否有links匹配；array=对象名；reaction 的quantity为 reaction_force、location=links，其余location=bodies；float64、三分量xyz、state轴、point语义和单位逐一通过检查。

每个实际输出quantity均绑定 pointwise/per_time/per_component：acceleration atol=.01 rtol=.0005，reaction_force atol=.05 rtol=.0005，position/velocity atol=rtol=1e-8。judge 仍按case等权全部必需输出通过计1；评分源来自实际 grading.json，未发现另设宽容差入口。40个 manifest/grading 文件SHA记录于同目录 final-review-binding-hashes.json。

runs/data-review/chrono-846/report.json 报告20 cases和2 samples、非法变体拒绝；它是本次交叉证据，隐藏数值和物理保证未在本次重审。oracle正确率不能替代独立参考数值正确性。

总预算静态公式为 max(模板,420+20*(10+30+5))=至少1320秒；当前新增baseline预算最多60秒、候选300秒，基础420秒尚留60秒。20/20时长为一次具体运行证据，不能替代最坏预算压力测试。

仍未覆盖：源码大小边界的真实容器提交；无输出、非法HDF5、超输出大小等source-repair端到端错误路径；实际评分阈值边界；候选主动逃离会话的后台进程；镜像digest与源码commit固定身份。无证据表明这些缺口已造成实际错误，不应将它们记作已通过。

## 本次审阅版本 SHA-256

```text
.agents/skills/caeoj-configure-judge/SKILL.md 249ff492000a2a3fe7fea2a0a08a3c21497f51371edc864c6d9a226d96274f15
qbank/19-solver-repair/19.1-constraints/constrained-assembly-repair/instruction.md 6fcb40465a6ce87aab863b10250b4ed2fd6fe0a8697643cb76b357547b9aa3e8
qbank/19-solver-repair/19.1-constraints/constrained-assembly-repair/DATA.md 9a80eb966fe4b6b7c0061f12a33fda59ebbd36d1669cabbc680a169263d032b0
qbank/19-solver-repair/19.1-constraints/constrained-assembly-repair/judge-config.json ec6138a53090a725b9ccf327df8480688ffe36896a8c04bb746cee1148fc9f4c
qbank/19-solver-repair/19.1-constraints/constrained-assembly-repair/harbor/source-repair.json 9a26e50f1ed4d7dfbb459cbf2b4bc3549cda870017fe40e3c1e741ce52ca6fd3
qbank/19-solver-repair/19.1-constraints/constrained-assembly-repair/harbor/task.toml ef0bad36bc744bdb4cc2455b8b1ec74883853d955689351d69cee5e449344365
qbank/19-solver-repair/19.1-constraints/constrained-assembly-repair/public/run_case.py 7e2fdabb82d9c058a860bd1fb72ca210612a33ee0a5c7774b5ab1d09afe4075e
qbank/19-solver-repair/19.1-constraints/constrained-assembly-repair/public/driver.cpp b505de2fb33ea0972712d82e4e479efa612dd12f44c11d68e87969cc508c3428
qbank/19-solver-repair/19.1-constraints/constrained-assembly-repair/author/backend_probe.py 47d674ac6c2e51775990c29394f845638cd77cfa9181496f0b935826a33d34ae
qbank/19-solver-repair/19.1-constraints/constrained-assembly-repair/author/verify_backend.py 1cbea2c05ff78f52a8edb1315f94454487a40195db742a733daffe9a99f2f50a
qbank/19-solver-repair/19.1-constraints/constrained-assembly-repair/author/data-evidence/oracle.json a8827d9f22e3c7ecd3a00cdfc1ffd82c20accbb9993f66f10b8c1a897204ab59
src/caeoj_tools/source_repair.py 71492c7e7ccd44656b9205d657cda9c796a9cace40504aeec5beaeb38dbab359
src/utils/prepare_harbor.py 805a2bfe93926cdaf6fccc91fba006a7a26e677cbd92b58f6f9b07bfc1625c34
src/utils/publish_dist.py 2f971d36593e89da4190f694f052e5308dcee4536c50d395e9ad325bbc406c3b
src/utils/harbor/tests/judge.py 28d13a7d6ab10393a5d960d1b5bf23358d57a23b1f3729fd6565adf1659fbae9
src/utils/harbor/tests/source_repair.py d2aef316bd98cadf49c159f1f0b93a8143ae7256265629a06d0f88090084196d
src/utils/harbor/tests/test.sh d1dc0539bd5fbe3fc60fd8e5f8cef4efb5cbb6a8a7c7908e79b6a1b03cf4f0d7
tests/test_harbor.py 75fb950f46d126d356c1609413e593f9fd614fe38d7bcd863f45a5592a9cf3d2
runs/data-review/chrono-846/report.json b9bdb86460486348bc41b4bbdc2e542eccd5f5f509d35f05d8b656bd780daa03
runs/benchmarks/chrono-846-repair/backend-probes/report.json 10890b858958928b737d73fc8ea710d20584138d87af1b372a8093405550edbe
runs/benchmarks/chrono-846-repair/backend-probes/baseline-stdout.log 0626ac6ea88159a58e283eaf1cf03e24f914f1485538b0c062674f03da38ce4b
runs/benchmarks/chrono-846-repair/backend-probes/compile-timeout-stdout.log 532af7648afc309684792563e6810c0b9666f9494aa0ed2a671f970bccca3d3c
runs/benchmarks/chrono-846-repair/backend-probes/extra-stdout.log 9debf54e9b0657504dd5dcc11bfb7352218abf398a117d91cf389d9fc3ddbe86
runs/benchmarks/chrono-846-repair/backend-probes/generic-stdout.log 446d6cbb3234b37352c0aa039f907df23fcb99778aae263bfd5876c2ce7f3faf
runs/benchmarks/chrono-846-repair/backend-probes/runtime-timeout-stdout.log f394cf6627a9c59199b7efa2c843f550b5a85a33553c9b4c9f66fc9a53ff34cf
runs/benchmarks/chrono-846-repair/backend-probes/symlink-stdout.log a25384ad2f825eeac90ceb749949baf5947ffa647b414d099a0cd2b9adb183fb
runs/benchmarks/chrono-846-repair/backend-probes/syntax-stdout.log 9328ef405e9987bd9c7bba4798947ec5f7a3fb28d601460fe5d9c798342e7300
runs/benchmarks/chrono-846-repair/backend-probes/valid-stdout.log 072492f316466e6d67a5b7db77f4388ba6e646dc293194932748f5ebac483e66
runs/benchmarks/chrono-846-repair/backend-probes/baseline-stderr.log e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
runs/benchmarks/chrono-846-repair/backend-probes/compile-timeout-stderr.log e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
runs/benchmarks/chrono-846-repair/backend-probes/extra-stderr.log e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
runs/benchmarks/chrono-846-repair/backend-probes/generic-stderr.log e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
runs/benchmarks/chrono-846-repair/backend-probes/runtime-timeout-stderr.log e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
runs/benchmarks/chrono-846-repair/backend-probes/symlink-stderr.log e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
runs/benchmarks/chrono-846-repair/backend-probes/syntax-stderr.log e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
runs/benchmarks/chrono-846-repair/backend-probes/valid-stderr.log e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```
