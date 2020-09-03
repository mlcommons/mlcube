from mlspeclib import MLObject


class DockerPlatform(object):
    """MLBox implementation is the singularity image."""
    def __init__(self, path: str):
        """
        Args:
            path (str): Path to a  'mlbox_docker.yaml' that is usually located in the MLBox root directory.
        """
        metadata, err = MLObject.create_object_from_file(path)
        if err:
            raise RuntimeError(err)
        self.type: str = 'docker'
        self.image: str = metadata['image']
        self.runtime: str = metadata['docker_runtime']

    def __str__(self) -> str:
        return f"DockerPlatform(type={self.type}, image={self.image}, runtime={self.runtime})"
