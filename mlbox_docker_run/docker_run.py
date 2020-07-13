# Lint as: python3
"""

TODO(vbittorf): DO NOT SUBMIT without a detailed description of docker_run.
"""

import sys
import os

from mlbox import mlbox_parse
from mlbox import mlbox_check


def main():
  if len(sys.argv) != 3:
    print('usage: docker_run.py MLBOX_ROOT INVOKE_FILE')
    sys.exit(1)

  metadata = mlbox_check.check_root_dir_or_die(sys.argv[1])
  invoke = mlbox_check.check_invoke_file_or_die(sys.argv[2])

  mlbox_check.check_invoke_semantics_or_die(metadata, invoke)

  workspace = os.path.abspath(sys.argv[1] + '/workspace')
  docker = build_invoke(invoke, 'docker', '-t hello_world:latest', workspace=workspace)

  print(docker.command_str())


def build_invoke(invoke, docker_command, image_tag, workspace):
  docker = DockerRun(docker_command, image_tag)

  args = [invoke.task_name]
  for input_name, input_path in invoke.input_binding.items():
    input_path = input_path.replace('$WORKSPACE', workspace)
    translated_path = docker.mount_and_translate_path(input_path)
    args.append('--{}={}'.format(input_name, translated_path))

  for output_name, output_path in invoke.output_binding.items():
    output_path = output_path.replace('$WORKSPACE', workspace)
    translated_path = docker.mount_and_translate_path(output_path)
    args.append('--{}={}'.format(output_name, translated_path))

  docker.set_args(args)
  return docker


class DockerRun:
  def __init__(self, docker_command, image_tag):
    self.mounts = {}
    self.docker_command = docker_command
    self.image_tag = image_tag
    self.args = []

  def mount_and_translate_path(self, path):
    if path not in self.mounts:
      self.mounts[path] = '/mlbox_io{}/{}'.format(len(self.mounts),
                                                  os.path.basename(path))
    return self.mounts[path]

  def set_args(self, args):
    self.args = args

  def mount_str(self):
    return ' '.join(
        ['-v {}:{}'.format(path, self.mounts[path])
         for path in self.mounts])

  def command_str(self):
    return 'sudo {} run {} --net=host --privileged=true -t {} {}'.format(
        self.docker_command,
        self.mount_str(),
        self.image_tag,
        ' '.join(self.args))


if __name__ == '__main__':
  main()
