import os
from typing import (Optional, Tuple)
from mlcube.common.objects import platform_config
from mlcube.common import (mlcube_metadata, objects)


class ResourcePath(object):

    LOCAL_DIR = 1        # file://
    LOCAL_FILE = 2       # file://
    REMOTE_FILE = 3      # http://, https://, ftp://
    GIT = 4              # https://, git://

    def __init__(self, mlcube: Optional[str]) -> None:
        if mlcube is None:
            mlcube = os.getcwd()
        self.path = mlcube

        is_file = os.path.isfile(mlcube) and os.path.exists(mlcube)
        is_dir = os.path.isdir(mlcube) and os.path.exists(mlcube)
        is_archive = mlcube.endswith(('.zip', '.tar', '.tar.gz', '.tar.bz', '.tar.xz'))

        if mlcube.startswith(('http:', 'https:', 'ftp:')) and is_archive:
            self.type = ResourcePath.REMOTE_FILE
        elif mlcube.startswith(('https:', 'git:')) and mlcube.endswith('.git'):
            self.type = ResourcePath.GIT
        elif is_dir:
            self.type = ResourcePath.LOCAL_DIR
        elif is_file and is_archive:
            self.type = ResourcePath.LOCAL_FILE
        elif is_file and mlcube.endswith('mlcube.yaml'):
            self.path = os.path.dirname(self.path)
            self.type = ResourcePath.LOCAL_DIR
        else:
            raise ValueError(f"Unrecognized MLCube path: '{mlcube}'")

        if self.type in (ResourcePath.LOCAL_DIR, ResourcePath.LOCAL_FILE):
            self.path = os.path.abspath(self.path)

    def base_name(self):
        name: str = os.path.basename(self.path)
        if self.type == ResourcePath.LOCAL_DIR:
            return name
        if name.endswith(('.zip', '.tar', '.git')):
            return name[:-4]
        if name.endswith(('.tar.gz', '.tar.bz', '.tar.xz')):
            return name[:-7]
        raise ValueError(f"Cannot find the file base name: '{self.path}'")


class CommandUtils(object):
    @staticmethod
    def get_mlcube_path(mlcube: Optional[str]) -> str:
        path = ResourcePath(mlcube)
        if path.type == ResourcePath.LOCAL_DIR:
            return path.path
        else:
            raise ValueError(f"Invalid MLCube path: '{mlcube}'")

    @staticmethod
    def get_file(mlcube: str, location: str, file_name: Optional[str]) -> str:
        if file_name is not None:
            if not file_name.endswith('.yaml') and os.path.basename(file_name) == file_name:
                return os.path.join(mlcube, location, f'{file_name}.yaml')
            return file_name
        else:
            mlcube_obj: mlcube_metadata.MLCube = mlcube_metadata.MLCube(path=mlcube)
            files = mlcube_obj.get_files(location)
            if len(files) != 1:
                raise ValueError(f"Could not automatically find the appropriate '{location}' file among: {files}")
            return files[0]

    @staticmethod
    def load_mlcube_runner(platform: str) -> Tuple[callable, callable]:
        platform = objects.load_object_from_file(file_path=platform, obj_class=platform_config.PlatformConfig)
        runner = platform.platform.name
        if runner == 'docker':
            from mlcube_docker import configure, run
        elif runner == 'singularity':
            from mlcube_singularity import configure, run
        elif runner == 'ssh':
            from mlcube_ssh import configure, run
        elif runner == 'k8s':
            from mlcube_k8s import configure, run
        else:
            raise ValueError(f"Loading '{runner}' runner is not supported yet")

        return configure, run
