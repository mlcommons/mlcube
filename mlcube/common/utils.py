import os
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
from typing import (Tuple, Any)
from mlcube.common import mlcube_metadata


class StandardPaths(object):
    """ Standard MLCube file system paths. """

    # Base path. Do not use hidden paths such as .mlcube. It does not work with Docker installed with snap.
    ROOT = '${HOME}/mlcube'
    # Default path to store singularity containers.
    CONTAINERS = ROOT + '/containers'
    # Default path to store MLCubes for runners such as SSH and GCP (Google Compute Platform).
    BOXES = ROOT + '/cubes'
    # Default path for user python environments for runners such as SSH.
    ENVIRONMENTS = ROOT + '/environments'


class Utils(object):
    """Collection of various helper functions from the old MLCube branch.
    Developed by: Victor Bittorf and Xinyuan Huang.
    Most of these methods are probably not used any more.
    """
    @staticmethod
    def get(d: dict, key: Any, default: Any) -> Any:
        """
        Args:
            d (dict): Input dictionary object.
            key (Any): Dictionary key to look up.
            default (Any): Default value to return if key not present OR key value is None
        Returns:
            Return default if key is not in d or d[key] is None.
        """
        value = d.get(key, default)
        return value if value is not None else default

    @staticmethod
    def load_yaml(path: str):
        with open(path) as stream:
            return yaml.load(stream.read(), Loader=Loader)

    @staticmethod
    def run_or_die(cmd):
        print(cmd)
        if os.system(cmd) != 0:
            raise Exception('Command failed: {}'.format(cmd))

    @staticmethod
    def container_args(mlcube: mlcube_metadata.MLCube) -> Tuple[dict, list]:
        mounts, args = {}, [mlcube.invoke.task_name]

        def create_(binding_: dict, input_specs_: dict):
            # name: parameter name, path: parameter value
            for name, path in binding_.items():
                path = path.replace('$WORKSPACE', mlcube.workspace_path)

                path_type = input_specs_[name]
                if path_type == 'directory':
                    os.makedirs(path, exist_ok=True)
                    mounts[path] = mounts.get(
                        path,
                        '/mlcube_io{}/{}'.format(len(mounts), os.path.basename(path))
                    )
                    args.append('--{}={}'.format(name, mounts[path]))
                elif path_type == 'file':
                    file_path, file_name = os.path.split(path)
                    os.makedirs(file_path, exist_ok=True)
                    mounts[file_path] = mounts.get(
                        file_path,
                        '/mlcube_io{}/{}'.format(len(mounts), file_path)
                    )
                    args.append('--{}={}'.format(name, mounts[file_path] + '/' + file_name))
                else:
                    raise RuntimeError(f"Invalid path type: '{path_type}'")

        create_(mlcube.invoke.input_binding, mlcube.task.inputs)
        create_(mlcube.invoke.output_binding, mlcube.task.outputs)

        return mounts, args
