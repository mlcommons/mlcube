import os
from enum import Enum
from mlspeclib import MLObject
from typing import Union

"""
Classes defined here are probably located temporarily. They are used for providing access to MLBox metadata parameters.
"""


class RuntimeType(Enum):
    """MLBox implementation type."""
    Unknown = 1  # MLBox implementation is unknown. That's probably an error.
    Docker = 2   # MLBox is implemented as docker image.


class Runtime(object):
    """Base class for all MLBox implementation types. By default, implementation is 'unknown'. """
    def __next__(self, runtime_type: RuntimeType = RuntimeType.Unknown):
        self.type = runtime_type

    def __str__(self) -> str:
        return f"Runtime(type={self.type})"


class DockerRuntime(object):
    """MLBox implementation is the docker image."""
    @classmethod
    def load(cls, path: str) -> Union[Runtime, 'DockerRuntime']:
        """ Sort of factory method. Will be moved to some other place later.
        TODO: make factory or something
        Args:
            path (str): Path to MLBox root directory.
        Returns:
            One of runtime instances describing this MLBox.
        """
        mlbox_docker_file = os.path.join(path, 'mlbox_docker.yaml')
        if os.path.exists(mlbox_docker_file):
            return cls(mlbox_docker_file)
        # Other implementations (bare metal, python, singularity) should be here.
        return Runtime()

    def __init__(self, file_path: str):
        """
        Args:
            file_path (str): Path to a  'mlbox_docker.yaml' that is usually located in the MLBox root directory.
        """
        metadata, err = MLObject.create_object_from_file(file_path)
        if err:
            raise RuntimeError(err)
        self.type = RuntimeType.Docker
        self.image = metadata['image']             # Docker image name
        self.docker = metadata['docker_runtime']   # Docker executable ('docker' or 'nvidia-docker').

    def __str__(self) -> str:
        return f"DockerRuntime(type={self.type}, image={self.image}, docker={self.docker})"


class MLBox(object):
    """Provides access to limited number of MLBox parameters."""
    def __init__(self, path: str):
        """
        Args:
            path (str): Path to a MLBox root directory.
        """
        path = os.path.abspath(path)
        metadata, err = MLObject.create_object_from_file(os.path.join(path, 'mlbox.yaml'))
        if err:
            raise RuntimeError(err)

        self.root = path
        self.name = metadata['name']
        self.version = metadata['version']
        self.runtime = DockerRuntime.load(path)

    @property
    def qualified_name(self) -> str:
        """Return a fully qualified name of this MLBox: '{name}-{version}'."""
        return f"{self.name}-{self.version}"

    def __str__(self) -> str:
        return f"MLBox(root={self.root}, name={self.name}, version={self.version}, runtime={self.runtime})"
