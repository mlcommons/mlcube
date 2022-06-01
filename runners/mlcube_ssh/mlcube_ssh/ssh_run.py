import os
import logging
import typing as t
from omegaconf import DictConfig, OmegaConf
from mlcube.errors import ExecutionError
from mlcube.runner import (RunnerConfig, Runner)
from mlcube.shell import Shell
from mlcube.validate import Validate
from mlcube_ssh.ssh_metadata import PythonInterpreter


logger = logging.getLogger(__name__)


class Config(RunnerConfig):
    """ Helper class to manage `ssh` environment configuration."""

    DEFAULT = OmegaConf.create({
        'runner': 'ssh',

        'host': '',                 # Remote host
        'platform': '',             # Platform (runner) to use on remote host
        'remote_root': '',          # Root path for MLCubes on remote host
        'interpreter': {},          # Remote python interpreter# Remote python interpreter
                                    #   1. type: system, python: ..., requirements: ...
                                    #   2. type: virtualenv, python: ..., requirements: ..., location: ..., name: ...
        'authentication': {}        # Authentication on remote host
                                    #   1. identity_file, user
    })

    @staticmethod
    def validate(mlcube: DictConfig) -> None:
        mlcube.runner = OmegaConf.merge(Config.DEFAULT, mlcube.runner)

        Validate(mlcube.runner, 'runner')\
            .check_unknown_keys(Config.DEFAULT.keys())\
            .check_values(['host', 'platform', 'remote_root'], str, blanks=False)\
            .check_values(['interpreter', 'authentication'], DictConfig)
        PythonInterpreter.get(mlcube.runner.interpreter).validate(mlcube.runner.interpreter)


class SSHRun(Runner):
    """
    Reference implementation of the remote runner based on SSH.

    SSH runner accepts standard MLCube configuration files that are not ssh runner-specific. SHH runner uses platform
    configuration file to access remote nodes to run MLCubes the same way other runners (e.g., docker runner) run
    the same MLCubes locally. So, the only difference is the requirement for platform configuration file.
    """

    CONFIG = Config

    def __init__(self, mlcube: t.Union[DictConfig, t.Dict], task: t.Text) -> None:
        super().__init__(mlcube, task)

    def get_connection_string(self) -> str:
        """ Return authentication string for tools like `ssh` and `rsync`.

            ssh -i PATH_TO_PRIVATE_KEY USER_NAME@HOST_NAME
        """
        auth_str = ''
        identify_file = self.mlcube.runner.authentication.get('identify_file', None)
        if identify_file:
            auth_str += f"-i {identify_file} "
        user = self.mlcube.runner.authentication.get('user', None)
        if user:
            auth_str += f'{user}@'
        return auth_str + self.mlcube.runner.host

    def configure(self) -> None:
        """Run 'configure' phase for SHH runner."""
        conn: t.Text = self.get_connection_string()
        remote_env: PythonInterpreter = PythonInterpreter.create(self.mlcube.runner.interpreter)

        # If required, create and configure python environment on remote host
        try:
            Shell.ssh(conn, remote_env.create_cmd())
        except ExecutionError as err:
            raise ExecutionError.mlcube_configure_error(
                self.__class__.__name__,
                f"Error occurred while creating remote python environment (env={remote_env}).",
                **err.context
            )
        try:
            Shell.ssh(conn, remote_env.configure_cmd())
        except ExecutionError as err:
            raise ExecutionError.mlcube_configure_error(
                self.__class__.__name__,
                f"Error occurred while configuring remote python environment (env={remote_env}).",
                **err.context
            )

        # The 'local_path' and 'remote_path' must both be directories.
        try:
            local_path: str = self.mlcube.runtime.root
            remote_path: str = os.path.join(self.mlcube.runner.remote_root, os.path.basename(local_path))
            Shell.ssh(conn, f'mkdir -p {remote_path}')
            Shell.rsync_dirs(source=f'{local_path}/', dest=f'{conn}:{remote_path}/')
        except ExecutionError as err:
            raise ExecutionError.mlcube_configure_error(
                self.__class__.__name__,
                "Error occurred while syncing local and remote folders.",
                **err.context
            )

        # Configure remote MLCube runner. Idea is that we use chain of runners, for instance, SHH Runner -> Docker
        # runner. So, the runner to be used on a remote host must configure itself.
        try:
            cmd = f"mlcube configure --mlcube=. --platform={self.mlcube.runner.platform}"
            Shell.ssh(conn, f'{remote_env.activate_cmd(noop=":")} && cd {remote_path} && {cmd}')
        except ExecutionError as err:
            raise ExecutionError.mlcube_configure_error(
                self.__class__.__name__,
                "Error occurred while configuring MLCube on a remote machine.",
                **err.context
            )

    def run(self) -> None:
        conn: t.Text = self.get_connection_string()
        remote_env: PythonInterpreter = PythonInterpreter.create(self.mlcube.runner.interpreter)

        # The 'remote_path' variable points to the MLCube root directory on remote host.
        remote_path: t.Text = os.path.join(self.mlcube.runner.remote_root, os.path.basename(self.mlcube.runtime.root))

        try:
            cmd = f"mlcube run --mlcube=. --platform={self.mlcube.runner.platform} --task={self.task}"
            Shell.ssh(conn, f'{remote_env.activate_cmd(noop=":")} && cd {remote_path} && {cmd}')
        except ExecutionError as err:
            raise ExecutionError.mlcube_run_error(
                self.__class__.__name__,
                f"Error occurred while running MLCube task (name={self.task}).",
                **err.context
            )

        # Sync back results
        try:
            # TODO: Only workspace/ directory is synced. Better solution?
            Shell.rsync_dirs(source=f'{conn}:{remote_path}/workspace/', dest=f'{self.mlcube.runtime.root}/workspace/')
        except ExecutionError as err:
            raise ExecutionError.mlcube_run_error(
                self.__class__.__name__,
                "Error occurred while syncing workspace.",
                **err.context
            )
