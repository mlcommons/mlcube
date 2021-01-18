# Lint as: python3
"""Generates a template of a docker.

This takes an MLCube directory which has metadata filled in
and produces docker and source files to build.
"""

import sys
import os

from mlcube import mlcube_check


DOCKER_TEMPLATE = """
FROM ubuntu:20.04

RUN apt update
RUN apt-get -y install python3

ADD internal_docker_* /

ENTRYPOINT ["/usr/bin/python3", "/internal_docker_mlcube_main.py"]
"""

INTERNAL_MAIN_TEMPLATE = """
# Lint as: python3
import sys
import os
import re

{functions}

def parse_command_line():
  task = sys.argv[1]

  iomap = {{}}
  for arg in sys.argv[2:]:
    match = re.match('--([^=]+)=(.+)', arg)
    if not match:
      raise Exception('Invalid argument: {{}}'.format(arg))
    ioname = match.group(1)
    path = match.group(2)
    iomap[ioname] = path
  return task, iomap


def main():
  print('MLCube starting.')
  task, iomap = parse_command_line()

{dispatch}


if __name__ == '__main__':
  main()
"""


TASK_MAIN = """
import sys


def main():
{args}

  # TODO Implement your task here, such as calling your main file.
  raise NotImplementedError 


if __name__ == '__main__':
  main()
"""


def generate_function(task_name, io_names):
  code = 'def mlcube_{}(iomap):\n'.format(task_name)
  for io_name in io_names:
    code += '  {} = iomap["{}"]\n'.format(io_name, io_name)

  command_line = '  return os.system("python3 internal_docker_mlcube_task_{}.py '.format(task_name)
  command_line += ' {} ' * len(io_names)
  command_line += '".format({}))'.format(', '.join(io_names))
  code += command_line
  return code


def generate_dispatch(task_names):
  code = ''
  for i, task_name in enumerate(task_names):
    if i == 0:
      code += '  if task == "{}":\n'.format(task_name)
    else:
      code += '  elif task == "{}":\n'.format(task_name)
    code += '    if not mlcube_{}(iomap):\n'.format(task_name)
    code += '      sys.exit(1)\n'
  code += '  else:\n'
  code += '    print("No known MLCube task: {}".format(task))\n'
  code += '    sys.exit(1)\n'
  return code


def write_file(filename, text):
  # TODO warn before overwriting
  print('Writing file: {}'.format(filename))
  with open(filename, 'w') as f:
    f.write(text)


def generate_task_main_text(task_name, io_names):
  args = ''
  for i, io_name in enumerate(io_names):
    args += '  {} = sys.argv[{}]\n'.format(io_name, i + 1)
  return TASK_MAIN.format(args=args)


def generate_readme_text(mlcube_root, mlcube, task_main_names):
  run_yamls = []
  for f in os.listdir(os.path.join(mlcube_root, 'run')):
    if '.yaml' in f:
      run_yamls.append(os.path.join(os.path.join(mlcube_root, 'run'), f))

  if len(run_yamls) == 0:
    run_text = 'You need to first create some run configs under {}'.format(os.path.join(mlcube_root, 'run'))
  else:
    run_text = ''
    for run in run_yamls:
      run_text += 'python3 mlcube_docker_run/docker_run.py --no-pull {}\n'.format(run)

  text = r"""Here is a starting point to create your MLCube's Docker Image.

Here are some notes to get started:
- Feel free to replace Dockerfile with an existing one you use!
- Make sure to use internal_docker_mlcube_main.py as your main file (even in a
  different docker).


1. Each task in your MLCube has a separate main file which was generated:
{task_mains}
Edit these files to call your model.

2. Build your docker;
sudo docker build . -t {docker_tag}

3. Try running your docker (may want to -f for overwriting output files);
{run_text}

4. Once  your docker works, upload it to the respository.
docker push {docker_tag}
""".format(task_mains=', '.join(task_main_names), docker_tag=mlcube.docker.image, run_text=run_text)
  return text


def generate_internal_main(mlcube):
  task_names = list(mlcube.tasks)
  task_main_texts = {}

  functions = ''
  for task_name in task_names:
    task = mlcube.tasks[task_name]
    io_names = []
    io_names.extend(task.inputs)
    io_names.extend(task.outputs)

    task_main_texts[task_name] = generate_task_main_text(task_name, io_names)

    functions += generate_function(task_name, io_names)
    functions += '\n\n'

  dispatch = generate_dispatch(task_names)
  text = INTERNAL_MAIN_TEMPLATE
  text = text.format(functions=functions, dispatch=dispatch)
  return text, task_main_texts


def generate(mlcube_dir, mlcube):
  internal_main_text, task_main_texts = generate_internal_main(mlcube)

  main_file_path = os.path.join(mlcube_dir, 'build', 'internal_docker_mlcube_main.py')
  if not os.path.exists(os.path.dirname(main_file_path)):
    os.mkdir(os.path.dirname(main_file_path))

  write_file(main_file_path, internal_main_text)

  task_main_names = []
  for task_name in task_main_texts:
    task_file_path = os.path.join(mlcube_dir, 'build', 'internal_docker_mlcube_task_{}.py'.format(task_name))
    task_main_names.append(task_file_path)
    write_file(task_file_path, task_main_texts[task_name])

  docker_file_path = os.path.join(mlcube_dir, 'build', 'Dockerfile')
  write_file(docker_file_path, DOCKER_TEMPLATE)

  readme_file_path = os.path.join(mlcube_dir, 'build', 'README.md')
  readme_text = generate_readme_text(mlcube_dir, mlcube, task_main_names)
  write_file(readme_file_path, readme_text)


def main():
  if len(sys.argv) != 2:
    print('usage: MLCUBE_DIR')
    sys.exit(-1)
  mlcube_dir = sys.argv[1]
  mlcube = mlcube_check.check_root_dir_or_die(mlcube_dir)
  generate(mlcube_dir, mlcube)


if __name__ == '__main__':
  main()
