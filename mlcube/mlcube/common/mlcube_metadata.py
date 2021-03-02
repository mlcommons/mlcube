import os
import textwrap

import yaml
from pathlib import Path
from mlspeclib import MLObject
from typing import (Any, Optional)


class MLCubeInvoke(object):
    def __init__(self, path: str):
        path = os.path.abspath(path)
        metadata, err = MLObject.create_object_from_file(path)
        if err:
            raise RuntimeError(err)

        self.task_name: str = metadata['task_name']
        # Input/output bindings map parameter name to parameter value
        self.input_binding: dict = metadata['input_binding']
        self.output_binding: dict = metadata['output_binding']

    def __str__(self) -> str:
        return f"MLCubeInvoke(task_name={self.task_name}, input_binding={self.input_binding}, "\
               f"output_binding={self.output_binding})"


class MLCubeTask(object):
    def __init__(self, path: str):
        """
        Args:
            path (str): Path to a MLCube task file.
        """
        path = os.path.abspath(path)
        metadata, err = MLObject.create_object_from_file(path)
        if err:
            raise RuntimeError(err)

        self.inputs = {input_['name']: input_['type'] for input_ in metadata.get('inputs', [])}
        self.outputs = {output['name']: output['type'] for output in metadata.get('outputs', [])}

    def __str__(self) -> str:
        return f"MLCubeTask(inputs={self.inputs}, outputs={self.outputs})"


class MLCube(object):
    """Provides access to limited number of MLCube parameters."""
    def __init__(self, path: str):
        """
        Args:
            path (str): Path to a MLCube root directory.
        """
        path = os.path.abspath(path)
        metadata, err = MLObject.create_object_from_file(os.path.join(path, 'mlcube.yaml'))
        if err:
            raise RuntimeError(err)

        self.root = path
        self.name = metadata['name']
        self.version = metadata['version']
        self.task: Optional[MLCubeTask] = None
        self.invoke: Optional[MLCubeInvoke] = None
        self.platform: Any = None

    @property
    def qualified_name(self) -> str:
        """Return a fully qualified name of this MLCube: '{name}-{version}'."""
        return f"{self.name}-{self.version}"

    @property
    def build_path(self) -> str:
        return os.path.join(self.root, 'build')

    @property
    def workspace_path(self) -> str:
        return os.path.join(self.root, 'workspace')

    @property
    def tasks_path(self) -> str:
        return os.path.join(self.root, 'tasks')

    def __str__(self) -> str:
        return f"MLCube(root={self.root}, name={self.name}, version={self.version}, task={self.task}, "\
               f"invoke={self.invoke}, platform={self.platform})"


class MLCubeFS(object):
    def __init__(self, path: Optional[str]) -> None:
        # All paths are absolute.
        self.root = Path(path or Path.cwd()).absolute()
        if self.root.is_file():
            self.root = self.root.parent
        self.mlcube_file = self.root / 'mlcube.yaml'
        self.compact_mlcube_file = self.root / '.mlcube.yaml'
        self.platforms = list((self.root / 'platforms').rglob('*.yaml'))
        self.tasks = list((self.root / 'tasks').rglob('*.yaml'))
        self.runs = list((self.root / 'run').rglob('*.yaml'))

    @property
    def num_platforms(self) -> int:
        return len(self.platforms)

    @property
    def num_tasks(self) -> int:
        return len(self.tasks)

    @property
    def num_runs(self) -> int:
        return len(self.runs)

    def summary(self):
        print("------------------- MLCubeFS -------------------")
        print(f"root = {self.root}")
        if self.mlcube_file.exists():
            print(f"mlcube file = {self.mlcube_file}")
        if self.compact_mlcube_file.exists():
            print(f"compact mlcube file = {self.compact_mlcube_file}")
        print(f"platforms = {self.platforms}")
        print(f"tasks = {self.tasks}")
        print(f"runs = {self.runs}")

    def get_platform_path(self, platform: Optional[str]) -> Path:
        if platform is None:
            if self.num_platforms != 1:
                raise RuntimeError(f"When platform is not specified, number of MLCube platforms must be one. "
                                   f"Platforms = {self.platforms}")
            return self.platforms[0]
        if not platform.endswith('.yaml'):
            platform = self.root / 'platforms' / f'{platform}.yaml'
        platform_path = Path(platform).absolute()
        if not platform_path.exists():
            raise RuntimeError(f"Platform does not exist: {platform_path}")
        return platform_path

    def get_task_instance_path(self, task_instance: Optional[str]) -> Path:
        if task_instance is None:
            if self.num_runs != 1:
                raise RuntimeError(f"When task instance is not specified, number of MLCube task instances must be one. "
                                   f"Task instances = {self.runs}")
            return self.runs[0]
        if not task_instance.endswith('.yaml'):
            task_instance = self.root / 'run' / f'{task_instance}.yaml'
        task_instance_path = Path(task_instance).absolute()
        if not task_instance_path.exists():
            raise RuntimeError(f"Task instance does not exist: {task_instance_path}")
        return task_instance_path

    @staticmethod
    def get_platform_runner(path: Path) -> str:
        platform: dict = yaml.safe_load(open(path, 'r'))
        runner = platform.get('platform', {}).get('name', None)
        if runner is None:
            raise RuntimeError(f"Unsupported platform: {platform}")
        if runner in ('docker', 'podman'):
            return 'mlcube_docker'
        if runner in ('singularity', ):
            return 'mlcube_singularity'
        raise RuntimeError(f"Unsupported runner: {runner}")

    def describe(self) -> None:
        mlcube: MLCube = MLCube(path=self.root)
        print(f"MLCube")
        print(f"  Path = {mlcube.root}")
        print(f"  Name = {mlcube.name}:{mlcube.version}")

        # -------------------------------------
        print(f"  Platforms:")
        for platform in self.platforms:
            platform: dict = yaml.safe_load(open(platform, 'r'))
            if 'platform' in platform:
                details = ""
                if 'container' in platform:
                    details = f", container = {platform['container']}"
                print(f"    Platform = {platform['platform']}{details}")

        # -------------------------------------
        print(f"  Tasks:")

        def _print(d: dict) -> None:
            text = textwrap.fill(f"{d['name']} ({d['type']}): {d['description']}", width=120, initial_indent=' ' * 8,
                                 subsequent_indent=' ' * 12)
            print(text)

        for task in self.tasks:
            print(f"    Task = {task.name[0:-5]}")
            task = yaml.safe_load(open(task, 'r'))
            print(f"      Inputs:")
            for input_ in task.get('inputs', []):
                _print(input_)
            print(f"      Outputs:")
            for output in task.get('outputs', []):
                _print(output)

        # -------------------------------------
        platforms = '|'.join([platform.name[:-5] for platform in self.platforms])
        print(f"Run this MLCube:")
        print("  Configure MLCube:")
        print(f"    mlcube configure --mlcube={self.root} --platform={platforms}")
        print("  Run MLCube tasks:")
        for task in self.tasks:
            print(f"    mlcube run --mlcube={self.root} --task={task.name[0:-5]} --platform={platforms}")
