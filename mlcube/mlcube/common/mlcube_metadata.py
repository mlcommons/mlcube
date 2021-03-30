import os
import yaml
import textwrap
import argparse
from pathlib import Path
from mlspeclib import MLObject
from typing import (Any, Optional, Union, List)


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

    def override_invoke_args(self, args: Optional[List[str]]) -> None:
        """ Override invoke parameters using user-provided values.
        A common example to run MLCube tasks is the following:
            $ mlcube run --mlcube=. --platform=platforms/docker.yaml --task=run/download.yaml
        Users can override task parameters (declared in task/download.yaml and defined in run/download.yaml):
            $ mlcube run --mlcube=. --platform=platforms/docker.yaml --task=run/download.yaml --data_dir=/MY/DATA/PATH

        This method modifies MLCube's `invoke` object. Corresponding yaml file remains unchanged.

        Args:
             args (Optional[List[str]]): List of user arguments. The`ArgParse.parse_args` method must be able to parse
                 it.
        """
        if None in (args, self.task, self.invoke) or len(args) == 0:
            return

        parser = argparse.ArgumentParser()
        for input_arg in self.task.inputs.keys():
            parser.add_argument(f'--{input_arg}', type=str, default=None)
        for output_arg in self.task.outputs.keys():
            parser.add_argument(f'--{output_arg}', type=str, default=None)

        parsed_args: dict = vars(parser.parse_args(args))
        for arg_name, arg_value in parsed_args.items():
            if arg_value is None:
                continue
            if arg_name in self.task.inputs:
                self.invoke.input_binding[arg_name] = arg_value
            elif arg_name in self.task.outputs:
                self.invoke.output_binding[arg_name] = arg_value


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


class CompactMLCube(object):
    def __init__(self, path: Optional[Union[str, MLCubeFS]]) -> None:
        if path is None or isinstance(path, str):
            self.mlcube_fs = MLCubeFS(path)
        elif isinstance(path, MLCubeFS):
            self.mlcube_fs = path
        else:
            raise ValueError(f"Invalid parameter: {path}")

    def unpack(self) -> 'CompactMLCube':
        # Compact MLCube exists if the root MLCube folder contains ".mlcube.yaml" file.
        if not self.mlcube_fs.compact_mlcube_file.exists():
            return

        # The code below "unpacks" compact MLCube by creating standard mlcube/task/run files if they do not exist.
        os.makedirs(self.mlcube_fs.root / 'tasks', exist_ok=True)
        os.makedirs(self.mlcube_fs.root / 'run', exist_ok=True)

        compact_mlcube: dict = yaml.safe_load(open(self.mlcube_fs.compact_mlcube_file, 'r'))
        self.create_mlcube_file(compact_mlcube)
        self.create_task_files(compact_mlcube)
        # Reload if task/run files have been created.
        self.mlcube_fs = MLCubeFS(self.mlcube_fs.root)

        return self

    def create_mlcube_file(self, compact_mlcube: dict) -> None:
        if self.mlcube_fs.mlcube_file.exists():
            return

        task_names = compact_mlcube['tasks'].keys()
        mlcube = {
            'schema_version': '1.0.0', 'schema_type': 'mlcube_root',
            'name': compact_mlcube.get('name', 'MLCube name'),
            'author': compact_mlcube.get('author', 'MLCube authors'), 'version': '0.1.0',
            'mlcube_spec_version': '0.1.0',
            'tasks': [f'tasks/{task_name}.yaml' for task_name in task_names]
        }
        yaml.safe_dump(mlcube, open(self.mlcube_fs.mlcube_file, 'w'))

    def create_task_files(self, compact_mlcube: dict) -> None:
        task_names = compact_mlcube['tasks'].keys()

        def _get_params(_params, _type):
            return [{'name': p['name'], 'type': p['type'], 'description': p.get('description', '')}
                    for p in _params if p['io'] == _type]

        for task_name in task_names:
            compact_task = compact_mlcube['tasks'][task_name]

            task = {
                'schema_version': '1.0.0',
                'schema_type': 'mlcube_task',
                'inputs': _get_params(compact_task['parameters'], 'input'),
                'outputs': _get_params(compact_task['parameters'], 'output')
            }
            task_file = self.mlcube_fs.root / 'tasks' / f'{task_name}.yaml'
            if not task_file.exists():
                yaml.safe_dump(task, open(task_file, 'w'))

            """
            input_binding: {}

            output_binding:
              cache_dir: $WORKSPACE/cache
              data_dir: $WORKSPACE/data

            {cache_dir: $WORKSPACE/cache, data_dir: $WORKSPACE/data}
            """
            inputs = [p['name'] for p in task['inputs']]
            outputs = [p['name'] for p in task['outputs']]
            for run_name, run_bindings in compact_task['tasks'].items():
                run = {
                    'schema_type': 'mlcube_invoke',
                    'schema_version': '1.0.0',
                    'task_name': task_name,
                    'input_binding': {k: v for k, v in run_bindings.items() if k in inputs},
                    'output_binding': {k: v for k, v in run_bindings.items() if k in outputs}
                }
                run_file = self.mlcube_fs.root / 'run' / f'{run_name}.yaml'
                if not run_file.exists():
                    yaml.safe_dump(run, open(run_file, 'w'))
