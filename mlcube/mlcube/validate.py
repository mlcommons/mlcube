import typing as t
from omegaconf import DictConfig
from mlcube.errors import (ConfigurationError, IllegalParameterTypeError, IllegalParameterValueError)

Keys = t.Union[t.Text, t.Iterable[t.Text]]


class Validate(object):
    """ Dictionary validation utils. To be replaced by something in the future, like schema checker. """

    @staticmethod
    def format_keys(keys: t.Optional[Keys]) -> t.Iterable[t.Text]:
        """ Ensures that keys are always represented as iterables (e.g. lists). """
        if keys is None:
            return []
        if isinstance(keys, str):
            return [keys]
        return keys

    def _namespace_msg(self) -> t.Text:
        return f" Namespace = {self.namespace}." if self.namespace else ""

    def _validate_string_values(self, keys: Keys, blanks: bool = True) -> None:
        """ Check that all values of these keys are strings. """
        keys = Validate.format_keys(keys)
        for key in keys:
            value = self.config.get(key, None)
            if not isinstance(value, str):
                raise IllegalParameterTypeError(key, value, str, self.namespace)
            if not blanks and value.isspace():
                raise IllegalParameterValueError(key, value, "'non-blank string'", self.namespace)

    def __init__(self, config: DictConfig, namespace: t.Optional[t.Text]) -> None:
        self.config = config
        self.namespace = namespace or ''

    def not_none(self, keys: t.Optional[Keys] = None) -> 'Validate':
        """ Check all values are not Nones. """
        keys = Validate.format_keys(keys)
        bad_keys: t.List[t.Text] = [key for key in keys if self.config.get(key, None) is None]
        if len(bad_keys) > 0:
            raise ConfigurationError(f"Parameters must present and not be None: {bad_keys}.{self._namespace_msg()}")
        return self

    def check_unknown_keys(self, known_keys: t.Iterable[t.Text]) -> 'Validate':
        """ Check if this dict contains unknown keys. """
        unknown_keys = [key for key in self.config if key not in known_keys]
        if unknown_keys:
            raise ConfigurationError(f"Unknown keys: {unknown_keys}.{self._namespace_msg()}")
        return self

    def check_values(self, keys: Keys, type_, **kwargs) -> 'Validate':
        """ Perform value checks based upon their type. """
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
        if not isinstance(obj, expected_type):
            raise TypeError(f"Actual object type ({type(obj)}) != expected type ({expected_type}).")
