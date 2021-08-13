import typing as t


__all__ = ['MLCubeError', 'ConfigurationError', 'IllegalParameterError']


class MLCubeError(Exception):
    """ Base class for all MLCube errors. """
    pass


class ConfigurationError(MLCubeError):
    """ Base class for all configuration errors. """
    pass


class IllegalParameterError(ConfigurationError):
    """ Exception to be raised when a configuration parameter is missing or has illegal value. """
    def __init__(self, name: t.Text, value: t.Any) -> None:
        """
        Args:
            name: Parameter name, possibly, qualified (e.g. `container.image`).
            value: Current parameter value.
        """
        super().__init__(f"{name} = {value}")
