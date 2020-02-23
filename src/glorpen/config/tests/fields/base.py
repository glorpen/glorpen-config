import unittest

from glorpen.config.fields import base as org

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

# class FieldTest(unittest.TestCase):
#     def test_packing(self):
#         #check if packed attr is set on value
#         pass
#     def test_validation(self):
#         pass
