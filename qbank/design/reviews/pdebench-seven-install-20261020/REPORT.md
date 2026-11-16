# 七题 DaRUS 本地制数、安装与消费验收

**已完成：七题各 20 条独立轨迹、20 个计分 case，其中 2 个引用为公开 example；合计 140 case、14 example。** 已安装到本仓库对应题目目录，未修改题面、DATA、评分和运行限额。不是模型评测，也不是独立的连续 PDE 精度或收敛认证。

冻结选择 SHA256 为 `267cdac230cc4680ba3b9ed5affdfab89b0c22283afaf71a3560c48e55590e5d`。来源、轨迹、原始帧及公开身份见 [selection.json](selection.json)，输入配方见 [spec.json](spec.json)，排重依据见 [selection-design.json](selection-design.json)。140 个来源文件与轨迹索引组合唯一，各题初态摘要不重复；14 个公开 example 与所属 case 共用身份并保留计分资格，不增加独立轨迹数。

## 安装结果

| 题目 | case / example | 题目目录 |
|---|---:|---|
| advection-1d | 20 / 2 | [advection-1d](../../../../qbank/01-prescribed-pdes/1.3-scalar-transport/advection-1d) |
| burgers-1d | 20 / 2 | [burgers-1d](../../../../qbank/01-prescribed-pdes/1.5-advection-diffusion/burgers-1d) |
| compressible-navier-stokes-1d | 20 / 2 | [compressible-navier-stokes-1d](../../../../qbank/01-prescribed-pdes/1.7-coupled-systems/compressible-navier-stokes-1d) |
| compressible-navier-stokes-2d | 20 / 2 | [compressible-navier-stokes-2d](../../../../qbank/01-prescribed-pdes/1.7-coupled-systems/compressible-navier-stokes-2d) |
| diffusion-sorption-1d | 20 / 2 | [diffusion-sorption-1d](../../../../qbank/01-prescribed-pdes/1.2-diffusion-reaction/diffusion-sorption-1d) |
| reaction-diffusion-2d | 20 / 2 | [reaction-diffusion-2d](../../../../qbank/01-prescribed-pdes/1.2-diffusion-reaction/reaction-diffusion-2d) |
| shallow-water-2d | 20 / 2 | [shallow-water-2d](../../../../qbank/01-prescribed-pdes/1.4-hyperbolic/shallow-water-2d) |

输入位于各题 `cases/001` 至 `020`，参考位于 `reference/001` 至 `020`，公开样例位于 `samples/01`、`02`。生成载荷与作者身份回执由 Git 忽略。上述三类已安装载荷合计 **1,760,678,530 字节（约 1.76 GB）**，不含缓存、工作区副本、公开包及 Harbor 副本；原目录已备份到本地运行记录中。

## 已执行的验收

- [完整制作与正反例校验](prepare-002.json)：140 条均 verified，参考回填控制逐例得分 1，错误值控制逐例得分 0；这是判题链自洽检查，不是独立参考精度验证。
- [安装核验](verify-installed.json)及[逐字节审计](installed-audit.json)：140 条安装输入与参考、14 份样例均与 stage 相同；实际加载输入与参考，核对时刻、有限值、输出形状及公开身份。22 份原题面/DATA 摘要不变。
- 七题均通过常规公开包发布和 Harbor 装配。[隔离消费结果](isolated-summary.json)：公开包离线安装为普通 site-packages wheel，无源码挂载；7 题共 140 条故意全零输出经真实 trusted judge 完成，均为 wrong_answer，没有 runtime_error，逐题保留 20 例分母和 2 个公开身份。
- 消费时使用已有 Linux AMD64 Docker 镜像、禁网及题目 CPU/内存配置，考生 UID 1000 无权读取 `/tests/reference`，并断言临时 `/tmp/new-tests` 副本不存在。早先四题临时验收 helper 曾复制后留下该临时副本，因此旧报告的隐藏参考隔离结论只覆盖 `/tests`；本轮改用移动并补充断言，完整隔离结论以本轮证据为准。这不是生产 judge 代码修改。

安装工具实现提交 aa3646b、相关说明及 fixture 隔离提交 f0637a7；此前 60 项相关回归和安装独立审阅已通过，本轮未无故重复实现测试。三道暂缓题及三维可压缩流未生成数据。

## 流量和费用

累计响应体保守扣额 **2,541,985,750 字节（2.542 GB）**，低于用户授权的 2,600,000,000 字节，剩余 58,014,250 字节。实收完整响应体 **1,269,943,168 字节（1.270 GB）**，不含头、TLS 和链路重传。两者不可相加；保守扣额包含重定向的预扣。详见[累计账目](network-total.json)和[尝试一](prepare-001-network.json)、[尝试二](prepare-002-network.json)。

首次在 138 条时安全停止，历史见 [BUDGET-STOP.md](BUDGET-STOP.md)。用户提高累计上限后，复用 138 条完整回执及范围缓存补齐剩余两条，没有重新下载完整数据集。无新增 HF Jobs、模型调用、求解器调用或远端上传费用；本地计算与流量费用不按美元另行计价。

本批本地数据与消费验收完成，定时监视关闭；未 push、未发 PR、未合并 Git 分支。[机器汇总](acceptance-summary.json)保留逐题路径与数据量。
