# 数据制作

本题的题面与 DATA 已按[2026-10-20核查](data-evidence/direct-20261020/REPORT.md)恢复四边零 Dirichlet。使用 [PDEBench 按需工具](../../../../../src/utils/PDEBench/README.md)显式选择 DaRUS 轨迹、生成 input/reference/example，并在隔离工作根接入现有评测。

```sh
python src/utils/PDEBench/prepare.py list --task darcy-flow-2d
```

随后按工具说明建立 spec，执行 plan、prepare、verify、assemble。默认不修改本题正式来源选择、不重新求解参考；来源适用性未通过时不进入评测。当前来源核查见 [direct-20261020](data-evidence/direct-20261020/REPORT.md)；既往制作配方与修正参考证据保留在 [reference](data-evidence/reference/)，不作为当前工具或本地数据就绪状态。

20条正式case与2个引用example的本地安装证据见[install-20261020/REPORT.md](data-evidence/install-20261020/REPORT.md)，五条临时回放是此前来源核查，不替代本批安装验收。

本题现有HF清单，按[统一数据获取流程](../../../../maintenance/PDEBENCH-DATA.md)装配；新制数先在隔离workspace完成。历史直接来源安装证据不作为HF下载回执，发布绑定见[记录](../../../../design/reviews/pdebench-hf-release-20261020/summary.json)。
