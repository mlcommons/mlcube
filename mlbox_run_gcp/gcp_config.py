# Lint as: python3
"""Config for running in GCP.

"""
from absl import app
from absl import flags

FLAGS = flags.FLAGS


class GCPConfig:
  pass


def main(argv):
  if len(argv) > 1:
    raise app.UsageError('Too many command-line arguments.')

if __name__ == '__main__':
  app.run(main)
