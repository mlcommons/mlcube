import os
from mlspeclib import (MLObject, MLSchema)


class MLSchemaRegistrar(object):
    @staticmethod
    def register():
        MLSchema.append_schema_to_registry(os.path.dirname(__file__))


class SingularityPlatform(object):
    """MLBox implementation is the singularity image."""
    def __init__(self, path: str):
        """
        Args:
            path (str): Path to a  'mlbox_docker.yaml' that is usually located in the MLBox root directory.
        """
        metadata, err = MLObject.create_object_from_file(path)
        if err:
            raise RuntimeError(err)
        self.type: str = 'singularity'
        self.image: str = metadata['image']

    def __str__(self) -> str:
        return f"SingularityPlatform(type={self.type}, image={self.image})"
