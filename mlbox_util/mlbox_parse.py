# Lint as: python3
"""Parses an MLBox directory tree.

Will return objects which represent the metadata of the box.
"""

import os
import pprint

from pathlib import Path

from mlspeclib import MLObject, MLSchema


def _register_schemas():
  MLSchema.populate_registry()
  # TODO fix pathing
  MLSchema.append_schema_to_registry(Path("schemas"))


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
  root, err = parse_mlbox_root(root_dir + 'mlbox.yaml')
  print(root, err)

  tasks = []
  for task_file in root.tasks:
    task, err = parse_mlbox_task(os.path.join(root_dir, task_file))
    print(task, err)
    tasks.append(task)

  docker, err = parse_mlbox_docker(root_dir +  'mlbox_docker.yaml')
  print(docker, err)
  







_register_schemas()
parse_mlbox('/usr/local/google/home/vbittorf/mlbox/examples/hello_world/mlbox/')

