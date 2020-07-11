# Lint as: python3
"""Says  Hello to you!

Takes a file which contaisn a name and outputs a file which contains a greeting.
"""

import sys


def main():
  name_file = sys.argv[1]
  greeting_file  = sys.argv[2]

  with open(name_file) as f:
    with open(greeting_file, 'w') as o:
      o.write('Hello, {}!\n'.format(f.read().strip()))


if __name__ == '__main__':
  main()
