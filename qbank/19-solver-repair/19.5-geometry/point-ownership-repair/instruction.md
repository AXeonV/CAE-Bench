# 19.5.1 域外点归属与可选外推修复

修复给定真实DOLFINx的点归属入口，使[DATA](DATA.md)规定的严格包含、可选外推及默认调用都正确。包围盒命中不能代替闭单元实际包含；关闭外推时，域外点必须保持未归属。开启外推时须保留既有包围盒候选内的最近单元回退。通用协议见[CONTRACT](../../../../docs/CONTRACT.md)。一个提交处理全部合法输入。

只提交一个普通文件`utils.h`，不超过1 MiB（1,048,576字节），替换真实`cpp/dolfinx/geometry/utils.h`。给`determine_point_ownership`保留原四参数调用，并增加可选第五参数`bool find_closest_cell = true`；DATA规定该参数及默认调用的语义。可重构本文件内部辅助实现，须保持本题所用真实网格和几何功能可编译并满足回归。不得修改其他源码、可信driver、适配器或编译规则，不得另写输出程序、读取参考或按输入身份硬编码。

完整固定源码及许可证位于`public/dolfinx-source.tar.gz`，同期Basix/UFCx源码另在两个依赖归档。真实调用见`public/driver.cpp`。driver只构造网格、调实际入口、按库返回身份恢复原单元标签，并调用实际几何距离入口；不另行判断包含或选择单元。对不具备第五参数的原件，兼容调度调用旧四参数入口，因此原件的缺失行为仍可观察。

环境提供真实库及离线依赖。修改对应源码后用`cmake --build /opt/dolfinx-repair-build --target repair_sources --parallel 4`构建，再用`python public/run_case.py --input samples/01/input/problem.json --output /tmp/result.h5`运行。可信后端冻结替换件，删除受影响翻译单元、库与driver产物后重新编译和链接，不采用提交中的二进制或缓存。

每例比较全部查询的归属标志、原单元标识和距离，全部通过才得分，计分例等权。归属及标识须精确相等；距离逐值满足`abs(actual-reference) <= 1e-8 m + 1e-8*abs(reference)`。非有限、缺输出、运行或候选编译失败均不通过。每例20秒，候选构建240秒，环境4 CPU、8 GiB内存。本题为单进程、静态线性三角形/四面体的指定API，不包含MPI分布式归属、非匹配函数插值、高阶单元或网格搜索性能评价。
