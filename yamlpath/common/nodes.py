"""
Implement Nodes, a static library of generally-useful code for data nodes.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
import ast
from distutils.util import strtobool
from typing import Any

from ruamel.yaml.comments import CommentedSeq, CommentedMap, TaggedScalar
from ruamel.yaml.scalarbool import ScalarBoolean
from ruamel.yaml.scalarfloat import ScalarFloat
from ruamel.yaml.scalarint import ScalarInt
from ruamel.yaml.scalarstring import (
    PlainScalarString,
    DoubleQuotedScalarString,
    SingleQuotedScalarString,
    FoldedScalarString,
    LiteralScalarString,
)

from yamlpath.enums import (
    PathSegmentTypes,
    YAMLValueFormats,
)
from yamlpath import YAMLPath


class Nodes:
    """Helper methods for common data node operations."""

    @staticmethod
    # pylint: disable=too-many-branches,too-many-statements,too-many-locals
    def make_new_node(
        source_node: Any, value: Any, value_format: YAMLValueFormats, **kwargs
    ) -> Any:
        """
        Create a new data node based on a sample node.

        This is achieved by effectively duplicaing the type and anchor of the
        node but giving it a different value.

        Parameters:
        1. source_node (Any) The node from which to copy type
        2. value (Any) The value to assign to the new node
        3. value_format (YAMLValueFormats) The YAML presentation format to
           apply to value when it is dumped

        Keyword Arguments:
        * tag (str) Custom data-type tag to apply to this node

        Returns: (Any) The new node

        Raises:
        - `NameError` when value_format is invalid
        - `ValueError' when the new value is not numeric and value_format
        requires it to be so
        """
        new_node = None
        new_type = type(source_node)
        new_value = value
        valform = YAMLValueFormats.DEFAULT

        if isinstance(value_format, YAMLValueFormats):
            valform = value_format
        else:
            strform = str(value_format)
            try:
                valform = YAMLValueFormats.from_str(strform)
            except NameError as wrap_ex:
                raise NameError(
                    "Unknown YAML Value Format:  {}".format(strform)
                    + ".  Please specify one of:  "
                    + ", ".join(
                        [l.lower() for l in YAMLValueFormats.get_names()]
                    )
                ) from wrap_ex

        if valform == YAMLValueFormats.BARE:
            new_type = PlainScalarString
            new_value = str(value)
        elif valform == YAMLValueFormats.DQUOTE:
            new_type = DoubleQuotedScalarString
            new_value = str(value)
        elif valform == YAMLValueFormats.SQUOTE:
            new_type = SingleQuotedScalarString
            new_value = str(value)
        elif valform == YAMLValueFormats.FOLDED:
            new_type = FoldedScalarString
            new_value = str(value)
        elif valform == YAMLValueFormats.LITERAL:
            new_type = LiteralScalarString
            new_value = str(value)
        elif valform == YAMLValueFormats.BOOLEAN:
            new_type = ScalarBoolean
            if isinstance(value, bool):
                new_value = value
            else:
                new_value = strtobool(value)
        elif valform == YAMLValueFormats.FLOAT:
            try:
                new_value = float(value)
            except ValueError as wrap_ex:
                raise ValueError(
                    ("The requested value format is {}, but '{}' cannot be"
                    + " cast to a floating-point number.")
                    .format(valform, value)
                ) from wrap_ex

            anchor_val = None
            if hasattr(source_node, "anchor"):
                anchor_val = source_node.anchor.value
            new_node = Nodes.make_float_node(new_value, anchor_val)
        elif valform == YAMLValueFormats.INT:
            new_type = ScalarInt

            try:
                new_value = int(value)
            except ValueError as wrap_ex:
                raise ValueError(
                    ("The requested value format is {}, but '{}' cannot be"
                    + " cast to an integer number.")
                    .format(valform, value)
                ) from wrap_ex
        else:
            # Punt to whatever the best Scalar type may be
            try:
                wrapped_value = Nodes.wrap_type(value)
            except ValueError:
                # Value cannot be safely converted to any native type
                new_type = PlainScalarString
                wrapped_value = PlainScalarString(value)

            if Nodes.node_is_leaf(wrapped_value):
                new_type = type(wrapped_value)
            else:
                # Disallow conversions to complex types
                new_type = PlainScalarString
                wrapped_value = PlainScalarString(value)

            new_format = YAMLValueFormats.from_node(wrapped_value)
            if new_format is not YAMLValueFormats.DEFAULT:
                new_node = Nodes.make_new_node(
                    source_node, value, new_format, **kwargs)

        if new_node is None:
            if hasattr(source_node, "anchor") and source_node.anchor.value:
                new_node = new_type(new_value, anchor=source_node.anchor.value)
            elif new_type is not type(None):
                new_node = new_type(new_value)

        # Apply a custom tag, if provided
        if "tag" in kwargs:
            new_node = Nodes.apply_yaml_tag(new_node, kwargs.pop("tag"))

        return new_node

    @staticmethod
    def make_float_node(value: float, anchor: str = None):
        """
        Create a new ScalarFloat data node from a bare float.

        An optional anchor may be attached.

        Parameters:
        1. value (float) The bare float to wrap.
        2. anchor (str) OPTIONAL anchor to add.

        Returns: (ScalarNode) The new node
        """
        minus_sign = "-" if value < 0.0 else None
        strval = format(value, '.15f').rstrip('0').rstrip('.')
        precision = 0
        width = len(strval)
        lastdot = strval.rfind(".")
        if -1 < lastdot:
            precision = strval.rfind(".")

        if anchor is None:
            new_node = ScalarFloat(
                value,
                m_sign=minus_sign,
                prec=precision,
                width=width
            )
        else:
            new_node = ScalarFloat(
                value
                , anchor=anchor
                , m_sign=minus_sign
                , prec=precision
                , width=width
            )

        return new_node

    @staticmethod
    def clone_node(node: Any) -> Any:
        """
        Duplicate a YAML Data node.

        This is necessary because otherwise, Python would treat any copies of a
        value as references to each other such that changes to one
        automatically affect all copies.  This is not desired when an original
        value must be duplicated elsewhere in the data and then the original
        changed without impacting the copy.

        Parameters:
        1. node (Any) The node to clone.

        Returns: (Any) Clone of the given node

        Raises:  N/A
        """
        # Clone str values lest the new node change whenever the original node
        # changes, which defeates the intention of preserving the present,
        # pre-change value to an entirely new node.
        clone_value = node
        if isinstance(clone_value, str):
            clone_value = ''.join(node)

        if hasattr(node, "anchor"):
            return type(node)(clone_value, anchor=node.anchor.value)
        return type(node)(clone_value)

    @staticmethod
    def wrap_type(value: Any) -> Any:
        """
        Wrap a value in one of the ruamel.yaml wrapper types.

        Parameters:
        1. value (Any) The value to wrap.

        Returns: (Any) The wrapped value or the original value when a better
            wrapper could not be identified.

        Raises:  N/A
        """
        wrapped_value = value

        try:
            ast_value = ast.literal_eval(value)
        except ValueError:
            ast_value = value
        except SyntaxError:
            ast_value = value

        typ = type(ast_value)
        if typ is list:
            wrapped_value = CommentedSeq(value)
        elif typ is dict:
            wrapped_value = CommentedMap(value)
        elif typ is str:
            wrapped_value = PlainScalarString(value)
        elif typ is int:
            wrapped_value = ScalarInt(value)
        elif typ is float:
            wrapped_value = Nodes.make_float_node(ast_value)
        elif typ is bool:
            wrapped_value = ScalarBoolean(bool(value))

        return wrapped_value

    @staticmethod
    def build_next_node(yaml_path: YAMLPath, depth: int,
                        value: Any = None) -> Any:
        """
        Get the best default value for the next entry in a YAML Path.

        Parameters:
        1. yaml_path (deque) The pre-parsed YAML Path to follow
        2. depth (int) Index of the YAML Path segment to evaluate
        3. value (Any) The expected value for the final YAML Path entry

        Returns:  (Any) The most appropriate default value

        Raises:  N/A
        """
        default_value = Nodes.wrap_type(value)
        segments = yaml_path.escaped
        if not (segments and len(segments) > depth):
            return default_value

        typ = segments[depth][0]
        if typ == PathSegmentTypes.INDEX:
            default_value = CommentedSeq()
        elif typ == PathSegmentTypes.KEY:
            default_value = CommentedMap()

        return default_value

    @staticmethod
    def append_list_element(data: Any, value: Any = None,
                            anchor: str = None) -> Any:
        """
        Append a new element to an ruamel.yaml List.

        This method preserves any tailing comment for the former last element
        of the same list.

        Parameters:
        1. data (Any) The parsed YAML data to process
        2. value (Any) The value of the element to append
        3. anchor (str) An Anchor or Alias name for the new element

        Returns:  (Any) The newly appended element node

        Raises:  N/A
        """
        if anchor is not None and value is not None:
            value = Nodes.wrap_type(value)
            if not hasattr(value, "anchor"):
                raise ValueError(
                    "Impossible to add an Anchor to value:  {}".format(value)
                )
            value.yaml_set_anchor(anchor)

        old_tail_pos = len(data) - 1
        data.append(value)
        new_element = data[-1]

        # Note that ruamel.yaml will inexplicably add a newline before the tail
        # element irrespective of this ca handling.  This issue appears to be
        # uncontrollable, from here.
        if hasattr(data, "ca") and old_tail_pos in data.ca.items:
            old_comment = data.ca.items[old_tail_pos][0]
            if old_comment is not None:
                data.ca.items[old_tail_pos][0] = None
                data.ca.items[old_tail_pos + 1] = [
                    old_comment, None, None, None
                ]

        return new_element

    @staticmethod
    def apply_yaml_tag(node: Any, value_tag: str) -> Any:
        """
        Apply a YAML Tag (AKA Schema) to a node or remove one.

        Using None for the tag simply preserves the existing tag.  To delete a
        tag, it must be set to an empty-string.

        Parameters:
        1. document (Any) the document in which the node exists
        2. node (Any) the node to update
        3. value_tag (str) Tag to apply (or None to remove)

        Returns: (Any) the updated node; may be new data, so replace your node
        with this returned value!
        """
        if value_tag is None:
            return node

        new_node = node
        if Nodes.node_is_leaf(new_node):
            if isinstance(new_node, TaggedScalar):
                if value_tag:
                    new_node.yaml_set_tag(value_tag)
                else:
                    # Strip off the tag
                    new_node = node.value
            elif value_tag:
                new_node = TaggedScalar(value=node, tag=value_tag)
                if hasattr(node, "anchor") and node.anchor.value:
                    new_node.yaml_set_anchor(node.anchor.value)
        else:
            new_node.yaml_set_tag(value_tag)

        return new_node

    @staticmethod
    def node_is_leaf(node: Any) -> bool:
        """Indicate whether a node is a leaf (Scalar data)."""
        return not isinstance(node, (dict, list, set))

    @staticmethod
    def tagless_elements(data: list) -> list:
        """Get a copy of a list with all elements stripped of YAML Tags."""
        detagged = []
        for ele in data:
            if isinstance(ele, TaggedScalar):
                detagged.append(ele.value)
            else:
                detagged.append(ele)
        return detagged

    @staticmethod
    def tagless_value(value: Any) -> Any:
        """Get a value in its true data-type, stripped of any YAML Tag."""
        evalue = value
        if isinstance(value, TaggedScalar):
            evalue = value.value

        try:
            untagged_value = ast.literal_eval(evalue)
        except ValueError:
            untagged_value = value
        except SyntaxError:
            untagged_value = value

        return untagged_value
