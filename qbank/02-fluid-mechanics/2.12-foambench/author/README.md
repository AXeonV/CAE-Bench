# FOAMBench 题面移植维护记录

## 范围与定位

用户要求：第二章独立 2.12 节，按固定源版本逐题移植全部 110 Basic + 16 Advanced；仅题面与数据契约，不移植实际输入、样例、参考或评分配置，不绑定 OpenFOAM，不修改 PHILOSOPHY。

general problem 仍是题库核心；本节是来源兼容专题，不用于推断通用能力覆盖。源题一一保留，不将同族十个变体折成一道题。源中仅数值设置不同的题允许物理等价，不能伪称独立能力。

固定来源与逐题对应以 [source-index.json](source-index.json) 为准；上游许可保存在 [UPSTREAM-LICENSE.txt](UPSTREAM-LICENSE.txt)。每题 author/source.json 记录原题描述及本次取舍。原始配置未作为考生要求交付。

## 转换规则

1. 公开题面用物理语言和本仓 problem.json、Gmsh、HDF5 协议；不要求源软件、字典目录、PISO/PIMPLE、特定线性求解器、网格细分数或内部步长。
2. 数学／材料／湍流／燃烧模型可以作为明确的物理或方法要求；这不绑定其实现软件。二维、轴对称、稳态迭代和真实物理时间分别识别。
3. prompt 给出目标工况，配置补足几何、材料和初态；冲突不静默继承，逐题记录并在 DATA 给出唯一解释。原始异常不以程序能运行作为正确依据。
4. 每题三文件阅读边界：instruction.md、DATA.md、docs/CONTRACT.md。维护索引和原仓库都不能补充隐含题意。
5. 当前为题面与接口文档阶段，新模型不注册到 runtime，不声称领域工具已支持。资源、容差及参考须在真实算例阶段校准后才能发布评测；无占位数据冒充样例。

## 验证边界

逐题覆盖、链接及静态检查、独立审阅记录见本次实施记录。未运行求解器、未验证数值、未创建 HF 数据或 PR、未运行模型 benchmark。

## 固定版本恢复与重建

从仓库根目录运行（使用环境中的 Python 3）：

```sh
python qbank/02-fluid-mechanics/2.12-foambench/author/rebuild.py --fetch
python qbank/02-fluid-mechanics/2.12-foambench/author/verify_statements.py --output runs/foambench-import/structure.json
python .agents/skills/caeoj-author-question/scripts/check_statements.py --section qbank/02-fluid-mechanics/2.12-foambench --output runs/foambench-import/static.json
```

`--fetch`仅将缺失的原题JSON下载到忽略的runs缓存；URL始终包含固定提交，写缓存前与读取缓存时均验证索引SHA-256。摘要不符直接失败，不改为拉取main或自动更新摘要。重建只写本节题面、DATA和作者记录，不生成任何实际算例，不执行下载内容中的代码。各生成器也经同一固定来源校验读取。

最终[实施与独立审阅记录](../../../design/reviews/section-2.12-foambench.md)保存问题、处理、验证边界与逐题覆盖。动态一方程滤波的源实现核查参考[公开源代码](https://github.com/OpenFOAM/OpenFOAM-10/blob/master/src/MomentumTransportModels/momentumTransportModels/LES/dynamicKEqn/dynamicKEqn.C)；本节公开DATA已给出软件无关公式及固定滤波定义，考生无需查阅该实现。
