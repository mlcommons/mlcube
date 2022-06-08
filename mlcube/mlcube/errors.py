import copy
import typing as t


__all__ = [
    'MLCubeError',
    'ConfigurationError', 'IllegalParameterValueError', 'IllegalParameterTypeError',
    'ExecutionError'
]


class MLCubeError(Exception):
    """ Base class for all MLCube errors. """
    pass


class ConfigurationError(MLCubeError):
    """ Base class for all configuration errors. """
    pass


class IllegalParameterError(ConfigurationError):
    pass


class IllegalParameterValueError(IllegalParameterError):
    """ Exception to be raised when a configuration parameter is missing or has illegal value. """
    def __init__(self, name: t.Text, value: t.Any, expected_value: t.Any, namespace: t.Optional[t.Text] = None) -> None:
        self.name = namespace + '.' + name if namespace else name
        self.value = value
        self.expected_value = expected_value

        super().__init__(f"name={self.name}, actual_value={self.value}, actual_value_type={type(self.value)}, "
                         f"expected_value={self.expected_value}")


class IllegalParameterTypeError(IllegalParameterError):
    def __init__(self, name: t.Text, value: t.Any, expected_type: t.Any, namespace: t.Optional[t.Text] = None) -> None:
        self.name = namespace + '.' + name if namespace else name
        self.value = value
        self.expected_type = expected_type

        super().__init__(f"name={self.name}, actual_value={self.value}, actual_value_type={type(self.value)}, "
                         f"expected_value_type={self.expected_type}")


class ExecutionError(MLCubeError):
    def __init__(self, message: str, description: t.Optional[str] = None, **kwargs) -> None:
        super().__init__(f"{message} {description}" if description else message)
        self.message = message
        self.description = description
        self.context = copy.deepcopy(kwargs)

    def describe(self, frmt: str = 'text') -> str:
        if frmt != 'text':
            raise ValueError(f"Unsupported error description format ('{frmt}').")
        msg = f"ERROR:\n\tmessage: {self.message}"
        if self.description:
            msg += f"\n\tdescription: {self.description}"
        if self.context:
            msg += f"\n\tcontext: {self.context}"
        return msg

    @classmethod
    def mlcube_configure_error(cls, runner: str, description: t.Optional[str] = None, **kwargs):
        return cls(f"{runner} runner failed to configure MLCube.", description, **kwargs)

    @classmethod
    def mlcube_run_error(cls, runner: str, description: t.Optional[str] = None, **kwargs):
        return cls(f"{runner} runner failed to run MLCube.", description, **kwargs)
