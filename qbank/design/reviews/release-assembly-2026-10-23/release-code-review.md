# 发行装配器独立审阅

## 有界复审状态

对修订版重新检查并实际运行22项release测试：通过，1项因Windows链接权限跳过。复审固定SHA：release.py `58a2654779cfd72598c2ee5ff58b3c0dbbbf2305de729fe77ae6b1fe2e6e3f8c`；test_release.py `286750149d87f989639596984cf6404cdcf3c9abf36ae72b1de8454ff02ca10a`。

此前三个P1与目录/提取P2在此版本关闭：format显式example映射、canonical selection摘要、case_id绑定及descriptor到receipt精确全集已实现；public正式case/reference与私有metadata拒绝；未选sample拒绝；输出与选中题资产不重叠、extract与release双向不重叠；跨ZIP命名空间和摘要预检，成功才写RELEASE-EXTRACT标记。空计划、重复稳定task_id和license复制后摘要也已有防护。来源checkout根下非选中空目录作为输出不直接覆盖输入，因此当前按选中资产隔离的边界可接受。

真实消费证据已阅：`runs/release-assembly/real-format-smoke.json`记录cc-1d-diffusion实际build/verify/extract后isolated Python加载正式判分及format输入成功；该证据明确不是新wheel安装或求解器执行。另阅父Agent的7类任务预装日志，不重复运行大数据装配。

**最终复审通过：**作者已追加`harbor/task.toml`：来源存在则按摘要冻结到私有qbank.zip，提取逐字节保留；整个题内harbor目录禁止进入public包。新增两测试分别验证自定义7CPU/12345MiB内容归档提取不变与公开拒绝。本审阅者实际复跑24测试通过（1项Windows链接权限跳过）。最终SHA：release.py `ba0fbc13ea5fd55ff6592a695afb71ae5eb10cea32828ef8c59cfa3adc924770`；test_release.py `f03fe90f0535635dd34e55494a8af7370f650591dd067e6ce9a2785011cb7b97`。

此前问题均关闭，可进入父Agent授权的41题流式装配及最终verify；这不提前宣称尚未执行的全量组装成功。父Agent确认普通数值样例的sample reference/grading本有公开授权，format样例无数值reference，现有实现保持这一边界。下文保留初审原始发现作为修复依据，不能再按旧结论判当前版本。

审阅范围：`src/caeoj_tools/release.py`、`tests/test_release.py`，以及只读真实第二章format样例布局。未修改实现。审阅期间作者仍在修改文件，因此以下以所描述行为和最小复现为准，修复后应重新定版核验。

结论：当前版本不宜用于宣称完整发行装配成功。12项现有单元测试通过（1项Windows symlink权限跳过），但没有覆盖真实format样例和以下负例。

## P1：真实format样例被拒绝

`_snapshot`无条件要求每个sample包含`reference/grading.json`，且descriptor的reference complete为真。实际第二章已随机化format样例只有`input/problem.json`、`input/input.h5`、`output/result.h5`；没有sample reference评分资产。24道CFDCodeBench和所选2道能力题会失败。

最小修复：按selection.kind分支处理format，不要求sample reference，完整绑定其真实descriptor内input/output资产；计分case仍严格要求reference完整。补一个来源布局一致的format样例测试，不以修改实际样例补假reference解决。

## P1：public ZIP允许携带本题隐藏参考

build对public仅禁`author/`和其他题的qbank前缀。本题的`reference/`、`cases/`、`.data-assembly.json`、`data-manifest.json`、`judge-config.json`仍可进入public；若与私有资产一致还会被认为无冲突。

实际复现：复用test_release.py fixture，将`qbank/01-science/01-test/test-task/reference/a/reference.h5`（内容`reference`）加入public及其MANIFEST，build成功。此处不是摘要错误，是公开边界未验证。

最小修复：明确public允许的题内材料集合（instruction/DATA/公开模型配置、精确所选公开sample及声明附件）与共享运行闭包；拒绝正式case/reference、回执、作者/判题配置等私有资产。补参考泄漏和额外未选sample测试。不能只禁`reference`目录，因为真实公开数值样例可有其自身声明的reference权限，应按角色处理。

## P1：receipt额外资产未反向绑定descriptor，selection身份可过期

`_snapshot`检查descriptor->receipt包含关系，但receipt->descriptor不要求相等；只要位于选中case目录，任意额外文件可被打包。也没有核对receipt.selection_sha256与当前manifest的规范摘要，或descriptor case_id与selection的绑定。

两个实际复现均成功build：

- fixture receipt.files增加`cases/a/UNBOUND.txt`并提供正确摘要；descriptor不含该资产。
- 仅把manifest.cases.a.case_id改成`different-stale`，保留旧descriptor/receipt。

最小修复：规范manifest并核对既有receipt.selection_sha256；按descriptor+样例角色推导精确应有文件集合并与receipt.files对等比较；核对case_id和descriptor内容身份。正式样例的descriptor映射与format样例不同，应复用已有data_pool机制或等价严格语义。补上述负例，确保无SHA256SUMS完成标记。

## P2：目录边界和extract完成状态

- extract拒绝target等于root或root位于target之下，但允许target位于root之下；一次提取会使后续verify因额外资产失败。应拒绝双向祖先重叠，并测试。
- build没有明确output与各source_root/task_root双向重叠检查。虽然非空输出限制拦住部分情形，仍允许在来源树内新建发行目录；应在创建目录前拒绝计划所有源范围重叠。
- extract验证最终SHA后会逐成员写入，若发现跨ZIP文件/目录前缀冲突或重叠冲突会留下半成品。当前失败有非零退出但没有独立提取完成标记；应预检两个归档的全体目标路径与冲突，然后开始写入，并明示失败目录不能运行。不得给半成品添加完成标记。

## 已有有效措施和尚未执行的边界

- 数据和归档SHA均以1MiB分块计算；qbank.zip直接从来源流式压缩，无8.3GB中间复制。公开ZIP只复制一次。
- ZIP路径遍历、绝对路径、Windows保留名/ADS、重复项、大小写碰撞、单归档文件/目录前缀冲突及链接条目已设防。
- 单独CLI使用标准库，现有测试会移除来源后调用extract，确实验证来源独立性；但fixture不证明真实闭包无作者路径依赖，仍需真实任务的独立消费。
- build末尾才写SHA256SUMS，前置校验失败不会产生正常完成标记，这一设计正确；修复负例也需保持此性质。
- 本轮未在8.3GB真实素材上执行build或提取，不推断压缩后空间和真实闭包已通过。

## 交给作者的最小验收清单

1. 完成前三项P1和目录重叠修复；补对应真实语义负例。
2. 实际从26题计划挑一个format任务，build->移走来源可访问性->CLI verify/extract->安装并加载每例输入及判分配置；不运行模型/求解器。
3. 固定release.py和测试SHA后通知复审；再执行全量流式装配。不要用人工编辑receipt、添加虚假sample reference或削减真实case规避失败。
