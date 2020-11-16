import os
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
from typing import (Tuple, Any)
from mlcommons_box.common import mlbox_metadata


class StandardPaths(object):
    """ Standard MLBox file system paths. """

    # Base path. Do not use hidden paths such as .mlcommons-box. It does not work with Docker installed with snap.
    ROOT = '${HOME}/mlcommons-box'
    # Default path to store singularity containers.
    CONTAINERS = ROOT + '/containers'
    # Default path to store MLBoxes for runners such as SSH and GCP (Google Compute Platform).
    BOXES = ROOT + '/boxes'
    # Default path for user python environments for runners such as SSH.
    ENVIRONMENTS = ROOT + '/environments'


class Utils(object):
    """Collection of various helper functions from the old MLBox branch.
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
    def container_args(mlbox: mlbox_metadata.MLBox) -> Tuple[dict, list]:
        mounts, args = {}, [mlbox.invoke.task_name]

        def create_(binding_: dict, input_specs_: dict):
            # name: parameter name, path: parameter value
            for name, path in binding_.items():
                path = path.replace('$WORKSPACE', mlbox.workspace_path)

                path_type = input_specs_[name]
                if path_type == 'directory':
                    os.makedirs(path, exist_ok=True)
                    mounts[path] = mounts.get(
                        path,
                        '/mlbox_io{}/{}'.format(len(mounts), os.path.basename(path))
                    )
                    args.append('--{}={}'.format(name, mounts[path]))
                elif path_type == 'file':
                    file_path, file_name = os.path.split(path)
                    os.makedirs(file_path, exist_ok=True)
                    mounts[file_path] = mounts.get(
                        file_path,
                        '/mlbox_io{}/{}'.format(len(mounts), file_path)
                    )
                    args.append('--{}={}'.format(name, mounts[file_path] + '/' + file_name))
                else:
                    raise RuntimeError(f"Invalid path type: '{path_type}'")

        create_(mlbox.invoke.input_binding, mlbox.task.inputs)
        create_(mlbox.invoke.output_binding, mlbox.task.outputs)

        return mounts, args
