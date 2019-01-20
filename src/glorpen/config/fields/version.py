# -*- coding: utf-8 -*-
'''
.. moduleauthor:: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>
'''
import semver
from glorpen.config.exceptions import ValidationError
from glorpen.config.fields.base import FieldWithDefault

class Version(FieldWithDefault):
    """Converts values to :class:`semver.VersionInfo`"""
    
    def make_resolvable(self, r):
        r.on_resolve(self._normalize)
    
    def _normalize(self, value, config):
        if value is None:
            return None
        
        try:
            return semver.VersionInfo.parse(value)
        except Exception as e:
            raise ValidationError("Bad version string: %s" % e)
    
    def is_value_supported(self, value):
        return isinstance(value, (str,)) or super(Version, self).is_value_supported(value)
