"""
Collection of general helper functions.

Copyright 2018, 2019 William W. Kimball, Jr. MBA MSIS
"""
from distutils.util import strtobool
from typing import Any

from ruamel.yaml.comments import CommentedSeq, CommentedMap
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

from yamlpath import YAMLPath
from yamlpath.enums import (
    YAMLValueFormats,
    PathSegmentTypes,
)


def build_next_node(yaml_path: YAMLPath, depth: int,
                    value: Any = None) -> Any:
    """
    Identifies and returns the most appropriate default value for the next
    entry in a YAML Path, should it not already exist.

    Parameters:
        1. yaml_path (deque) The pre-parsed YAML Path to follow
        2. depth (int) Index of the YAML Path segment to evaluate
        3. value (Any) The expected value for the final YAML Path entry

    Returns:  (Any) The most appropriate default value

    Raises:  N/A
    """
    default_value = wrap_type(value)
    segments = yaml_path.escaped
    if not (segments and len(segments) > depth):
        return default_value

    typ = segments[depth][0]
    if typ == PathSegmentTypes.INDEX:
        default_value = CommentedSeq()
    elif typ == PathSegmentTypes.KEY:
        default_value = CommentedMap()

    return default_value

def append_list_element(data: Any, value: Any = None,
                        anchor: str = None) -> Any:
    """
    Appends a new element to an ruamel.yaml presented list, preserving any
    tailing comment for the former last element of the same list.

    Parameters:
        1. data (Any) The parsed YAML data to process
        2. value (Any) The value of the element to append
        3. anchor (str) An Anchor or Alias name for the new element

    Returns:  (Any) The newly appended element node

    Raises:  N/A
    """
    if anchor is not None and value is not None:
        value = wrap_type(value)
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

def wrap_type(value: Any) -> Any:
    """
    Wraps a value in one of the ruamel.yaml wrapper types.

    Parameters:
        1. value (Any) The value to wrap.

    Returns: (Any) The wrapped value or the original value when a better
        wrapper could not be identified.

    Raises:  N/A
    """
    wrapped_value = value
    typ = type(value)
    if typ is list:
        wrapped_value = CommentedSeq(value)
    elif typ is dict:
        wrapped_value = CommentedMap(value)
    elif typ is str:
        wrapped_value = PlainScalarString(value)
    elif typ is int:
        wrapped_value = ScalarInt(value)
    elif typ is float:
        wrapped_value = ScalarFloat(value)
    elif typ is bool:
        wrapped_value = ScalarBoolean(value)

    return wrapped_value

def clone_node(node: Any) -> Any:
    """
    Duplicates a YAML Data node.  This is necessary because otherwise,
    Python would treat any copies of a value as references to each other
    such that changes to one automatically affect all copies.  This is not
    desired when an original value must be duplicated elsewhere in the data
    and then the original changed without impacting the copy.

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

# pylint: disable=locally-disabled,too-many-branches,too-many-statements
def make_new_node(source_node: Any, value: Any,
                  value_format: YAMLValueFormats) -> Any:
    """
    Creates a new data node based on a sample node, effectively duplicaing
    the type and anchor of the node but giving it a different value.

    Parameters:
        1. source_node (Any) The node from which to copy type
        2. value (Any) The value to assign to the new node
        3. value_format (YAMLValueFormats) The YAML presentation format to
            apply to value when it is dumped

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
        except NameError:
            raise NameError(
                "Unknown YAML Value Format:  {}".format(strform)
                + ".  Please specify one of:  "
                + ", ".join(
                    [l.lower() for l in YAMLValueFormats.get_names()]
                )
            )

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
        except ValueError:
            raise ValueError(
                ("The requested value format is {}, but '{}' cannot be"
                 + " cast to a floating-point number.")
                .format(valform, value)
            )

        strval = str(value)
        precision = 0
        width = len(strval)
        lastdot = strval.rfind(".")
        if -1 < lastdot:
            precision = strval.rfind(".")

        if hasattr(source_node, "anchor"):
            new_node = ScalarFloat(
                new_value
                , anchor=source_node.anchor.value
                , prec=precision
                , width=width
            )
        else:
            new_node = ScalarFloat(new_value, prec=precision, width=width)
    elif valform == YAMLValueFormats.INT:
        new_type = ScalarInt

        try:
            new_value = int(value)
        except ValueError:
            raise ValueError(
                ("The requested value format is {}, but '{}' cannot be"
                 + " cast to an integer number.")
                .format(valform, value)
            )
    else:
        # Punt to whatever the best type may be
        new_type = type(wrap_type(value))

    if new_node is None:
        if hasattr(source_node, "anchor"):
            new_node = new_type(new_value, anchor=source_node.anchor.value)
        else:
            new_node = new_type(new_value)

    return new_node
