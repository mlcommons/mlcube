import subprocess
import sys
from typing import List
from mlbox.runners.runner import MLBoxRunner


class LocalRunner(MLBoxRunner):
  """ A placeholder for a local runner implementation. """

  def __init__(self, platform_config: dict):
    """
    Args:
        platform_config (dict): A configuration dictionary for the platform.
    """
    super(LocalRunner, self).__init__(platform_config)

  def configure(self):
    """ Configure a (remote) platform."""
    # Nothing to do or checking for missing python/other packages?
    pass

  def execute(self, cmd: List[str]) -> int:
    """ Execute command `cmd` on a platform specified by `platform_config`.
    Args:
        cmd (List[str]): Command to execute. It is built with assumptions that it will run locally on the
            specific platform described by `platform_config`.
    """
    if self.run_with_docker(cmd):
      # TODO: Implement me.
      return 0
    try:
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
    return process.poll()
