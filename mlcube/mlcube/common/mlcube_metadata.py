import os
from mlspeclib import MLObject
from typing import (Any, Optional, List)


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

    def get_files(self, location: str, recursive: bool = False) -> List[str]:
        """ Return list of full paths to YAML files located in the $location sub-directory of the MLCube root directory.
        Args:
            location (str): MLCube sub-directory, such as `platforms`, `tasks` or `run`.
            recursive (bool): If true search for files recursively.

        Returns:
             List of full paths to YAML files (list of strings).
        """
        def _walk(location_: str, recursive_: bool) -> List[str]:
            files = [os.path.join(location_, file_) for file_ in os.listdir(location_) if file_.endswith('.yaml')]
            if recursive_:
                folders = [folder for folder in os.listdir(location_) if os.path.isdir(os.path.join(location_, folder))]
                for folder in folders:
                    files.extend(_walk(os.path.join(location_, folder), recursive_))
            return files

        return _walk(os.path.join(self.root, location), recursive_=recursive)
