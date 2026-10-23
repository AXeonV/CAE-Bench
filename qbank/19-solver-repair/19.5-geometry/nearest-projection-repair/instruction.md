# 19.5.2 最近投影与单元插值回退修复

修复给定preCICE真实源码的几何选择，使[DATA](DATA.md)定义的二维/三维最近投影和单元插值回退都返回正确的重心权重及节点场传递。通用协议见[CONTRACT](../../../../docs/CONTRACT.md)。一个提交须处理全部合法输入。

当查询点不能在源网格单元内部插值时，应投影到给定离散几何集合中的最近点；较远的面或边不能仅因维度较高而胜过较近的边或顶点。问题族可含不连通的低阶单纯形和独立节点。单元内部的线性插值、标准面/边投影及仅有节点时的回退必须保持。DATA完整规定几何集合、两种模式、身份、唯一性与输出，不要求建立整个耦合通信过程或演化求解。

只提交`Index.cpp`，文件不超过1 MiB（1,048,576字节），替换真实`src/query/Index.cpp`，保持原头文件及类和函数签名。允许在该文件内重构；禁止改写头文件、可信driver、协议转换器、其他源码、编译规则，或另写替代输出程序、读取参考及按算例标识硬编码。数值与方法要求分别核查。完整固定源码及许可证在`public/precice-source.tar.gz`，真实API调用在`public/driver.cpp`。

运行环境提供原始库与离线依赖。修改源码后用`cmake --build /opt/precice-repair-build --target repair_sources --parallel 4`构建，再以`python public/run_case.py --input samples/01/input/problem.json --output /tmp/result.h5`运行。可信后端冻结替换件并从原件强制重编实现、重新链接真实库及driver；提交中的可执行程序或缓存不参与判题。

每例比较全部查询点的全部输出，逐值满足`abs(actual-reference) <= atol+rtol*abs(reference)`才通过，计分例等权。所有量rtol为1e-8；权重atol=1e-9，投影位置和距离atol=1e-8 m，传递场atol=1e-8。非有限、缺输出、运行或候选编译失败均未通过。每例30秒，候选编译180秒，环境4 CPU、8 GiB内存。本题评价静态、单进程的指定查找API，不包含MPI/GPU、通信、网格搜索性能或高阶曲面。
