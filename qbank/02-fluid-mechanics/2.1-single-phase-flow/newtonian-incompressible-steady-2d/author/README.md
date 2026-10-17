# 2.1.1 算例维护材料

- [初次制池与来源记录](data-evidence/supplement-20261017/README.md)：工况来源、Lethe 参考生产者、Ghia 中线比较、数值和资源验收、全部输入及判分链审计。
- [交付与选样入口](data-evidence/supplement-20261017/delivery.md)：固定 HF 分支及提交、20 个 case ID、逐例描述和显式指定 revision 的选样命令。
- [OpenFOAM 独立交叉验证](data-evidence/independent-openfoam-20261017/report.md)：其余 19 例的逐例差异、三档网格结果、判分链验证及局限；转换方法和复现命令见同目录 README。

正式数据清单只登记池位置，cases／samples 保持空。数据取得、装配与上传复用[数据池操作](../../../../maintenance/DATA-SYNC.md)；直接使用已交付的固定提交即可核验，不需重新运行历史建分支脚本。

求解器配置、执行日志、采样结果和摘要保存在上述证据目录。脚本及证据按原始字节入 Git，避免换行转换破坏记录的 SHA-256；其中 runs 子目录是维护证据，任务级忽略规则明确保留。大配置和原始场另存维护档案，位置、摘要和实际清理状态见相应证据记录。
