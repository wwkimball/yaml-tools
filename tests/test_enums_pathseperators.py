import pytest

from yamlpath.enums import PathSeperators


class Test_enums_PathSeperators():
	"""Tests for the PathSeperators enumeration."""
	def test_get_names(self):
		assert PathSeperators.get_names() == [
			"AUTO",
			"DOT",
			"FSLASH",
		]

	@pytest.mark.parametrize("input,output", [
		(PathSeperators.AUTO, '.'),
		(PathSeperators.DOT, '.'),
		(PathSeperators.FSLASH, '/'),
	])
	def test_str(self, input, output):
		assert output == str(input)

	@pytest.mark.parametrize("input,output", [
		(".", PathSeperators.DOT),
		("/", PathSeperators.FSLASH),
		("DOT", PathSeperators.DOT),
		("FSLASH", PathSeperators.FSLASH),
		(PathSeperators.DOT, PathSeperators.DOT),
		(PathSeperators.FSLASH, PathSeperators.FSLASH),
	])
	def test_from_str(self, input, output):
		assert output == PathSeperators.from_str(input)

	def test_from_str_nameerror(self):
		with pytest.raises(NameError):
			PathSeperators.from_str("NO SUCH NAME")

	@pytest.mark.parametrize("input,output", [
		("abc", PathSeperators.DOT),
		("abc.123", PathSeperators.DOT),
		("/abc", PathSeperators.FSLASH),
		("/abc/123", PathSeperators.FSLASH),
	])
	def test_infer_seperator(self, input, output):
		assert output == PathSeperators.infer_seperator(input)
