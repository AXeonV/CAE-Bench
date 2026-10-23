# 梯度电极锂库存：来源、制作与验收

来源为[PyBaMM #5810](https://github.com/pybamm-team/PyBaMM/issues/5810)及[PR #5813](https://github.com/pybamm-team/PyBaMM/pull/5813)。基线07d642caa864aecb5032d241cd70e3f36958535e，修复来源bd572504ebf6619e14d4e0f26d4809ee407fd685。PR完整实现包含依赖判断和除法平均两项改动；本题只应用前者的`_is_independent_of`函数，保留基线除法规则。最小参考SHA见source.json；不是将另一缺陷悄悄纳入隐藏评分。

## 环境与源码

共享运行依赖镜像来自已验收19.4.2的`caeoj-pybamm5859-core:offline-sdk`；本题删除其中求解器源码，再安装自己固定的真实基线，替换可信driver与CMake。不会把19.4.2修复带入本题基线。全部常规源码按归档逐文件校验；链接核查复用19.4.2的固定归档核验器。无Git元数据的版本号显示0.0.0，源码身份以提交／归档／树清单为准。

```sh
python -m pip download --only-binary=:all: --require-hashes -r <本题>/author/runtime-requirements.txt --dest <wheel缓存>
python <本题>/author/prepare_runtime.py --work <缓存目录> --wheel-dir <wheel缓存> --build --docker <Docker路径>
```

缓存目录需有固定base.tar.gz和fixed.tar.gz，缺少时脚本通过上游HTTPS下载并验证固定SHA。构建工具为固定纯Pythonwheel；脚本核对每个wheel哈希，Docker构建禁网。运行时源码与依赖分别来自固定基线归档和共享公开运行环境，实际镜像ID见runtime-images.json。

## 状态、参考与数据

本题是给定有限体积状态的观测修复，不积分DFN轨迹。浓度变量保留真实粒子主域、电极辅助域；真实r_average、TotalConcentration、参数处理和FV离散生产输出。driver只构建该真实接口的输入表达式与返回输出；独立代数核对在作者制数流程，不在可信驱动中修正库结果。

```sh
python <本题>/author/generate.py --output <数据目录>
python <本题>/author/replay.py --dataset <数据目录> --image caeoj-pybamm5813-reference:fixed --mode reference --docker <Docker路径>
python <本题>/author/replay.py --dataset <数据目录> --image caeoj-pybamm5813-core:base --mode defect --docker <Docker路径>
```

首次参考在真实基线镜像只读挂载最小修复文件产生，报告记录overlay SHA；随后独立最小参考镜像重放14/14并核对全部存储参考。独立核查按公开分片常数、球壳差立方和厚度权重直接求和，不使用PyBaMM平均实现。14例共84个状态，修复14/14、原件5/14；独立误差最大约8.63e-8个评分容差，实际逐例参考运行最大约3.99秒。常体积分数、常浓度、径向变化、零值和饱和值作为非触发回归，另覆盖正反相关、相反两极梯度、随机非线性分布、不同分辨率与尺度。

用现有DATA-SYNC流程pack、upload、assemble、verify，不另写同步。稳定ID为caeoj-190401，固定HF分支cases/repair-22-20261023提交d557494b9b02a9b91822981877e17c292129ad6e。公开样例01、02分别与两个计分case共享身份；计分14例为公开2、隐藏12。固定提交装配与strict核验见hf-fixed-assembly.json及hf-strict-verification.json。

## 实际验收与边界

独立设计和三文件考生审阅通过，公开考试材料审阅读取两个样例并按公开定义复核432个分量。audit_data.py遍历全部14例和2样例，核对全部输入／输出、评分绑定及8种非法变体。公开ZIP已发布并经Harbor普通装配安装，独立Oracle `repair22-inventory-oracle-v1` complete=true，14/14，exception_info=null；它消费的数据与HF固定提交装配一致。

六种实际后端探针全部通过：真实模块／pyc路径和源码／缓存哈希绑定、未来缓存强制重建、语法错误、额外文件、符号链接、基线依赖损坏的基础设施分类及候选导入死循环的实际超时退出。valid还核查UID1000、限定路径访问权限和4CPU/8GiB cgroup值。权限使用os.access，网络只试一个目标连接，进程清理只覆盖该导入死循环；不据此宣称任意候选代码的全系统安全证明。共享Python后端适配及C++回归的独立审阅归19.4.2/backend-review.md，本题未再更改共享框架。

全部来源、运行、审阅、数据及版本证据见data-evidence。原始完整临时日志在运行缓存；没有收费模型Benchmark成绩，不把Oracle称为考生模型实测。输入是作者按真实缺陷机理改编的有限体积状态，不冒称上游循环实验或独立电池实验。
