# 考生侧公开接口与材料装配

本文件规定考生工具的交付边界；内部职责见[核心与扩展](CORE-AND-EXTENSIONS.md)，描述字段与操作见[运行装配维护说明](../maintenance/RUNTIME.md)。

## 材料与安装

考生的题意与数据规则只来自本题 `instruction.md`、`DATA.md` 和通用 `CONTRACT.md`。包根 README 提供安装、真实样例路径和命令，不增加题意；公开样例包含完整输入与可复现判分的参考；完整提交示例单独保存，不能用稀疏参考冒充。公开样例的 `reference/grading.json` 仅用于本地复现评分；隐藏case配置不进入公开包，题意仍完整由三文件定义。

公开包包含装配后的核心、必要领域扩展及资源，统一执行一次普通安装：

```sh
python -m pip install .
```

Harbor 在构建阶段完成同等安装。考生无需选择扩展、输入 extras、注册模型、修改 PYTHONPATH 或寻找维护仓库。一个装配作为一个 `cae-bench-oj` 发行包拥有全部公开命名空间，不能靠依次覆盖多个单题安装合并支持范围。

Python 与第三方依赖要求由生成的安装元数据声明；Gmsh 等系统库由目标运行环境预置。普通安装不保证跨平台或离线可用，目标平台仍须独立验证。

维护工具、作者代码、隐藏 cases、私有 reference、内部规范及审核记录不进入公开包。运行代码和资源逐项列入白名单，不递归公开整个题目或扩展目录。文件清单与装配身份只绑定公开内容，不包含隐藏数据的清单或哈希。

这里的隐藏／私有指考生运行环境的装配角色；HF 上数据可公开访问，存储边界见[数据存储设计](DATA-STORAGE.md)。整题 `data-manifest.json` 不进入考生包。

维护方用 `caeoj-maint data assemble` 按清单装配本地测试或完整样例。发布器离线严格核验已装配的选中样例，Harbor 准备严格核验全套材料与重复选样；两者均不联网获取或自动重选。发布只带样例及其依赖，不把池索引、条目描述、回执或未选材料打入考生包。

## CLI 与基础 SDK

`python -m caeoj` 和 `caeoj` 进入同一实现。发布包将下列占位符替换为真实路径：

```sh
python -m caeoj validate-input <sample>/input/problem.json
python -m caeoj validate-output --input <sample>/input/problem.json --output result.h5
python -m caeoj grade --input <sample>/input/problem.json --output result.h5 --grading <sample>/reference/grading.json
python -m caeoj info --input <sample>/input/problem.json
```

CLI 与 SDK 使用同一装配契约。校验只检查结构、引用及声明约束；grade 比较明确给出的参考与策略，不查找隐藏参考、不执行求解器。结果为机器可读 JSON；`--version` 和 `info` 提供工具版本、装配及支持范围。

| 基础 SDK | 含义 |
|---|---|
| `load_problem(path)` | 按清单所在目录解析资源并校验，返回 manifest、arrays、meshes |
| `load_result(problem, path)` | 校验结果结构并返回数组 |
| `read_constant(data)`、`read_option(data)` | 读取明确的标量或选项，不换单位或猜默认值 |
| `read_field(problem, reference)` | 从逻辑字段引用找到实际数组，保留 shape、dtype 和顺序 |
| `target_ids(problem, location)`、`id_to_row(ids)` | 读取实体身份并建立 tag 到行号的映射 |
| `sample_field(problem, name, time)` | 按明确 sampling 声明进行时间采样，不做空间重建 |
| `write_result(path, problem, fields)` | 按输出 array key 写场，复制必需 IDs／时间轴并校验 |

已有领域辅助调用由可信装配中的别名转发到实际扩展；签名适配不改变公式、单位或物理口径。内部模块不因此成为题意来源。C++、Fortran 等程序可按三文件契约直接读写，SDK 始终可选。

校验命令退出码为 0（合法）、1（不合法），工具与用法错误为 2。grade 接受为 0，答案错误或非法输出为 1，输入／参考／配置／工具错误为 2。基础设施错误的 score 为 null，不计为考生失分。

## 装配与验证

1. 读取可信题目绑定，求扩展依赖闭包，拒绝版本、注册、Schema、路径或资源冲突。
2. 按白名单收集公开代码及材料，锁定构建环境中的依赖，生成安装元数据、装配身份及文件清单。
3. 隔离加载实际公开闭包，验证完整样例与评分策略，通过后原子替换发布 ZIP。
4. Harbor 验证发布内容未过期，从同一装配准备考生与独立 verifier；私有材料只交 verifier。

多题包合并有限题集的依赖与材料，保持各题绑定，一次安装后按当前输入选择检查规则。它不表示 Harbor 已支持多题联合调度；当前 prepare 仍逐题运行。

变更须覆盖普通安装后移走源码、换工作目录、CLI／SDK 读写、缺扩展与非法声明、公开样例判分、接口转发及多题装配。目标平台的容器、限额和离线运行应另行实测。已执行范围见[实施记录](reviews/runtime-refactor.md)；工具验证不证明隐藏数据完整、参考精度或预算已校准。
