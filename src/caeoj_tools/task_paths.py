"""Locate author-side qbank tasks by stable slug, independently of chapter order."""
from pathlib import Path
import re


def task_directory(task, root):
    """Require a unique chapter/section/task directory and reject linked paths.

    This module uses only the standard library so offline source planning can
    locate tasks without installing numerical dependencies. It is author-side
    infrastructure, not part of a candidate's data contract.
    """
    if not isinstance(task, str) or not re.fullmatch(
        r"[A-Za-z0-9](?:[A-Za-z0-9_.-]*[A-Za-z0-9_-])?", task
    ):
        raise ValueError("Task must be a directory name, without paths")
    root = Path(root).resolve()
    matches = sorted(p for p in (root / "qbank").glob(f"*/*/{task}")
                     if p.is_dir() and (p / "instruction.md").is_file())
    if len(matches) != 1:
        raise ValueError(f"Expected one qbank task named {task}, found {len(matches)}")
    directory = matches[0]
    current = root
    for part in directory.relative_to(root).parts:
        current /= part
        if current.is_symlink() or getattr(current, "is_junction", lambda: False)():
            raise ValueError(f"Task directory must not be a link: {current}")
    return directory
