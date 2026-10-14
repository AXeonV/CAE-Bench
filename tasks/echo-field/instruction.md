# 网格与场数据回传

实现一个程序，读取 `problem.json` 及其引用的 `.msh`、`.h5`，将输入场按 `outputs` 要求原样写入结果 HDF5。保持实体、时间、分量和数值的对应关系。

启动方式：`python solve.py --input problem.json --output result.h5`。

通用数据协议的完整约定见 `docs/CONTRACT.md`。元数据满足 `src/caeoj/problem.schema.json`；输入场由 `fields` 描述。本任务中 `fields` 与 `outputs` 的描述完全相同，这属于回传任务规则，不是通用协议限制。

输出必须包含要求的场数组，以及它们引用的固定 IDs 和时间轴数组；不得增加或遗漏 key。所有场保留时间、实体和分量轴，即使稳态或标量也不省略轴。SDK 可协助复制支持数组，但不纠正错误数据。

可以调用 `caeoj validate-input` 和 `caeoj validate-output` 检查结构。检查工具不提供参考值比较。每例输出结构合法且所有回传场值满足 `|结果−输入| ≤ 1e-6 + 1e-5×|输入|`，整数／布尔值完全一致得 1 分，否则得 0 分；比较标准 HDF5 读取后的数值，不比较压缩或文件字节。此题不涉及物理求解。
