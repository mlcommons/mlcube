import glob
import os
import sys

import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


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
        io[name] = val
    return mlbox_dir, task, input_group, io


class MLBoxDir(object):
    """A way to access files in an mlbox directory."""
    def __init__(self, path):
        self.path = path

    @property
    def metadata_path(self):
        return os.path.join(self.path, 'mlbox.yaml')

    @property
    def internals_path(self):
        return os.path.join(self.path, 'internals')

    @property
    def tasks_path(self):
        return os.path.join(self.path, 'tasks')

    @property
    def standard_docker_metadata_path(self):
        return os.path.join(self.internals_path, 'mlbox_standard_docker.yaml')

    @property
    def metadata(self):
        with open(self.metadata_path) as f:
            return yaml.load(f.read(), Loader=Loader)

    @property
    def standard_docker_metadata(self):
        with open(self.standard_docker_metadata_path) as f:
            return yaml.load(f.read(), Loader=Loader)

    @property
    def task_names(self):
        l = []
        for path in os.listdir(self.tasks_path):
            if os.path.isdir(os.path.join(self.tasks_path, path)):
                l.append(path)
        return l

    def task_metadata_path(self, task_name):
        return os.path.join(self.tasks_path, task_name, 'mlbox_task.yaml')

    def task_metadata(self, task_name):
        with open(self.task_metadata_path(task_name)) as f:
            return yaml.load(f.read(), Loader=Loader)

    @property
    def task_names(self):
        l = []
        for path in os.listdir(self.tasks_path):
            if os.path.isdir(os.path.join(self.tasks_path, path)):
                l.append(path)
        return l

    def directory_for_task(self, task_name):
        return os.path.join(self.tasks_path, task_name)

    def outputs_directory(self, task_name, input_group):
        return os.path.join(self.tasks_path, task_name, input_group, 'outputs')

    def list_defaults_for_task(self, task_name):
        task_path = self.directory_for_task(task_name)
        l = []
        for default in os.listdir(task_path):
            if os.path.isdir(os.path.join(task_path, default)):
                l.append(default)
        return l

    def get_default_input_path(self, task_name, input_group_name, input_name):
        task_path = self.directory_for_task(task_name)
        pat = os.path.join(task_path, input_group_name, 'input', '{}.*'.format(input_name))
        matches = glob.glob(pat)
        if not matches:
            return None
        if len(matches) > 1:
            raise Exception('Too many matching files: {}'.format(pat))
        return matches[0]


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


def run_docker(docker_name, input_map):
    """Prints the command to run the docker

    Example input_map:
    {'params': 'tasks/big_run/input/params.yaml', ...}
    """
    volumes, mapped_inputs = get_volumes_and_paths(input_map.values())
    print('volumes: ', volumes)
    print('mapped_inputs:', mapped_inputs)
    volumes_str = ' '.join(
          ['-v {}:{}'.format(t[0], t[1]) for t in volumes.items()])
    arguments = []
    for input_name in input_map:
        inner_path = mapped_inputs[input_map[input_name]]
        arguments.append('--{}={}'.format(input_name, inner_path))
    cmd = 'sudo docker run {} --net=host --privileged=true -t {} {}'.format(
          volumes_str, docker_name, ' '.join(arguments))
    print(cmd)
    # ensure failure is shown to caller.
    # if os.system(cmd) != 0:
    #     sys.exit(1)


def construct_docker_command_with_default_inputs(mlbox_dir, task_name, input_group,
        override_paths):
    # TOOD: this function isn't perfect, this just demonstrates the basic idea
    # This function will need to be modified to work reliably  (or at all)

    #volume_map = {}

    task_metadata = mlbox_dir.task_metadata(task_name)
    print(task_metadata)

    names_to_paths =  {}

    # determine the input paths
    for input_name in task_metadata['inputs']:
        path = None
        if input_name in override_paths:
            path = override_paths[input_name]
        else:
            path = mlbox_dir.get_default_input_path(task_name, input_group, input_name)
        path = os.path.abspath(path)
        names_to_paths[input_name] = path

    outputs_directory = mlbox_dir.outputs_directory(task_name, input_group)
    for output_name in task_metadata['outputs']:
        path = None
        if output_name in override_paths:
            path = override_paths[output_name]
        else:
            path = os.path.join(outputs_directory, output_name)
        path = os.path.abspath(path)
        names_to_paths[output_name] = path

    print(mlbox_dir.standard_docker_metadata)
    run_docker(mlbox_dir.standard_docker_metadata['container']['image'], names_to_paths)





def main():
    mlbox_dir, task_name, input_group, io = get_commandline_args()

    mlbox_dir = MLBoxDir(mlbox_dir)
    print(mlbox_dir.metadata)
    print(mlbox_dir.standard_docker_metadata)
    for task_name in mlbox_dir.task_names:
        defaults = mlbox_dir.list_defaults_for_task(task_name)
        print('{}: {}'.format(task_name, ', '.join(defaults)))
        for input_group in defaults:
            print(mlbox_dir.get_default_input_path(task_name, input_group, 'params'))

    # TODO: clean this up and parse things from commandline
    construct_docker_command_with_default_inputs(mlbox_dir, task_name, input_group, io)


if __name__ == '__main__':
    main()
