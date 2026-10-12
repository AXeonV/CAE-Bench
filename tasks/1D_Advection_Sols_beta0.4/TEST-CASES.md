# 测试点设计

12 个预先选定的官方完整样本。每点 1024 个单元、201 帧，t=0～2 s；所有实际空间和时间数据均参与逐值判分，不重采样、不截断轨迹。

| 测试点 | 官方 tensor 样本索引 | 公开示例 |
|---|---:|---|
| 01-official-0000 | 0 | samples/01 |
| 02-official-0001 | 1 | samples/02 |
| 03-official-0002 | 2 | — |
| 04-official-0003 | 3 | — |
| 05-official-0004 | 4 | — |
| 06-official-0005 | 5 | — |
| 07-official-0006 | 6 | — |
| 08-official-0007 | 7 | — |
| 09-official-0008 | 8 | — |
| 10-official-0009 | 9 | — |
| 11-official-0010 | 10 | — |
| 12-official-0011 | 11 | — |

初始场直接取官方首帧，包含不同模式、振幅及局部形状，不用自定义函数替代。源数组哈希见 `author/SOURCE.json`，每点转换映射见 `reference/<case>/certificate.json`。历史速度修复、未对应任何帧的额外时间坐标与误差阈值依据见 [DESIGN.md](DESIGN.md)。
