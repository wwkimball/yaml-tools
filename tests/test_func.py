import pytest

from types import SimpleNamespace

from ruamel.yaml.comments import CommentedSeq, CommentedMap
from ruamel.yaml.scalarstring import PlainScalarString
from ruamel.yaml.scalarbool import ScalarBoolean
from ruamel.yaml.scalarfloat import ScalarFloat
from ruamel.yaml.scalarint import ScalarInt

from yamlpath.enums import YAMLValueFormats
from yamlpath import YAMLPath
from yamlpath.func import (
    append_list_element,
    build_next_node,
    clone_node,
    get_yaml_editor,
    make_new_node,
    wrap_type,
)


class Test_func():
    def test_get_yaml_editor(self):
        assert get_yaml_editor()

    def test_anchorless_list_element_error(self):
        with pytest.raises(ValueError) as ex:
            append_list_element({}, YAMLPath("foo"), "bar")
        assert -1 < str(ex.value).find("Impossible to add an Anchor")

    @pytest.mark.parametrize("value,checktype", [
        ([], CommentedSeq),
        ({}, CommentedMap),
        ("", PlainScalarString),
        (1, ScalarInt),
        (1.1, ScalarFloat),
        (True, ScalarBoolean),
        (SimpleNamespace(), SimpleNamespace),
    ])
    def test_wrap_type(self, value, checktype):
        assert isinstance(wrap_type(value), checktype)

    def test_clone_node(self):
        test_val = "test"
        assert test_val == clone_node(test_val)

        anchor_val = PlainScalarString(test_val, anchor="anchor")
        assert anchor_val == clone_node(anchor_val)

    @pytest.mark.parametrize("source,value,check,vformat", [
        ("", " ", " ", YAMLValueFormats.BARE),
        ("", '" "', '" "', YAMLValueFormats.DQUOTE),
        ("", "' '", "' '", YAMLValueFormats.SQUOTE),
        ("", " ", " ", YAMLValueFormats.FOLDED),
        ("", " ", " ", YAMLValueFormats.LITERAL),
        (True, False, False, YAMLValueFormats.BOOLEAN),
        (True, "no", False, YAMLValueFormats.BOOLEAN),
        (1.1, 1.2, 1.2, YAMLValueFormats.FLOAT),
        (ScalarFloat(1.1, anchor="test"), 1.2, 1.2, YAMLValueFormats.FLOAT),
        (1, 2, 2, YAMLValueFormats.INT),
    ])
    def test_make_new_node(self, source, value, check, vformat):
        assert check == make_new_node(source, value, vformat)

    @pytest.mark.parametrize("source,value,vformat,etype,estr", [
        ("", " ", "DNF", NameError, "Unknown YAML Value Format"),
        (1.1, "4F", YAMLValueFormats.FLOAT, ValueError, "cannot be cast to a floating-point number"),
        (1, "4F", YAMLValueFormats.INT, ValueError, "cannot be cast to an integer number"),
    ])
    def test_make_new_node_errors(self, source, value, vformat, etype, estr):
        with pytest.raises(etype) as ex:
            value == make_new_node(source, value, vformat)
        assert -1 < str(ex.value).find(estr)
