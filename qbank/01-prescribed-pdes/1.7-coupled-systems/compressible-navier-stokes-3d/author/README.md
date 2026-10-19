# 数据制作

本题的题面与 DATA 保持现有定义。使用 [PDEBench 按需工具](../../../../../src/utils/PDEBench/README.md)显式选择 DaRUS 轨迹、生成 input/reference/example，并在隔离工作根接入现有评测。

```sh
python src/utils/PDEBench/prepare.py list --task compressible-navier-stokes-3d
```

随后按工具说明建立 spec，执行 plan、prepare、verify、assemble。默认不修改本题正式来源选择、不重新求解参考；来源适用性未通过时不进入评测。既往制作配方与证据保留在 [reference](data-evidence/reference/)，不作为当前工具或本地数据就绪状态。
