# 第19章发行审计（2026-10-23）

## 结论

22题现有旧接口资产可收录为明确标记的待迁移材料；本轮不能将其称作已完成repo_patch迁移或可在团队干净机器直接运行的正式发行。建议运行发行默认排除，保留全部22题的候选目录、case身份与延期原因，避免无声丢题。

- 当前全部使用source_repair v1：提交指定替换文件，限制普通源码文件名，固定构建目标及删除指定object/so。不能只修改文档就宣称接受任意仓库patch。
- 检查22题public-materials.json资产摘要全部匹配；所有源码归档均保留至少一项LICENSE/COPYING/NOTICE/COPYRIGHT声明。这不等于完成依赖及二进制镜像的分发许可审核。
- 本机22基础镜像存在，逻辑大小合计86,880,473,047字节（约80.9 GiB，共享层未去重；不是实际归档传输量）。本地RepoDigests和caeoj-*名称不证明团队能从公共registry拉取。
- 22个既有公开agent ZIP合计388,925,451字节（约370.9 MiB）；21个与当前重新收集的公开闭包完全一致。Chrono仅README.md及MANIFEST.json不同，需要重新publish。
- 真实最小publish：OpenSees任务生成42文件/2样例ZIP，退出0；摘要40e4da217f8eb7d96f198b21a439db1801874433536148ee6dc3a6ee0523ac3b。其隔离预检只加载Python公开闭包与样例，不代表原生构建或异机离线安装通过。

## 许可和交付边界

OpenSees公开归档的COPYRIGHT给教育、研究、非营利实体非商业使用/修改/分发许可；其他实体文字允许内部使用、复制、修改。不得将其按根目录MIT许可覆盖或标记无限制分发。实际使用实体与用途未在本轮确定；该题需要明确许可适用范围。其他上游和镜像系统依赖也需保留各自声明及适用的源码交付义务。这里只记录实际归档文字，不替代分发资格审定。

现行生成的repair Dockerfile以本地base_image标签为FROM，再pip install /app；部分题的公开包提供离线wheel闭包且作者有断网安装记录，但未逐题在新主机重复验证。可复用原验收证据，不把本机已存在镜像当成发行镜像已送达。

完整repo_patch迁移至少需：固定完整基线仓库；不限文件的patch安全应用；可信测试及结果采集位于仓库外；头文件/构建配置修改导致的依赖重建；干净构建预算；正确/错误/部分/旧范围外合法patch控制；Gold及未来修复资料与可见镜像层隔离；重新冻结并验证。不要长期保留两套默认协议来掩盖未迁移。

## 逐题资产

|题目|正式case|公开样例|ZIP现行匹配|镜像GiB|源码许可声明|
|---|---:|---:|---|---:|---|
|constrained-assembly-repair|20|2|否|1.39|归档内已保留，分发资格待审|
|hysteretic-trial-state-repair|10|2|是|1.63|归档内已保留，分发资格待审|
|grand-potential-derivatives-repair|12|2|是|11.22|归档内已保留，分发资格待审|
|spatial-beam-transform-repair|10|2|是|2.88|归档内已保留，分发资格待审|
|deformed-tangential-boundary-repair|12|2|是|8.60|归档内已保留，分发资格待审|
|migration-soret-scaling-repair|12|2|是|1.87|归档内已保留，分发资格待审|
|multisite-surface-concentration-repair|9|2|是|3.29|归档内已保留，分发资格待审|
|reconstructed-energy-repair|9|2|是|3.55|归档内已保留，分发资格待审|
|surface-flow-constraint-repair|9|2|是|3.29|归档内已保留，分发资格待审|
|two-temperature-state-repair|12|2|是|3.28|归档内已保留，分发资格待审|
|diffusion-element-heat-repair|16|2|是|2.14|归档内已保留，分发资格待审|
|graded-electrode-inventory-repair|14|2|是|2.24|归档内已保留，分发资格待审|
|granular-pair-stress-repair|12|2|是|3.47|归档内已保留，分发资格待审|
|hysteresis-heat-repair|14|2|是|2.11|归档内已保留，分发资格待审|
|solid-fluid-energy-observation-repair|12|2|是|12.18|归档内已保留，分发资格待审|
|wall-heat-flux-repair|10|2|是|3.54|归档内已保留，分发资格待审|
|nearest-projection-repair|10|2|是|1.67|归档内已保留，分发资格待审|
|point-ownership-repair|12|2|是|2.13|归档内已保留，分发资格待审|
|complex-helmholtz-fmm-repair|12|2|是|2.82|归档内已保留，分发资格待审|
|cylindrical-field-pml-repair|8|2|是|1.71|归档内已保留，分发资格待审|
|dft-decimation-repair|9|2|是|1.71|归档内已保留，分发资格待审|
|parallel-pml-reduction-repair|8|2|是|4.19|归档内已保留，分发资格待审|

细粒度源归档、摘要、许可声明路径、替换列表、镜像ID与RepoDigest、全部case身份见同目录repair-report.json。未重新编译22题、运行付费模型或复制镜像。未修改源题、中央配置或现有dist包。
