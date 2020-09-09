import os
import logging
from mlcommons_box import parse   # Do not remove (it registers schemas on import)
from mlbox_ssh_run.ssh_metadata import InterpreterType
from mlbox_ssh_run.utils import Utils
from mlcommons_box.common import mlbox_metadata

logger = logging.getLogger(__name__)


class SSHRun(object):
    """
    Reference implementation of the remote runner based on SSH.

    SSH runner accepts standard MLBox configuration files that are not ssh runner-specific. SHH runner uses platform
    configuration file to access remote nodes to run MLBoxes the same way other runners (e.g., docker runner) run
    the same MLBoxes locally. So, the only difference is the requirement for platform configuration file.
    """

    def get_runner_on_remote_host(self):
        config: dict = Utils.load_yaml(os.path.join(self.mlbox.root, 'platforms', self.mlbox.platform.mlbox_platform))
        if config.get('schema_type', None) == 'mlbox_singularity':
            return 'mlbox_singularity_run'
        if config.get('schema_type', None) == 'mlbox_docker':
            return 'mlbox_docker_run'
        raise ValueError(f"Invalid platform configuration file")

    def __init__(self, mlbox: mlbox_metadata.MLBox):
        """"""
        self.mlbox: mlbox_metadata.MLBox = mlbox
        self.remote_runner: str = self.get_runner_on_remote_host()

    def configure(self):
        """Run 'configure' phase for SHH runner."""
        conn = "{}@{}".format(self.mlbox.platform.user, self.mlbox.platform.host)

        # Sync mlbox library (runners) root directory with the remote host.
        if self.mlbox.platform.env.sync is True:
            # Local and remote paths of MLBox library.
            # Implement differently.
            local_path = os.path.abspath((os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))
            remote_path = self.mlbox.platform.env.path
            # Create target directory on a remote host and sync selected folders.
            Utils.run_or_die(f"ssh -o StrictHostKeyChecking=no {conn} 'mkdir -p {remote_path}'")
            for path in ('mlcommons_box', 'runners'):
                Utils.run_or_die(f"rsync -r {local_path}/{path} {conn}:{remote_path}")

        # Sync MLBox workload directories
        if self.mlbox.platform.mlbox.sync is True:
            # The 'local_path' and 'remote_path' must both be directories.
            local_path, remote_path = self.mlbox.root, self.mlbox.platform.mlbox.path
            Utils.run_or_die(f"ssh -o StrictHostKeyChecking=no {conn} 'mkdir -p {remote_path}'")
            Utils.run_or_die(f"rsync -r {local_path}/ {conn}:{remote_path}/")

        # Create python environment and install 'mlspeclib' library and/or other requirements.
        if self.mlbox.platform.env.interpreter.type == InterpreterType.System:
            # Assuming it has already been configured. Do not want to deal with 'sudo' and other things here.
            python = self.mlbox.platform.env.interpreter.python
        else:
            # In other cases it may be required to create virtualenv/conda environments and install dependencies.
            # Since python environment is fully specified by the python executable, in all other places we just need
            # to know the full path to python that is provided by metadata helper classes.
            raise ValueError("Unsupported python interpreter")

        # Configure remote MLBox runner. Idea is that we use chain of runners, for instance, SHH Runner -> Docker
        # runner. So, the runner to be used on a remote host must configure itself.

        # Path to a MLBox workload on a remote host relative to the MLBox library directory.
        mlbox_rel_path = os.path.relpath(self.mlbox.platform.mlbox.path, self.mlbox.platform.env.path)
        cmd = f"export PYTHONPATH=$(pwd)/mlcommons_box:$(pwd)/runners/{self.remote_runner}; "\
              f"{python} -m {self.remote_runner} configure --mlbox={mlbox_rel_path} "\
              f"--platform={mlbox_rel_path}/platform/{self.mlbox.platform.mlbox_platform}"
        cmd = f"ssh -o StrictHostKeyChecking=no {conn} 'cd {self.mlbox.platform.env.path}; {cmd}'"
        Utils.run_or_die(cmd)

    def run(self, task_file: str):
        """ Run 'run' phase, one of the MLBox tasks.
        Args:
             task_file (str): A file path to a task file on a local host. It is assumed the relative path to the mlbox
                root folder is "run/{task_name}.yaml"
        """
        # This is all temporary solution. SSH runner needs to delegate it to the runner on a remote host.
        if self.mlbox.platform.env.interpreter.type != InterpreterType.System:
            raise ValueError("Only system python interpreters are supported.")

        if self.mlbox.platform.env.interpreter.type == InterpreterType.System:
            python = self.mlbox.platform.env.interpreter.python
        else:
            raise ValueError("Unsupported python interpreter")
        conn = "{}@{}".format(self.mlbox.platform.user, self.mlbox.platform.host)
        # Path to a MLBox workload on a remote host relative to the MLBox library directory.
        mlbox_rel_path = os.path.relpath(self.mlbox.platform.mlbox.path, self.mlbox.platform.env.path)
        remote_task_file = os.path.join(mlbox_rel_path, 'run', os.path.basename(task_file))
        cmd = f"export PYTHONPATH=$(pwd)/mlcommons_box:$(pwd)/runners/{self.remote_runner}; "\
              f"{python} -m {self.remote_runner} run --mlbox={mlbox_rel_path} "\
              f"--platform={mlbox_rel_path}/platforms/{self.mlbox.platform.mlbox_platform} "\
              f"--task={remote_task_file}"
        cmd = f"ssh -o StrictHostKeyChecking=no {conn} 'cd {self.mlbox.platform.env.path}; {cmd}'"
        Utils.run_or_die(cmd)

        # Sync back results
        # TODO: Only workspace/ directory is synced. Better solution?
        remote_path, local_path = self.mlbox.platform.mlbox.path, self.mlbox.root
        Utils.run_or_die("rsync -r {}:{}/workspace/ {}/workspace/".format(conn, remote_path, local_path))
