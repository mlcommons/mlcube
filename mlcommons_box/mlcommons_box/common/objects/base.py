import abc
import logging
from typing import (Any)
import mlspeclib


logger = logging.getLogger(__name__)


class BaseField(abc.ABC):

    @abc.abstractmethod
    def get_default_value(self) -> Any:
        raise NotImplementedError

    @abc.abstractmethod
    def get_value_from_primitive(self, primitive: Any = None) -> Any:
        raise NotImplementedError


class ObjectField(BaseField):

    def __init__(self, obj_class: callable) -> None:
        self.object_class = obj_class

    def get_default_value(self) -> 'BaseObject':
        instance = self.object_class().default()
        return instance

    def get_value_from_primitive(self, primitive: Any = None) -> 'BaseObject':
        instance = self.object_class()
        instance.from_primitive(primitive=primitive)
        return instance


class PrimitiveField(BaseField):

    def __init__(self, default: Any = None) -> None:
        self.default_value = default

    def get_default_value(self) -> Any:
        return self.default_value

    def get_value_from_primitive(self, primitive: Any = None) -> Any:
        instance = self.get_default_value()
        if primitive is not None:
            instance = primitive
        return instance


class BaseObject(abc.ABC):

    @classmethod
    @abc.abstractmethod
    def validate(cls, primitive: Any) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def default(self) -> 'BaseObject':
        raise NotImplementedError

    @abc.abstractmethod
    def from_primitive(self, primitive: Any) -> 'BaseObject':
        raise NotImplementedError


class StandardObject(BaseObject):

    SCHEMA_TYPE = None
    SCHEMA_VERSION = None

    fields = {}
    schema = {}

    @classmethod
    def validate(cls, primitive: Any) -> bool:
        if not isinstance(primitive, dict):
            return False
        mlobject = mlspeclib.MLObject()
        mlobject.set_type(
            schema_type=cls.SCHEMA_TYPE,
            # This is the mlspec-schema version and not this object's schema version
            schema_version="1.0.0"
        )
        mlspeclib.MLObject.update_tree(mlobject, primitive)
        errors = mlobject.validate()
        if errors:
            logger.error("Object validation errors: {}".format(errors))
            return False
        return True

    def default(self) -> 'StandardObject':
        if self.fields is None:
            self.fields = {}
        for fld_name, fld in self.fields.items():
            attr = fld.get_default_value()
            setattr(self, fld_name, attr)
        return self

    def from_primitive(self, primitive: Any) -> 'StandardObject':
        if not self.validate(primitive):
            raise ValueError("Validation failed for {}".format(
                    self.__class__.__name__))
        for fld_name, fld in self.fields.items():
            attr = fld.get_default_value()
            prim_fld_val = primitive.get(fld_name, None)
            if prim_fld_val is not None:
                attr = fld.get_value_from_primitive(prim_fld_val)
            setattr(self, fld_name, attr)
        return self


class ListOfObject(BaseObject):

    item_class = StandardObject

    def __init__(self):
        self._data = []
        super(ListOfObject, self).__init__()

    def __repr__(self): return repr(self._data)

    def __len__(self): return len(self._data)

    def __getitem__(self, i):
        if isinstance(i, slice):
            return self.__class__(self._data[i])
        else:
            return self._data[i]

    @classmethod
    def validate(cls, primitive: Any) -> bool:
        if not isinstance(primitive, list):
            return False
        for item in primitive:
            if (item is not None) and (
                    not cls.item_class.validate(item)):
                return False
        return True

    def default(self) -> 'ListOfObject':
        self._data = []
        return self

    def from_primitive(self, primitive: Any) -> 'ListOfObject':
        if not self.validate(primitive):
            raise ValueError("Validation failed for {}".format(
                    self.__class__.__name__))
        for item in primitive:
            if item is not None:
                obj_instance = self.item_class().from_primitive(item)
                self._data.append(obj_instance)
        return self


class DictOfObject(BaseObject):

    value_class = StandardObject

    def __init__(self):
        self._data = {}
        super(DictOfObject, self).__init__()

    def __repr__(self): return repr(self._data)

    def __len__(self): return len(self._data)

    def __getitem__(self, key):
        if key in self._data:
            return self._data[key]
        if hasattr(self.__class__, "__missing__"):
            return self.__class__.__missing__(self, key)
        raise KeyError(key)

    @classmethod
    def validate(cls, primitive: Any) -> bool:
        if not isinstance(primitive, dict):
            return False
        for key, value in primitive.items():
            if (value is not None) and (
                    not cls.value_class.validate(value)):
                return False
        return True

    def default(self):
        self._data = {}
        return self

    def from_primitive(self, primitive: Any) -> 'DictOfObject':
        if not self.validate(primitive):
            raise ValueError("Validation failed for {}".format(
                    self.__class__.__name__))
        for key, value in primitive.items():
            if value is not None:
                obj_instance = self.value_class().from_primitive(value)
                self._data[key] = obj_instance
        return self
