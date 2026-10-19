# PDEBench 归档 case 池

这三个数据池直接保留 PDEBench 轨迹，题目身份由各自 data-manifest.json 拥有，迁移范围见[执行规划](../../design/pdebench-hf-migration.md)。它们不沿用旧题的初态重解释或替代参考。

- [平流](pdebench-advection-1d/instruction.md)
- [Burgers](pdebench-burgers-1d/instruction.md)
- [可压缩流](pdebench-compressible-1d/instruction.md)

每例可按标准工具装配和读取。当前为数据迁移池，正式评测的完整物理题意、容差、资源和选样另行确定；归档身份验收不等于独立数值认证。正式清单保持为空，试验选择绑定在云端批次记录。

## 本地按需取用

安装维护工具后，使用[标准数据池流程](../../maintenance/DATA-SYNC.md)。以下以平流为例，Burgers 和可压缩流将 task 分别改为 `pdebench-burgers-1d`、`pdebench-compressible-1d`。

```sh
python -m pip install -e '.[maint]'
caeoj-maint data list --task pdebench-advection-1d --limit 5
```

从列表取得 case ID 和固定 `revision`。为避免把开发试用写入正式选样，先在忽略的 `work/` 下建立独立工作区，再选择、装配和严格校验：

```sh
mkdir -p work/pdebench-local/qbank/01-prescribed-pdes/pdebench-archive
cp -R qbank/01-prescribed-pdes/pdebench-archive/pdebench-advection-1d work/pdebench-local/qbank/01-prescribed-pdes/pdebench-archive/
caeoj-maint data select --root work/pdebench-local --task pdebench-advection-1d --revision <列表返回的完整提交SHA> --case '001=<case-id>'
caeoj-maint data assemble --root work/pdebench-local --task pdebench-advection-1d --revision <同一完整提交SHA>
caeoj-maint data verify --root work/pdebench-local --task pdebench-advection-1d --strict
```

`select` 只取元数据；`assemble` 下载所选 case 所在的完整 TAR，复用缓存并核验摘要，然后装配 `cases/001/` 与 `reference/001/`。这不是按字节范围只取单例，少量 case 也可能涉及多个数据片；不要全仓库下载。空的正式清单不会自动选取 25 万条，开发选样不会替代正式评测子集。
