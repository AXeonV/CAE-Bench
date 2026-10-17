# 材料组织演化声明维护

本文件供维护使用。各题 instruction、DATA 与通用 CONTRACT 定义完整考生要求。

共享扩展 `microstructure.phase_field` 位于 `qbank/extensions/caeoj_ext/microstructure/`，检查周期矩形、初态模态、分量与保守幅值界、迁移率矩阵、公开尺度和时程等声明。复用核心 entities、points、field 引用和基础 SDK，不求解物理问题或修正输入。模型注册与白名单见[运行装配](../RUNTIME.md)。

`python qbank/maintenance/authoring/build_microstructure.py` 重建题面、DATA、执行配置、作者评分模板及公开声明资源，不生成数值数据。公开 `models.json` 经 `public_model_catalog` 剥离作者侧时限和容差；评分模板仅保存在本题 `author/grading-template.json`，制数时据此生成实际 case 配置，见[评测配置](../EVALUATION.md)。

专项测试：`python -m unittest discover -s tests -p test_microstructure_contract.py -v`。独立安装使用共享入口 `python qbank/maintenance/authoring/verify_install.py --domain microstructure --output runs/install-microstructure`，要求新的输出目录；也可追加其他 `--domain` 联合验证。临时 fixture 只验证工具链，不作为正式数据。

设计与历史验证见[本章进度](../../design/reviews/chapter-16-progress.md)。正式数据、独立参考、容差与资源校准及发布仍待完成。
