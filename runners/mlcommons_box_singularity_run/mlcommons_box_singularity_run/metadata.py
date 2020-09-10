import os
from typing import Any
from mlspeclib import (MLObject, MLSchema)


class MLSchemaRegistrar(object):
    @staticmethod
    def register():
        MLSchema.append_schema_to_registry(os.path.dirname(__file__))


class SingularityPlatform(object):

    def __init__(self, path: str, **kwargs: Any):
        """
        Args:
            path (str): Path to a Singularity platform that is usually located in the MLBox `platforms` directory.
            **kwargs (Any): Reserved for future use to unify implementation of Platform Definition classes across
                various runners.
        """
        metadata, err = MLObject.create_object_from_file(path)
        if err:
            raise RuntimeError(err)
        self.type: str = 'singularity'
        self.image: str = metadata['image']

    def __str__(self) -> str:
        return f"SingularityPlatform(type={self.type}, image={self.image})"
