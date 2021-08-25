import typing as t


__all__ = ['MLCubeError', 'ConfigurationError', 'IllegalParameterValueError', 'IllegalParameterTypeError']


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
