# 输入输出契约

采用[CONTRACT.md](../../docs/CONTRACT.md)，路径相对入口清单目录。task=pinnacle-poisson-cg，spatial_dimension=2，physics.model=laplace_square_four_holes。geometries、meshes、fields为空对象，conditions=[]；无网格或初值。

physics.parameters全部必有，每项为带value和unit的有限标量对象。x_min、x_max、y_min、y_max为矩形端点，unit=m；hole_1_x、hole_1_y、hole_1_r至hole_4_x、hole_4_y、hole_4_r为四圆心和正半径，unit=m；outer_value、inner_value为整段外矩形周界和全部圆周的势，unit=1。Ω为矩形开域去除四闭圆盘，内部Δu=0。条件列表为空不表示没有边界；参数缺失不表示零。源圆编号依次(-.3,-.3)、(-.3,.3)、(.3,-.3)、(.3,.3)。

locations.observations为kind=points、ids=probe_ids、coordinates=probe_coordinates；time_axes为steady:times。输入NPZ恰好三项：probe_ids int64[N]非负严格递增唯一；probe_coordinates float64[N,2]按IDs行序的x,y，m；times float64[1]=[0.0]。N随输入变化，源子集IDs保留原始零基行号。点无连接关系，不定义插值；不得以坐标排序或固定下标猜测关联。时间标记不是内部迭代步长。

outputs.state：array=state，quantity=dimensionless_potential，location=observations，time_axis=steady，dtype=float64，kind=scalar，component_shape=[1]，components=[value]，unit=1，value_kind=point。结果恰好probe_ids、times、state；轴原样复制。state[0,i,0]为probe_coordinates[i]处连续解点值；不输出坐标或诊断。结构校验不检验几何、PDE与精度。

闭合计算域包括矩形外周界和四个圆周；不含圆孔内部。边界观测点直接取相应Dirichlet值。

以下为可解析JSON清单片段，不是完整输入：

```json
{
  "locations":{"observations":{"kind":"points","ids":"probe_ids","coordinates":"probe_coordinates"}},
  "time_axes":{"steady":"times"},
  "physics":{"model":"laplace_square_four_holes","parameters":{"outer_value":{"value":1.0,"unit":"1"},"hole_1_r":{"value":0.1,"unit":"m"}}}
}
```

完整清单必须补齐所有参数、其他顶层字段以及outputs声明，不能将片段缺项解释为缺省。
