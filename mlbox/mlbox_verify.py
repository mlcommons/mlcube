# Lint as: python3
"""Verfies a directory is an MLBox.

Will print any errors that are found.
"""

import pprint
import sys

from pathlib import Path

import mlbox_check


def main():
  if len(sys.argv) != 2:
    print('usage: mlbox_verify.py DIRECTORY')
    sys.exit(1)

  metadata, err = mlbox_check.check_root_dir(
      Path(sys.argv[1]).resolve().as_posix())

  if err:
    print(err)
    sys.exit(1)

  pprint.pprint(metadata.root)
  pprint.pprint(metadata.tasks)
  pprint.pprint(metadata.docker)


if __name__ == '__main__':
  main()
