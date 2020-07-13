# Lint as: python3
"""Checks MLBox metadata to ensure it is valid.

Will crawl a parsed metadata and check for sanity and correctness.
"""

from pathlib import Path

import mlbox_parse


def check_root_dir(root_dir):
  metadata, err = mlbox_parse.parse_mlbox(Path(root_dir).resolve().as_posix())

  if err:
    return None, err

  return metadata, None


