# 核心、扩展与公开运行装配

本文件供维护方使用，不进入考生包，也不增加题意。架构依据见[职责设计](../design/CORE-AND-EXTENSIONS.md)和[公开接口设计](../design/PUBLIC-INTERFACE.md)。

## 开发与考生安装

开发环境安装核心／维护工具及独立题库 provider：

```sh
python -m pip install -e '.[maint]' -e qbank/extensions
python -m caeoj_tools.cli smoke
```

`packaging` 是维护 extra，供发布前校验与锁定依赖；核心的运行依赖不包含它。开发发行包含维护命令，公开装配包则只安装核心、必要扩展及 provider，不携带 caeoj_tools。

考生从已解压材料根目录一次普通安装：`python -m pip install .`。Harbor 构建时提前安装。公开命令为 validate-input、validate-output、grade、info 和 --version，主入口始终是 `python -m caeoj`；生成、发布和 smoke 命令只属维护侧。

## 当前归属与注册

- `src/caeoj/`：通用数组、对象、Schema、诊断、几何、基础 SDK、评分和 runtime；不写物理模型／章节分派。
- `qbank/extensions/caeoj_ext/fluid/`：single_phase、thermal_flow、turbulence、multiphase、thin_film、depth_averaged、rarefied、complex_fluid；公共声明与几何适配按需复用。
- `qbank/extensions/caeoj_bundle/runtime.json`：可信开发注册描述，包括 extensions、tasks、SDK aliases、旧模块 modules 和模型名字空间诊断；当前135题均显式绑定。tasks 的值是直接扩展 ID 列表，空列表明确表示该题使用通用声明检查，不是遗漏装配。
- `src/caeoj_tools/`：定位题目、策略读取、作者入口、依赖锁定与装配。publish_dist.py、prepare_harbor.py 仍为现有维护命令入口，均消费同一装配逻辑。
- smoke-test 的 examples、smoke 在其 author 目录，维护工具显式加载。测试使用维护 loader，不从核心借题库根路径。

扩展按物理组织，章节重排不改扩展 ID。旧 cfd-2.1 与 fluid-* 输入标识保持兼容，不能因迁移模块重写冻结数据。

## 描述字段与检查接口

每项 extensions 描述声明以下实际支持字段；未使用的能力不必填：

| 字段 | 意义 |
|---|---|
| version | 正整数版本，记录在安装装配中 |
| requires | 必需的其他扩展 ID，先加载依赖；拒绝缺失和循环 |
| requires_versions | 可选的依赖 ID 到精确整数版本映射，必须同时出现在 requires；不满足则阻止发布 |
| selectors | 若干匹配对象，任一个匹配则启用；键为清单点路径，后缀 _prefix 明确表示字符串前缀。选择器来自维护描述，不能由输入指定代码路径 |
| files | 显式公开代码／资源白名单，目标必须在 caeoj_ext/ 或 caeoj_task_ext/ 下；不能覆盖核心或安装元数据 |
| schemas | package:resource 相对资源路径，必须在 files 内 |
| schema_overrides | 仅允许使用核心 public-runtime.json 明确列出的扩展点；不同扩展不能轮流覆盖同一点 |
| check | module:function，接收已通过通用检查的 problem、errors，追加标准诊断；无额外检查时省略 |
| geometry | 是否需要网格连接关系与节点坐标等较昂贵的几何信息 |
| condition_compatibility | module:function，接收 problem、condition、field_spec；返回 None 表示沿用通用关联规则，True／False 表示该领域的关联判断 |
| dependencies | 可选 PEP 508 Python 依赖要求，与核心依赖合并后验证并锁定完整传递闭包 |

Schema 由核心结构和所需扩展片段组合，仍严格拒绝未知键。不同类型／枚举／约束的同名定义不能按加载顺序覆盖；相同定义去重，allOf 添加约束。当前核心仅开放条件 data 的 minProperties 这一明确扩展点，以保留既有 CFD 与普通输入的差异；开放新点属于核心接口变更。

语法层先检查 JSON 结构，不因未登记的物理名字抛出非结构异常；完成结构检查后，注册检查拒绝保留名字空间中的未知模型。开发 provider 支持无 task 的旧输入，仍按物理声明检查。严格公开包无 task 时仅可使用唯一题目绑定；多题包无法确定归属时明确报错。已有 task 的类型错误属于输入错误，不得直接用来查字典导致 traceback。

