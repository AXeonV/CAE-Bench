# 四圆孔二维稳态Laplace问题

矩形开域去除四个闭圆盘，求Δu=0的无量纲势；整个外矩形周界u=outer_value，全部圆周u=inner_value。连续域与边界值由输入确定，输出指定观测点处连续解点值。观测点不是计算网格。采用[通用协议](../../docs/CONTRACT.md)，[DATA.md](DATA.md)为题目一部分。

程序冻结后逐例读取新输入，自由使用解析或数值方法、核心语言和库。入口python solve.py --input problem.json --output result.npz可包装任意语言实现。

范围：矩形端点[-2,2]m，两边长度[.5,3]m；半径[.02,.3]m，四圆互不相交且严格在矩形内部；边界值[-2,2]，N为1至20000，观测点位于闭合计算域。源实例[-.5,.5]²、圆心(±.3,±.3)、r=.1m、外1内0。参考只覆盖固定源实例的来源点；更大范围为OJ新增定义，尚未完整数值验收。

结果仅含复制的probe_ids、times及有限float64 state[1,N,1]，单位1，按输入IDs行序。当前草稿评分阈值、时限和内存待数值验收冻结，不能正式评测。完整样例见[samples/source-001/input/problem.json](samples/source-001/input/problem.json)及[samples/source-001/output/result.npz](samples/source-001/output/result.npz)，64个源观测行，不插值。数值参考不等于精确连续真解。
