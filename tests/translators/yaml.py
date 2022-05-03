import dataclasses
import typing

from glorpen.config import Schema
from glorpen.config.translators.yaml import YamlRenderer


def render(cls):
    r = YamlRenderer()
    model = Schema().generate(cls)
    return r.render(model)


def test_optional_fields():
    @dataclasses.dataclass
    class Dummy:
        comment_field: str = dataclasses.field(metadata={"doc": "some string value"})
        required_field: str
        nullable_field: typing.Optional[str]
        optional_field: str = dataclasses.field(default="test1")
        optional_comment_field: str = dataclasses.field(
            default="test2", metadata={"doc": """some multiline
                                                 string value"""
                                       }
        )

    assert render(Dummy) == """# some string value
comment_field: # required str
required_field: # required str
nullable_field: ~
# optional_field: test1
# some multiline
# string value
# optional_comment_field: test2
"""


def test_multiline_defaults():
    @dataclasses.dataclass
    class Dummy:
        field: str = """line1
line2
line3"""

    assert render(Dummy) == "# field: |-\n#        line1\n#        line2\n#        line3\n"


def test_nested_fields():
    @dataclasses.dataclass
    class Dummy2:
        field: str

    @dataclasses.dataclass
    class Dummy1:
        field: Dummy2

    assert render(Dummy1) == "field:\n  field: # required str\n"
