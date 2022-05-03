import textwrap
import typing

import yaml

from glorpen.config.model.schema import Field


def list_indent(items: typing.Iterable[str], prefix):
    for item in items:
        yield f"{prefix}{item}"


class YamlRenderer:

    _indent_size = 2

    def __init__(self):
        super(YamlRenderer, self).__init__()

    def render(self, model: Field):
        return "\n".join(list(self._render(model))) + "\n"

    def _render(self, model: Field):
        if isinstance(model.args, dict):
            yield from self._render_dict(model.args)
        else:
            yield from self._render_value(model)

    def _render_dict(self, fields: typing.Dict[str, Field]):
        for name, field in fields.items():
            if field.doc:
                yield from list_indent(textwrap.wrap(field.doc, width=60), "# ")
            value = list(self._render(field))
            key = f"{name}: "
            prefix = "# " if field.default_factory else ""

            if isinstance(field.args, dict):
                yield prefix + key.rstrip()
                for line in list_indent(value, " " * self._indent_size):
                    yield prefix + line
            else:
                yield prefix + key + value[0]
                for line in list_indent(value[1:], " " * len(key)):
                    yield prefix + line

    def _render_value(self, model: Field):
        if model.is_nullable():
            yield "~"
        elif model.default_factory:
            msg = yaml.safe_dump(model.default_factory(), default_style='|')
            if msg.endswith("\n...\n"):
                msg = msg[:-5]
            lines = msg.splitlines(keepends=False)
            if lines[0] == "|-" and len(lines) == 2:
                yield lines[1].lstrip()
            else:
                yield lines[0]
                yield from textwrap.dedent("\n".join(lines[1:])).splitlines(keepends=False)
        else:
            yield f"# required {model.type.__name__}"
