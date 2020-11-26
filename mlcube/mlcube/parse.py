# Lint as: python3
"""Parses an MLCube directory tree.

Will return objects which represent the metadata of the mlcube.
"""

import os
from pathlib import Path

from mlspeclib import MLObject, MLSchema


class MLCubeMetadata:
  def __init__(self, root, tasks, docker):
    self.root = root
    self.tasks = tasks
    self.docker = docker


def _register_schemas():
  MLSchema.populate_registry()
  # TODO fix pathing
  MLSchema.append_schema_to_registry(Path(Path(__file__).parent, "schemas"))


def parse_mlcube_invoke(filename):
  if not os.path.exists(filename):
    return None, 'No such invocation file: {}'.format(filename)
  (root, err) = MLObject.create_object_from_file(filename)
  return root, err


def parse_mlcube_root(filename):
  (root, err) = MLObject.create_object_from_file(filename)
  return root, err


def mlobject_from_dict(schema_type, schema_version, dict_value):
    ml_object = MLObject()
    ml_object.set_type(
        schema_version=schema_version,
        schema_type=schema_type,
    )
    dict_value['schema_type'] = schema_type
    dict_value['schema_version'] = schema_version
    MLObject.update_tree(ml_object, dict_value)
    errors = ml_object.validate()

    if errors:
        return None, errors
    else:
        return ml_object, None


def parse_mlcube_task(filename):
    (task, err) = MLObject.create_object_from_file(filename)
    if err:
      return None, err

    inputs = {}
    for input_dict in task.inputs:
      input_obj, err = mlobject_from_dict('mlcube_task_input', '1.0.0', input_dict)
      if err:
        return None, err
      inputs[input_obj.name] = input_obj

    outputs = {}
    for output_dict in task.outputs:
      output_obj, err = mlobject_from_dict('mlcube_task_output', '1.0.0', output_dict)
      if err:
        return None, err
      outputs[output_obj.name] = output_obj

    task.inputs = inputs
    task.outputs = outputs
    return task, None


def parse_mlcube_docker(filename):
    (docker, err) = MLObject.create_object_from_file(filename)
    return docker, err


def parse_mlcube(root_dir):
  path = Path(root_dir, 'mlcube.yaml').as_posix()
  if not os.path.exists(path):
    return None, 'root metadata does not exist: {}'.format(path)

  root, err = parse_mlcube_root(path)
  if err:
    return None, err

  tasks = {}
  for task_file in root.tasks:
    task, err = parse_mlcube_task(os.path.join(root_dir, task_file))
    if err:
      return None, err
    if task is None:
      raise Exception(root_dir)
    name = Path(task_file).name.strip('.yaml')
    tasks[name] = task

  docker, err = parse_mlcube_docker(Path(root_dir, 'mlcube_docker.yaml').as_posix())
  if err:
    return None, err

  return MLCubeMetadata(root, tasks, docker), None


_register_schemas()
