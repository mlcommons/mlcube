import os
import sys
import glob

import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


import mlbox_metadata

class MLBoxDir(object):
    """A way to access files in an mlbox directory."""
    def __init__(self, path):
        self.path = path

    @property
    def standard_docker_metadata_path(self):
        return os.path.join(self.internals_path, 'mlbox_standard_docker.yaml')

    @property
    def metadata(self):
        with open(self.metadata_path) as f:
            return yaml.load(f.read(), Loader=Loader)

    @property
    def metadata(self):
        return os.path.join(self.path, 'mlbox.yaml')

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


def load_yaml(path):
    with open(path) as f:
        return yaml.load(f.read(), Loader=Loader)


def create_metadata(box_dir):
    box_dir = os.path.abspath(box_dir)
    mlbox = mlbox_metadata.MLBox(box_dir)

    # Discover each task
    metadata = load_yaml(mlbox.mlbox_file)

    print(metadata)

    mlbox.set_name(metadata['name'])
    print(mlbox.name)


    for task_name in metadata['tasks']:
        print('loading task: {}'.format(task_name))
        task = metadata['tasks'][task_name]

        mltask = mlbox_metadata.MLTask(task_name)

        for input_name in task['inputs']:
            print('input: {}'.format(input_name))
            task_input = task['inputs'][input_name]
            mltask_input = mlbox_metadata.MLTaskInput(input_name,
                    task_input['desc'])
            mltask.inputs[input_name] = mltask_input
        for output_name in task['outputs']:
            print('output: {}'.format(output_name))
            task_output = task['outputs'][output_name]
            mltask_output = mlbox_metadata.MLTaskOutput(output_name,
                    task_output['desc'])
            mltask.outputs[output_name] = mltask_output
        mlbox.tasks[task_name] = mltask

    impl = load_yaml(mlbox.implementation_file)

    if impl['implementation_type'] != 'direct_python':
        raise Exception('Only direct python supported.')

    print('Implementation main file: {}'.format(impl['main_file']))
    mlbox.implementation_type = 'direct_python'
    mlbox.implementation = mlbox_metadata.DirectPythonImplementation(impl['main_file'])

    # Find the defaults for tasks
    print("listing: {}".format(mlbox.tasks_dir))
    for task_name in os.listdir(mlbox.tasks_dir):
        if task_name not in mlbox.tasks:
            print('WARNING: Found tasks/{} but no such task in mlbox.ymal'.format(task_naem))
            continue
        print('Discovering defaults for task {}'.format(task_name))
        for default_name in glob.glob(os.path.join(mlbox.tasks_dir, task_name, '*.yaml')):
            defaults = load_yaml(os.path.join(mlbox.tasks_dir, default_name))
            default_name = os.path.basename(default_name).strip('.yaml')
            print('Found default: {}'.format(default_name))
            mldefaults = mlbox_metadata.MLTaskDefaults(default_name, defaults)
            mlbox.tasks[task_name].defaults[default_name] = mldefaults


    return mlbox


def main():
    create_metadata(sys.argv[1])


if __name__ == '__main__':
    main()
