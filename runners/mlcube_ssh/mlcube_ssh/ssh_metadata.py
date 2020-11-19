from typing import (Optional, Dict, TypeVar)
from mlcube.common.utils import (Utils, StandardPaths)

"""
Classes that provide convenient access to SHH runner-specific platform parameters. Pretty much all is initialized based
on configuration in a platform definition file.
"""

Interpreter = TypeVar('Interpreter', bound='PythonInterpreter')


class PythonInterpreter(object):
    """ Base class for Python interpreters.

    A python interpreter is responsible for running MLCube runners on remote hosts. It also provides additional
    functionality such as providing commands for:
        - Creating an interpreter (create_cmd).
        - Activating an interpreter (activate_cmd).
        - Configuring an interpreter (configure_cmd).

    Note on activation. As far as I know, activation is not required in general, this is just a convenience feature.
    Tools like python and pip executables can be used using their absolute paths.
    """
    type: str = 'unknown'
    _interpreters: Dict[str, callable] = {}

    def __init_subclass__(cls, **kwargs):
        """ Register all python interpreters in this method. """
        if cls.type in PythonInterpreter._interpreters:
            raise ValueError(f"Duplicate interpreter name: {cls.type}.")
        PythonInterpreter._interpreters[cls.type] = cls

    @staticmethod
    def create(config: dict) -> Interpreter:
        if not isinstance(config, dict):
            raise ValueError(f"Invalid configuration object type('{type(config)}'). Expected: 'dict'.")
        interpreter_type = config.get('type', None)
        if interpreter_type is None:
            raise ValueError("Python interpreter configuration does not provide 'type' field.")
        if interpreter_type not in PythonInterpreter._interpreters:
            raise ValueError(f"Invalid python interpreter ('{interpreter_type}'). "
                             f"Expected: {PythonInterpreter._interpreters.keys()}")
        return PythonInterpreter._interpreters[interpreter_type](config)

    def __init__(self, config: dict) -> None:
        """  """
        # Python executable, possibly, including the full path (python, python3, /my/custom/path/python etc.).
        self.python: str = config.get('python', 'python')
        # String of python dependencies.
        self.requirements: str = Utils.get(config, 'requirements', '')

    def __str__(self) -> str:
        return f"PythonInterpreter(python={self.python}, requirements={self.requirements})"

    def create_cmd(self, noop: Optional[str] = None) -> Optional[str]:
        """ Return command to create an interpreter. """
        return noop

    def configure_cmd(self, noop: Optional[str] = None) -> Optional[str]:
        """ Configure python: install requirements. """
        if not self.requirements:
            return noop
        config_cmd = ""
        activate_cmd = self.activate_cmd()
        if activate_cmd is not None:
            config_cmd += f"{activate_cmd} && "
        return config_cmd + f"{self.python} -m pip install {self.requirements}"

    def activate_cmd(self, noop: Optional[str] = None) -> Optional[str]:
        """ Return command to activate an interpreter. """
        return noop


class SystemInterpreter(PythonInterpreter):

    type: str = 'system'

    """ Just a formal wrapper on top of Python Interpreter. """
    def __init__(self, config: dict) -> None:
        super().__init__(config)

    def __str__(self) -> str:
        return f"SystemInterpreter(python={self.python}, requirements={self.requirements})"


class VirtualEnvInterpreter(PythonInterpreter):

    type: str = 'virtualenv'

    def __init__(self, config: dict) -> None:
        super().__init__(config)

        self.location = Utils.get(config, 'location', StandardPaths.ENVIRONMENTS)
        self.name = Utils.get(config, 'name', '')
        if not self.name:
            raise ValueError(f"Invalid python interpreter name: '{self.name}'")

    def create_cmd(self, noop: Optional[str] = None) -> Optional[str]:
        env_path = f'{self.location}/{self.name}'
        return f'[ ! -d "{env_path}" ] && {{ mkdir -p {self.location} && cd {self.location} && '\
               f'virtualenv -p {self.python} {self.name}; }}'

    def activate_cmd(self, noop: Optional[str] = None) -> Optional[str]:
        return f"source {self.location}/{self.name}/bin/activate"

    def __str__(self) -> str:
        return f"VirtualEnvInterpreter(python={self.python}, requirements={self.requirements}, "\
               f"location={self.location}, name={self.name})"


class Platform(object):
    def __init__(self, path: str) -> None:
        self.type: str = 'ssh'

        cfg = Utils.load_yaml(path)
        if not isinstance(cfg, dict):
            raise ValueError(f"Invalid platform configuration, type={type(cfg)}. Expected: 'dict'.")

        self.host: str = Utils.get(cfg, 'host', '')
        if not self.host:
            raise ValueError(f"Invalid host name: '{self.host}'.")

        self.authentication: dict = Utils.get(cfg, 'authentication', {})
        if not isinstance(self.authentication, dict):
            self.authentication = {}

        self.platform: str = Utils.get(cfg, 'platform', '')
        if not self.platform:
            raise ValueError(f"Invalid platform: '{self.platform}'.")

        self.interpreter: PythonInterpreter = PythonInterpreter.create(Utils.get(cfg, 'interpreter', {}))

    def get_connection_string(self) -> str:
        """ Return authentication string for tools like `ssh` and `rsync`.

            ssh -i PATH_TO_PRIVATE_KEY USER_NAME@HOST_NAME
        """
        auth_str = ''
        identify_file = Utils.get(self.authentication, 'identify_file', '')
        if identify_file:
            auth_str += f"-i {identify_file} "
        user = Utils.get(self.authentication, 'user', '')
        if user:
            auth_str += f'{user}@'
        return auth_str + self.host

    def __str__(self) -> str:
        return f"Platform(host={self.host}, authentication={self.authentication}, platform={self.platform}, "\
               f"interpreter={self.interpreter})"
