import argparse


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument(
        "--task", type=str,
        help="The MLBox task to preform.",
        metavar="<TASK>")


if __name__ == "__main__":
  main()
