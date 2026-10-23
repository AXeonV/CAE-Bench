# 开路电势滞回热源：制作记录

本题正在制作，尚未完成数据入池和可信判题验收，不计已完成。来源PyBaMM issue3867及PR4893；维护者在issue评论明确PR已解决所报遗漏热源。基线273ccd4ec832efd9d5d783aa51a4421a4d8f70e4，修复来源f04a1f8ed421fc4653071eaa089be9b85b0855de，实际只替换thermal/base_thermal.py，不引入PR中的OCP状态模型与参数接口重构。原文、固定归档及最小文件SHA见data-evidence/source.json。

该旧库声明Python>=3.10,<3.13且NumPy<2；当前SDK需NumPy>=2。运行环境使用Python3.11，真实求解器在/opt/solver-venv的NumPy1.x，SDK在根环境NumPy2.x；固定协议转换器通过JSON调用真实求解器解释器，不放宽依赖声明或在驱动补热源。Dockerfile固定官方Python镜像digest，最终实际依赖版本和镜像ID在验收时记录。

```sh
python <本题>/author/prepare_runtime.py --work <缓存目录> --build --docker <Docker路径>
python <本题>/author/generate.py --output <数据目录>
python <本题>/author/replay.py --dataset <数据目录> --image caeoj-pybamm3867-reference:fixed --mode reference --docker <Docker路径>
python <本题>/author/replay.py --dataset <数据目录> --image caeoj-pybamm3867-core:base --mode defect --docker <Docker路径>
```

首次真实reference在双环境原型基线中挂载唯一固定修复文件产生，报告记录overlay与driver哈希。14例覆盖单/双相、两电极开关、混合相开关、零流、零差值、非零反应/可逆热、允许的负瞬时贡献、几何尺度与明确的闭环状态；全部参考已用独立输入热与几何账本核对。最终基线/最小参考镜像仍需重新验证该完整数据集，随后按DATA-SYNC入池与固定提交核验、公开考试材料审阅及完整Oracle。

范围设计和三文件考生审阅已经通过，记录在data-evidence；它们不替代运行验收。闭环状态只用于有明确路径的额外能量核对，不把任意瞬时状态或这批作者新增工况冒称上游完整电池循环实验。
