"""Classes to perform various validation checks against function input parameters or config files.

- `Validate`: Validation utils for dictionary-like objects (in particular, DictConfig from omegaconf).
"""
import typing as t

from mlcube.errors import (ConfigurationError, IllegalParameterTypeError, IllegalParameterValueError)

from omegaconf import DictConfig

__all__ = ['Validate']

Keys = t.Union[str, t.Iterable[str]]
"""One or many dictionary keys."""


class Validate(object):
    """Dictionary validation utils. To be replaced by something in the future, like schema checker."""

    @staticmethod
    def format_keys(keys: t.Optional[Keys]) -> t.Iterable[str]:
        """Format keys so that they are always represented as list of strings."""
        if keys is None:
            return []
        if isinstance(keys, str):
            return [keys]
        return keys

    def _namespace_msg(self) -> str:
        return f" Namespace = {self.namespace}." if self.namespace else ""

    def _validate_string_values(self, keys: Keys, blanks: bool = True) -> None:
        """Check that all values of these keys are strings.

        Args:
            keys: List of keys that must contain string values.
            blanks: If false, empty strings are not allowed.
        """
        keys = Validate.format_keys(keys)
        for key in keys:
            value = self.config.get(key, None)
            if not isinstance(value, str):
                raise IllegalParameterTypeError(key, value, str, self.namespace)
            if not blanks and value.isspace():
                raise IllegalParameterValueError(key, value, "'non-blank string'", self.namespace)

    def __init__(self, config: DictConfig, namespace: t.Optional[str]) -> None:
        """Initialize dictionary validation class.

        Args:
            config: Dictionary to run various validation checks.
            namespace: Namespace (key path) if this dictionary is a (nested) value in some other dictionary.
        """
        self.config = config
        self.namespace = namespace or ''

    def not_none(self, keys: t.Optional[Keys] = None) -> 'Validate':
        """Check all values are not Nones.

        Args:
            keys: List of keys that must not contain None values. Keys that contain None values are equivalent to keys
                that do not exist in dictionary - all trigger fail check.
        """
        keys = Validate.format_keys(keys)
        bad_keys: t.List[str] = [key for key in keys if self.config.get(key, None) is None]
        if len(bad_keys) > 0:
            raise ConfigurationError(f"Parameters must present and not be None: {bad_keys}.{self._namespace_msg()}")
        return self

    def check_unknown_keys(self, known_keys: t.Iterable[str]) -> 'Validate':
        """Check if this dict contains unknown (== unexpected) keys.

        Args:
            known_keys: Dictionary is expected to contain only these keys.
        """
        unknown_keys = [key for key in self.config if key not in known_keys]
        if unknown_keys:
            raise ConfigurationError(f"Unknown keys: {unknown_keys}.{self._namespace_msg()}")
        return self

    def check_values(self, keys: Keys, type_, **kwargs) -> 'Validate':
        """Perform value checks based upon their type."""
        if type_ is str:
            self._validate_string_values(keys, **kwargs)
        elif len(kwargs) != 0:
            raise ValueError(f"Unknown arguments ({kwargs}) for type '{type_}'")
        else:
            keys = Validate.format_keys(keys)
            for key in keys:
                value = self.config.get(key, None)
                if not isinstance(value, type_):
                    raise ConfigurationError(f"Expecting {type_} value, key={key}.{self._namespace_msg()}")
        return self

    @staticmethod
    def validate_type(obj, expected_type) -> None:
        """Check that `obj` is of expected type.

        Args:
            obj: An object to check its type.
            expected_type: Expected type of the `obj` parameter.
        """
        if not isinstance(obj, expected_type):
            raise TypeError(f"Actual object type ({type(obj)}) != expected type ({expected_type}).")
