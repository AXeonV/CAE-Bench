# 数据准备

在项目根目录运行当前算例适配器：

```sh
python src/utils/PDEBench/prepare.py --tasks darcy-flow-2d --budget-gb 60 --no-bootstrap
```

工具的依赖、缓存及完整用法见[数据准备说明](../../../../../src/utils/PDEBench/README.md)。本目录保存本地准备状态 `preparation.json` 和可再生的 `prepared/` 记录，不进入 Agent 公开包。

算例来源、冻结选择、历史记录与参考证据统一保存在 [来源记录](data-evidence/reference/README.md)。新增来源应服从现有 instruction.md 与 DATA.md；若数学问题发生变化，需明确修订契约及参考绑定，不能由来源文件名隐式改变方程或参数。
