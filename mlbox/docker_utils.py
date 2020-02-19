"""
DockerUtils is based on Validator class from here:
    https://github.com/HewlettPackard/dlcookbook-dlbs/blob/master/python/dlbs/validator.py#L282
"""
import sys
import subprocess


class DockerUtils(object):

  def __init__(self, mlbox_docker_info: dict):
    self.__mlbox_docker_info = mlbox_docker_info

  def pull_image(self) -> bool:
    """ Pull an image - initial implementation.
    It may take substantial amount of time to complete this command, so output is printed out immediately.
    """
    try:
      cmd = ['docker', 'pull', self.__mlbox_docker_info['image']]
      ret_code = subprocess.check_call(cmd, stdout=sys.stdout, stderr=sys.stderr)
    except subprocess.CalledProcessError as err:
      ret_code = err.returncode
    return ret_code == 0

  def build_image(self) -> bool:
    """ Build an image - initial implementation.
    It may take substantial amount of time to complete this command, so output is printed out immediately.
    """
    cmd = ['docker', 'build']
    build_args = self.__mlbox_docker_info['build_args']
    for arg in build_args:
      cmd.extend(['--build-arg', '{}={}'.format(arg, build_args[arg])])
    cmd.extend(['-t', self.__mlbox_docker_info['image'], self.__mlbox_docker_info['context_path']])
    try:
      ret_code = subprocess.check_call(cmd, stdout=sys.stdout, stderr=sys.stderr)
    except subprocess.CalledProcessError as err:
      ret_code = err.returncode
    return ret_code == 0

  def can_run_docker(self) -> bool:
    """ Checks if MLBox can run docker/nvidia-docker/nvidia-docker2. """
    runtime = self.__mlbox_docker_info['docker']
    if runtime == 'docker' and '--runtime=nvidia' in self.__mlbox_docker_info['run_args']:
      runtime = "nvidia_docker2"

    def _get_docker_runtimes(info):
      for line in info:
        line = line.strip()
        if line.startswith('Runtimes:'):
          return line[9:].strip().split()
      return []

    try:
      if runtime in ['nvidia', 'nvidia-docker2', 'nvidia_docker2']:
        cmd = ["docker", "info"]
        ret_code, output = DockerUtils.run_process(cmd)
        if ret_code == 0 and 'nvidia' not in _get_docker_runtimes(output):
          ret_code = -1
      elif runtime in ['docker', 'runc']:
        ret_code, output = DockerUtils.run_process(["docker", "--version"])
      elif runtime in ['nvidia-docker', 'nvidia_docker']:
        ret_code, output = DockerUtils.run_process(["nvidia-docker", "--version"])
      else:
        ret_code = 1
    except OSError:
      ret_code = 1

    return ret_code == 0

  def docker_image_exists(self) -> bool:
    """ Checks if this docker image exists. """
    try:
      docker_image = self.__mlbox_docker_info['image']
      cmd = ["docker", "inspect", "--type=image", docker_image]
      ret_code, output = DockerUtils.run_process(cmd)
    except OSError:
      ret_code = 1
    return ret_code == 0

  @staticmethod
  def run_process(cmd, env=None):
    """Runs process with subprocess.Popen (run a test).
    Args:
        cmd (list): A command with its arguments to run.
        env (dict): Environmental variables to initialize environment.
    Returns:
        tuple: (return_code (int), command_output (list of strings))
    """
    process = subprocess.Popen(cmd, universal_newlines=True, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, env=env)
    output = []
    while True:
        line = process.stdout.readline()
        if line == '' and process.poll() is not None:
            break
        if line:
            output.append(line)
    return process.returncode, output
