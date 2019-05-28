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


class Test_enums_YAMLValueFormats():
	"""Tests for the YAMLValueFormats enumeration."""
	def test_get_names(self):
		assert YAMLValueFormats.get_names() == [
			"BARE",
			"BOOLEAN",
			"DEFAULT",
			"DQUOTE",
			"FLOAT",
			"FOLDED",
			"INT",
			"LITERAL",
			"SQUOTE",
		]

	@pytest.mark.parametrize("input,output", [
		("BARE", YAMLValueFormats.BARE),
		("BOOLEAN", YAMLValueFormats.BOOLEAN),
		("DEFAULT", YAMLValueFormats.DEFAULT),
		("DQUOTE", YAMLValueFormats.DQUOTE),
		("FLOAT", YAMLValueFormats.FLOAT),
		("FOLDED", YAMLValueFormats.FOLDED),
		("INT", YAMLValueFormats.INT),
		("LITERAL", YAMLValueFormats.LITERAL),
		("SQUOTE", YAMLValueFormats.SQUOTE),
	])
	def test_from_str(self, input, output):
		assert output == YAMLValueFormats.from_str(input)

	def test_from_str_nameerror(self):
		with pytest.raises(NameError):
			YAMLValueFormats.from_str("NO SUCH NAME")

	@pytest.mark.parametrize("input,output", [
		(FoldedScalarString(""), YAMLValueFormats.FOLDED),
		(LiteralScalarString(""), YAMLValueFormats.LITERAL),
		(DoubleQuotedScalarString(''), YAMLValueFormats.DQUOTE),
		(SingleQuotedScalarString(""), YAMLValueFormats.SQUOTE),
		(PlainScalarString(""), YAMLValueFormats.BARE),
		(ScalarBoolean(False), YAMLValueFormats.BOOLEAN),
		(ScalarFloat(1.01), YAMLValueFormats.FLOAT),
		(ScalarInt(10), YAMLValueFormats.INT),
		(None, YAMLValueFormats.DEFAULT),
	])
	def test_from_node(self, input, output):
		assert output == YAMLValueFormats.from_node(input)
