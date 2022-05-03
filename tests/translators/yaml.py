import dataclasses
import typing

from glorpen.config import Schema
from glorpen.config.translators.yaml import YamlRenderer


def test_asd():
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

    r = YamlRenderer()

    model = Schema().generate(Dummy)
    assert r.render(model) == """# some string value
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

    model = Schema().generate(Dummy)
    r = YamlRenderer()
    data = r.render(model)

    assert data == "# field: |-\n#        line1\n#        line2\n#        line3\n"
