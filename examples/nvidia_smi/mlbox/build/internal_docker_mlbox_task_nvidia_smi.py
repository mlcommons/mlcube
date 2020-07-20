
import subprocess
import sys


def main():
  nvidia_smi = sys.argv[1]

  output = subprocess.check_output('/usr/bin/nvidia-smi')

  with open(nvidia_smi, 'w') as f:
    f.write(output.decode('utf-8'))


if __name__ == '__main__':
  main()
