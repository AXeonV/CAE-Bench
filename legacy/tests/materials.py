"""Stage archived tasks in isolation to exercise the current public packager."""
from pathlib import Path
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def collect_archived_materials(collect, task):
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        for name in ('pyproject.toml', 'LICENSE'):
            shutil.copy2(ROOT / name, root / name)
        for name in ('docs', 'src/caeoj'):
            shutil.copytree(ROOT / name, root / name)
        shutil.copytree(ROOT / 'legacy' / task, root / 'tasks' / task)
        return collect(task, root=root)
