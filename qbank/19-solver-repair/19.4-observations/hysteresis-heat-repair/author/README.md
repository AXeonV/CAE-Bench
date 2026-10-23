# 开路电势滞回热源：制作记录

本题已完成真实源码、独立参考、数据入池、可信判题及各阶段独立审阅。来源PyBaMM issue3867及PR4893；维护者在issue评论明确PR已解决所报遗漏热源。基线273ccd4ec832efd9d5d783aa51a4421a4d8f70e4，修复来源f04a1f8ed421fc4653071eaa089be9b85b0855de，实际只替换thermal/base_thermal.py，不引入PR中的OCP状态模型与参数接口重构。原文、固定归档及最小文件SHA见data-evidence/source.json。

该旧库声明Python>=3.10,<3.13且NumPy<2；当前SDK需NumPy>=2。运行环境使用Python3.11，真实求解器在/opt/solver-venv的NumPy1.x，SDK在根环境NumPy2.x；固定协议转换器通过JSON调用真实求解器解释器，不放宽依赖声明或在驱动补热源。Dockerfile固定官方Python镜像digest，最终实际依赖版本和镜像ID在验收时记录。

```sh
python <本题>/author/prepare_runtime.py --work <缓存目录> --build --docker <Docker路径>
python <本题>/author/generate.py --output <数据目录>
python <本题>/author/replay.py --dataset <数据目录> --image caeoj-pybamm3867-reference:fixed --mode reference --docker <Docker路径>
python <本题>/author/replay.py --dataset <数据目录> --image caeoj-pybamm3867-core:base --mode defect --docker <Docker路径>
```

首次真实reference在双环境原型基线中挂载唯一固定修复文件产生，报告记录overlay与driver哈希。14例覆盖单/双相、两电极开关、混合相开关、零流、零差值、非零反应/可逆热、允许的负瞬时贡献、几何尺度与明确的闭环状态；全部参考已用独立输入热与几何账本核对。最终最小参考镜像已重新执行全部14例并通过；原始基线3/14通过，对应无滞回、零电流及零电势差回归。真实参考逐量误差及容差比例记录在[重放](data-evidence/reference-replay.json)，最终镜像一致性在[再次验证](data-evidence/final-reference-validation.json)。所有正式输入为依缺陷机制新设计的工况，不冒称来自上游原例。

范围设计和三文件考生审阅已经通过，记录在data-evidence；它们不替代运行验收。闭环状态只用于有明确路径的额外能量核对，不把任意瞬时状态或这批作者新增工况冒称上游完整电池循环实验。

## 实际验收证据

- 正式Harbor Oracle `repair22-hysteresis-oracle-v1`：1次Oracle trial、14/14、reward1、exception为空；冻结提交、逐例结果和真实原件/候选强制编译回执见[Oracle](data-evidence/oracle.json)。没有调用收费模型考生。
- [实际后端探针](data-evidence/backend-probes.json)：有效修复即使缓存时间戳在未来也强制重编并加载冻结源码；语法、额外文件和符号链接按候选错误拒绝；真实依赖故障归基础设施；实际导入候选死循环触发逐例超时并清理进程。低权限路径检查包含两个解释器、源及缓存、driver、构建规则和导入配置；无网、4CPU/8GiB实际限制得到核对。有限探针不等于完整容器安全认证。两处历史探针自身的HOME/解释器路径错误已修正，未因此改动正式运行环境或评分规则。
- [三组闭环功核查](data-evidence/loop-energy-check.json)：明确指定各1秒的两态充放电，电荷平衡且平衡OCP功相消；真实库热积分与另算支线功之差在7.22e-16J内。它只核查给定局部热源的能量账本，不是DFN演化或完整电池循环实验。
- 14例共84状态及2公开样例通过[实际数据审计](data-evidence/data-audit.json)；2样例的全部输出另经[独立考试材料审阅](data-evidence/candidate-exam-review.md)核查。公开包SHA、三文件SHA及检查限制保留在审阅记录。

HF稳定ID `caeoj-190403`，固定提交 `c2da4f591c0f5764226c9f0d0f12e70fbf13b89a` 已官方上传、从新缓存回取装配及strict verify；见[data-evidence中的上传/装配/核验回执](data-evidence/hf-fixed-assembly.json)。实际双解释器版本与镜像ID见[runtime-dependencies](data-evidence/runtime-dependencies.json)，维护摘要与原始日志分离。[独立全数据审阅](data-evidence/independent-data-review.md)与[独立后端审阅](data-evidence/backend-review.md)均通过；前者覆盖全部实际数据、两来源重放的payload与输出摘要，并独立验证6个合法及17个非法契约变体；后者核对正式Oracle冻结SHA、真实导入及依赖隔离。本题当前验收完成，完成状态以建设清单为准。
