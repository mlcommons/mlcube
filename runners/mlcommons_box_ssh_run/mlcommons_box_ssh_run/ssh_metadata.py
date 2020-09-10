import os
import copy
from enum import Enum
from typing import Optional
from mlcommons_box.common import mlbox_metadata
from mlcommons_box.common.utils import Utils


"""
Classes that provide convenient access to SHH runner-specific platform parameters. Pretty much all is initialized based
on configuration in a platform definition file.
"""


class InterpreterType(str, Enum):
    """Type of a python interpreter on a remote host for running mlbox runners.
    PS - MLBoxes may have their own Python environment.
    """
    System = "system"           # Python that's already available. Can be user existing existing environment.
    VirtualEnv = "virtualenv"   # Is used to automatically create a new python environment in the MLBox root folder.
    Conda = "conda"             # Is used to automatically create a new python environment in the MLBox root folder.


class SystemInterpreter(object):
    """System interpreter is the one already available on a remote host that does not need to be configured.
    It can also be a user existing environment (virtualenv, conda etc.).
    """
    def __init__(self, python: str = 'python'):
        """
        Args:
            python (str): Python executable, can be a full path to user python executable.
        """
        self.type = InterpreterType.System
        self.python = python

    def __str__(self) -> str:
        return f"SystemInterpreter(type=system, python={self.python})"


class Env(object):
    """Class that describes remote mlbox library (runners) environment."""
    def __init__(self, path: str, sync: bool, interpreter: dict, variables: dict):
        """
        Args:
            path (str): A path to a mlbox library on a remote host. Relative paths are relative to user home dir.
            sync (bool): If true, mlbox library will be synced (local -> remote) during the configure phase.
            interpreter (dict): Definition of a remote python interpreter for running mlbox runners.
            variables (dict): Environmental variables to use at a remote host. In particular, they will be passed to
                docker build/run.
        """
        self.path = path
        self.sync = sync
        if interpreter['type'] == InterpreterType.System:
            self.interpreter = SystemInterpreter(interpreter['python'])
        else:
            raise ValueError("Unsupported interpreter: {}".format(interpreter['type']))
        self.variables = copy.deepcopy(variables)

    def __str__(self) -> str:
        return f"Env(path={self.path}, sync={self.sync}, interpreter={self.interpreter})"

    def docker_build_args(self) -> str:
        """
        Returns:
            A string that contains definitions of variables for docker 'build' phase.
        """
        return " ".join([f"--build-arg {name}={value}" for name, value in self.variables.items()])

    def docker_run_args(self) -> str:
        """
        Returns:
            A string that contains definitions of variables for docker 'run' phase.
        """
        return " ".join([f"-e {name}={value}" for name, value in self.variables.items()])


class MLBox(object):
    """Class that describes remote mlbox location."""
    def __init__(self, path: str, sync: bool = True):
        """
        Args:
            path (str): Path on a remote host for a mlbox-packaged workload.
            sync (bool): If true, local mlbox directory is synced with the remote host during the configure phase.
        """
        self.path = path
        self.sync = sync

    def __str__(self) -> str:
        return f"MLBox(path={self.path}, sync={self.sync})"


class Platform(object):

    def __init__(self, path: str, mlbox: mlbox_metadata.MLBox):
        """
        Args:
            path (str): Path to a SSH platform that is usually located in the MLBox `platforms` directory.
            mlbox (MLBox): MLBox definition object.
        """
        metadata = Utils.load_yaml(path)

        if 'host' not in metadata:
            raise ValueError("Missing mandatory parameter 'host'")
        if 'user' not in metadata:
            raise ValueError("Missing mandatory parameter 'user'")
        #
        metadata['env'] = Utils.get(metadata, 'env', {'path': None, 'sync': True,
                                                      'interpreter': {'type': 'system', 'python': 'python'},
                                                      'variables': {}})
        metadata['env']['path'] = Utils.get(metadata['env'], 'path', '.mlbox')
        metadata['env']['sync'] = Utils.get(metadata['env'], 'sync', True)
        metadata['env']['interpreter'] = Utils.get(metadata['env'], 'interpreter',
                                                   {'type': 'system', 'python': 'python'})
        metadata['env']['variables'] = Utils.get(metadata['env'], 'variables', {})

        metadata['mlbox'] = Utils.get(metadata, 'mlbox', {'path': None, 'sync': True})
        metadata['mlbox']['path'] = Utils.get(
            metadata['mlbox'],
            'path',
            os.path.join(metadata['env']['path'], 'mlboxes', mlbox.qualified_name)
        )
        metadata['mlbox']['sync'] = Utils.get(metadata['mlbox'], 'sync', True)

        self.type: str = 'ssh'
        self.platform: dict = copy.deepcopy(metadata)

    @property
    def host(self) -> Optional[str]:
        """
        Returns:
            Name (or IP address) of a remote host.
        """
        return self.platform.get('host', None)

    @property
    def user(self) -> Optional[str]:
        """
        Returns:
            User to use on a remote host. It's better to have a password-less access for this user.
        """
        return self.platform.get('user', None)

    @property
    def mlbox_platform(self) -> Optional[str]:
        """Rename me."""
        return self.platform.get('platform', None)

    @property
    def env(self) -> Env:
        """
        Returns:
            Instance of the 'Env' class that describes environment of the mlbox library (runners) on a remote host.
        """
        return Env(**self.platform['env'])

    @property
    def mlbox(self) -> MLBox:
        """
        Returns:
            Instance of the 'MLBox' class that describes location of the MLBox workload on a remote host.
        """
        return MLBox(**self.platform['mlbox'])

    def __str__(self) -> str:
        return f"Platform(host={self.host}, user={self.user}, platform={self.platform}, "\
               f"env={self.env}, mlbox={self.mlbox})"
