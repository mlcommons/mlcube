import os
import sys
from typing import Any

import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


class Utils(object):
    """Collection of various helper functions from the old MLCube branch.
    Developed by: Victor Bittorf and Xinyuan Huang.
    Most of these methods are probably not used any more.
    """
    @staticmethod
    def get(d: dict, key: Any, default: Any) -> Any:
        """
        Args:
            d (dict): Input dictionary object.
            key (Any): Dictionary key to look up.
            default (Any): Default value to return if key not present OR key value is None
        Returns:
            Return default if key is not in d or d[key] is None.
        """
        value = d.get(key, default)
        return value if value is not None else default

    @staticmethod
    def load_yaml(path: str):
        with open(path) as stream:
            return yaml.load(stream.read(), Loader=Loader)

    @staticmethod
    def get_volumes_and_paths(inputs):
        """Given a bunch of local paths on the host. Determine where the containing
        directories need to be mounted in the docker.

        For Example,
        ['/home/me/foo/bar', '/home/me/foo/bar2', '/home/me/whiz/bang']
        Becomes
        {'/home/me/foo': '/input0', '/home/me/whiz': '/input1'},
        {'/home/me/foo/bar': '/input0/bar',
         '/home/me/foo/bar2': '/input0/bar2',
         '/home/me/whiz/bang': '/input1/bang'}
        """
        dir_map = {}
        path_map = {}
        for i, input_path in enumerate(inputs):
            outer_dir = os.path.dirname(input_path)
            if outer_dir not in dir_map:
                dir_map[outer_dir] = '/input{}'.format(i)
            path_map[input_path] = os.path.join(dir_map[outer_dir], os.path.basename(input_path))
        return dir_map, path_map

    @staticmethod
    def get_commandline_args(mlcube: str = None, user_args: list = None):
        """Parses command line.
        For example:
            cube/path:TASK/params --params=/foo/bar
        Becomes:
            'cube/path', {'params': '/foo/bar'}
        """
        mlcube = mlcube if mlcube is not None else sys.argv[1]
        parts = mlcube.split(':')
        mlcube_dir = parts[0]
        if len(parts) == 1:
            task = input_group = None
        else:
            task_and_inputs = parts[1]
            task_and_inputs = task_and_inputs.split('/')
            if len(task_and_inputs) == 1:
                task, input_group = task_and_inputs[0], 'default'
            elif len(task_and_inputs) == 2:
                task, input_group = task_and_inputs
            else:
                raise ValueError("Wrong task specification ({})".format(parts[1]))

        io = {}
        user_args = user_args if user_args is not None else sys.argv[2:]
        for arg in user_args:
            args = arg.split('=')
            name = args[0].strip('--')
            val = args[1]
            print(name, val)
            io[name] = val
        return mlcube_dir, task, input_group, io

    @staticmethod
    def construct_docker_run_command(mlcube, mount_volumes, kw_args, run_args=None) -> str:
        volumes_str = ' '.join(['-v {}:{}'.format(t[0], t[1]) for t in mount_volumes.items()])
        run_args = run_args if run_args is not None else {}
        docker_args_str = ' '.join(['-e {}:{}'.format(t[0], t[1]) for t in run_args.items()])
        args_str = ' '.join(sorted(['--{}={}'.format(k, v) for k, v in kw_args.items()]))
        cmd = 'sudo {} run {} {} --net=host --privileged=true -t {} {}'.format(
            mlcube.implementation.docker_runtime, volumes_str, docker_args_str, mlcube.implementation.image, args_str
        )
        return cmd

    @staticmethod
    def construct_docker_build_command(mlcube_root: str, image_name: str) -> str:
        return 'cd {}; sudo docker build -t {} -f implementation/docker/dockerfiles/Dockerfile .'.format(mlcube_root,
                                                                                                         image_name)

    @staticmethod
    def get_args_with_defaults(mlcube, overrides, task_name, defaults=None) -> dict:
        """Returns an argument map, {'arg_name': '/path/to/file'}"""
        task = mlcube.tasks[task_name]
        if defaults not in task.defaults:
            raise Exception('No such defaults for: {}'.format(defaults))

        args = {}
        task_args: list = list(task.inputs.keys()) + list(task.outputs.keys())

        # print("Defaults: ", defaults)  # A string
        # print("Task.Inputs: ", task.inputs)  # Mapping from a name to a MLTaskInput(name, desc)
        # print("Task.Outputs: ", task.outputs)  # Mapping from a name to a MLTaskOutput(name, desc)
        # print("Task.Defaults: ", task.defaults)
        # print("Overrides: ", overrides)  # Almost always empty

        # The 'task_args' is the list of input/output parameter names for this task.
        # The 'overrides' the dict of parameters that use has overridden on a command line
        # The 'defaults' is the parameter set for the current task
        for task_arg in task_args:
            if task_arg not in task.defaults[defaults].default_paths:
                raise Exception('Defaults for {} does not include {}.'.format(defaults, task_arg))
            # TODO: This is probably not the greatest idea, but I need to be able to work with unset parameters
            param_value = task.defaults[defaults].default_paths[task_arg]
            if task_arg in overrides:
                param_value = overrides[task_arg]

            if param_value is not None:
                args[task_arg] = os.path.join(mlcube.workspace_dir, param_value)
            else:
                print("[WARNING] Skipping '{}' argument for {}:{} (not set).".format(task_arg, task_name, defaults))
        return args

    @staticmethod
    def run_or_die(cmd):
        print(cmd)
        if os.system(cmd) != 0:
            raise Exception('Command failed: {}'.format(cmd))
