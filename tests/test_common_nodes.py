import pytest

import ruamel.yaml as ry

from yamlpath.enums import YAMLValueFormats
from yamlpath.common import Nodes

class Test_common_nodes():
    """Tests for the Nodes helper class."""

    ###
    # make_new_node
    ###
    def test_dict_to_str(self):
        assert "{}" == Nodes.make_new_node("", "{}", YAMLValueFormats.DEFAULT)

    def test_list_to_str(self):
        assert "[]" == Nodes.make_new_node("", "[]", YAMLValueFormats.DEFAULT)

    def test_anchored_string(self):
        node = ry.scalarstring.PlainScalarString("value")
        node.yaml_set_anchor("anchored")
        new_node = Nodes.make_new_node(node, "new", YAMLValueFormats.DEFAULT)
        assert new_node.anchor.value == node.anchor.value


    ###
    # apply_yaml_tag
    ###
    def test_tag_map(self):
        new_tag = "!something"
        old_node = ry.comments.CommentedMap({"key": "value"})
        new_node = Nodes.apply_yaml_tag(old_node, new_tag)
        assert new_node.tag.value == new_tag

    def test_update_tag(self):
        old_tag = "!tagged"
        new_tag = "!changed"
        old_node = ry.scalarstring.PlainScalarString("tagged value")
        tagged_node = ry.comments.TaggedScalar(old_node, tag=old_tag)
        new_node = Nodes.apply_yaml_tag(tagged_node, new_tag)
        assert new_node.tag.value == new_tag
        assert new_node.value == old_node

    def test_delete_tag(self):
        old_tag = "!tagged"
        new_tag = ""
        old_node = ry.scalarstring.PlainScalarString("tagged value")
        tagged_node = ry.comments.TaggedScalar(old_node, tag=old_tag)
        new_node = Nodes.apply_yaml_tag(tagged_node, new_tag)
        assert not hasattr(new_node, "tag")
        assert new_node == old_node


    ###
    # tagless_value
    ###
    def test_tagless_value_syntax_error(self):
        assert "[abc" == Nodes.tagless_value("[abc")
