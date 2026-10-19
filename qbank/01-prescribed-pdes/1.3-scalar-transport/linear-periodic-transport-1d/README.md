# 一维周期线性输运维护入口

考生材料仅为 [instruction.md](instruction.md)、[DATA.md](DATA.md) 和通用 CONTRACT。题目属于从零建设的 [HF 迁移试验](../../../design/pdebench-hf-trial.md)，不是原 advection-1d 的静默替换；现有题目和正式选择不变。

来源为固定版本的 HF 平流初始数组与速度。输入显式定义原单元内的常数初态；参考由文献周期平移公式积分得到。归档后续帧只用于来源差异诊断，不能称为新连续问题的精确标答。实际公式、SHA 绑定、验证与远端提交见[试验验收](../../../design/reviews/pdebench-hf-trial.md)及本题 author/data-evidence。

云端执行步骤见[操作入口](../../../../src/utils/PDEBench/HF-TRIAL.md)。复用通用数据池工具，不在本机下载来源数组；数据只在云端生成、上传并按固定提交重新读取。题目定位清单采用空正式选择；试验验证选择单独保存，不默认纳入 benchmark。

评分模板由 author/grading-template.json 拥有，实际逐例 grading.json 随参考入 HF。judge-config.json 与 harbor/task.toml 保存声明的执行目标；实际 Solver 容器资源限额尚需验证，不能由参考生产或直接判分成功代替。试验没有运行 LLM 考生。