任务绑定要求的扩展不能因缺少或错误声明而静默跳过。校验报告的 scope 区分通用结构、声明扩展与已装配题目契约；这些状态均不证明物理适定或数值准确。

## 题目专用扩展

普通题目复用现有扩展，只需在可信 tasks 表中显式绑定，不修改核心和发布器。确需题目运行代码时，可以新增本题 `extension/runtime.json`，使用上述扩展字段并增加唯一的 `id: task.<name>`；其 files 相对 extension 目录，例如 `caeoj_task_ext/<name>/__init__.py`。该扩展可以依赖共享扩展；其整个目录不会递归公开。

题目特有检查必须对应 instruction／DATA 的公开约束。参数、阈值与资源差异使用现有数据／配置，不为这些差异制造 Python 模块。当前自定义运行钩子用于契约检查；需要新评分指标时仍先修通用指标或设计明确的评分接口，不能把参考解包装成检查扩展。

## 装配与交付

`caeoj_tools.assembly.runtime_materials({task: task_directory, ...}, root)` 返回公开运行文件及严格装配描述。它验证依赖、版本、模型重复注册、Schema 冲突、路径和发布白名单，生成安装元数据及 caeoj_bundle 包资源。runtime 只从已安装的固定 provider 读取可信目标，不扫描输入指定的插件，也不按工作目录找维护仓库。

构建环境的全部有效 Python 依赖及传递依赖被精确锁定，验证安装版本、Python 要求、markers 与 extras；缺包、冲突和不可核实 URL 依赖阻止发布。锁定依据构建环境，不等于另一 OS／架构已经可安装；面向其他平台仍须执行安装与运行验证。

装配身份包含版本、依赖、绑定和公开运行文件哈希，不包含隐藏数据清单。MANIFEST 另外绑定公开材料。未安装领域扩展的独立核心只能宣称通用结构检查；严格题目包缺支持则报工具错误，不降级通过。

发布器在写 ZIP 前调用 `validate_public_runtime(files)`，隔离加载暂存的公开闭包，验证样例输入、输出及策略。开发 provider 检查通过不能代替这一步；它同样不能代替普通安装与目标平台测试。

单题发布：

```sh
python src/utils/publish_dist.py --task heat-conduction-steady-2d
```

多题一次装配，重复 --task：

```sh
python src/utils/publish_dist.py --task heat-conduction-steady-2d --task heat-conduction-transient-2d
```

单题产物名保持 `<task>-agent.zip`；多题为稳定题集摘要命名的 ZIP。装配器合并依赖与材料，考生不覆盖安装多个单题 ZIP。Harbor 当前 prepare 入口仍逐题准备，但单题公开安装机制相同；多题包支持不表示已经有多题联合 Harbor 调度。

候选与 verifier 使用同一公开装配。隐藏数据、私有参考、运行资源设置和受信任 judge 由后端另行组装；正式判分不使用考生改写的本地代码。发布后内容变更会使旧包过期，prepare 拒绝沿用。

## 稳定调用与验证

基础 SDK 的名称、返回结构、数组 key／IDs 行为不因领域拆分改变。旧领域模块由通用别名加载器映射到扩展；SDK 的 params=、mass= 等旧关键字由独立适配保持。旧模块与 SDK 中同名但签名不同的周期配对函数分别兼容，不能混用。别名不把领域实现放回核心。

变更后至少检查实际依赖闭包、非法输入、旧接口、独立公开包和相关回归；安装验证使用普通 wheel 安装、移走源码并换目录，不能由 editable checkout 掩盖遗漏。临时 fixture 只证明工具，不代表正式案例、可信参考或预算校准。实施证据见[重构记录](../design/reviews/runtime-refactor.md)。

第四章新增通用entities身份表和multibody.mechanics共享声明检查，不使用伪points坐标，不扩充发布器文件清单。12题普通安装与CLI／SDK验证及平台限制见[第四章实施记录](../design/reviews/chapter-04-implementation.md)。

第五章新增thermal.transport共享热学声明检查与局部焓图映射，复用现有mesh／entities及SDK，无核心或发布器改动；13题独立普通安装与CLI／SDK验证见[第五章记录](../design/reviews/chapter-05-implementation.md)。

第六章新增acoustic.linear共享声学声明检查、封闭表面与接收点支持检查及自由场核组件，复用既有mesh／points／entities及SDK，无核心或发布器改动；10题独立普通安装与CLI／SDK验证见[第六章记录](../design/reviews/chapter-06-implementation.md)。
