# point-ownership-repair 全数据独立审计

最终复核结论：**通过**。最终ZIP SHA256 `576823e42c10a91ca840cf6d21325340bf116ffa1582698b0f5f77bed6823a61`。原P2零probe身份已由调用方修复，本轮独立26变体全部符合预期；全12cases71queries和两samples在新包SDK上再次全部通过。原发现与旧版本证据原样保留，最终版本差异及复核见末尾。

初次冻结版本结论：**需修订（公开SDK一项声明检查缺口，现已关闭；见末尾增补）**。全部正式数据与参考数值检查通过；没有发现实际输入越界或参考不符。此轮已扩大权限读取作者与隐藏数据，是独立全数据审计，不能再称盲考生审阅。

## 范围与版本

按 caeoj-data-review 技能执行，只写 runs。对照三文件与前轮盲审相同：instruction SHA256 `981ca344aabbe5c40902ebea2c92945ae1edf142c0b8707c0211b5bdff542bb3`，DATA `186545a6156cb954112f8b444e267b92c81cd4ca6b3c80af75deab237da58b65`，CONTRACT `130d4416fd533812493780c8bc6afbc0a158de6800b59bbec14a852f3cf1c063`。选择manifest SHA256 `543f41830ff40936b27e5412ecf564591ca7aa68d28d8ab8ee4d987794b8f7de`。

读取完整12正式cases（71查询）及全部两samples（14重复公开查询）。每份problem.json、source.msh、input.h5、reference/grading.json、reference.h5的完整内容均已加载；两公开output/result.h5完整加载。没有未读大数组切片。全部manifest、原MSH内容、数组dtype/shape/全值、逐查询重心坐标/候选集/到所有闭单纯形距离及参考误差保存于 [all-data.json](all-data.json)；实际文件哈希也在其中。

官方固定HF提交为 `cbcaa0680927b4dcaed80ea18e5e3e5daecbe933`。固定新缓存回取报告complete=true、72files、无差异；本轮未重新下载，独立核对正式manifest、装配receipt中全部12个原始descriptor哈希及其每份输入/参考资产的长度与SHA256，连同两samples映射全部一致。独立现有data verify执行valid=true，无errors，两公开case复用身份如声明。绑定详见 [bindings-variants.json](bindings-variants.json)。这证明当前装配与选择绑定一致，不单凭作者的HF成功记录作数值认证。

## 发现与最小修订

**P2：公开SDK接受DATA明确禁止的零probe身份。** DATA“声明及输入数组”规定probe_ids为正整数；CONTRACT独立points一般允许非负，故本题扩展应收紧。当前extension/caeoj_task_ext/ownership.py只检查长度与diff>0，没有检查probe_ids>0。把公开sample02的probe_ids改成int64 `[0,1,2,3,4,5,6]`，其他输入不变，包内load_problem接受；这是文档禁止却被任务契约检查接受的分支。

复现目录 `variants/bad-zero-probe-identity`，结果在bindings-variants.json。建议扩展检查补充非正身份拒绝，同步正式扩展与公开包并重验。它不影响当前正式case或样例：所有实际probe_ids均为正。未建议更改数学题意或正式参考。

## 全查询独立数学审计

审计程序是只读检验器，不生产/覆盖reference，不替代真实DOLFINx库。没有导入作者independent.evaluate：从实际MSH连接和原tag独立计算仿射重心坐标、逐轴闭bbox+padding，以及枚举闭单纯形各面的正交投影，核对距离与归属。多单元内部不重叠以分离轴检测核对；全部单元非退化、所有节点被使用、节点与查询最小间距及范围由中性结构/声明校验与实际几何读数共同核对。

每点先包含，再依据mode与bbox候选选最短欧氏距离；严格模式不归属候选外部点，空候选不全局搜索。实际输入维度2/3、mode0/1/2均出现。所有输出精确owned/cell_id与独立结果相同，distance逐值在1e-8+1e-8*abs(reference)范围内，最大误差约 `1.0255800382752408e-15 m`。最小实际域外到任意闭单元距离 `0.0019999999999988916 m`；最小多候选最短/次短差 `0.006201920231797886 m`，均满足公开保证。闭包含点最多一个，原单元tag31/60在库重排后的恢复身份也与独立选择吻合。

