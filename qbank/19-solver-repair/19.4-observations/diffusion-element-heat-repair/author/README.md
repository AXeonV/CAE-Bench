# 扩散元件电压与热功率：制作与验收

来源为[PyBaMM #5859](https://github.com/pybamm-team/PyBaMM/issues/5859)及[PR #5869](https://github.com/pybamm-team/PyBaMM/pull/5869)。基线`371b41d7db6246bddcd9fba4d1c6a20deeabf8b6`，修复`d76aed8f0152b790d088f298ebb25755f0d33485`。本题取真实扩散／热子模型的瞬时状态求值，不把这批作者改编状态冒充原帖完整充放电轨迹。

## 源码和环境

```text
python <本题>/author/prepare_runtime.py --work <缓存目录> --build --docker <Docker可执行文件>
```

脚本核对两个归档SHA、所有常规源码文件与已有解包／context缓存，再生成原件和只替换两个修复文件的参考镜像。归档中的五个文档链接在Windows可能被跳过或复制，只允许该明确列表及精确内容；不会因此放过其他差异。源码闭包、许可证与白名单由该脚本生成；源码包和`author/generated`不进Git。归档无Git版本元数据，安装版本显示0.0.0，实际身份以提交和归档哈希为准。

`public/driver.py`调用真实PyBaMM子模型、参数处理及有限体积边界求值，`public/run_case.py`只转换协议。源码位于构建子树内，两个真实导入pyc由固定CMake目标产生并强制删除重建，不能仅通过未来缓存时间戳跳过候选构建。`baseline_probe`在候选替换前实际导入SDK运行依赖并调用一个非触发状态；原件故障归基础设施，候选语法错误和候选运行故障另记。

部署配置使用本地镜像别名`caeoj-pybamm5859-core:offline-sdk`，正常构建脚本默认将其指向原件镜像，Harbor可在线安装公开SDK依赖。若包索引不可达，可以使用已有、具有所需依赖的本地SDK镜像：

```text
python <本题>/author/prepare_offline_sdk.py --work <新的空缓存目录> --build-tools-site <setuptools和wheel的site-packages目录> --sdk-image <已验证SDK镜像> --docker <Docker可执行文件>
```

该操作只从SDK依赖镜像复制site-packages和Gmsh共享库，不复制其私有tests、reference、提交或日志。纯Python构建工具通过标准wheel工具从已安装分发重新打包，版本／哈希明确记录，不冒称下载轮子的原字节。离线部署别名包含相同求解器源码及SDK缓存；运行计划须固定实际镜像ID，不能仅认同名标签。导入路径、cache_tag、源码与pyc哈希、权限以及实际输出由容器探针与最终Oracle核查，复制目录本身不是绑定证明。实际采用的依赖来源见`data-evidence/offline-sdk.json`。

## 制数和数值核对

```text
python <本题>/author/generate.py --output <数据目录>
python <本题>/author/replay.py --dataset <数据目录> --image caeoj-pybamm5859-reference:fixed --mode reference --docker <Docker可执行文件>
python <本题>/author/replay.py --dataset <数据目录> --image caeoj-pybamm5859-core:base --mode defect --docker <Docker可执行文件>
```

generate只生成输入与独立代数核对量，reference必须由replay实际调用固定修复后的PyBaMM产生。独立核对采用线性分布精确表面值、OCV多项式直接求值和输入电流／元件功率账本，分别核对全部状态的四个输出。

首轮参考生产在实际原件镜像中只读挂载两个固定上游修复文件，并保存overlay哈希；随后独立构建的最小参考镜像用`--mode validation`对全部参考重新验证。实际生产者与镜像身份以逐次报告为准，不将作者独立核对数组标作PyBaMM输出。

16个case共192个独立状态，覆盖放电、充电、分布未翻转的反向电流、非线性OCV、零电流、均匀分布、关闭扩散、多RC热源、正负可逆热及不同采样数。原件3/16，固定修复16/16，全部独立核对通过。它们验证公开瞬时问题族的本批工况，不证明完整扩散轨迹或电池温度演化正确。

## 数据与可信执行

数据池稳定ID为`caeoj-190402`，按仓库DATA-SYNC执行pack、专用HF分支上传和固定提交取回；数值数据不进Git。公开01／02与两个计分case共享身份，计分16例中公开2、隐藏14，不能称16个未见case。

装配后运行`audit_data.py --output <报告路径>`，覆盖全部16例与2样例、评分绑定、公开输出及8类非法变体。随后使用现有publish_dist／prepare_harbor装配，并以Oracle实际走通完整可信编译及全部逐例评分。`backend_probe.py`在单独私有verifier镜像中测试未来pyc时间戳、实际导入路径与源／pyc绑定、只读隔离、非法提交、可信依赖损坏及候选导入死循环的进程组超时；不能把有限探针解释为整个容器的安全证明。

实际审阅、数据、运行报告和版本绑定在`data-evidence/`；完整临时日志留runs及工作缓存。准备过程中外部HTTPS失败与SDK缓存漏Gmsh共享库曾导致Oracle基础设施失败，均保留原始记录，没有记成考生数值零分，也没有追加收费模型运行。
