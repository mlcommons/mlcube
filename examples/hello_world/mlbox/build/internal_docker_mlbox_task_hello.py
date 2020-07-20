
import sys


def main():
  name = sys.argv[1]
  greeting = sys.argv[2]

  with open(name_file) as f:
    with open(greeting_file, 'w') as o:
      o.write('Hello, {}!\n'.format(f.read().strip()))


if __name__ == '__main__':
  main()
