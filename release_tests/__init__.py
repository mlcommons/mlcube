import os
import sys
from typing import List
from pathlib import Path
from unittest import TestCase


class CurrentDir(object):
    def __init__(self, new_work_dir: Path) -> None:
        self.new_work_dir: Path = new_work_dir
        self.old_work_dir = os.getcwd()

    def __enter__(self):
        os.chdir(self.new_work_dir)
        return self.new_work_dir

    def __exit__(self, *args):
        os.chdir(self.old_work_dir)


class SysPath(object):
    def __init__(self, prepend_path: Path) -> None:
        self.prepend_path: Path = prepend_path.resolve()

    def __enter__(self):
        sys.path.insert(0, str(self.prepend_path))
        return self.prepend_path

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            sys.path.remove(str(self.prepend_path))
        except ValueError:
            pass


class ReleaseTest(TestCase):
    @property
    def project_dir(self) -> Path:
        return Path(__file__).resolve().parent.parent

    @property
    def mlcommons_box_dir(self) -> Path:
        return self.project_dir.joinpath('mlcommons_box')

    @property
    def runner_dirs(self) -> List[Path]:
        return [dir_item for dir_item in self.project_dir.joinpath('runners').iterdir() if dir_item.is_dir()]
