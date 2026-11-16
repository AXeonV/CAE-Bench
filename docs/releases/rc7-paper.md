# RC7 论文冻结快照

本快照对应论文实际使用的 82 题、647 个正式算例。论文成绩覆盖其中的 80 道计算题和 630 个计算算例。主分支维护这 82 道题，其他题目和章节的开发资料见 `dev`。旧的 [fast-v1](rc7-fast-v1.md) 是独立的历史子集。

[冻结配置清单](../../release-patches/rc7-paper/PROFILE.json)列出题目、逐题判题配置、HF 资源声明和修正后的开发配置。论文的历史运行还包含旧版开发配置和 Gemini 本地 Harbor 批次，逐题运行记录见论文补充材料。历史 HF 镜像标签没有固定的镜像摘要。

公开 ZIP 内有 82 个独立的考生包。解开所需题包后，按其中的 README 安装工具和题目依赖。完整评测所需的正式输入、参考解和逐例判分文件由维护者本地保管。630 个计算算例使用 RMS NRMSE，基础设施用例保留原判分。

可以通过 [GitHub Release 下载 ZIP](https://github.com/AXeonV/CAE-Bench/releases/download/caeoj-qbank-20261029-rc7/caeoj-qbank-rc7-paper-public.zip)，也可以通过 [Hugging Face 下载同一 ZIP](https://huggingface.co/datasets/jimzhouzzy2006/CAE-Bench/resolve/main/caeoj-qbank-rc7-paper-public.zip?download=true)。

## 本地构建与校验

先用论文仓库的 `scripts/rebuild_evaluation_snapshot.py`，按论文清单从 RC6 基础归档和评测 overlay 重建全部任务。再用以下命令生成公开 ZIP：

```sh
python release-patches/rc7-paper/package_snapshot.py --reconstructed <reconstructed-dir> --supplement <paper-supplement-dir> --output <empty-output-dir>
```

脚本逐个读取生成的考生题包，核对文件列表和内容哈希，并在本地检查 RMS 判分数量。`VERIFICATION.json` 记录公开 ZIP 的 SHA-256。
