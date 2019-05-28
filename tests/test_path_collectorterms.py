import pytest

from yamlpath.enums import CollectorOperators
from yamlpath.path import CollectorTerms

class Test_path_CollectorTerms():
	"""Tests for the CollectorTerms class."""

	@pytest.mark.parametrize("path,operator,output", [
		("abc", CollectorOperators.NONE, "(abc)"),
		("abc", CollectorOperators.ADDITION, "+(abc)"),
		("abc", CollectorOperators.SUBTRACTION, "-(abc)"),
	])
	def test_str(self, path, operator, output):
		assert output == str(CollectorTerms(path, operator))
