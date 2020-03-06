import unittest
import yaml

from glorpen.config.fields.simple import Dict, List, Any
from glorpen.config.translators.yaml import YamlRenderer

class YamlRendererTest(unittest.TestCase):
    def test_dict_nested_in_list(self):
        f = Dict({
            "a-dict": List(
                Dict({'a':Any().help(value=1), 'i':Any().help(value=1)}),
            )
        })

        out_str = YamlRenderer().render(f.help_config)
        out = yaml.safe_load(out_str)
        self.assertEqual(out, {'a-dict':[{'a': 1, 'i': 1}]})
