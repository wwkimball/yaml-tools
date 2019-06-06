import pytest

from yamlpath.enums import PathSearchMethods
from yamlpath.path import SearchTerms

class Test_path_SearchTerms():
	"""Tests for the SearchTerms class."""

	@pytest.mark.parametrize("invert,method,attr,term,output", [
		(False, PathSearchMethods.CONTAINS, "abc", "b", "[abc%b]"),
		(True, PathSearchMethods.REGEX, "abc", "^abc$", "[abc!=~/^abc$/]"),
	])
	def test_str(self, invert, method, attr, term, output):
		assert output == str(SearchTerms(invert, method, attr, term))

	# Disabled until Python matures enough to permit classes and types to play
	# nicely together...
	# def test_from_path_segment_attrs(self):
	# 	from yamlpath.types import PathAttributes
	# 	st = SearchTerms(False, PathSearchMethods.EQUALS, ".", "key")
	# 	assert str(st) == str(SearchTerms.from_path_segment_attrs(st))

	# 	with pytest.raises(AttributeError):
	# 		_ = SearchTerms.from_path_segment_attrs("nothing-to-see-here")
