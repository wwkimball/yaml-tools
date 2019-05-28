import pytest

from yamlpath.eyaml.enums import EYAMLOutputFormats


class Test_eyaml_enums_EYAMLOutputFormats():
	def test_get_names(self):
		assert EYAMLOutputFormats.get_names() == [
			"BLOCK",
			"STRING",
		]

	@pytest.mark.parametrize("input,output", [
		(EYAMLOutputFormats.BLOCK, "block"),
		(EYAMLOutputFormats.STRING, "string"),
	])
	def test_str(self, input, output):
		assert output == str(input)

	@pytest.mark.parametrize("input,output", [
		("block", EYAMLOutputFormats.BLOCK),
		("string", EYAMLOutputFormats.STRING),
		("BLOCK", EYAMLOutputFormats.BLOCK),
		("STRING", EYAMLOutputFormats.STRING),
		(EYAMLOutputFormats.BLOCK, EYAMLOutputFormats.BLOCK),
		(EYAMLOutputFormats.STRING, EYAMLOutputFormats.STRING),
	])
	def test_from_str(self, input, output):
		assert output == EYAMLOutputFormats.from_str(input)

	def test_from_str_nameerror(self):
		with pytest.raises(NameError):
			EYAMLOutputFormats.from_str("NO SUCH NAME")
