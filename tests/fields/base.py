import unittest
from unittest.mock import Mock

from glorpen.config.fields import base as org
from glorpen.config.fields.simple import String, Any, List

class FakeField(org.Field):
    pass

class ContainerValueTest(unittest.TestCase):
    def test_passing_values(self):
        v = org.ContainerValue([
            ["key", "value"],
            [FakeField, "other value"]
        ], FakeField())

        self.assertEqual(v.values["key"], "value", "handling simple key and value")
        self.assertEqual(v.values[FakeField], "other value", "handling object as key")

class OptionalTest(unittest.TestCase):
    def test_interpolation(self):
        f = org.Optional(String(), default='{asd}')
        v = f.normalize(None)
        self.assertEqual(f.get_dependencies(v), [])
        self.assertEqual(f.pack(v), '{asd}', "Default values are not interpolated")

        v = f.normalize('{asd}')
        self.assertEqual(f.get_dependencies(v), (('asd',),), "Non default values are interpolated")

    def test_optional_container_value(self):
        f = org.Optional(List(Any()))
        v = f.normalize(None)
        self.assertEqual(f.pack(v), [])

class FieldTest(unittest.TestCase):
    def test_default_dependencies(self):
        self.assertEqual(org.Field().get_dependencies("something"), [], "No field dependencies by default")

    def test_help_args_passing(self):
        f = org.Field()
        m = Mock(['set'])
        f.help_config = m
        f.help(value=1).help(value=2)
        
        self.assertEqual(m.set.call_count, 2)
        m.set.assert_any_call(value=1)
        m.set.assert_any_call(value=2)
