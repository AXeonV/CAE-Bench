"""Package and verify an already reconstructed paper evaluation snapshot."""

import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile


def digest(stream):
    return hashlib.file_digest(stream, "sha256").hexdigest()


def file_digest(path):
    with path.open("rb") as stream:
        return digest(stream)


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def file_map(task, kind):
    return {path: entry["sha256"] for path, entry in task[f"{kind}_files"].items()}


def safe_path(path):
    parts = PurePosixPath(path).parts
    if not parts or path.startswith("/") or ".." in parts or "\\" in path or ":" in path:
        raise ValueError(f"Unsafe archive member: {path}")
    return parts


def verify_members(archive, expected, metadata=()):
    names = archive.namelist()
    if len(names) != len(set(names)) or set(names) != set(expected) | set(metadata):
        raise ValueError("Unexpected archive inventory")
    for name, sha in expected.items():
        with archive.open(name) as member:
            if digest(member) != sha:
                raise ValueError(f"File differs from paper snapshot: {name}")


def package(reconstructed, supplement, output):
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = supplement / "evaluation_manifest.json"
    result_path = supplement / "experiment_results.json"
    manifest = json.loads(manifest_path.read_bytes())
    if file_digest(result_path) != manifest["reported_results"]["sha256"]:
        raise ValueError("Paper experiment data does not match its manifest")
    results = json.loads(result_path.read_bytes())
    tasks = manifest["tasks"]
    coverage = {"task_count": len(tasks), "case_count": sum(t["case_count"] for t in tasks),
                "computational_tasks": results["computational_task_count"],
                "computational_cases": manifest["scoring_policy"]["computational_cases"]}
    if coverage != {"task_count": 82, "case_count": 647,
                    "computational_tasks": 80, "computational_cases": 630}:
        raise ValueError(f"Unexpected paper coverage: {coverage}")
    if {p.name for p in reconstructed.iterdir()} != {t["task"] for t in tasks}:
        raise ValueError("Reconstruction task set differs from manifest")

    public_path = output / "caeoj-qbank-rc7-paper-public.zip"
    metadata = {
        "release": "caeoj-qbank-20261029-rc7",
        "profile": "paper-frozen",
        "coverage": coverage,
        "paper_manifest_sha256": file_digest(manifest_path),
        "tasks": [{"task": t["task"], "path": t["path"], "formal_cases": t["case_count"]}
                  for t in tasks],
    }
    public_readme = (
        "# CAE-Bench RC7 paper snapshot: public candidate packages\n\n"
        "Extract the per-task ZIP from public/, read its README and task instructions, "
        "and install the package and its declared task dependencies. Each ZIP reproduces "
        "the files in that task's frozen public payload. Its sample outputs illustrate "
        "the format. Formal evaluation requires the matching private evaluation files.\n"
    )
    public_members = {}
    migrated = 0
    for task in tasks:
        for name, expected in file_map(task, "private").items():
            if not name.startswith("reference/") or not name.endswith("/grading.json"):
                continue
            spec = (reconstructed / task["task"] / "private").joinpath(*safe_path(name))
            raw = spec.read_bytes()
            if hashlib.sha256(raw).hexdigest() != expected:
                raise ValueError(f"Grading file differs from the paper snapshot: {spec}")
            grading = json.loads(raw)
            migrated += grading.get("scoring", {}).get("metric") == "rms_nrmse"
    if migrated != coverage["computational_cases"]:
        raise ValueError(f"Expected RMS scoring in 630 cases, found {migrated}")

    with ZipFile(public_path, "x", compression=ZIP_STORED) as public:
        for task in tasks:
            slug = task["task"]
            if safe_path(slug) != (slug,):
                raise ValueError(f"Invalid task slug: {slug}")
            source = reconstructed / slug / "public"
            expected = file_map(task, "public")
            actual = {p.relative_to(source).as_posix() for p in source.rglob("*")
                      if p.is_file() and "__pycache__" not in p.relative_to(source).parts}
            if actual != set(expected):
                raise ValueError(f"Unexpected reconstructed files in {slug}/public")
            inner = io.BytesIO()
            with ZipFile(inner, "w", compression=ZIP_DEFLATED) as candidate:
                for name in sorted(expected):
                    parts = safe_path(name)
                    if set(parts) & {"private", "cases", "reference"} or parts[-1] in {
                        "judge-config.json", "selection.json", "grading.json"
                    }:
                        raise ValueError(f"Evaluator material in public payload: {slug}/{name}")
                    candidate.write(source.joinpath(*parts), name)
            name = f"public/{slug}-agent.zip"
            value = inner.getvalue()
            public_members[name] = hashlib.sha256(value).hexdigest()
            public.writestr(name, value)
        public.writestr("README.md", public_readme)
        public.writestr("PROFILE.json", json_bytes(metadata))
        public.writestr("SHA256SUMS.json", json_bytes(public_members))
    with ZipFile(public_path) as public:
        verify_members(public, public_members, ("README.md", "PROFILE.json", "SHA256SUMS.json"))
        for task in tasks:
            with ZipFile(io.BytesIO(public.read(f"public/{task['task']}-agent.zip"))) as candidate:
                verify_members(candidate, file_map(task, "public"))
    report = dict(metadata, public_payload_files=sum(len(file_map(t, "public")) for t in tasks),
                  local_verified_rms_cases=migrated, archives={
                      public_path.name: {"sha256": file_digest(public_path), "bytes": public_path.stat().st_size}
                  })
    (output / "VERIFICATION.json").write_bytes(json_bytes(report))
    print(json.dumps({k: v for k, v in report.items() if k != "tasks"}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reconstructed", type=Path, required=True)
    parser.add_argument("--supplement", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    package(args.reconstructed, args.supplement, args.output)
