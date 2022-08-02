"""Collection of MLCube exceptions.

-MLCubeError: Base class for all MLCube errors.
 |-ConfigurationError: Base class for all configuration errors.
 | |-IllegalParameterError: Base class for all configuration errors.
 |   |-IllegalParameterValueError: Configuration parameter is missing or has illegal value.
 |   |-IllegalParameterTypeError: Configuration parameter has invalid type.
 |-ExecutionError: Any error related to executing MLCubes with one of MLCube runners.
"""
import copy
import typing as t


__all__ = [
    'MLCubeError',
    'ConfigurationError', 'IllegalParameterValueError', 'IllegalParameterTypeError',
    'ExecutionError'
]


class MLCubeError(Exception):
    """Base class for all MLCube errors."""

    pass


class ConfigurationError(MLCubeError):
    """Base class for all configuration errors."""

    pass


class IllegalParameterError(ConfigurationError):
    """Base exception for all errors related to invalid input arguments."""

    pass


class IllegalParameterValueError(IllegalParameterError):
    """Exception to be raised when a configuration parameter is missing or has illegal value."""

    def __init__(self, name: str, value: t.Any, expected_value: t.Any, namespace: t.Optional[str] = None) -> None:
        """Initialize instance of this error.

        Args:
            name: Parameter name.
            value: Actual parameter value.
            expected_value: Expected parameter value.
            namespace: Path to this parameter (e.g., for `docker.image` parameter `image` is parameter name and
                `docker` is namespace).
        """
        self.name = namespace + '.' + name if namespace else name
        self.value = value
        self.expected_value = expected_value

        super().__init__(f"name={self.name}, actual_value={self.value}, actual_value_type={type(self.value)}, "
                         f"expected_value={self.expected_value}")


class IllegalParameterTypeError(IllegalParameterError):
    """Exception to be raised when a configuration parameter has invalid type."""

    def __init__(self, name: str, value: t.Any, expected_type: t.Any, namespace: t.Optional[str] = None) -> None:
        """Initialize instance of this error.

        Args:
            name: Parameter name.
            value: Actual parameter value.
            expected_type: Expected parameter type.
            namespace: Path to this parameter (e.g., for `docker.image` parameter `image` is parameter name and
                `docker` is namespace).
        """
        self.name = namespace + '.' + name if namespace else name
        self.value = value
        self.expected_type = expected_type

        super().__init__(f"name={self.name}, actual_value={self.value}, actual_value_type={type(self.value)}, "
                         f"expected_value_type={self.expected_type}")


class ExecutionError(MLCubeError):
    """Any error related to executing MLCubes with one of MLCube runners."""

    def __init__(self, message: str, description: t.Optional[str] = None, **kwargs) -> None:
        """Initialize instance of this error.

        Args:
            message: Brief message.
            description: Extended description.
            kwargs: Any related context associated with this error.
        """
        super().__init__(f"{message} {description}" if description else message)
        self.message = message
        self.description = description
        self.context = copy.deepcopy(kwargs)

    def describe(self, frmt: str = 'text') -> str:
        """Convert this error into some other representation.

        Args:
            frmt: Format error according to this value. The only supported value is `text` (human-readable description).
        """
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
        """Return error at configure execution phase."""
        return cls(f"{runner} runner failed to configure MLCube.", description, **kwargs)

    @classmethod
    def mlcube_run_error(cls, runner: str, description: t.Optional[str] = None, **kwargs):
        """Return error at run execution phase."""
        return cls(f"{runner} runner failed to run MLCube.", description, **kwargs)
