# Lint as: python3
"""Says  Hello to you!

Takes a file which contaisn a name and outputs a file which contains a greeting.
"""

import sys


def main():
  name_file = sys.argv[1]
  greeting_file  = sys.argv[2]
  farewell_file  = sys.argv[3]

  with open(name_file) as f:
    with open(greeting_file) as g:
      with open(farewell_file, 'w') as o:
        o.write('Once I said "{}" to you, now I say Goodbye {}!\n'.format(
            g.read().strip(),
            f.read().strip()))


if __name__ == '__main__':
  main()
