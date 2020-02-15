from typing import List, Union

from mlbox.runners.local import LocalRunner
from mlbox.runners.runner import MLBoxRunner


class SSHRunner(MLBoxRunner):
  """ SHH Runner that runs commands on remote machines using SSH protocol.

  Why would we want to use it instead of just logging in that node and running there with local runner?
    - More convenient? That's questionable.
    - For running distributed workloads.
    - Benchmark tools like DLBS can run benchmarks in parallel.

  Parameters that users can provide: user name, host, port, parameters for `ssh`.
  Users are responsible for setting password-less login to remote nodes.

  TODO: Several python packages can help with better implementation that will also introduce additional dependencies.
  """

  def __init__(self, platform_config: dict):
    """
    Args:
        platform_config (dict): A configuration dictionary for the platform.
    """
    super(SSHRunner, self).__init__(platform_config)

  def configure(self):
    """ Configure a (remote) platform.
    TODO: We target docker runtime, so, possibly, check for docker/nvidia-docker and a container, data sets as well?
    What if we need to build a container and user home directory is not on a shared drive? rsync?
    """
    pass

  def execute(self, cmd: Union[List[str], str]) -> int:
    """ Execute command `cmd` on a remote platform specified by `platform_config`.
    Args:
        cmd (List[str]): Command to execute. It is built with assumptions that it will run locally on the
            specific platform described by `platform_config`.

    ssh -o StrictHostKeyChecking=no ${USER}@${NODE} -p ${PORT} "command"
    Standard SSH port is 22
    """
    ssh_runner = ['ssh'] + self.platform_config.get("ssh_args", []) + [self.platform_config["host"]]
    cmd = LocalRunner.format_command(cmd)
    return LocalRunner({}).execute(ssh_runner + cmd)
