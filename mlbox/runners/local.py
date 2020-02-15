import subprocess
import sys
from typing import List, Union
from mlbox.runners.runner import MLBoxRunner


class LocalRunner(MLBoxRunner):
  """ Local MLBox runner executes ML models on a local node: bare metal or docker containers. """

  def __init__(self, platform_config: dict):
    """
    Args:
        platform_config (dict): A configuration dictionary for the platform.
    """
    super(LocalRunner, self).__init__(platform_config)

  def configure(self):
    """ Configure a (remote) platform.
    TODO: We target docker runtime, so, possibly, check for docker/nvidia-docker and a container, data sets as well?
    """
    pass

  def execute(self, cmd: Union[List[str], str]) -> int:
    """ Execute command `cmd` on a platform specified by `platform_config`.
    Args:
        cmd (List[str]): Command to execute. It is built with assumptions that it will run locally on the
            specific platform described by `platform_config`.
    TODO: Should output be redirected to somewhere instead of just writing to standard output?
    """
    try:
      cmd = LocalRunner.format_command(cmd)
      print("Executing: {}".format(cmd))
      process = subprocess.Popen(cmd, universal_newlines=True, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, env=None)
    except OSError as err:
      print("Error executing MLBox: cmd={}, err={}".format(cmd, err))
      raise err

    while True:
      output = process.stdout.readline()
      if output == '' and process.poll() is not None:
        break
      if output:
        sys.stdout.write(output)
        sys.stdout.flush()

    for fd in (process.stdout, process.stdin, process.stderr):
      if fd:
        fd.close()

    return process.poll()
