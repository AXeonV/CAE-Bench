"""Stable task IDs must not resolve to an ambiguous or escaped author directory."""
from pathlib import Path
import tempfile
import unittest

from caeoj_tools.task_paths import task_directory


class TaskPathTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def make_task(self, chapter="01-pdes", section="1.1-elliptic"):
        directory = self.root / "qbank" / chapter / section / "example-2d"
        directory.mkdir(parents=True)
        (directory / "instruction.md").write_text("Task", encoding="utf-8")
        return directory

    def test_slug_survives_a_chapter_or_section_move(self):
        first = self.make_task()
        self.assertEqual(task_directory("example-2d", self.root), first.resolve())
        second = self.root / "qbank/03-other/3.2-other/example-2d"
        second.parent.mkdir(parents=True)
        first.rename(second)
        self.assertEqual(task_directory("example-2d", self.root), second.resolve())

    def test_duplicate_and_missing_ids_are_rejected(self):
        self.make_task()
        self.make_task("02-other", "2.1-other")
        with self.assertRaisesRegex(ValueError, "found 2"):
            task_directory("example-2d", self.root)
        with self.assertRaisesRegex(ValueError, "found 0"):
            task_directory("missing", self.root)

    def test_task_argument_cannot_be_a_path(self):
        for name in ("../example-2d", "/tmp/example-2d", "a/b", "a\\b", "", None):
            with self.subTest(name=name), self.assertRaises(ValueError):
                task_directory(name, self.root)

    def test_linked_task_is_rejected(self):
        target = self.root / "outside"
        target.mkdir()
        (target / "instruction.md").write_text("Private", encoding="utf-8")
        parent = self.root / "qbank/01-pdes/1.1-elliptic"
        parent.mkdir(parents=True)
        try:
            (parent / "example-2d").symlink_to(target, target_is_directory=True)
        except OSError:
            self.skipTest("Creating directory links is unavailable")
        with self.assertRaisesRegex(ValueError, "must not be a link"):
            task_directory("example-2d", self.root)


if __name__ == "__main__":
    unittest.main()
