
# Lint as: python3
import sys
import os
import re

def mlcube_nvidia_smi(iomap):
  nvidia_smi = iomap["nvidia_smi"]
  return os.system("python3 internal_docker_mlcube_task_nvidia_smi.py  {} ".format(nvidia_smi))



def parse_command_line():
  task = sys.argv[1]

  iomap = {}
  for arg in sys.argv[2:]:
    match = re.match('--([^=]+)=(.+)', arg)
    if not match:
      raise Exception('Invalid argument: {}'.format(arg))
    ioname = match.group(1)
    path = match.group(2)
    iomap[ioname] = path
  return task, iomap


def main():
  print('MLCube starting.')
  task, iomap = parse_command_line()

  if task == "nvidia_smi":
    if not mlcube_nvidia_smi(iomap):
      sys.exit(1)
  else:
    print("No known MLCube task: {}".format(task))
    sys.exit(1)



if __name__ == '__main__':
  main()
