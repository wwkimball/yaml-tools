import pytest

from ruamel.yaml.scalarstring import (
    PlainScalarString,
    DoubleQuotedScalarString,
    SingleQuotedScalarString,
    FoldedScalarString,
    LiteralScalarString,
)
from ruamel.yaml.scalarbool import ScalarBoolean
from ruamel.yaml.scalarfloat import ScalarFloat
from ruamel.yaml.scalarint import ScalarInt

from yamlpath.enums import YAMLValueFormats

@pytest.mark.parametrize("check_type,for_node", [
	(YAMLValueFormats.DEFAULT, None),
    (YAMLValueFormats.FOLDED, FoldedScalarString("")),
    (YAMLValueFormats.LITERAL, LiteralScalarString("")),
    (YAMLValueFormats.DQUOTE, DoubleQuotedScalarString("")),
    (YAMLValueFormats.SQUOTE, SingleQuotedScalarString("")),
    (YAMLValueFormats.BARE, PlainScalarString("")),
	(YAMLValueFormats.BOOLEAN, ScalarBoolean(False)),
	(YAMLValueFormats.INT, ScalarInt(10)),
	(YAMLValueFormats.FLOAT, ScalarFloat(1.1)),
])
def test_best_type_for_node(check_type, for_node):
	assert check_type == YAMLValueFormats.from_node(for_node)

@pytest.mark.parametrize("check_type,for_name", [
    (YAMLValueFormats.BARE, "bare"),
    (YAMLValueFormats.BARE, "BARE"),
	(YAMLValueFormats.BOOLEAN, "boolean"),
	(YAMLValueFormats.BOOLEAN, "BOOLEAN"),
	(YAMLValueFormats.DEFAULT, "default"),
	(YAMLValueFormats.DEFAULT, "DEFAULT"),
    (YAMLValueFormats.DQUOTE, "dquote"),
    (YAMLValueFormats.DQUOTE, "DQUOTE"),
	(YAMLValueFormats.FLOAT, "float"),
	(YAMLValueFormats.FLOAT, "FLOAT"),
    (YAMLValueFormats.FOLDED, "folded"),
    (YAMLValueFormats.FOLDED, "FOLDED"),
	(YAMLValueFormats.INT, "int"),
	(YAMLValueFormats.INT, "INT"),
    (YAMLValueFormats.LITERAL, "literal"),
    (YAMLValueFormats.LITERAL, "LITERAL"),
    (YAMLValueFormats.SQUOTE, "squote"),
    (YAMLValueFormats.SQUOTE, "SQUOTE"),
])
def test_name_from_str(check_type, for_name):
    assert check_type == YAMLValueFormats.from_str(for_name)

def test_unknown_name_from_str():
    with pytest.raises(NameError):
        _ = YAMLValueFormats.from_str("THIS NAME DOES NOT EXIST!")
