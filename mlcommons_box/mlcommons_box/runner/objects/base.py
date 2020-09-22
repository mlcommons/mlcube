import abc
import collections
import os
import typing


class BaseField(abc.ABC):

    @abc.abstractmethod
    def default(self):
        return NotImplementedError

    @abc.abstractmethod
    def from_primitive(self, primitive):
        return NotImplementedError


class ObjectField(BaseField):

    def __init__(self, obj_class: 'BaseObject', embedded: bool=False):
        self.object_class = obj_class
        self.embedded = embedded

    def default(self):
        instance = self.object_class()
        return instance

    def from_primitive(self, primitive):
        instance = self.object_class(primitive=primitive)
        return instance


class PrimitiveField(BaseField):

    def __init__(self, default_value: typing.Optional[typing.Any]=None):
        self.default_value = default_value

    def validate(self, primitive):
        # TODO: implement proper validation
        return True

    def default(self):
        result = None
        if self.default_value is not None:
            result = self.default_value
        return result

    def from_primitive(self, primitive):
        instance = self.default()
        if not self.validate(primitive):
            raise ValueError("Validation failed for {}".format(
                    self.__class__.__name__))
        if primitive is not None:
            instance = primitive
        return instance


class BaseObject(abc.ABC):

    def __init__(self, primitive=None):
        if primitive is None:
            self.init_default()
        else:
            self.init_from_primitive(primitive)

    @classmethod
    @abc.abstractmethod
    def validate(cls, primitive):
        raise NotImplementedError

    @abc.abstractmethod
    def init_default(self):
        raise NotImplementedError

    @abc.abstractmethod
    def init_from_primitive(self, primitive):
        raise NotImplementedError

    @abc.abstractmethod
    def merge(self, overlay):
        raise NotImplementedError


class StandardObject(BaseObject):

    fields = {}

    @classmethod
    def validate(cls, primitive):
        # TODO: implement proper validation
        if not isinstance(primitive, dict):
            return False
        return True

    def init_default(self):
        if self.fields is None:
            self.fields = {}
        for fld_name, fld in self.fields.items():
            attr = fld.default()
            setattr(self, fld_name, attr)
            if isinstance(fld, ObjectField) and fld.embedded is True:
                self._embed_object(attr)

    def init_from_primitive(self, primitive):
        if not self.validate(primitive):
            raise ValueError("Validation failed for {}".format(
                    self.obj_class.__name__))
        for fld_name, fld in self.fields.items():
            if isinstance(fld, ObjectField) and fld.embedded is True:
                attr = fld.from_primitive(primitive)
                setattr(self, fld_name, attr)
                self._embed_object(attr)
            else:
                attr = fld.default()
                prim_fld_val = primitive.get(fld_name, None)
                if prim_fld_val is not None:
                    attr = fld.from_primitive(prim_fld_val)
                setattr(self, fld_name, attr)

    def _embed_object(self, obj):
        # Embed an object by copying its attributes to the current (parent)
        # object, with the exception that the current object has an existing
        # attribute of the same name, in which case the attribute in the
        # current (parent) object takes priority.
        if obj.fields is not None:
            for subfld_name, subfld in obj.fields.items():
                if subfld_name not in self.fields.keys():
                    subattr = getattr(obj, subfld_name)
                    setattr(self, subfld_name, subattr)

    def merge(self, overlay):
        def _merge_list(base, overlay):
            result = base or {}
            result.extend(overlay)
            return result
        def _merge_dict(base, overlay):
            result = base or {}
            for key, val in overlay.items():
                if isinstance(val, dict):
                    node = result.setdefault(key, {})
                    result[key] = _merge_dict(node[key], val)
                else:
                    result[key] = val
            return result
        if not isinstance(overlay, self.__class__):
            raise TypeError("Cannot merge instances of different classes.")
        for attr_name in self.fields.keys():
            attr = getattr(self, attr_name)
            overlay_attr = getattr(overlay, attr_name)
            if isinstance(attr, BaseObject):
                attr.merge(overlay_attr)
            elif isinstance(overlay_attr, list):
                attr = _merge_list(attr, overlay_attr)
            elif isinstance(overlay_attr, dict):
                attr = _merge_dict(attr, overlay_attr)
            elif overlay_attr is not None:
                attr = overlay_attr
            setattr(self, attr_name, attr)


class StandardObjectList(BaseObject):

    item_class = StandardObject

    def __init__(self, primitive=None):
        self.data = []
        super(StandardObjectList, self).__init__(primitive=primitive)

    def __repr__(self): return repr(self.data)
    def __len__(self): return len(self.data)
    def __getitem__(self, i):
        if isinstance(i, slice):
            return self.__class__(self.data[i])
        else:
            return self.data[i]

    @classmethod
    def validate(cls, primitive):
        # TODO: implement proper validation
        if not isinstance(primitive, list):
            return False
        return True

    def init_default(self):
        if self.item_class is None:
            self.item_class = StandardObject

    def init_from_primitive(self, primitive):
        if not self.validate(primitive):
            raise ValueError("Validation failed for {}".format(
                    self.obj_class.__name__))
        for item in primitive:
            if item is not None:
                obj_instance = self.item_class(item)
                self.data.append(obj_instance)

    def merge(self, overlay):
        if not isinstance(overlay, self.__class__):
            raise TypeError("Cannot merge instances of different classes.")
        self.data.extend(overlay)
