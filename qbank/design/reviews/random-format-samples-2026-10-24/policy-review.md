# 统一随机格式样例：发布策略与角色隔离审阅

审阅范围：本轮 release.py、publish_dist.py、format_examples.py、三个样例生成器及相关测试 diff；只读审阅代码与资产，唯一新增文件为本报告。未运行模型、数值 solver 或 HF 操作。

## 结论

生产代码未发现阻断性缺陷。启用 public_sample_policy=random-format-only 的当前82题计划要求每个样例显式声明format，公开MANIFEST声明完全匹配，公开样例资产完整且不能混入reference。正式grading代码没有改变，格式示例的发布分支不调用数值判分属于现有角色设计，不放宽正式case判题。

当前工作树审阅时两项测试fixture仍需修正并重跑；详见下文。不能把现有测试日志描述为全通过。

## 实际独立验证

- 读取 runs/uniform-samples/plan.json：82题、96例全部显式format，策略已启用。
- 对比 runs/prepublication-review-rc2/reviewed-plan.json：82题的正式case名与case_id全部不变；其余78题samples所有现存文件逐字节一致。
- 对 conversion-report.json 中四题437个正式input/reference文件逐项重新计算SHA-256：全部与转换基线匹配。该范围包含grading.json及原数值reference文件。
- 用 tests/test_release.py 的临时纯字节fixture独立构造5条路径：完整format包通过；缺sample_kinds、错误graded声明、缺output均被对应guard拒绝；额外sample/reference资产被此前的精确资产选择guard拒绝。没有向公开ZIP加入example.json。
- 独立提取并执行sample_kind函数的临时文件测试：单题及多题公开MANIFEST恢复format成功；无声明的其他样例仍为graded；作者data-manifest的显式graded优先于公开MANIFEST。
- 已读release-tests.log：27项，OK，跳过1项。已读generator-tests.log：5 passed、23 deselected、2 subtests passed。其输出只证明这些测试实际覆盖的路径。

## 发现与待闭环项

1. [P2] tests/test_publish.py:test_quantity_policy_runs_from_extracted_bundle_with_varying_logical_names：从解压公开包造数值角色fixture时，numerical_role_fixture只移除example.json并创建reference；根MANIFEST仍声明format。重新发布按公开MANIFEST正确保留format角色，reference不会打包，随后grade命令失败。应在该测试的显式角色变更中同步更新根公开MANIFEST的sample_kinds，保持产品逻辑按唯一声明恢复角色。不能通过优先检测reference目录或额外打包未绑定example.json修复。
2. [P2] tests/test_harbor.py:test_instruction_handles_mixed_sample_examples：旧日志中的fixture仅把sample01转为graded，sample02现在仍是format，因此预期一个“完整提交示例”不成立。审阅中已看到工作树改为把两例都建立numerical_role_fixture，需以新重跑结果闭环。
3. [P3] 建议把本次独立执行的缺/错公开sample_kinds与漏output负例固化为release回归测试。目前提交中的新增policy测试主要覆盖显式format的成功路径及数值角色拒绝路径，缺少这几项guard各自的稳定回归覆盖。

format-publish-harbor-tests.log本轮初次运行结果：44 passed、12 subtests passed、2 failed；失败就是前两项。该日志产生后工作树仍在修正，因此本报告不把旧日志失败当成未更改生产代码的缺陷。

## 边界与解释

- 保留ID与资产的比较基线是旧reviewed-plan指向的RC资产，不是Git HEAD。smoke-test相对HEAD已有11个case_id差异且HEAD尚无样例；本轮转换与旧RC相比较均保留，不能把“相对RC不变”写成“相对HEAD不变”。
- 公开角色保存在MANIFEST，不需要将维护用example.json加入公开ZIP。作者侧marker、data-manifest和公开MANIFEST具有分阶段来源与明确优先序。
- format_examples仅由公开input声明确定形状、dtype和支撑轴；float64/int64/bool分别随机生成值，随后调用write_result及结构校验。三个生成器改动保持正式case参考生成路径，仅样例不再求解或读取参考。
- 随机输出可能偶然命中正确值，因此承诺应是“不保证数值正确”，不能声称“每项数值必错”。
- 本报告不证明物理参考准确、资源达标、82题全部真实数值判题通过、HF已更新，亦未执行新的全量82题release build。公开内容与资源完整性另由发布包审阅覆盖。

## 复核追加：初轮两项失败已关闭

已只读检查最终 format-publish-harbor-fixed-tests.log、generator-report.md 及两处当前测试fixture代码，未重新运行测试或solver。

- 第一项已关闭：quantity-policy测试现在显式将解压根MANIFEST的全部sample_kinds更新为graded，与它主动建立的数值角色fixture一致；没有改变sample_kind的生产恢复逻辑，也没有增加公开example.json。
- 第二项已关闭：Harbor混合示例测试现在对两例建立内部数值角色fixture，再移除sample01的可选输出，保留一个完整提交示例的原断言。
- 定点重跑日志显示2 passed in 35.34s；结合初轮44 passed与12 subtests passed，这46项format/publish/Harbor测试都有对应通过运行。此表述是分批运行的联合覆盖，不是声称最终全套重跑。

原发现保留作为修复证据。当前没有尚未关闭的P2项；P3 guard负例固化建议保留，不影响本次发布策略审阅结论。生成器验证与数值/资源验证的边界仍按前文及generator-report.md说明。

## 追加窄范围审阅：PDEBench生成链

只读审阅最后追加的 src/utils/PDEBench/pipeline.py、src/utils/PDEBench/README.md、tests/test_pdebench_prepare.py，并对照当前通用grading_policy.materialize_references实现与pdebench-offline-tests.log；未改代码、下载或执行solver/模型。

未发现新增阻断性问题：

- prepare_entry的public分支把输入移入sample后，依据build_key前16位确定随机种子调用统一randomize_example，不再将私有reference复制为公开output。format_example生成证据同时写入私有certificate及author/prepared记录；返回状态仍取reference_prepared/reference_pending，随机输出不提升参考就绪状态。
- 原official-candidate、审核reference、certificate仍在reference/sample-certificates/<id>，样例目录只安装input、output及作者侧角色marker。prepare_entry的record继续绑定公开与私有文件摘要，用于完整复用检查。
- tool_hash新增绑定format_examples.py字节，生成算法变化会使旧build_key失效，避免继续复用旧数值样例缓存。未引入公开reference路径或改变公开ZIP白名单。
- prepare_task替换materialize_references为正式cases的显式循环。对照原函数，其echo=False的正式case分支就是同样的glob、reference存在条件及write_direct_grading调用；policy仍由同一author_policy取得，正式评分配置生成语义等价。删除的是会将公开随机output复制进sample/reference的原样例分支。
- README准确区分随机格式输出、私有源对照及参考准备状态；没有将随机输出存在视为物理答案就绪。
- 新测试覆盖已备参考时随机输出与私有证据保留、pending参考时仍有合法格式输出、种子/摘要/证据绑定及复用字节不变；既有离线prepare_task集成路径增加全部样例的格式角色断言。

pdebench-offline-tests.log显示4 passed in 3.10s。该日志是离线定点通过证据，不代表PDEBench全族准备或数值参考重新验证通过。正式grading等价性结论来自上述逐句实现比较，未重跑正式数值求解或判题。
