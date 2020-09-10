from typing import Any
from mlspeclib import MLObject


class DockerPlatform(object):

    def __init__(self, path: str, **kwargs: Any):
        """
        Args:
            path (str): Path to a Docker platform that is usually located in the MLBox `platforms` directory.
            **kwargs (Any): Reserved for future use to unify implementation of Platform Definition classes across
                various runners.
        """
        metadata, err = MLObject.create_object_from_file(path)
        if err:
            raise RuntimeError(err)
        self.type: str = 'docker'
        self.image: str = metadata['image']
        self.runtime: str = metadata['docker_runtime']

    def __str__(self) -> str:
        return f"DockerPlatform(type={self.type}, image={self.image}, runtime={self.runtime})"
