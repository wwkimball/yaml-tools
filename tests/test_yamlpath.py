import pytest

from yamlpath.exceptions import YAMLPathException
from yamlpath.enums import PathSegmentTypes, PathSeperators
from yamlpath import YAMLPath

class Test_path_Path():
    """Tests for the Path class."""

    @pytest.mark.parametrize("yamlpath,pathsep,output", [
        (YAMLPath(""), PathSeperators.AUTO, ""),
        (YAMLPath("abc"), PathSeperators.AUTO, "abc"),
        ("abc", PathSeperators.AUTO, "abc"),
        ("/abc", PathSeperators.AUTO, "/abc"),
        ("abc.bcd", PathSeperators.AUTO, "abc.bcd"),
        ("/abc[1]", PathSeperators.AUTO, "/abc[1]"),
        ("&abc", PathSeperators.AUTO, "&abc"),
        ("/abc[&def]", PathSeperators.AUTO, "/abc[&def]"),
        ("abc[!def^ghi]", PathSeperators.AUTO, "abc[def!^ghi]"),
        ("/(abc)[0]", PathSeperators.AUTO, "/(abc)[0]"),
        ("abc[def =~ /ghi/]", PathSeperators.AUTO, "abc[def=~/ghi/]"),
        ("/(abc)+(def)-(ghi)", PathSeperators.AUTO, "/(abc)+(def)-(ghi)"),
        (r"abc.'def.g\"h\"i'", PathSeperators.AUTO, r"abc.def\.g\"h\"i"),
        ("/abc[def>=1]", PathSeperators.AUTO, "/abc[def>=1]"),
        ("abc[def<=10]", PathSeperators.AUTO, "abc[def<=10]"),
        ("/abc[def==1]", PathSeperators.AUTO, "/abc[def=1]"),
        ("abc[def$ghi]", PathSeperators.AUTO, "abc[def$ghi]"),
        ("/abc[def%1]", PathSeperators.AUTO, "/abc[def%1]"),
        ("abc[def%'ghi']", PathSeperators.AUTO, "abc[def%ghi]"),
    ])
    def test_str(self, yamlpath, pathsep, output):
        # Test twice to include cache hits
        testpath = YAMLPath(yamlpath, pathsep)
        assert output == str(testpath) == str(testpath)

    def test_repr(self):
        assert repr(YAMLPath("abc.123")) == "YAMLPath('abc.123', '.')"

    def test_seperator_change(self):
        # IMPORTANT:  The YAML Path is only lazily parsed!  This means parsing
        # ONLY happens when the path is in some way used.  Casting it to string
        # qualifies as one form of use, so this test will instigate parsing via
        # stringification.  THIS MATTERS WHEN YOUR INTENTION IS TO **CHANGE**
        # THE PATH SEPERATOR!  So, if an original path uses dot-notation and
        # you wish to change it to forward-slash-notation, you must first cause
        # the original to become parsed, AND THEN change the seperator.
        testpath = YAMLPath("abc.def")
        dotted = str(testpath)
        testpath.seperator = PathSeperators.FSLASH
        assert "/abc/def" == str(testpath) != dotted

    def test_escaped(self):
        testpath = YAMLPath(r"abc.def\.ghi")
        assert list(testpath.escaped) == [
            (PathSegmentTypes.KEY, "abc"),
            (PathSegmentTypes.KEY, "def.ghi"),
        ]

    def test_unescaped(self):
        testpath = YAMLPath(r"abc.def\.ghi")
        assert list(testpath.unescaped) == [
            (PathSegmentTypes.KEY, "abc"),
            (PathSegmentTypes.KEY, r"def\.ghi"),
        ]

    def test_parse_double_inversion_error(self):
        with pytest.raises(YAMLPathException) as ex:
            str(YAMLPath("abc[!def!=ghi]"))
        assert -1 < str(ex.value).find("Double search inversion is meaningless")

    @pytest.mark.parametrize("input", [
        ("abc[=ghi]"),
        ("abc[^ghi]"),
    ])
    def test_parse_missing_operand_errors(self, input):
        with pytest.raises(YAMLPathException) as ex:
            str(YAMLPath(input))
        assert -1 < str(ex.value).find("Missing search operand")

    def test_parse_bad_equality_error(self):
        with pytest.raises(YAMLPathException) as ex:
            str(YAMLPath("abc[def^=ghi]"))
        assert -1 < str(ex.value).find("Unsupported search operator")

    def test_parse_bad_tilde_error(self):
        with pytest.raises(YAMLPathException) as ex:
            str(YAMLPath("abc[def~ghi]"))
        assert -1 < str(ex.value).find("Unexpected use of ~ operator")

    def test_parse_bad_int_error(self):
        with pytest.raises(YAMLPathException) as ex:
            str(YAMLPath("abc[4F]"))
        assert -1 < str(ex.value).find("Not an integer index")

    def test_parse_unmatched_collector_error(self):
        with pytest.raises(YAMLPathException) as ex:
            str(YAMLPath("(abc"))
        assert -1 < str(ex.value).find("contains an unmatched () collector")

    def test_parse_unmatched_regex_error(self):
        with pytest.raises(YAMLPathException) as ex:
            str(YAMLPath("abc[def=~/ghi]"))
        assert -1 < str(ex.value).find("contains an unterminated Regular Expression")

    def test_parse_unmatched_demarcation_error(self):
        with pytest.raises(YAMLPathException) as ex:
            str(YAMLPath("abc.'def"))
        assert -1 < str(ex.value).find("contains at least one unmatched demarcation mark")
