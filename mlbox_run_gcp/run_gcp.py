# Lint as: python3
"""Runs an MLBox on GCP.

The general executin procceeds as follows;

1. Create a VM
2. Copy data to the VM
3. Execute the MLBox
4. Copy the data back
5. Delete the VM
"""

import yaml

import vm_manager


def read_config(filename):
  with open(filename) as f:
    return yaml.load(f, Loader=yaml.FullLoader)


class VMHandle:
  def __init__(self):
    pass


def create_vm():
  pass


def copy_data_to_vm(vm_handle):
  pass


def exeute_mlbox(vm_handle):
  pass


def copy_data_back(vm_handle):
  pass


def delete_vm(vm_handle):
  pass


def main(argv):
  pass


if __name__ == '__main__':
  main()
