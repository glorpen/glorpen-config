import yaml
import textwrap
from glorpen.config.translators.base import Renderer, Reader

class YamlRenderer(Renderer):
    def reset(self):
        self._data = []
        self._key = []
        self._depth = 0

        self._entered_list_item = False

    def finish(self):
        return "\n".join(self._data)

    def padding(self):
        return " " * (self._depth * 2)
    
    def render_value(self, value):
        ret_v = yaml.dump(value, explicit_start=False, explicit_end=False).strip()
        if ret_v.endswith("\n..."):
            ret_v = ret_v[:-4].strip()
        return ret_v
    
    def render_value_with_key(self, value):
        if self._key and self._key[-1] is not None:
            return self.render_value({self._key[-1]:value})
        else:
            return self.render_value(value)

    def render_description(self, node):
        return [(self.padding() + "# " + i) for i in textwrap.wrap(node.description, 60)]

    def render_item_value(self, node, commented = False):
        if node.has_description:
            if self._key and not commented:
                yield ""
            yield from self.render_description(node)
        
        if node.has_value:
            prefix = "#" if commented else ""
            if self._entered_list_item:
                yield self.padding() + prefix + "- " + self.render_value_with_key(node.value)
            else:
                yield self.padding() + prefix + self.render_value_with_key(node.value)
    
    def visit_node(self, node):
        # skip if not root node
        if node.has_children and self._key:
            return
        
        self._data.extend(self.render_item_value(node))
        for n in node.variants:
            self._data.extend(self.render_item_value(n, True))
        
        if node.has_value and self._entered_list_item:
            self._entered_list_item = False
    
    def visit_item_hash(self, k, node):
        self._key.append(k)
        if not node.has_value:
                
            if node.has_description:
                self._data.append("")
                self._data.extend(self.render_description(node))
        
            if self._entered_list_item:
                self._data.append(self.padding() + "- " + self.render_value(k) + ":")
                self._entered_list_item = False
            else:
                self._data.append(self.padding() + self.render_value(k) + ":")
            self._depth += 1
    
    def leave_item_hash(self, k, node):
        self._key.pop()
        if not node.has_value:
            self._depth -= 1
    
    def visit_item_list(self, node):
        self._key.append(None)
        self._entered_list_item = True
        self._depth -= 1
    
    def leave_item_list(self, node):
        self._key.pop()
        self._depth += 1

class YamlReader(Reader):
    def __init__(self, path):
        super().__init__()
        self.path = path
    
    def read(self):
        with open(self.path, "rt") as f:
            return yaml.safe_load(f.read())
