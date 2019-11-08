import argparse

from mlbox import util
from mlbox import container_manager as cm


def main():
  parser = argparse.ArgumentParser(description="MLBox")
  subparsers = parser.add_subparsers(dest="subcommand")
  subparsers.required = True
  subparser_run = subparsers.add_parser("run", help="Run an MLBox.")
  subparser_run.add_argument(
      "--config", type=str, help="MLBox configuration file", required=True)

  args = parser.parse_args()
  if args.subcommand == "run":
    config = util.get_config(args.config)
    container_manager = cm.ContainerManager(
        config["container"], config["volumes"])
    container_manager.run()
