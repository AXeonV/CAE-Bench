# 第 1 章：给定 PDE 问题的求解

章、节、子节方向见[第一章规划](../design/chapter-01-prescribed-pdes.md)。该规划先于迁移清单独立提交，按数学问题与求解能力组织；下表是已有题目对规划的当前覆盖，不以现有来源限定未来题目。

## 已迁入题目

| 节 | 题目 | 数学范围与归属理由 |
|---|---|---|
| 1.1 椭圆型边值问题 | [heat-conduction-steady-2d](1.1-elliptic/heat-conduction-steady-2d/instruction.md) | 二维常系数 Poisson 边值，混合边界及纯 Neumann 规范 |
| 1.1 | [darcy-flow-2d](1.1-elliptic/darcy-flow-2d/instruction.md) | 二维正变系数散度型椭圆方程 |
| 1.2 扩散与反应扩散初边值问题 | [heat-conduction-transient-2d](1.2-diffusion-reaction/heat-conduction-transient-2d/instruction.md) | 二维线性扩散、三角形分片线性初态及齐次边界 |
| 1.2 | [diffusion-sorption-1d](1.2-diffusion-reaction/diffusion-sorption-1d/instruction.md) | 一维非线性储存／迟滞扩散，含明确的平均值耦合边界 |
| 1.2 | [reaction-diffusion-1d](1.2-diffusion-reaction/reaction-diffusion-1d/instruction.md) | 一维标量扩散与 logistic 局部反应 |
| 1.2 | [reaction-diffusion-2d](1.2-diffusion-reaction/reaction-diffusion-2d/instruction.md) | 二维两变量反应扩散系统，无独立对流机制 |
| 1.3 一阶标量输运 | [advection-1d](1.3-scalar-transport/advection-1d/instruction.md) | 一维周期线性平流，无扩散项 |
| 1.4 双曲型方程与守恒律系统 | [shallow-water-2d](1.4-hyperbolic/shallow-water-2d/instruction.md) | 二维浅水守恒律系统，熵选择与全湿支持范围；当前圆形初态是受支持算例限制 |
| 1.5 标量对流—扩散—反应 | [burgers-1d](1.5-advection-diffusion/burgers-1d/instruction.md) | 一维含正黏性的非线性标量守恒律 |
| 1.6 约束与混合系统 | [incompressible-navier-stokes-2d](1.6-constrained-systems/incompressible-navier-stokes-2d/instruction.md) | 给定不可压缩速度约束、初态投影及输运驱动标量，不作为自主建模 CFD 题 |
| 1.7 多机制耦合系统 | [compressible-navier-stokes-1d](1.7-coupled-systems/compressible-navier-stokes-1d/instruction.md) | 给定质量、黏性动量与能量系统及状态关系，一维 |
| 1.7 | [compressible-navier-stokes-2d](1.7-coupled-systems/compressible-navier-stokes-2d/instruction.md) | 同类给定系统的二维问题，具体通量严格按题面 |
| 1.7 | [compressible-navier-stokes-3d](1.7-coupled-systems/compressible-navier-stokes-3d/instruction.md) | 同类给定系统的三维问题，具体通量严格按题面 |

以上 13 题保留原 slug 与输入 `task`，目录变化不改变方程、数据身份、参数范围或评分配置。1.1—1.7 也仅有部分方向被覆盖；1.8—1.12 目前是规划，尚无迁入题面，不用占位题冒充实现。

## 使用与维护

考生只需本题 instruction.md、DATA.md 和通用 CONTRACT.md。各题 README 和 author 为维护资料；来源与离散参考的局限保留在算例及参考层，不成为题名或隐藏要求。

项目工具按唯一 slug 在 `qbank/<chapter>/<section>/<task>/` 定位题目。保持 slug 唯一；同名目录或链接目录会被拒绝，避免误选题。迁移后的命令仍使用 `--task <slug>`：

```sh
python src/utils/publish_dist.py --task heat-conduction-steady-2d
python src/utils/prepare_harbor.py --task heat-conduction-steady-2d
```

公开 ZIP 内保留真实 qbank 相对路径，Harbor 说明使用 `/app/qbank/...`；生成任务仍在 `runs/harbor/tasks/<slug>/`。数值载荷不足时不能发布或组装，先按对应题目的维护说明准备真实数据，不补造假样例。

两道热传导题的生成／检查工具随目录迁移。来源适配器默认写入各题真实 qbank 目录，`--output-root` 仍可选择另一个扁平临时题目树；缓存与报告继续在 runs 中。配置与既有数据保留不代表参考精度、预算或正式发布已经重新验证，见[迁移记录](../design/reviews/chapter-01-migration.md)。

已发布PDEBench算例按[统一获取流程](../maintenance/PDEBENCH-DATA.md)装配；正式选样由各题data-manifest.json维护。来源直接制数与HF消费为两条明确的装配路径。
