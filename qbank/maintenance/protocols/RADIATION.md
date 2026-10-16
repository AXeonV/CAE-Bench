# 辐射输运与核工程声明维护

本文件仅供维护，不增加题意，不进入考生包。实际物理、字段、矩阵轴和观测定义逐题完整保存在第十五章instruction及DATA。通用结构仍为docs/CONTRACT.md，无核心表示修改。

共享能力`radiation.nuclear`位于`qbank/extensions/caeoj_ext/radiation/`。可信runtime.json显式绑定八个slug及八个精确model，保留`radiation-`名字空间诊断E_RADIATION；输入不能加载代码。models.json是公开检查资源，白名单与实现一起装配，考生无注册或额外阅读要求。SDK沿用caeoj.sdk，未增加领域辅助求解器。

检查覆盖：参数单位及整数、真实entities／points、层顺序与界面净距、群及核素矩阵轴形状、非负率、缓发组和、裂变谱和、分支列和／对角／稳定核素列／衰变无环、独立控制与请求时间、准确quantity和输出形状及规模。检查不求解输运、临界、动力学或库存，不证明参考正确性、适定性或预算可达性。physics沿用核心的typed field引用，不需领域Schema片段；领域组合由扩展检查，不放松核心未知键检查。

维护文档展开器：`python qbank/maintenance/authoring/build_radiation.py`，仅写八题文档、配置和公开模型检查资源，不生成数值数据。重生成后核对最终审阅散列，不可借模板恢复已清理的跨题段落。

验证：`python -m unittest discover -s tests -p test_radiation_contract.py -v`。独立安装审计：`python tests/radiation_install_check.py --work runs/authoring/chapter-15/install-new`，要求新空目录；它创建临时协议fixture、全新venv、普通安装、移开装配源目录并用-I从其他目录运行CLI及SDK。依赖须可获取，命令不发布评测。Windows某些沙箱临时目录不允许HDF5写入，应使用授权的测试环境，不能将权限失败解释为契约失败。

配置消费沿用grading v2 quantity+unit绑定，以及prepare_harbor.task_config资源合并；没有数据时不运行publish_dist或prepare正式入口。详细验证和剩余限制见[第十五章进度](../../design/reviews/chapter-15-progress.md)。
