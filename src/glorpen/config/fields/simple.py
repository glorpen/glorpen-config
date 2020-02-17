# -*- coding: utf-8 -*-
'''
.. moduleauthor:: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>
'''
import os
import re
from collections import OrderedDict
from glorpen.config.exceptions import ValidationError
from glorpen.config.fields.base import Field, path_validation_error,\
    FieldWithDefault

class Dict(Field):
    """Converts values to :class:`collections.OrderedDict`
    
    Supports setting whole schema (specific keys and specific values)
    or just keys type and values type.
    
    Dict values are lazy resolved.
    """
    
    _schema = None
    _key_field = None
    _value_field = None
    
    def __init__(self, schema=None, keys=None, values=None, **kwargs):
        """
        To set specific schema pass dict to schema argument: ``{"param1": SomeField()}``.
        
        To specify keys and values type use keys and values arguments: ``Dict(keys=String(), values=Number())``. 
        """
        super(Dict, self).__init__(**kwargs)
        
        if schema is None:
            self._key_field = keys or String()
            self._value_field = values
        else:
            self._schema = schema
    
    def on_resolve(self, v, config):
        if self._schema:
            v = self._check_keys_with_schema(v, config)
            v = self._normalize_with_schema(v, config)
        else:
            v = self._normalize(v, config)
        return v
    
    def _check_keys_with_schema(self, value, config):
        if value is None:
            value = {}
        
        spec_blanks = set()
        spec=set(self._schema.keys())
        val_keys = set(value.keys())
        
        for def_k, def_v in self._schema.items():
            try:
                if def_v.allow_blank or def_v.has_valid_default():
                    spec_blanks.add(def_k)
                    continue
            except AttributeError:
                spec_blanks.add(def_k)
                continue
        
        diff_new = val_keys.difference(spec)
        diff_missing = spec.difference(val_keys).difference(spec_blanks)
        if diff_new or diff_missing:
            msgs = []
            if diff_missing:
                msgs.append("missing keys %r" % diff_missing)
            if diff_new:
                msgs.append("excess keys %r" % diff_new)
            raise ValidationError("Found following errors: %s" % ", ".join(msgs))
        
        return value
    
    def _normalize_with_schema(self, value, config):
        ret = OrderedDict()
        for k,field in self._schema.items():
            with path_validation_error([k]):
                ret[k] = field.resolve(value.get(k))
        return ret
    
    def _normalize(self, value, config):
        ret = OrderedDict()
        
        if value is None:
            return ret
        
        for k,v in value.items():
            with path_validation_error(k):
                ret[self._key_field.resolve(k).resolve(config)] = self._value_field.resolve(v)
        
        return ret
    
    def is_value_supported(self, value):
        return value is None or isinstance(value, (dict,)) or super(Dict, self).is_value_supported(value)
    
class String(FieldWithDefault):
    """Converts value to string with optional interpolation."""
    
    re_part = re.compile(r'{{\s*([a-z._A-Z0-9]+)\s*}}')
    
    def resolve_parts(self, value, config):
        if value:
            def replace(matchobj):
                return config.get(matchobj.group(1))
            return self.re_part.sub(replace, value)
    
    def to_string(self, value, config):
        if value:
            try:
                return str(value)
            except Exception as e:
                raise ValidationError("Could not convert %r to string, got %r" % (value, e))
    
    def on_resolve(self, v, config):
        v = self.to_string(v, config)
        return self.resolve_parts(v, config)
    
    def is_value_supported(self, value):
        return isinstance(value, (str,)) or super(String, self).is_value_supported(value)

class Path(String):
    """Converts given value to disk path."""
    
    def to_path(self, value, config):
        return os.path.realpath(value)
    
    def on_resolve(self, v, config):
        v = super(Path, self).on_resolve(v, config)
        return self.to_path(v, config)

class PathObj(Path):
    """Converts value to :class:`pathlib.Path` object"""
    def to_obj(self, value, config):
        import pathlib
        return pathlib.Path(value)
    
    def on_resolve(self, v, config):
        v = super(PathObj, self).on_resolve(v, config)
        return self.to_obj(v, config)

class List(FieldWithDefault):
    """Converts value to list.
    
    List values are lazy resolved.
    """
    
    def __init__(self, schema, **kwargs):
        super(List, self).__init__(**kwargs)
        
        self._values_field = schema
    
    def on_resolve(self, v, config):
        return self.normalize(v, config)
    
    def normalize(self, value, config):
        if value is None:
            return None
        ret = []
        for i, v in enumerate(value):
            with path_validation_error(i):
                ret.append(self._values_field.resolve(v if v else None))
        return ret
    
    def is_value_supported(self, value):
        return isinstance(value, (tuple, list)) or super(List, self).is_value_supported(value)

class Variant(FieldWithDefault):
    """Converts value to normalized state using one :class:`.Field` chosen from multiple provided.
    
    To allow blank values you have to pass child field with enabled blank values.
    First field which supports value (:meth:`.Field.is_value_supported`) will be used to convert it.

    When ``try_resolving`` mode is disabled (default), value for child fields will only be checked
    with ``is_value_supported``, so resulting field will be based only of data type, not value.

    When enabled, in addition to checking for supported values data will be resolved and first
    non error result used.
    """
    def __init__(self, schema, try_resolving=False):
        allow_blank = False
        
        for s in schema:
            try:
                s_blank = s.allow_blank
            except AttributeError:
                continue
            
            if s_blank:
                allow_blank = True
                break
        
        super(Variant, self).__init__(allow_blank=allow_blank)
        
        self._values_fields = schema
        self._try_resolving = try_resolving
    
    def on_resolve(self, r, config):
        return self.normalize(r, config)
    
    def normalize(self, value, config):
        for f in self._values_fields:
            if f.is_value_supported(value):
                if self._try_resolving:
                    try:
                        return f.resolve(value, checked=True).resolve(config)
                    except ValidationError:
                        pass
                else:
                    return f.resolve(value, checked=True)
        
        raise ValidationError("Unsupported data %r" % (value,))
    
    def is_value_supported(self, value):
        if super(Variant, self).is_value_supported(value):
            return True
        
        for f in self._values_fields:
            if f.is_value_supported(value):
                return True
        return False

class Any(FieldWithDefault):
    """Field that accepts any value."""
    def is_value_supported(self, value):
        return True
    
    def on_resolve(self, v, config):
        return v

class Number(FieldWithDefault):
    """Converts value to numbers."""
    #TODO: float, deciaml points
    def is_value_supported(self, value):
        try:
            int(value)
        except (ValueError, TypeError):
            return super(Number, self).is_value_supported(value)
        
        return True
    
    def on_resolve(self, r, config):
        return self._normalize(r, config)
    
    def _normalize(self, value, config):
        if value is not None:
            return int(value)

class Bool(FieldWithDefault):
    truthful = [
        "true",
        "True",
        "t",
        1,
        "y",
        "yes",
        "on",
        True
    ]
    def is_value_supported(self, value):
        return True
    def on_resolve(self, v, config):
        if v is not None:
            return v in self.truthful
