import docker


class ContainerManager(object):
  """ContainerManager manages execution of MLBox container.
  """

  def __init__(self, container, volumes):
    """Initialize ContainerManager.
    Arguments:
      container: a dictionary containing container information
      volumes: list of volumes to be attached to the container
    """
    self.container_config = container
    self.volume_config = self._get_volume_config(volumes)
    self.client = docker.from_env()
    self.container = None

  def _get_volume_config(self, volumes):
    volume_config = {}
    for volume in volumes:
      path = volume.get("path", None)
      mount_path = volume.get("mountPath", None)
      mode = volume.get("mode", "ro")
      # TODO: need better error checking
      if (path is not None) and (mount_path is not None):
        volume_config[path] = {"bind": mount_path, "mode": mode}
    return volume_config

  def run(self, detach=True):
    """Run a container in detach mode.
    The container info will be saved in the ContainerManager object.
    """
    image = self.container_config.get("image", None)
    command = self.container_config.get("command", None)
    try:
      self.container = self.client.containers.run(
          image=image,
          command=command,
          volumes=self.volume_config,
          detach=detach)
      print("Started container: {}".format(self.container.short_id))
    except:
      raise

  def stop(self):
    """Stop a running container.
    """
    try:
      self.container.stop()
    except:
      raise
