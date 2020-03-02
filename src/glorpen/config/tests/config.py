import unittest
import pathlib

from glorpen.config.fields.base import Field
from glorpen.config import Config

class MockField(Field):
    pass

class ConfigTest(unittest.TestCase):
    def test_resolving_unknown_dependency(self):
        c = Config(MockField())
        path = ('a','b')
        with self.assertRaisesRegex(Exception, f"{repr(path)}"):
            c._resolve_dependencies({}, {path: []})
