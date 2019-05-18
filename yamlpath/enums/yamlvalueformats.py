"""Implements the YAMLValueFormats enumeration.

Copyright 2019 William W. Kimball, Jr. MBA MSIS
"""
from enum import Enum, auto

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


class YAMLValueFormats(Enum):
    """Supported representation formats for YAML values."""
    BARE = auto()
    BOOLEAN = auto()
    DEFAULT = auto()
    DQUOTE = auto()
    FLOAT = auto()
    FOLDED = auto()
    INT = auto()
    LITERAL = auto()
    SQUOTE = auto()

    @staticmethod
    def get_names():
        """Returns all entry names for this enumeration.

        Positional Parameters:  N/A

        Returns:  (list) Upper-case names from this enumeration

        Raises:  N/A
        """
        return [entry.name.upper() for entry in YAMLValueFormats]

    @staticmethod
    def from_str(name):
        """Converts a string value to a value of this enumeration, if valid.

        Positional Parameters:
          1. name (str) The name to convert

        Returns:  (YAMLValueFormats) the converted enumeration value

        Raises:
          NameError when name doesn't match any enumeration values.
        """
        check = str(name).upper()
        if check in YAMLValueFormats.get_names():
            return YAMLValueFormats[check]
        raise NameError("YAMLValueFormats has no such item, " + check)

    @staticmethod
    def from_node(node):
        """Identifies the best matching enumeration value from a sample data
        node.  Will return YAMLValueFormats.DEFAULT if the node is None or its
        best match cannot be determined.

        Parameters:
          1. node (ruamel.yaml data node) The node to type

        Returns:  (YAMLValueFormats) one of the enumerated values

        Raises:  N/A
        """
        best_type = YAMLValueFormats.DEFAULT
        if node is None:
            return best_type

        node_type = type(node)
        if node_type is FoldedScalarString:
            best_type = YAMLValueFormats.FOLDED
        elif node_type is LiteralScalarString:
            best_type = YAMLValueFormats.LITERAL
        elif node_type is DoubleQuotedScalarString:
            best_type = YAMLValueFormats.DQUOTE
        elif node_type is SingleQuotedScalarString:
            best_type = YAMLValueFormats.SQUOTE
        elif node_type is PlainScalarString:
            best_type = YAMLValueFormats.BARE
        elif node_type is ScalarBoolean:
            best_type = YAMLValueFormats.BOOLEAN
        elif node_type is ScalarFloat:
            best_type = YAMLValueFormats.FLOAT
        elif node_type is ScalarInt:
            best_type = YAMLValueFormats.INT

        return best_type