正式71查询中：33包含、38域外；57有候选、14无候选；13严格拒绝候选内域外点、11允许外推点；6多候选，其中2包含优先；20位于闭外表面/边/顶点。正式材料没有非空候选内局部最近与全局最近不同的点；14个空候选点已可检查禁止任意全局回退。此处只报告覆盖，不把case名称当作覆盖证据。

| 正式case | D | mode | padding(m) | Q | 独立reference / defect通过 |
|---|---|---|---|---|---|
| 01-tetra-strict-public | 3 | 0 | 0 | 7 | 1 / 0 |
| 02-triangle-extrapolation-public | 2 | 1 | 0.25 | 7 | 1 / 1 |
| 03-strict-ignores-padding | 2 | 0 | 0.5 | 7 | 1 / 0 |
| 04-tetra-padding-bounds | 3 | 1 | 0.3 | 4 | 1 / 1 |
| 05-default-tetra-regression | 3 | 2 | 0 | 7 | 1 / 1 |
| 06-disconnected-triangles-strict | 2 | 0 | 0.1 | 5 | 1 / 0 |
| 07-two-candidate-triangles | 2 | 1 | 1 | 5 | 1 / 1 |
| 08-disconnected-tetra-strict | 3 | 0 | 0.4 | 5 | 1 / 0 |
| 09-rotated-tetra-strict | 3 | 0 | 0.1 | 7 | 1 / 0 |
| 10-small-translated-tetra | 3 | 0 | 0.01 | 7 | 1 / 0 |
| 11-default-no-global-search | 2 | 2 | 0 | 5 | 1 / 1 |
| 12-two-candidate-tetra | 3 | 1 | 0.8 | 5 | 1 / 1 |

12份reference各自通过完整outputs结构检查和现有grade（每例score1）。两samples与对应正式case共享相同输入资产、descriptor和参考；公开输出数组与参考精确相同，各自grade1。配置owned/cell_id均pointwise、atol=rtol=0，distance逐点atol=rtol=1e-8，无额外私有判据或缺失参考轴。复制probe_ids/times、三个float64[1,Q,1]字段、无归属0/-1/-1均按全部值核对；输出不含节点IDs或坐标。

## 实际生产者与来源绑定

读取public/driver.cpp、run_case.py及author/replay.py：driver构造真实mesh，mode2调用四参数默认API；旧baseline无第五参数时兼容分派仍调用真实四参数，其他调用传mode==1。归属由真实determine_point_ownership给出，距离直接来自真实geometry::shortest_vector；driver只把库original_cell_index映射回MSH标签，不重判包含或最近单元。adapter仅串行化真实网格身份/坐标并转换真实stdout为HDF5，author mathchecker仅验证，不生产正式reference。

对全部12例，独立从实际JSON/MSH/HDF5重新序列化payload，核对reference/defect replay的input_assets、input_payload_sha256，并对保存的原始input.json逐字节核对；reference stdout重建的每个输出值与正式reference完全相同且HDF5摘要吻合。重新对全部raw stdout逐查询比较独立数学结果，reference为12/12、defect为6/12，与作者记录吻合；没有只复述作者得分。

原始source.json固定DOLFINx baseline `2d6d22a8c2cc9d3488f8910238e9740c6247f83b`，PR head `56977f3dd3e9a0418306f4c6a1d591693dc66457`。本轮独立逐项读原始tar和materialized cache全部文件字节：DOLFINx456、Basix183、FFCx128，归档SHA与显式符号链接映射及树摘要全部吻合，详情见bindings-variants.json。DOLFINx原件头SHA `6035e24b27014a25a66cf5325807bb80eace12a26de0ee2b72eb3e056223f132`，PR完整头SHA `44cee2d91b2400ce193c6a93879884cdf6aaec06c343b3c36718590b6fb7b4eb`、Git blob `b14ab337c22c5ba4d4516ab59913a91753e718eb` 均独立核对。

