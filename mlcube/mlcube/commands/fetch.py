import argparse
import os
import shutil
from typing import (Optional, List)
from mlcube.commands import ResourcePath
from mlcube.common.utils import StandardPaths


class FetchCommand(object):
    def __init__(self, mlcube: Optional[str], args: Optional[List[str]]) -> None:
        self.mlcube = ResourcePath(mlcube)
        self.args = args if args is not None else []

    def execute(self) -> None:
        if self.mlcube.type == ResourcePath.LOCAL_DIR:
            self.fetch_from_local_directory()
        elif self.mlcube.type == ResourcePath.LOCAL_FILE:
            self.fetch_from_local_file()
        elif self.mlcube.type == ResourcePath.GIT:
            self.fetch_from_git()
        else:
            raise NotImplementedError(f"Can't fetch ({self.mlcube.path}) - not implemented yet.")
        print("done")

    def fetch_from_local_directory(self, mlcube: Optional[ResourcePath] = None) -> None:
        if mlcube is None:
            mlcube = self.mlcube
        dest_dir = os.path.join(os.getcwd(), mlcube.base_name())
        if os.path.exists(dest_dir):
            raise ValueError("Destination directory exists.")
        shutil.copytree(mlcube.path, dest_dir)

    def fetch_from_local_file(self, mlcube: Optional[ResourcePath] = None) -> None:
        """
        https://slashdot.org/poll/3059/should-archive-files-such-as-zip-and-targz-packages-store-their-content-inside-a-single-top-level-root-directory
        """
        if mlcube is None:
            mlcube = self.mlcube
        dest_dir = os.path.join(os.getcwd(), mlcube.base_name())
        if os.path.exists(dest_dir):
            raise ValueError("Destination directory exists.")
        shutil.unpack_archive(mlcube.path, dest_dir)

    def fetch_from_git(self) -> None:
        """
        https://github.com/mlflow/mlflow/blob/8e74cdd108ff324175e38d621b12d9b2aced05bd/mlflow/projects/utils.py
        Just PoC for now.
        pip install GitPython
        """
        parser = argparse.ArgumentParser()
        parser.add_argument('--branch', type=str, default='master')
        parser.add_argument('--project', type=str, default=None)
        args = parser.parse_args(args=self.args)

        try:
            import git
            from git.repo.base import Repo
        except ImportError:
            print("Please, install GitPython: pip install GitPython")
            raise

        cache_dir = os.path.expandvars(StandardPaths.CACHE)
        os.makedirs(cache_dir, exist_ok=True)
        repo_dir = os.path.join(cache_dir, self.mlcube.base_name())

        if not os.path.exists(repo_dir):
            Repo.clone_from(self.mlcube.path, repo_dir)
        git.cmd.Git(working_dir=repo_dir).pull(self.mlcube.path, args.branch)

        self.fetch_from_local_directory(
            mlcube=ResourcePath(repo_dir if args.project is None else os.path.join(repo_dir, args.project))
        )
