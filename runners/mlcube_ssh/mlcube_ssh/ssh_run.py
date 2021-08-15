import os
import logging
import typing as t
from omegaconf import DictConfig
from mlcube.errors import ConfigurationError, IllegalParameterError
from mlcube.runner import (BaseConfig, BaseRunner)
from mlcube.shell import Shell
from mlcube_ssh.ssh_metadata import PythonInterpreter


logger = logging.getLogger(__name__)


class Config(BaseConfig):
    """ Helper class to manage `ssh` environment configuration."""

    CONFIG_SECTION = 'ssh'

    DEFAULT_CONFIG = {}

    """
    ssh:
        host: str                     # Remote host
        platform: str                 # Platform (runner) to use on remote host
        remote_root                   # Root path for mlcubes on remote host
        interpreter: dict             # Remote python interpreter
            1. type: system, python: ..., requirements: ...
            1. type: virtualenv, python: ..., requirements: ..., location: ..., name: ...
        authentication: dict          # Authentication on remote host
            1.: identity_file, user
    """

    @staticmethod
    def from_dict(ssh_env: DictConfig) -> DictConfig:
        for param_name in ('host', 'platform', 'remote_root', 'interpreter', 'authentication'):
            if ssh_env.get(param_name, None) is None:
                raise ConfigurationError(f"SSH runner: missing mandatory parameter '{param_name}'")
        for param_name in ('interpreter', 'authentication'):
            if not isinstance(ssh_env[param_name], DictConfig):
                raise IllegalParameterError(f'ssh.{param_name}', ssh_env[param_name])
        PythonInterpreter.get(ssh_env.interpreter).validate(ssh_env.interpreter)

        logger.debug(f"SSHRun configuration: {str(ssh_env)}")
        return ssh_env


class SSHRun(BaseRunner):
    """
    Reference implementation of the remote runner based on SSH.

    SSH runner accepts standard MLCube configuration files that are not ssh runner-specific. SHH runner uses platform
    configuration file to access remote nodes to run MLCubes the same way other runners (e.g., docker runner) run
    the same MLCubes locally. So, the only difference is the requirement for platform configuration file.
    """

    PLATFORM_NAME = 'ssh'

    def __init__(self, mlcube: t.Union[DictConfig, t.Dict], task: t.Text) -> None:
        super().__init__(mlcube, task, Config)

    def get_connection_string(self) -> str:
        """ Return authentication string for tools like `ssh` and `rsync`.

            ssh -i PATH_TO_PRIVATE_KEY USER_NAME@HOST_NAME
        """
        auth_str = ''
        identify_file = self.mlcube.ssh.authentication.get('identify_file', None)
        if identify_file:
            auth_str += f"-i {identify_file} "
        user = self.mlcube.ssh.authentication.get('user', None)
        if user:
            auth_str += f'{user}@'
        return auth_str + self.mlcube.ssh.host

    def configure(self) -> None:
        """Run 'configure' phase for SHH runner."""
        conn: t.Text = self.get_connection_string()
        remote_env: PythonInterpreter = PythonInterpreter.create(self.mlcube.ssh.interpreter)

        # If required, create and configure python environment on remote host
        Shell.ssh(conn, remote_env.create_cmd())
        Shell.ssh(conn, remote_env.configure_cmd())

        # The 'local_path' and 'remote_path' must both be directories.
        local_path: str = self.mlcube.runtime.root
        remote_path: str = os.path.join(self.mlcube.ssh.remote_root, os.path.basename(local_path))
        Shell.ssh(conn, f'mkdir -p {remote_path}')
        Shell.rsync_dirs(source=f'{local_path}/', dest=f'{conn}:{remote_path}/')

        # Configure remote MLCube runner. Idea is that we use chain of runners, for instance, SHH Runner -> Docker
        # runner. So, the runner to be used on a remote host must configure itself.
        cmd = f"mlcube configure --mlcube=. --platform={self.mlcube.ssh.platform}"
        Shell.ssh(conn, f'{remote_env.activate_cmd(noop=":")} && cd {remote_path} && {cmd}')

    def run(self) -> None:
        conn: t.Text = self.get_connection_string()
        remote_env: PythonInterpreter = PythonInterpreter.create(self.mlcube.ssh.interpreter)

        # The 'remote_path' variable points to the MLCube root directory on remote host.
        remote_path: t.Text = os.path.join(self.mlcube.ssh.remote_root, os.path.basename(self.mlcube.runtime.root))

        cmd = f"mlcube run --mlcube=. --platform={self.mlcube.ssh.platform} --task={self.task}"
        Shell.ssh(conn, f'{remote_env.activate_cmd(noop=":")} && cd {remote_path} && {cmd}')

        # Sync back results
        # TODO: Only workspace/ directory is synced. Better solution?
        Shell.rsync_dirs(source=f'{conn}:{remote_path}/workspace/', dest=f'{self.mlcube.runtime.root}/workspace/')
