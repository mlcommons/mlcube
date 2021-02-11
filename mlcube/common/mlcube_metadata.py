import os
from mlspeclib import MLObject
from typing import (Any, Optional, Tuple)


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
