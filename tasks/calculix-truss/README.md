# CalculiX两杆桁架出题草稿

题面[instruction.md](instruction.md)，I/O[DATA.md](DATA.md)，来源[DESIGN.md](DESIGN.md)，测试[TEST-CASES.md](TEST-CASES.md)。基于CalculiX2.20 truss验证实例，输出每杆轴向应力；源张量参考按杆方向投影，不伪造原节点位移。

cases保存输入，reference保存私有参考，samples为完整公开I/O，author为归档身份、映射与转换证据。原tag及重编号案例同一物理实例；新增参数范围缺独立参考。当前结构草稿，许可、参考精度、正式评分与资源尚待验收。公开包仅题面、DATA、工具及标记样例，其他维护材料不公开。


统一准备入口：

python src/utils/authoring/workflow.py prepare --task calculix-truss
sample模式只准备原tag source-001及完整公开样例；selected只准备显式--case指定的实例；all准备原tag、重编号两个源实例和无参考材料/力变体。

单题入口：

```sh
python tasks/calculix-truss/author/prepare.py --mode sample
python tasks/calculix-truss/author/prepare.py --mode selected --case source-002
python tasks/calculix-truss/author/prepare.py --mode all --allow-all
```

规模仅表示来源获取和结构转换，不代表数值验收通过。

下载与转换规模：sample、selected、all在未缓存时均至少下载完整12,636,197 B官方归档，仅提取393 B的truss.inp及1,676 B的truss.dat.ref；不支持通过Range单独获取归档成员。已命中并验证缓存时可零下载。all仅准备两项登记来源case，不获取整套CalculiX验证库；无参考参数变体仍单列pending。以上是来源文件规模声明，尚未宣称本次冷拉取成功。
