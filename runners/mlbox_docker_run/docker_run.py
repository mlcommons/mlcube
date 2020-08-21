# Lint as: python3
"""Runs an MLBox.

"""

import argparse
import sys
import os

import pprint

from mlbox import mlbox_parse
from mlbox import mlbox_check


def make_parser():
  parser = argparse.ArgumentParser(description='Process some integers.')
  parser.add_argument('invoke_file', type=str)
  parser.add_argument('--mlbox-root', dest='mlbox_root', type=str, default=None)
  parser.add_argument('--nvidia-docker-command', type=str, default='nvidia-docker', dest='nvidia_docker')
  parser.add_argument('--docker-command', type=str, default='sudo docker run', dest='docker')
  parser.add_argument('--pull', dest='pull', action='store_true')
  parser.add_argument('--no-pull', dest='pull', action='store_false')
  parser.add_argument('--dry-run', dest='dry_run', action='store_true', default=False)
  parser.add_argument('--force', '-f', dest='force', action='store_true', default=False)
  parser.set_defaults(pull=True)
  return parser


def resolve_docker_command(mlbox, docker, nvidia_docker):
  if mlbox.docker.docker_runtime == 'docker':
    return 'docker'
  if mlbox.docker.docker_runtime == 'nvidia-docker':
    return nvidia_docker


def main():
  parser = make_parser()
  args = parser.parse_args()

  mlbox_root = os.path.dirname(os.path.dirname(args.invoke_file))
  if args.mlbox_root is not None:
    mlbox_root = args.mlbox_root

  mlbox_root = os.path.abspath(mlbox_root)
  mlbox = mlbox_check.check_root_dir_or_die(mlbox_root)
  invoke = mlbox_check.check_invoke_file_or_die(args.invoke_file)
  mlbox_check.check_invoke_semantics_or_die(mlbox, invoke)
  workspace = os.path.abspath(os.path.join(mlbox_root, 'workspace'))
  docker_command = resolve_docker_command(mlbox, docker=args.docker, nvidia_docker=args.nvidia_docker)

  if args.pull:
    command = pull_image_command(mlbox.docker.image)
    print(command)
    if not args.dry_run:
      if os.system(command) != 0:
        sys.exit(1)

  docker = build_invoke(mlbox, invoke, docker_command, mlbox.docker.image,
                        workspace=workspace, force=args.force)

  command = docker.command_str()
  print(command)
  if not args.dry_run:
    sys.exit(os.system(command))


def check_input_path_or_die(metadata, invoke, input_name, input_path, force=False):
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


def check_output_path_or_die(metadata, invoke, output_name, output_path, force=False):
  if os.path.exists(output_path) and not force:
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


def build_invoke(metadata, invoke, docker_command, image_tag, workspace, force=False):
  docker = DockerRun(docker_command, image_tag)

  args = [invoke.task_name]
  for input_name, input_path in invoke.input_binding.items():
    input_path = input_path.replace('$WORKSPACE', workspace)
    check_input_path_or_die(metadata, invoke, input_name, input_path, force=force)

    translated_path = docker.mount_and_translate_path(input_path)
    args.append('--{}={}'.format(input_name, translated_path))

  for output_name, output_path in invoke.output_binding.items():
    output_path = output_path.replace('$WORKSPACE', workspace)
    check_output_path_or_die(metadata, invoke, output_name, output_path, force=force)

    translated_path = docker.mount_and_translate_path(output_path)
    args.append('--{}={}'.format(output_name, translated_path))

  docker.set_args(args)
  return docker


def pull_image_command(image_name):
  return 'docker pull {}'.format(image_name)


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
    return '{} run {} {} --net=host --privileged=true -t {} {}'.format(
        self.docker_command,
        self.mount_str(),
        os.environ.get('MLBOX_DOCKER_ARGS', ''),
        self.image_tag,
        ' '.join(self.args))


if __name__ == '__main__':
  main()
