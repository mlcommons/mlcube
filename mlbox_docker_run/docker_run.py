# Lint as: python3
"""

TODO(vbittorf): DO NOT SUBMIT without a detailed description of docker_run.
"""

import sys
import os

import pprint

from mlbox import mlbox_parse
from mlbox import mlbox_check


def main():
  if len(sys.argv) != 3:
    print('usage: docker_run.py MLBOX_ROOT INVOKE_FILE')
    sys.exit(1)

  metadata = mlbox_check.check_root_dir_or_die(sys.argv[1])
  pprint.pprint(metadata.tasks)
  print('Checked')
  invoke = mlbox_check.check_invoke_file_or_die(sys.argv[2])

  mlbox_check.check_invoke_semantics_or_die(metadata, invoke)

  workspace = os.path.abspath(sys.argv[1] + '/workspace')

  # TODO pull the image
  # pull_image(metadata.docker.image)
  docker = build_invoke(metadata, invoke, 'docker', metadata.docker.image,
                        workspace=workspace)

  print(docker.command_str())


def check_input_path_or_die(metadata, invoke, input_name, input_path):
  task_metadata = metadata.tasks[invoke.task_name]
  is_file = task_metadata.inputs[input_name].type == 'file'

  if not os.path.exists(input_path):
    print('FATAL: Input "{}" not found at: {}'.format(input_name, input_path))
    sys.exit(1)

  # TODO support other file systems such as S3 and GCS.
  if is_file and not os.path.isfile(input_path):
    print('FATAL: Expected Input "{}" to be a file, found directory at {}'.format(
        input_name, input_path))
    sys.exit(1)

  if not is_file and not os.path.isdir(input_path):
    print('FATAL: Expected Input "{}" to be a directory, found file at {}'.format(
        input_name, input_path))
    sys.exit(1)


def check_output_path_or_die(metadata, invoke, output_name, output_path):
  if os.path.exists(output_path):
    print('WARNING: Refusing verwrite Output "{}" already exists: {}'.format(
        output_name, output_path))
    sys.exit(1)

  task_metadata = metadata.tasks[invoke.task_name]
  is_file = task_metadata.outputs[output_name].type == 'file'
  if is_file:
    # The file must exist or else it will be mounted as a directory into docker
    status = os.system('touch {}'.format(output_path))
    if status != 0:
      print('FATAL Unable to touch output file at: {}'.format(output_path))

  # TODO similar check for the directory


def build_invoke(metadata, invoke, docker_command, image_tag, workspace):
  docker = DockerRun(docker_command, image_tag)

  args = [invoke.task_name]
  for input_name, input_path in invoke.input_binding.items():
    input_path = input_path.replace('$WORKSPACE', workspace)
    check_input_path_or_die(metadata, invoke, input_name, input_path)

    translated_path = docker.mount_and_translate_path(input_path)
    args.append('--{}={}'.format(input_name, translated_path))

  for output_name, output_path in invoke.output_binding.items():
    output_path = output_path.replace('$WORKSPACE', workspace)
    check_output_path_or_die(metadata, invoke, output_name, output_path)

    translated_path = docker.mount_and_translate_path(output_path)
    args.append('--{}={}'.format(output_name, translated_path))

  docker.set_args(args)
  return docker


def pull_image(image_name):
  os.system('docker pull {}'.format(image_name)


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
