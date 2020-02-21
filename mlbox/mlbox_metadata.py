import sys
import os


class MLBox:
    def __init__(self, path, tasks=None):
        # Maps name to MLTask
        self.name = None
        self.path = path
        self.tasks = {}
        if tasks:
            self.tasks = tasks

        self.implementation_type = None
        self.implementation = None

    def set_name(self, name):
        self.name = name

    def get_task(self, name):
        return self.tasks[name]

    @property
    def readme_file(self):
        return os.path.join(self.path, 'README.md')

    @property
    def mlbox_file(self):
        return os.path.join(self.path, 'mlbox.yaml')

    @property
    def implementation_dir(self):
        return os.path.join(self.path, 'implementation')

    @property
    def workspace_dir(self):
        return os.path.join(self.path, 'workspace')

    @property
    def tasks_dir(self):
        return os.path.join(self.path, 'tasks')

    @property
    def implementation_file(self):
        return os.path.join(self.implementation_dir, 'mlbox_implementation.yaml')




class MLTask:
    def __init__(self, name):
        self.name = name
        self.inputs = {}
        self.outputs = {}
        self.defaults = {}


class MLTaskInput:
    def __init__(self, name, desc):
        self.name = name
        self.desc = desc


class MLTaskOutput:
    def __init__(self, name, desc):
        self.name = name
        self.desc = desc


class MLTaskDefaults:
    def __init__(self, name, default_paths):
        self.name = name
        self.default_paths = default_paths


class DirectPythonImplementation:
    def __init__(self, main_file):
        self.main_file = main_file


