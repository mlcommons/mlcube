import typing as t
from omegaconf import DictConfig
from mlcube.errors import ConfigurationError

"""
Classes that provide convenient access to SHH runner-specific platform parameters. Pretty much all is initialized based
on configuration in a platform definition file.
"""

Interpreter = t.TypeVar('Interpreter', bound='PythonInterpreter')


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
    type: t.Text = 'unknown'
    _interpreters: t.Dict[t.Text, t.Callable] = {}

    def __init_subclass__(cls, **kwargs):
        """ Register all python interpreters in this method. """
        if cls.type in PythonInterpreter._interpreters:
            raise ValueError(f"Duplicate interpreter name: {cls.type}.")
        PythonInterpreter._interpreters[cls.type] = cls

    @staticmethod
    def get(config: DictConfig):
        if not isinstance(config, DictConfig):
            raise ValueError(f"Invalid configuration object type('{type(config)}'). Expected: 'DictConfig'.")
        interpreter_type = config.get('type', None)
        if interpreter_type is None:
            raise ValueError("Python interpreter configuration does not provide 'type' field.")
        if interpreter_type not in PythonInterpreter._interpreters:
            raise ValueError(f"Invalid python interpreter ('{interpreter_type}'). "
                             f"Expected: {PythonInterpreter._interpreters.keys()}")
        return PythonInterpreter._interpreters[interpreter_type]

    @staticmethod
    def create(config: DictConfig) -> Interpreter:
        """ Create helper class for this python interpreter
        Args:
            config: Python interpreter configuration that must contain at least `type` field/
        Returns:
            Instance of respective python interpreter.
        """
        return PythonInterpreter.get(config)(config)

    def __init__(self, config: DictConfig) -> None:
        """
        Args:
            config: Python interpreter configuration. At least two fields are expected here - `python` and
                `requirements`.
        """
        # Python executable, possibly, including the full path (python, python3, /my/custom/path/python etc.).
        self.python: t.Text = config.get('python', None) or 'python'
        # String of python dependencies.
        self.requirements: t.Text = config.get('requirements', None) or ''

    def __str__(self) -> t.Text:
        return f"PythonInterpreter(python={self.python}, requirements={self.requirements})"

    def create_cmd(self, noop: t.Optional[t.Text] = None) -> t.Optional[t.Text]:
        """ Return command to create an interpreter. """
        return noop

    def configure_cmd(self, noop: t.Optional[t.Text] = None) -> t.Optional[t.Text]:
        """ Configure python: install requirements. """
        if not self.requirements:
            return noop
        activate_cmd = self.activate_cmd(noop)
        config_cmd = "" if not activate_cmd else f"{activate_cmd} && "
        return config_cmd + f"{self.python} -m pip install {self.requirements}"

    def activate_cmd(self, noop: t.Optional[t.Text] = None) -> t.Optional[t.Text]:
        """ Return command to activate an interpreter. """
        return noop


class SystemInterpreter(PythonInterpreter):
    """
    interpreter:
        type: system
        python: python3.6
        requirements: ...
    """

    type: t.Text = 'system'

    @staticmethod
    def validate(config: DictConfig) -> DictConfig:
        if not config.get('python', None) or config.get('requirements', None) is None:
            raise ConfigurationError(
                f"Invalid python system interpreter configuration: {str(config)}. It must contain three fields: "
                f"`type`, `python` and `requirements`. The `type` must equal to `system`. The `python` is a python "
                f"interpreter to use, can be either an executable name (python3.6) or a full path. The `requirements` "
                f"is a whitespace-separated list of python dependencies to install in the host environment (e.g., "
                f"mlcube core library and one of the runners).")
        return config

    """ Just a formal wrapper on top of Python Interpreter. """
    def __init__(self, config: DictConfig) -> None:
        super().__init__(config)

    def __str__(self) -> t.Text:
        return f"SystemInterpreter(python={self.python}, requirements={self.requirements})"


class VirtualEnvInterpreter(PythonInterpreter):
    """
    interpreter:
        type: virtualenv
        python: python3.6
        requirements: ...
        location: ...
        name: ...
    """

    type: t.Text = 'virtualenv'

    @staticmethod
    def validate(config: DictConfig) -> DictConfig:
        if not config.get('python', None) or config.get('requirements', None) is None:
            raise ConfigurationError(
                f"Invalid python system interpreter configuration: {str(config)}. It must contain five fields: "
                f"`type`, `python`, `requirements`, `location` and `name`. The `type` must equal to `system`. The "
                f"`python` is a python interpreter to use, can be either an executable name (python3.6) or a full "
                f"path. The `requirements` is a whitespace-separated list of python dependencies to install in the "
                f"host environment (e.g., mlcube core library and one of the runners). The `location` is the root "
                f"directory to create python environment in, and `name` is the environment name.")
        return config

    def __init__(self, config: DictConfig) -> None:
        super().__init__(config)

        self.location = config.get('location', None)
        self.name = config.get('name', None)
        if not self.location or not self.name:
            raise ValueError(f"Invalid virtualenv location or interpreter name: {config}")

    def create_cmd(self, noop: t.Optional[t.Text] = None) -> t.Optional[t.Text]:
        condition = f'[ ! -d "{self.location}/{self.name}" ]'
        create_cmd = f'mkdir -p {self.location} && cd {self.location} && virtualenv -p {self.python} {self.name}'
        noop_cmd = 'true'
        return f'if {condition}; then {create_cmd}; else {noop_cmd}; fi'

    def activate_cmd(self, noop: t.Optional[t.Text] = None) -> t.Optional[t.Text]:
        return f"source {self.location}/{self.name}/bin/activate"

    def __str__(self) -> str:
        return f"VirtualEnvInterpreter(python={self.python}, requirements={self.requirements}, "\
               f"location={self.location}, name={self.name})"
