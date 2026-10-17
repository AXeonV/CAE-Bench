# 交付记录

后续独立交叉验证已完成：19 例 × 3 档 OpenFOAM 实算，原参考及 HF 提交不变。逐例结果见[独立验证报告](../independent-openfoam-20261017/report.md)。

HF main 起点：`d46b17a03d444646157e1e2fe4b4f00587dc5d89`。指定分支：`cases/2-1-1-supplement`。最终提交：`fbe115effe8131bd575c0cde1c9ca87a9d87fd3a`。

[固定提交中的数据池](https://huggingface.co/datasets/jimzhouzzy2006/CAE-Bench-OJ/tree/fbe115effe8131bd575c0cde1c9ca87a9d87fd3a/qbank/02-fluid-mechanics/2.1-single-phase-flow/newtonian-incompressible-steady-2d/pool)

20 例全部完成参考计算、全批接口审计、本地严格核验，以及固定提交重新获取后的严格完整性／参考／判分链路验证。HF main 未改变。正式 cases／samples 均保持空；首次创建的 data-manifest.json 只登记池位置。

| 后续本地编号 | 名称 | Case ID | 内容 |
|---|---|---|---|
| 001 | force-island-chamber | `case-026d4fd42eeba2d5268e1be8` | 内岛障碍物＋旋转型体加速度 |
| 002 | force-split-recess | `case-e8f85c3a1f5574b5b7210265` | 两个深侧凹槽＋随 x 变化的竖向体加速度 |
| 003 | force-three-ribs | `case-4c8211e10cfe6755bdc61e0e` | 三块不等高底肋＋剪切型体加速度 |
| 004 | four-wall-circulation | `case-0e6015c13e8f493dbf620799` | 四侧切向运动形成整体环流 |
| 005 | lid-central-pedestal | `case-dbefd5f506818454526b5154` | 中央底台阶＋运动顶壁 |
| 006 | lid-cross-chamber | `case-3fe4488e94450f59afd66166` | 十字形连通腔＋局部高位运动顶壁 |
| 007 | lid-L-chamber | `case-fda4785a3d9d80b6a0822fb6` | L 形凹域＋运动顶壁 |
| 008 | lid-offset-baffle | `case-68c02a8d2b43c88ee8b57f70` | 偏置底部高挡板＋运动顶壁 |
| 009 | lid-serpentine-chamber | `case-9b46104936e50028823b2557` | 曲折串联腔＋运动壁及体加速度共同驱动 |
| 010 | lid-square | `case-546a59784b18a631bf12dd6a` | Re=100 标准方腔，Ghia 中线独立比对 |
| 011 | lid-square-obstacle | `case-3332523b90c9f1044dc4b9af` | 封闭方形内孔＋运动顶壁 |
| 012 | lid-staggered-islands | `case-a738752d73231f6a64c0f942` | 两个交错内岛＋运动顶壁 |
| 013 | lid-step-floor | `case-4585e0421691b3f39b24058f` | 不等高底面台阶＋运动顶壁 |
| 014 | lid-T-chamber | `case-f9894cc19c74db756546b5a9` | T 形主腔及下支腔＋运动顶壁 |
| 015 | lid-two-obstacles | `case-cfc58477001d526050bc651f` | 两块并列内障碍物＋运动顶壁 |
| 016 | opposed-lids | `case-8f50767a53296e3d12436c21` | 上下壁反向运动，双侧剪切驱动 |
| 017 | opposed-side-walls | `case-154ee75bd3aeb1ff6008c91b` | 左右壁竖向反向运动 |
| 018 | rotational-force-square | `case-5b87a66b28e481e82ab5cf2b` | 全静止壁方腔＋非保守旋转型体加速度 |
| 019 | shear-force-slip-channel | `case-a50104253013998d8905d65e` | 剪切型体加速度＋侧面滑移、上下无滑移 |
| 020 | side-driven | `case-f5d5b32cc81a01f07530987b` | 单侧竖向运动壁＋封闭静止壁 |

全部 case 描述 SHA-256、输入身份及逐资产摘要在 catalog.json。来源、生产者、独立比对、数值和资源局限见 README.md。

在仓库根目录运行以下命令，生成明确包含这 20 例的临时选择；不会启动 benchmark，也不会修改正式清单：

```powershell
& ./qbank/02-fluid-mechanics/2.1-single-phase-flow/newtonian-incompressible-steady-2d/author/data-evidence/supplement-20261017/select-cases.ps1
```

等价命令：

```sh
python -m caeoj_tools.cli data select --task newtonian-incompressible-steady-2d --revision fbe115effe8131bd575c0cde1c9ca87a9d87fd3a --output work/211-supplement-benchmark-selection.json --case 001=case-026d4fd42eeba2d5268e1be8 --case 002=case-e8f85c3a1f5574b5b7210265 --case 003=case-4c8211e10cfe6755bdc61e0e --case 004=case-0e6015c13e8f493dbf620799 --case 005=case-dbefd5f506818454526b5154 --case 006=case-3fe4488e94450f59afd66166 --case 007=case-fda4785a3d9d80b6a0822fb6 --case 008=case-68c02a8d2b43c88ee8b57f70 --case 009=case-9b46104936e50028823b2557 --case 010=case-546a59784b18a631bf12dd6a --case 011=case-3332523b90c9f1044dc4b9af --case 012=case-a738752d73231f6a64c0f942 --case 013=case-4585e0421691b3f39b24058f --case 014=case-f9894cc19c74db756546b5a9 --case 015=case-cfc58477001d526050bc651f --case 016=case-8f50767a53296e3d12436c21 --case 017=case-154ee75bd3aeb1ff6008c91b --case 018=case-5b87a66b28e481e82ab5cf2b --case 019=case-a50104253013998d8905d65e --case 020=case-f5d5b32cc81a01f07530987b
```

选样命令已实际执行验证。以后装配和 benchmark 应继续固定本提交，按运行技能审核并使用生成的选择；本次未装配正式测试或冻结评测条件。

原始结果、详细审计和逐档记录已另存 HF 独立维护分支；固定提交、大小和摘要由上级目录的 [archive-index.json](../archive-index.json) 绑定。获取与装配见[维护入口](../../README.md)，不再要求访问工作站目录。

原始清理状态仍按执行时的事实保存在冻结证据中的 cleanup.json；本次迁移不改写历史记录。迁移后的取回、完整性及判分验证结果见上级目录 migration-validation.json。
