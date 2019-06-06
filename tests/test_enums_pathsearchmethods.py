import pytest

from yamlpath.enums import PathSearchMethods


class Test_enums_PathSearchMethods():
	"""Tests for the PathSearchMethods enumeration."""

	@pytest.mark.parametrize("input,output", [
		(PathSearchMethods.CONTAINS, "%"),
		(PathSearchMethods.ENDS_WITH, "$"),
		(PathSearchMethods.EQUALS, "="),
		(PathSearchMethods.STARTS_WITH, "^"),
		(PathSearchMethods.GREATER_THAN, ">"),
		(PathSearchMethods.LESS_THAN, "<"),
		(PathSearchMethods.GREATER_THAN_OR_EQUAL, ">="),
		(PathSearchMethods.LESS_THAN_OR_EQUAL, "<="),
		(PathSearchMethods.REGEX, "=~"),
	])
	def test_str(self, input, output):
		assert output == str(input)

	@pytest.mark.parametrize("input,result", [
		("!", False),
		("%", True),
		("$", True),
		("=", True),
		("^", True),
		(">", True),
		("<", True),
		(">=", True),
		("<=", True),
		("=~", True),
	])
	def test_is_operator(self, input, result):
		assert result == PathSearchMethods.is_operator(input)
