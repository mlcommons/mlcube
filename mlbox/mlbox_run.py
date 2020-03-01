import glob
import os
import sys

import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

import mlbox_parser


def get_commandline_args():
    """Parses commandline.
    For example:
    box/path:TASK/params --params=/foo/bar
    Becomes:
    'box/path', {'params': '/foo/bar'}
    """
    print(sys.argv)
    mlbox = sys.argv[1]
    parts = mlbox.split(':')
    mlbox_dir = parts[0]
    task_and_inputs = parts[1]
    task = task_and_inputs.split('/')[0]
    input_group = task_and_inputs.split('/')[1]

    io = {}
    for arg in sys.argv[2:]:
        args = arg.split('=')
        name = args[0].strip('--')
        val = args[1]
        print(name, val)
        io[name] = val
    return mlbox_dir, task, input_group, io


# def construct_docker_command_with_default_inputs(mlbox_dir, task_name, input_group,
#         override_paths):
#     # TOOD: this function isn't perfect, this just demonstrates the basic idea
#     # This function will need to be modified to work reliably  (or at all)
# 
#     #volume_map = {}
# 
#     task_metadata = mlbox_dir.task_metadata(task_name)
#     print(task_metadata)
# 
#     names_to_paths =  {}
# 
#     # determine the input paths
#     for input_name in task_metadata['inputs']:
#         path = None
#         if input_name in override_paths:
#             path = override_paths[input_name]
#         else:
#             path = mlbox_dir.get_default_input_path(task_name, input_group, input_name)
#         path = os.path.abspath(path)
#         names_to_paths[input_name] = path
# 
#     outputs_directory = mlbox_dir.outputs_directory(task_name, input_group)
#     for output_name in task_metadata['outputs']:
#         path = None
#         if output_name in override_paths:
#             path = override_paths[output_name]
#         else:
#             path = os.path.join(outputs_directory, output_name)
#         path = os.path.abspath(path)
#         names_to_paths[output_name] = path
# 
#     print(mlbox_dir.standard_docker_metadata)
#     run_docker(mlbox_dir.standard_docker_metadata['container']['image'], names_to_paths)
# 
# 
# def get_volumes_and_paths(inputs):
#     """Given a bunch of local paths on the host. Determine where the containing
#     directories need to be mounted in the docker.
# 
#     For Example, 
#     ['/home/me/foo/bar', '/home/me/foo/bar2', '/home/me/whiz/bang']
#     Becomes
#     {'/home/me/foo': '/input0', '/home/me/whiz': '/input1'}, 
#     {'/home/me/foo/bar': '/input0/bar',
#      '/home/me/foo/bar2': '/input0/bar2',
#      '/home/me/whiz/bang': '/input1/bang'}
#     """
#     dir_map = {}
#     path_map = {}
#     for i, input_path in enumerate(inputs):
#         outer_dir = os.path.dirname(input_path)
#         if outer_dir not in dir_map:
#             dir_map[outer_dir] = '/input{}'.format(i)
#         path_map[input_path] = os.path.join(dir_map[outer_dir], os.path.basename(input_path))
#     return dir_map, path_map
# 
# 
# def run_docker(docker_name, input_map):
#     """Prints the command to run the docker
# 
#     Example input_map:
#     {'params': 'tasks/big_run/input/params.yaml', ...}
#     """
#     volumes, mapped_inputs = get_volumes_and_paths(input_map.values())
#     print('volumes: ', volumes)
#     print('mapped_inputs:', mapped_inputs)
#     volumes_str = ' '.join(
#           ['-v {}:{}'.format(t[0], t[1]) for t in volumes.items()])
#     arguments = []
#     for input_name in input_map:
#         inner_path = mapped_inputs[input_map[input_name]]
#         arguments.append('--{}={}'.format(input_name, inner_path))
#     cmd = 'sudo docker run {} --net=host --privileged=true -t {} {}'.format(
#           volumes_str, docker_name, ' '.join(arguments))
#     print(cmd)
#     # ensure failure is shown to caller.
#     # if os.system(cmd) != 0:
#     #     sys.exit(1)


def get_args_with_defaults(mlbox, overrides, task_name, defaults=None):
    args = {}
    task = mlbox.tasks[task_name]
    io_name_list = list(task.inputs.keys())
    io_name_list.extend(list(task.outputs.keys()))

    print(task.inputs)
    print(task.outputs)
    print(task.defaults)
    print(overrides)

    for io_name in io_name_list:
        if io_name in overrides:
            args[io_name] = overrides[io_name]
        elif defaults not in task.defaults:
            raise Exception('No such defaults for: {}'.format(defaults))
        elif io_name not in task.defaults[defaults].default_paths:
            raise Exception('Defaults for {} does not include {}.'.format(defaults, io_name))
        else:
            args[io_name] = os.path.join(mlbox.workspace_dir,
                    task.defaults[defaults].default_paths[io_name])
    return args


def main():
    mlbox_dir, task_name, input_group, io = get_commandline_args()

    # Run using a direct python runner
    mlbox = mlbox_parser.create_metadata(mlbox_dir)

    print('Going to {}'.format(mlbox.implementation_dir))
    os.chdir(mlbox.implementation_dir)


    args = get_args_with_defaults(mlbox, io, task_name, input_group)
    args['mlbox_task'] = task_name
    cmd = 'python {} {}'.format(mlbox.implementation.main_file,
        ' '.join(['--{}={}'.format(k, v) for k, v in args.items()]))
    print(cmd)
    os.system(cmd)


if __name__ == '__main__':
    main()