原issue三点prototype源程序只构造标准四面体调用真实API：内点(.1,.1,.1)、盒内外点(.5,.5,.5)、盒外点(1.1,1.1,1.1)。独立数学预期严格[0,-1,-1]、外推[0,0,-1]。保存stdout中原件两模式都[0,0,-1]，PR严格[0,-1,-1]、外推[0,0,-1]；两份完整stdout SHA与prototype.json逐字节匹配。完整真实源码构建/头依赖闭包记录已读，未在本轮重跑编译。

## SDK合法/非法变体与公开运行证据

从最终DATA独立选择26变体：mode0/1/2、padding0/5、非连续正probe身份、去除可选point元素为合法；mode浮点/布尔/越界、padding布尔/负/超5、零身份、节点子集、非零时间、float32查询、未使用节点、退化拓扑、输出多数组/错误身份/错误shape为非法。除已报告零身份外，其余25个结果均符合DATA预期；全部夹具及异常诊断只在runs，未修改正式实现。

原冻结公开ZIP SHA `5dae9c7e11e452550ad8b5c074bb9a92ec03a80d787511ed023053cbcc7fe158`。已读root的真实断网普通pip安装日志dolfinx-public-install.stdout.log：ordinary_offline_pip_install=true、SDK源码已移走、pip_check无破损要求，baseline native样例执行均exit0，grade01=0/02=1，与预期缺陷检出/回归吻合，不能误报成安装失败。此安装是root实际执行证据，本轮没有再次安装；本轮数学与中性SDK审计使用Windows Python3.11.9和先前冻结包src、NumPy2.4.1，不替代Linux锁定环境证明。

## 未验证内容

没有在本轮重建Docker库、重跑真实C++binary、重做原始网络抓取或远端HF下载，不认证新的候选修复或构建/运行资源上限；资源性能结论仍由真实运行方单独负责。没有审计MPI、多阶单元或题面明确排除的功能。正式输入和全部数值参考已全读核对；需修订结论仅来自公开SDK与DATA的一项不一致。


## 最终修订增补：零身份缺口关闭

最终包 `dist/point-ownership-repair-agent.zip` 的实际SHA256为 `576823e42c10a91ca840cf6d21325340bf116ffa1582698b0f5f77bed6823a61`，45文件，文件集合无增删。与旧冻结包逐文件哈希比较，只有四个文件变化：ownership.py加入 `np.any(np.asarray(probes)<=0)`；runtime.json仅变assembly id；pyproject.toml仅变bundle版本；MANIFEST.json更新assembly id与相应资产摘要。driver、adapter、真实solver归档、SDK核心、三文件及全部公开样例输入/参考/输出均无字节变化。正式扩展字节等于最终包扩展，新增条件恰好落实DATA原有正身份要求，没有改变数学输入或参考。

版本全清单见 [final-version-diff.json](final-version-diff.json)。新包MANIFEST每项摘要再次核对，无差异；三文件和全部样例实际资产逐字节等于当前正式文件，见 [final-evidence/zip-bindings.json](final-evidence/zip-bindings.json)。正式数据选择、descriptor、载荷与源码树又独立完整核对一次，没有数据变更。

本次明确从新ZIP提取src到独立final-snapshot，运行相同只读审计程序与26个DATA驱动变体。零身份现在被E_OWNERSHIP拒绝，其他25变体结果保持预期；26/26相符，errors=[]，原P2关闭。完整变体诊断、选择与全部资产/源码树绑定见 [final-evidence/bindings-variants.json](final-evidence/bindings-variants.json)。12正式case71查询及两公开样例在最终SDK上再次完整读取、逐点独立数学比较、结构校验与参考判分；无错误，所有分类计数和数学结果保持不变，详见 [final-evidence/all-data.json](final-evidence/all-data.json) 和同目录audit/variants的stdout/stderr。

原ZIP `5dae9c7e...` 的真实Oracle12/12/exception=null，以及早前普通断网pip安装证据，只绑定其实际旧版本；不能将它们说成新ZIP的Oracle或安装验收。本轮只完成新版本独立SDK、全部真实数据/参考与修订范围复核；新ZIP真实Oracle/可信后端重验由root另行执行，其结果不在本报告中预断。
