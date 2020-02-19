import subprocess
import sys
import logging
from typing import List, Union

from mlbox.docker_utils import DockerUtils
from mlbox.runners.runner import MLBoxRunner


logger = logging.getLogger(__name__)


class LocalRunner(MLBoxRunner):
  """ Local MLBox runner executes ML models on a local node: bare metal or docker containers. """

  def __init__(self, platform_config: dict):
    """
    Args:
        platform_config (dict): A configuration dictionary for the platform.
    """
    super(LocalRunner, self).__init__(platform_config)

  def configure_docker(self):
    cfg = self.platform_config
    logger.info("Configuring MLBox '%s' (%s)", cfg['name'], cfg['_mlbox_path'])
    docker_utils = DockerUtils(cfg['mlbox_docker_info'])

    logger.info("Checking if can run docker ... ")
    if not docker_utils.can_run_docker():
      raise ValueError("Docker runtime is not available")

    logger.info("Checking if docker image exists ... ")
    if not docker_utils.docker_image_exists():
      action = cfg['mlbox_docker_info']['configure']
      if action == 'build':
        logger.info("Image does not exist, building ... ")
        docker_utils.build_image()
      elif action == 'pull':
        logger.info("Image does not exist, pulling ... ")
        docker_utils.pull_image()
      elif action == 'load':
        logger.info("Image does not exist, loading ... ")
        raise NotImplementedError("Not Implemented")
      else:
        raise ValueError("Unknown docker action for configure step ('{}').".format(action))
    else:
      logger.info("Image found (%s).", cfg['mlbox_docker_info']['image'])

  def configure(self):
    """ Configure a (remote) platform.
    TODO: We target docker runtime, so, possibly, check for docker/nvidia-docker and a container, data sets as well?
    """
    cfg = self.platform_config
    if cfg['implementation'] == 'mlbox_docker':
      self.configure_docker()
    else:
      print("MLBox '{}' ({})".format(cfg['name'], cfg['_mlbox_path']), flush=True)

  def execute(self, cmd: Union[List[str], str]) -> int:
    """ Execute command `cmd` on a platform specified by `platform_config`.
    Args:
        cmd (List[str]): Command to execute. It is built with assumptions that it will run locally on the
            specific platform described by `platform_config`.
    TODO: Should output be redirected to somewhere instead of just writing to standard output?
    """
    cmd = LocalRunner.format_command(cmd)
    logging.info("Executing: %s", str(cmd))
    try:
      return subprocess.check_call(cmd, stdout=sys.stdout, stderr=sys.stderr)
    except subprocess.CalledProcessError as err:
      logging.warning("Error while executing MLBox: cmd=%s, err=%s", str(cmd), str(err))
      return err.returncode
