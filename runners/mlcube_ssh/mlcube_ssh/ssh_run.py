import os
import logging
from typing import Optional
from mlcube import parse   # Do not remove (it registers schemas on import)
from mlcube.common import mlcube_metadata
from mlcube.common.utils import StandardPaths
from mlcube_ssh.ssh_metadata import PythonInterpreter
from mlcube_ssh.utils import Utils


logger = logging.getLogger(__name__)


class Shell(object):
    @staticmethod
    def run_or_die(cmd):
        print(cmd)
        if os.system(cmd) != 0:
            raise Exception('Command failed: {}'.format(cmd))

    @staticmethod
    def ssh(conn: str, cmd: Optional[str]):
        if cmd:
            Shell.run_or_die(f"ssh -o StrictHostKeyChecking=no {conn} '{cmd}'")

    @staticmethod
    def rsync_dirs(source: str, dest: str):
        Shell.run_or_die(f"rsync -e 'ssh' -r '{source}' '{dest}'")


class SSHRun(object):
    """
    Reference implementation of the remote runner based on SSH.

    SSH runner accepts standard MLCube configuration files that are not ssh runner-specific. SHH runner uses platform
    configuration file to access remote nodes to run MLCubes the same way other runners (e.g., docker runner) run
    the same MLCubes locally. So, the only difference is the requirement for platform configuration file.
    """

    def get_runner_on_remote_host(self) -> str:
        config: dict = Utils.load_yaml(os.path.join(self.mlcube.root, 'platforms', self.mlcube.platform.platform))

        # Old-style definition
        if config.get('schema_type', None) == 'mlcube_singularity':
            return 'mlcube_singularity'
        if config.get('schema_type', None) == 'mlcube_docker':
            return 'mlcube_docker'

        # New-style definition
        if config.get('schema_type', None) == 'mlcube_platform':
            platform_name = config.get('platform', {}).get('name', None)
            if platform_name == 'docker':
                return 'mlcube_docker'
        raise ValueError(f"Invalid platform configuration file")

    def __init__(self, mlcube: mlcube_metadata.MLCube) -> None:
        """"""
        self.mlcube: mlcube_metadata.MLCube = mlcube
        self.remote_runner: str = self.get_runner_on_remote_host()

    def configure(self) -> None:
        """Run 'configure' phase for SHH runner."""
        conn: str = self.mlcube.platform.get_connection_string()
        remote_env: PythonInterpreter = self.mlcube.platform.interpreter

        # If required, create and configure python environment on remote host
        Shell.ssh(conn, remote_env.create_cmd())
        Shell.ssh(conn, remote_env.configure_cmd())

        # The 'local_path' and 'remote_path' must both be directories.
        local_path: str = self.mlcube.root
        remote_path: str = os.path.join(StandardPaths.BOXES, os.path.basename(self.mlcube.root))
        Shell.ssh(conn, f'mkdir -p {remote_path}')
        Shell.rsync_dirs(source=f'{local_path}/', dest=f'{conn}:{remote_path}/')

        # Configure remote MLCube runner. Idea is that we use chain of runners, for instance, SHH Runner -> Docker
        # runner. So, the runner to be used on a remote host must configure itself.
        cmd = f"{remote_env.python} -m {self.remote_runner} configure "\
              f"--mlcube=. --platform=platforms/{self.mlcube.platform.platform}"
        Shell.ssh(conn, f'{remote_env.activate_cmd(noop=":")} && cd {remote_path} && {cmd}')

    def run(self, task_file: str) -> None:
        """ Run 'run' phase, one of the MLCube tasks.
        Args:
             task_file (str): A file path to a task file on a local host. It is assumed the relative path to the mlcube
                root folder is "run/{task_name}.yaml"
        """
        conn: str = self.mlcube.platform.get_connection_string()
        remote_env: PythonInterpreter = self.mlcube.platform.interpreter

        # The 'remote_path' variable points to the MLCube root directory on remote host.
        remote_path = os.path.join(StandardPaths.BOXES, os.path.basename(self.mlcube.root))
        task_file_rel = os.path.relpath(  # -- Path to a task file relative to MLCube root directory
            os.path.abspath(task_file),   # ----- Local absolute path to a task file
            self.mlcube.root               # ----- Local MLCube root directory
        )

        cmd = f"{remote_env.python} -m {self.remote_runner} run "\
              f"--mlcube=. --platform=platforms/{self.mlcube.platform.platform} --task={task_file_rel}"
        Shell.ssh(conn, f'{remote_env.activate_cmd(noop=":")} && cd {remote_path} && {cmd}')

        # Sync back results
        # TODO: Only workspace/ directory is synced. Better solution?
        Shell.rsync_dirs(source=f'{conn}:{remote_path}/workspace/', dest=f'{self.mlcube.root}/workspace/')
