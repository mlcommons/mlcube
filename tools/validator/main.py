import argparse
import os
import yaml

from . import validators


def main():
  parser = argparse.ArgumentParser(description="MLBox Validator")
  parser.add_argument(
      "--root-dir", type=str, help="Root directory of the new MLBox",
      required=True)
  args = parser.parse_args()

  config_file = os.path.join(
      os.path.dirname(os.path.realpath(__file__)), "config.yaml")
  with open(config_file) as f:
    config = yaml.load(f)
  all_passed = True
  all_err = []
  for entry in config:
    path = os.path.join(args.root_dir, entry.get("path"))
    validator_list = entry.get("validators")
    for val in validator_list:
      val_class = getattr(validators, val.get("name"))
      val_args = val.get("args")
      passed, msg = val_class.validate(path, **val_args)
      all_passed = all_passed and passed
      if not passed:
        all_err.append(msg)
  if not all_passed:
    print("Validation failed. Errors:")
    for m in all_err:
      print(m)
  else:
    print("OK")


if __name__ == "__main__":
  main()
