import argparse
import os
import shutil
import sys


def main():
  parser = argparse.ArgumentParser(description="MLBox Cookie Cutter")
  parser.add_argument(
      "--root-dir", type=str, help="Root directory of the new MLBox",
      default="example_mlbox")
  args = parser.parse_args()

  if os.path.isdir(args.root_dir):
    print("Path already exists: {}".format(args.root_dir))
    sys.exit(1)

  cookie_cutter_path = os.path.dirname(os.path.realpath(__file__))
  template_path = os.path.join(cookie_cutter_path, "template")
  shutil.copytree(template_path, args.root_dir)
  print("Template MLBox created at {}".format(args.root_dir))


if __name__ == "__main__":
  main()
