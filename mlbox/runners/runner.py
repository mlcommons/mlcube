from copy import deepcopy
from typing import List

try:
  from mlbox.container_manager import ContainerManager
except ImportError:
  ContainerManager = None


class MLBoxRunner(object):
  """Base class for all MLBox runners"""
  def __init__(self, platform_config: dict):
    """
    Args:
        platform_config (dict): A configuration dictionary for the platform.
    """
    self.__platform_config = deepcopy(platform_config)

  @property
  def platform_config(self):
    return self.__platform_config

  def configure(self):
    """ Configure a (remote) platform.
    TODO: Do we want here to setup the remote environment, such as installing missing packages?
    """
    raise NotImplementedError()

  def execute(self, cmd: List[str]) -> int:
    """ Execute command `cmd` on a platform specified by `platform_config`.
    Args:
        cmd (List[str]): Command to execute. It is built with assumptions that it will run locally on the
            specific platform described by `platform_config`.

    TODO: Do we need to capture output?
    """
    raise NotImplementedError()

  def run_with_docker(self, cmd: List[str]):
    cfg = self.platform_config
    if 'container' not in cfg:
      return False

    if ContainerManager is None:
      raise RuntimeError("The 'docker' package is missing.")
    cfg["container"]["command"] = ' '.join(cmd)
    container_manager = ContainerManager(cfg["container"], cfg["volumes"])
    container_manager.run()
    return True
