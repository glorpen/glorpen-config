import yaml
import textwrap
import itertools
from glorpen.config.translators.base import Renderer, Reader
from io import StringIO

class YamlRenderer(Renderer):
    def reset(self):
        self._data = StringIO()
        self._key = []
        self._value_prefix = []
        self._first_list_item = False
        self._parent_containers = []

    def finish(self):
        ret = self._data.getvalue()
        self._data.close()
        return ret

    def padding(self, diff = 0):
        return " " * ((len(self._key) + diff) * 2)
    
    def render_value(self, value):
        ret_v = yaml.dump(value, explicit_start=False, explicit_end=False).strip()
        if ret_v.endswith("\n..."):
            ret_v = ret_v[:-4].strip()
        return ret_v
    
    def render_current_parent_key(self):
        k = self._key[-1]
        if k is None:
            return '- '
        else:
            return f'{k}: '
    
    def get_current_nested_lists_count(self):
        return len(list(itertools.takewhile(lambda x: x is None, reversed(self._key))))
    
    def get_current_container(self):
        return self._parent_containers[-1] if self._parent_containers else None

    def render_value_as_variant(self, value, comment=''):
        z = -1
        # when in nested list item, parent key list is on same line
        key_repeat_count = 1
        if self._first_list_item:
            key_repeat_count = self.get_current_nested_lists_count()
            z = z - key_repeat_count + 1

        return self.padding(z) + (self.render_current_parent_key() * key_repeat_count) + self.render_value(value) + comment + '\n'


    def visit_node(self, node):
        if hasattr(node, "description"):
            self._data.write(self.padding(-1) + f"# {node.description}\n")
    
    def visit_variant(self, variant, node):
        if variant.has_description:
            self._data.write(self.padding(-1) + f"# {variant.description}" + "\n")
        
        if variant.has_value:
            value = variant.value
            comment = ''
        else:
            value = 'something'
            comment = ' # required and no default'
        
        self._data.write(self.render_value_as_variant(value, comment))
    
    def leave_variant(self, variant, node):
        self._first_list_item = False

    def visit_node_variants(self, node):
        if not node.variants:
            parent = self.get_current_container()
            if parent and parent.has_value:
                self._data.write(self.render_value_as_variant(parent.value))
            else:
                self._data.write(self.render_value_as_variant('something', ' # required and no default'))

    def leave_node_variants(self, node):
        # when no variants exist in this node
        self._first_list_item = False

    def visit_item_hash(self, k, node):
        self._key.append(k)

    def leave_item_hash(self, k, node):
        self._key.pop()

    def visit_item_list(self, node):
        self._key.append(None)
    
    def leave_item_list(self, node):
        self._key.pop()
        self._first_list_item = False

    def visit_container(self, node):
        self._parent_containers.append(node)
    
    def leave_container(self, node):
        self._parent_containers.pop()
    
    def visit_container_list(self, node):
        self._first_list_item = True
        if self._key and self._key[-1] is not None:
            self._data.write(self.padding(-1) + self.render_current_parent_key() + "\n")
    
    def visit_container_hash(self, node):
        if self._key:
            self._data.write(self.padding(-1) + self.render_current_parent_key() + "\n")

class YamlReader(Reader):
    def __init__(self, path):
        super().__init__()
        self.path = path
    
    def read(self):
        with open(self.path, "rt") as f:
            return yaml.safe_load(f.read())
