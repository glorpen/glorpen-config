import yaml
import textwrap
import itertools
from glorpen.config.translators.base import Renderer, Reader
from io import StringIO

# TODO: comment all but first variants, key alternatives
# TODO: comment char at line start?

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
    
    def render_key(self, k):
        if k is None:
            return '- '
        else:
            return f'{k}: '

    def render_current_parent_key(self):
        return self.render_key(self._key[-1])
    
    def get_current_keys_until_main_list_start(self):
        ret = list(reversed(list(itertools.takewhile(lambda x: x is None, reversed(self._key[0:-1])))))
        if ret:
            ret.append(self._key[-1])
        else:
            if len(self._key) > 0 and self._key[-1] is None:
                ret.append(None)

        return ret
    
    def get_current_container(self):
        return self._parent_containers[-1] if self._parent_containers else None

    def render_value_as_variant(self, value, comment=''):
        z = -1
        # when in nested list item, parent key list is on same line
        if self._first_list_item:
            # it could be nested list or hash in a list
            # so handle laying multiple keys in one line
            keys = self.get_current_keys_until_main_list_start()
            keys_prefix = "".join(self.render_key(i) for i in keys)
            z = z - len(keys) + 1
        else:
            keys_prefix = self.render_current_parent_key()

        return self.padding(z) + keys_prefix + self.render_value(value) + comment + '\n'


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
        if self._key and self._key[-1] is not None:
            self._data.write(self.padding(-1) + self.render_current_parent_key() + "\n")
    
    # def visit_any(self, tag, node, *args):
    #     self._data.write(f"<{tag}>\n")
    # def leave_any(self, tag, node, *args):
    #     self._data.write(f"</{tag}>\n")

class YamlReader(Reader):
    def __init__(self, path):
        super().__init__()
        self.path = path
    
    def read(self):
        with open(self.path, "rt") as f:
            return yaml.safe_load(f.read())
