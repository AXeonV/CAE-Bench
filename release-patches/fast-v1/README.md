# RC5 / RC6 快速版支持补丁 fast-v1

本补丁是只读选题工具，不修改 catalog、qbank.zip、公开包、题面、输入、参考、评分、时限或历史成绩。适用于原 RC5（先应用 rc5-environment-v1 环境补丁）、RC6，以及 RC7。

保留74题，排除8题：transition-gas、incompressible-navier-stokes-2d、compressible-navier-stokes-2d、compressible-navier-stokes-3d、thermal-rans-3d、viscoelastic-steady、rans-steady-3d、reaction-diffusion-2d。名单为固定 fast-v1，不根据每次机器耗时动态变化。

## 使用

将补丁解压到完整发行目录之外。ROOT 是已恢复并解压的原发行目录。

```sh
python ROOT/release.py verify
python fast.py --root ROOT list
python fast.py --root ROOT manifest > fast-manifest.json
python fast.py --root ROOT extract darcy-flow-2d EMPTY_TARGET
```

调度器只运行 manifest 中的74个tasks，每题保持全部正式case及原资源配置。模型、重试及并发由运行方显式冻结；本工具不调用模型。extract拒绝快速集之外的题目；提取沿用原 release.py 的完整性及安全检查。

RC5必须先按 rc5-environment-v1 的说明修复每个生成任务的考生和判题环境并重建两侧镜像。本工具不自动安装或认证该环境补丁。RC6/7沿用发行包 environment/README.md。

每题按全部case连续score均值，快速版总分按74题等权平均，并明确标注 fast-v1；不能与完整82题成绩混作同一榜单。失败仍计入分母，不按已完成题目重新归一化。不使用遇错即停、不删case、不放宽时限。

筛选依据为既有本地提交的判分累计耗时：任一观察超过60分钟的8题。其他题也可能随模型程序变慢；不是硬性运行时间保证。原参考数值资格和异机资源限制继续适用。
