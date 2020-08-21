import os
import sys
import argparse
import logging
import copy
from mlbox import mlbox_parse  # Do not remove (it registers schemas on import)
from mlbox_ssh_run import (ssh_metadata, mlbox_metadata)
from mlbox_ssh_run.mlbox_metadata import RuntimeType
from mlbox_ssh_run.ssh_metadata import InterpreterType
from mlbox_ssh_run.utils import Utils


logger = logging.getLogger(__name__)


class SSHRun(object):
    """
    Reference implementation of the remote runner based on SSH.

    SSH runner accepts standard MLBox configuration files that are not ssh runner-specific. SHH runner uses platform
    configuration file to access remote nodes to run MLBoxes the same way other runners (e.g., docker runner) run
    the same MLBoxes locally. So, the only difference is the requirement for platform configuration file.
    """

    def __init__(self, mlbox: mlbox_metadata.MLBox, platform: dict):
        """
        Mandatory key: host, user, runtime. mlbox
        Args:
            platform (dict): Platform configuration dictionary.
        """
        self.mlbox: mlbox_metadata.MLBox = mlbox

        platform = copy.deepcopy(platform)
        # The following code is to verify that all fields are present.
        if 'host' not in platform:
            raise ValueError("Missing mandatory parameter 'host'")
        if 'user' not in platform:
            raise ValueError("Missing mandatory parameter 'user'")
        #
        platform['env'] = Utils.get(platform, 'env', {'path': None, 'sync': True,
                                                      'interpreter': {'type': 'system', 'python': 'python'},
                                                      'variables': {}})
        platform['env']['path'] = Utils.get(platform['env'], 'path', '.mlbox')
        platform['env']['sync'] = Utils.get(platform['env'], 'sync', True)
        platform['env']['interpreter'] = Utils.get(platform['env'], 'interpreter',
                                                   {'type': 'system', 'python': 'python'})
        platform['env']['variables'] = Utils.get(platform['env'], 'variables', {})

        platform['mlbox'] = Utils.get(platform, 'mlbox', {'path': None, 'sync': True})
        platform['mlbox']['path'] = Utils.get(
            platform['mlbox'],
            'path',
            os.path.join(platform['env']['path'], 'mlboxes', mlbox.qualified_name)
        )
        platform['mlbox']['sync'] = Utils.get(platform['mlbox'], 'sync', True)

        self.platform: ssh_metadata.Platform = ssh_metadata.Platform(platform)

    def configure(self):
        """Run 'configure' phase for SHH runner."""
        conn = "{}@{}".format(self.platform.user, self.platform.host)

        # Sync mlbox library (runners) root directory with the remote host.
        if self.platform.env.sync is True:
            # Local and remote paths of MLBox library.
            local_path = os.path.abspath((os.path.dirname(os.path.dirname(__file__))))
            remote_path = self.platform.env.path
            # Create target directory on a remote host and sync selected folders.
            Utils.run_or_die(f"ssh -o StrictHostKeyChecking=no {conn} 'mkdir -p {remote_path}'")
            for path in ('mlbox', 'mlbox_docker_run', 'mlbox_old', 'mlbox_ssh_run'):
                Utils.run_or_die(f"rsync -r {local_path}/{path} {conn}:{remote_path}")

        # Sync MLBox workload directories
        if self.platform.mlbox.sync is True:
            # The 'local_path' and 'remote_path' must both be directories.
            local_path, remote_path = self.mlbox.root, self.platform.mlbox.path
            Utils.run_or_die(f"ssh -o StrictHostKeyChecking=no {conn} 'mkdir -p {remote_path}'")
            Utils.run_or_die(f"rsync -r {local_path}/ {conn}:{remote_path}/")

        # Create python environment and install 'mlspeclib' library and/or other requirements.
        if self.platform.env.interpreter.type == InterpreterType.System:
            # Assuming it has already been configured. Do not want to deal with 'sudo' and other things here.
            pass
        else:
            # In other cases it may be required to create virtualenv/conda environments and install dependencies.
            # Since python environment is fully specified by the python executable, in all other places we just need
            # to know the full path to python that is provided by metadata helper classes.
            raise ValueError("Unsupported python interpreter")

        # Configure remote MLBox runner. Idea is that we use chain of runners, for instance, SHH Runner -> Docker
        # runner. So, the runner to be used on a remote host must configure itself.
        # TODO: A temporary solution (while porting to main branch). This must be implemented in the respective runners.
        if self.mlbox.runtime.type == RuntimeType.Docker:
            # Path to a MLBox workload on a remote host relative to the MLBox library directory.
            mlbox_rel_path = os.path.relpath(self.platform.mlbox.path, self.platform.env.path)
            build_args = self.platform.env.docker_build_args()
            cmd = f"docker build {mlbox_rel_path}/build {build_args} -t {self.mlbox.runtime.image}"
            cmd = f"ssh -o StrictHostKeyChecking=no {conn} 'cd {self.platform.env.path}; {cmd}'"
            Utils.run_or_die(cmd)

    def run(self, task_file: str):
        """ Run 'run' phase, one of the MLBox tasks.
        Args:
             task_file (str): A file path to a task file on a local host. It is assumed the relative path to the mlbox
                root folder is "run/{task_name}.yaml"
        """
        # This is all temporary solution. SSH runner needs to delegate it to the runner on a remote host.
        if self.mlbox.runtime.type != RuntimeType.Docker:
            raise ValueError("Only docker-based MLBoxes are supported.")
        if self.platform.env.interpreter.type != InterpreterType.System:
            raise ValueError("Only system python interpreters are supported.")

        conn = "{}@{}".format(self.platform.user, self.platform.host)
        mlbox_rel_path = os.path.relpath(self.platform.mlbox.path, self.platform.env.path)
        remote_task_file = os.path.join(mlbox_rel_path, 'run', os.path.basename(task_file))
        docker_args = self.platform.env.docker_run_args()
        if docker_args != "":
            docker_args = f"MLBOX_DOCKER_ARGS=\"{docker_args}\""

        # Run task
        cmd = f"{self.platform.env.interpreter.python} mlbox_docker_run/docker_run.py --no-pull {remote_task_file}"
        cmd = f"ssh -o StrictHostKeyChecking=no {conn} "\
              f"'cd {self.platform.env.path}; PYTHONPATH=$(pwd) {docker_args} {cmd};'"
        Utils.run_or_die(cmd)

        # Sync back results
        # TODO: Only workspace/ directory is synced. Better solution?
        remote_path, local_path = self.platform.mlbox.path, self.mlbox.root
        Utils.run_or_die("rsync -r {}:{}/workspace/ {}/workspace/".format(conn, remote_path, local_path))
        return 0


def main():
    if len(sys.argv) <= 1:
        raise ValueError("Usage: python {} configure|run mlbox_path|task_file --platform PLATFORM".format(sys.argv[0]))

    action, action_args = sys.argv[1], sys.argv[2:]
    if action not in ('configure', 'run'):
        raise ValueError(f"Wrong action: '{action}'")

    parser = argparse.ArgumentParser(description='[MLBox] SSH Runner.')
    parser.add_argument('path', type=str)
    parser.add_argument('--platform', dest='platform', type=str, default=None)
    args = parser.parse_args(action_args)

    mlbox_root = args.path if action == 'configure' else os.path.dirname(os.path.dirname(args.path))
    mlbox: mlbox_metadata.MLBox = mlbox_metadata.MLBox(path=mlbox_root)
    platform: dict = Utils.load_yaml(args.platform)

    ssh_runner = SSHRun(mlbox, platform)
    print(ssh_runner.mlbox)
    print(ssh_runner.platform)

    if action == 'configure':
        ssh_runner.configure()
    else:
        ssh_runner.run(task_file=args.path)


if __name__ == '__main__':
    main()
