# Lint as: python3
"""Parses an MLBox directory tree.

Will return objects which represent the metadata of the box.
"""

import os
import pprint

from pathlib import Path

from mlspeclib import MLObject, MLSchema


class MLBoxMetadata:
  def __init__(self, root, tasks, docker):
    self.root = root
    self.tasks = tasks
    self.docker = docker


def _register_schemas():
  MLSchema.populate_registry()
  # TODO fix pathing
  MLSchema.append_schema_to_registry(Path(Path(__file__).parent,  "schemas"))


def parse_mlbox_root(filename):
  (root, err) = MLObject.create_object_from_file(filename)
  return root, err


def parse_mlbox_task(filename):
    (task, err) = MLObject.create_object_from_file(filename)
    return task, err


def parse_mlbox_docker(filename):
    (docker, err) = MLObject.create_object_from_file(filename)
    return docker, err


def parse_mlbox(root_dir):
  root, err = parse_mlbox_root(Path(root_dir, 'mlbox.yaml').as_posix())
  if err:
    return None, err

  tasks = {}
  for task_file in root.tasks:
    task, err = parse_mlbox_task(os.path.join(root_dir, task_file))
    name = Path(task_file).name.strip('.yaml')
    if err:
      return None, err
    tasks[name] = task

  docker, err = parse_mlbox_docker(Path(root_dir, 'mlbox_docker.yaml').as_posix())
  if err:
    return None, err

  return MLBoxMetadata(root, tasks, docker), None


_register_schemas()
parse_mlbox('/usr/local/google/home/vbittorf/mlbox/examples/hello_world/mlbox/')

