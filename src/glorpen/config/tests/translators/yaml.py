import unittest
import yaml

from glorpen.config.fields.simple import Dict, List, Any, Variant
from glorpen.config.translators.yaml import YamlRenderer

class YamlRendererTest(unittest.TestCase):

    def _render_and_load(self, f):
        help_str = YamlRenderer().render(f.help_config)
        return yaml.safe_load(help_str)
    
    def test_dict_nested_in_list(self):
        f = Dict({
            "a-dict": List(
                Dict({'a':Any().help(value=1), 'i':Any().help(value=1)}),
            )
        })

        out = self._render_and_load(f)
        self.assertEqual(out, {'a-dict':[{'a': 1, 'i': 1}]})
    
    def test_dict_with_first_list_item(self):
        f = List(Any().help(value="test"))
        out = self._render_and_load(f)
        self.assertEqual(out, ['test'])

    def test_alternative_nested_lists(self):
        f = List(
            Variant([
                Dict({'a':Any().help(value=1), 'i':Any().help(value=1)}),
                Dict({'b':Any().help(value=1)}),
            ])
        )

        out = self._render_and_load(f)
        self.assertEqual(out, [{'a':1, 'i':1}, {'b':1}])
