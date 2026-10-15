"""Publish one task's public Agent materials as a reproducible ZIP.

Usage: python src/utils/publish_dist.py --task <task> [--output dist]
Only explicitly selected documents, shared tools and public sample assets ship.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
import zipfile

from caeoj.sdk import load_problem
from caeoj.task_paths import task_directory
from caeoj.grading_policy import task_policy, validate_policy, render_policy
from caeoj.validation import ContractError, validate_input, validate_output

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_FILES = ("pyproject.toml", "LICENSE", "docs/CONTRACT.md", "docs/GRADING.md")
TOOL_FILES = ("__init__.py", "__main__.py", "cli.py", "validation.py", "sdk.py", "storage.py",
              "problem.schema.json", "grading.py", "grading_policy.py",
              "grading_metrics.py", "grading.schema.json", "cfd.py", "mesh_geometry.py",
              "fluid_energy.py", "fluid_multiphase.py", "fluid_reduced.py")


def read_public_file(root, path):
    """No symlinks or files outside the source project may enter a release."""
    root, path = Path(root).resolve(), Path(path)
    relative = path.relative_to(root)
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink() or getattr(current, "is_junction", lambda: False)():
            raise ValueError(f"Public material must not be a link: {relative}")
    if not path.resolve().is_relative_to(root):
        raise ValueError(f"Public material escapes project: {relative}")
    return path.read_bytes()


def agent_readme(task_path):
    return f"""# 解题材料

阅读 `{task_path}/instruction.md`、同题 DATA.md 和 `docs/CONTRACT.md` 即可确定完整任务与数据规则。公开示例在 `{task_path}/samples/`；grading.json 与 GRADING.md 是供工具使用的评分策略及其可读表示。

安装共享工具：`python -m pip install -e .`。h5py、NumPy、Gmsh、jsonschema 是协议依赖；求解所需额外依赖由程序选择。

在理解输入、编写和调试程序时可随时使用：

```text
python -m caeoj validate-input {task_path}/samples/<sample>/input/problem.json
python solve.py --input {task_path}/samples/<sample>/input/problem.json --output result.h5
python -m caeoj validate-output --input {task_path}/samples/<sample>/input/problem.json --output result.h5
python -m caeoj grade --input {task_path}/samples/<sample>/input/problem.json --output result.h5 --reference {task_path}/samples/<sample>/output/result.h5 --grading {task_path}/grading.json
```

校验器只检查结构和引用，不验证或纠正物理结果。
可用 `caeoj.sdk` 的 `load_problem`、`read_constant`、`read_field`、`write_result` 读写数据，
示例见 CONTRACT.md 和题目 DATA.md。提交程序接口及支持范围以题面为准。

本包只含公开解题材料。MANIFEST.json 记录所含文件的 SHA-256。
""".encode("utf-8")


def collect_materials(task, root=PROJECT_ROOT):
    root = Path(root).resolve()
    task_dir = task_directory(task, root)
    task_path = task_dir.relative_to(root).as_posix()
    files = {}

    def add(path):
        files[path.relative_to(root).as_posix()] = read_public_file(root, path)

    for name in PUBLIC_FILES:
        add(root / name)
    for name in TOOL_FILES:
        add(root / "src/caeoj" / name)
    add(task_dir / "instruction.md")
    if (task_dir / "DATA.md").is_file():
        add(task_dir / "DATA.md")
    paths = sorted((task_dir / "samples").glob("*/input/problem.json"))
    if not paths:
        raise ValueError(f"No complete public samples in {task_path}/samples; add them before publishing")
    policy = task_policy(task_dir, load_problem(paths[0]), read_bytes=lambda p: read_public_file(root, p))
    files[f'{task_path}/grading.json'] = (json.dumps(policy, ensure_ascii=False, indent=2) + '\n').encode()
    files[f'{task_path}/GRADING.md'] = render_policy(policy).encode()
    samples = []
    for path in paths:
        # Check the path before allowing the contract loader to read it.
        add(path)
        manifest = json.loads(files[path.relative_to(root).as_posix()])
        assets = [manifest["data_file"]]
        assets += [item["file"] for item in manifest["geometries"].values()]
        assets += [item["file"] for item in manifest["meshes"].values()]
        for name in assets:
            asset = path.parent / name
            if not asset.resolve().is_relative_to(path.parent.resolve()):
                raise ValueError(f"Sample asset escapes its input directory: {name}")
            add(asset)
        validate_policy(policy, load_problem(path))
        diagnostics = validate_input(path)
        if not diagnostics["valid"]:
            raise ContractError(diagnostics)
        sample = path.parent.parent
        result = sample / "output/result.h5"
        add(result)
        diagnostics = validate_output(path, result)
        if not diagnostics["valid"]:
            raise ContractError(diagnostics)
        samples.append(sample.name)
    files["README.md"] = agent_readme(task_path)
    manifest = {"task": task, "public_samples": samples,
                "files": {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())}}
    files["MANIFEST.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    return files, samples


def publish(task, output=None, root=PROJECT_ROOT):
    root = Path(root).resolve()
    files, samples = collect_materials(task, root)
    output = Path(output).resolve() if output is not None else root / "dist"
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"{task}-agent.zip"
    # Atomic replacement leaves an existing release intact if building fails.
    handle, temporary = tempfile.mkstemp(prefix=f".{task}-agent-", suffix=".tmp", dir=output)
    os.close(handle)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
            for name, data in sorted(files.items()):
                entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                entry.create_system = 3
                entry.external_attr = 0o100644 << 16
                entry.compress_type = zipfile.ZIP_DEFLATED
                bundle.writestr(entry, data, compresslevel=9)
        os.replace(temporary, archive)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {"archive": str(archive), "file_count": len(files), "public_samples": samples,
            "sha256": hashlib.sha256(archive.read_bytes()).hexdigest()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True, help="Unique task directory name under qbank/<chapter>/<section>/")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "dist", help="ZIP output directory")
    args = parser.parse_args(argv)
    try:
        result = publish(args.task, args.output)
    except (OSError, ValueError, KeyError, ContractError) as exc:
        parser.exit(1, f"Publish failed: {exc}\n")
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
