# Darcy：20 case / 2引用example制作与安装验收

已在当前codex/pdebench-direct-cases分支完成20条case和2个引用example，直接取原始DaRUS发布解；没有补算、修正参考或进行收敛/精度筛选。case001/020分别公开为example01/02；仍计分20例，其中18例未公开。本次没有模型、PDE求解器、HF Jobs或上传。

## 来源与契约

前置[来源核查与契约修复](../direct-20261020/REPORT.md)已以4ba40ca合入当前分支：恢复四边零Dirichlet，保留系数中心点双线性重建、外侧常值延拓和原单元平均输出。本批相对该修复版本不再修改题面、DATA、评分、资源。零虚单元与连续零边界的离散差异、未认证稳态收敛及精确历史生成版本均保留为上游参考局限，不设额外迁移门槛。

五个来源文件133217–133221，各有10000条128²系数/单帧解，beta=.01/.1/1/10/100；实际beta属性与文件标签及每例输入source_strength一致。五档各取4条，种子20261020；跨参数文件全局选择20个不同来源索引，避免复用跨beta共享的系数样本，安装后再核对20个系数摘要均唯一。系数场是独立随机场，不把同一场的源项缩放计作独立系数样本；不存在精度筛选。选样与映射见[selection-design.json](selection-design.json)，固定SHA256 `b8aa5c7ffda8e0974c6515b745d89b533effe3445ea49b9b268aa973ea9fc45b`。

源`nu`为系数，`tensor`为解，顺序[x,y]；源实际中心坐标由文件读取，对应Gmsh原单元和coefficient_coordinates。时间[0.0]只是稳态占位，未把原文件可能遗留的时间坐标解释成瞬态初值。系数float32的0.1表示按工具既有语义规范为float64的0.1，发布state仅转float64与数组排布，不改变数值。

## 验收

- [prepare.json](prepare.json)：20条正控制1/错误值控制0，2个引用example身份绑定通过。
- [verify-installed.json](verify-installed.json)和[installed-audit.json](installed-audit.json)：全部安装输入、参考及example逐字节等于stage；20个不同系数场；相对修复后题面/DATA两个摘要不变。
- 安装审计用0网络预算重新打开原始范围缓存，对20条重新读取nu/tensor、实际beta、坐标。参考逐值等于源state，输入系数等于工具的源值规范表达，系数坐标与源坐标一一对应；未使用历史修正参考或五条回放替代本批真实读取。
- 公开包/Harbor canonical装配完成；[isolated-summary.json](isolated-summary.json)记录20条全零错误控制均wrong_answer、无runtime_error、20/20完整执行、2个公开身份；公开wheel独立安装，UID1000不能读隐藏参考、临时隐藏副本不存在，4CPU/4096MiB实际生效。原生Docker控制禁网；它不是模型benchmark或独立数值正确性认证。
- 原九题180条既有输入/参考按原stage回执逐文件校验不变。

安装为本题cases/001..020、reference/001..020、samples/01与02。载荷40,484,420字节，实际数据及安装回执Git忽略；配方和验收证据跟随代码提交。旧目录由install --replace按工具保留备份。公开题面仍写20例，完整判分比较原始发布参考，不把未通过一概解释为物理解错误。

## 流量及复现

先将旧五文件1MiB缓存按SHA核验拆为64KiB并保留同一来源身份/ETag，拆块0网络。全部新增下载均经按需工具及本批剩余额度管控；首轮探测完成选样后仅因before-install调用缺root中止，零网络账目保留，单独补齐快照后继续，未重新探测授额。

本批保守响应体扣额10,485,920，完整实收5,242,880字节；此前累计（含Darcy论文资料8MB保守扣额）3,502,951,798，最终累计3,513,437,718，低于3,800,000,000上限。响应体外头/TLS不计，实收与保守扣额不可相加。完整账目见[network-total.json](network-total.json)。

复现使用[spec.json](spec.json)经PDEBench工具新建选择/prepare/install/verify-installed，读取源时自动核对实际属性。旧五条来源核查留在direct-20261020，不覆盖历史记录。中文commit、工作树干净、不push。数据就绪与模型成绩、参考精度认证分别陈述。
