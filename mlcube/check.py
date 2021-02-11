# Lint as: python3
"""Checks MLCube metadata to ensure it is valid.

Will crawl a parsed metadata and check for sanity and correctness.
"""

import sys

from pathlib import Path
from mlcube.parse import parse_mlcube

def check_root_dir(root_dir):
  metadata, err = parse_mlcube(Path(root_dir).resolve().as_posix())
  if err:
    return None, err

  # TODO more checks
  return metadata, None


def check_root_dir_or_die(root_dir):
  metadata, err = check_root_dir(root_dir)
  if not err:
    return metadata

  print('FATAL root directory failed checks: {}'.format(root_dir))
  print(err)
  sys.exit(1)


def check_invoke_file(invoke_file):
  metadata, err = parse_mlcube_invoke(Path(invoke_file).resolve().as_posix())
  if err:
    return None, err

  # TODO more checks
  return metadata, None


def check_invoke_file_or_die(invoke_file):
  invoke, err = check_invoke_file(invoke_file)
  if not err:
    return invoke

  print('FATAL Checks failed for invoke file: {}'.format(invoke_file))
  print(err)
  sys.exit(1)


def check_invoke_semantics(metadata, invoke):
  task_name = invoke.task_name

  if task_name not in metadata.tasks:
    return 'No such task "{}"'.format(task_name)

  for input_name in invoke.input_binding:
    if input_name not in metadata.tasks[task_name].inputs:
      return 'No such input named "{}" for task "{}"'.format(
          input_name, task_name)

  for output_name in invoke.output_binding:
    if output_name not in metadata.tasks[task_name].outputs:
      return 'No such output named "{}" for task "{}"'.format(
          output_name, task_name)

  return None


def check_invoke_semantics_or_die(metadata, invoke):
  err = check_invoke_semantics(metadata, invoke)
  if not err:
    return
  print('FATAL invoke not valid for this mlcube: {}'.format(err))
  sys.exit(1)

