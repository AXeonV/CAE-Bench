# 四圆孔Laplace草稿

题面[instruction.md](instruction.md)，接口[DATA.md](DATA.md)，证据[DESIGN.md](DESIGN.md)，测试[TEST-CASES.md](TEST-CASES.md)。适配1246个真实COMSOL点，3案例取64/591/591行、样例64点，不插值不生成网格。新增物理范围待参考。cases为输入，reference为私有数值，samples为公开I/O，author为证据。当前只来源与结构阶段，数值、许可和资源待验收。草稿包公开instruction、DATA、工具与标记样例，维护材料不公开。


统一准备入口：

python src/utils/authoring/workflow.py prepare --task pinnacle-poisson-cg
sample模式只准备source-001（64观测点）与完整公开样例；selected只准备显式--case指定的源子集；all准备三个来源子集（64/591/591点）及无参考参数变体。

单题入口：

```sh
python tasks/pinnacle-poisson-cg/author/prepare.py --mode sample
python tasks/pinnacle-poisson-cg/author/prepare.py --mode selected --case source-002
python tasks/pinnacle-poisson-cg/author/prepare.py --mode all --allow-all
```

规模仅表示来源获取和结构转换，不代表数值验收通过。

下载与转换规模：未缓存时获取完整85,477 B来源表；sample转换64行，selected仅转换显式case清单对应行，all覆盖全部1,246行（64/591/591三个登记来源子集）。已命中并验证缓存时可零下载。无参考参数变体不增加来源参考行数。以上是来源文件规模声明，尚未宣称本次冷拉取成功。
