
import sys


def main():
  name = sys.argv[1]
  greeting = sys.argv[2]
  message = sys.argv[3]

  with open(name_file) as f:
    with open(greeting_file) as g:
      with open(farewell_file, 'w') as o:
        o.write('Once I said "{}" to you, now I say Goodbye {}!\n'.format(
            g.read().strip(),
            f.read().strip()))


if __name__ == '__main__':
  main()
