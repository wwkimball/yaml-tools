"""
Implements the YAMLValueFormats enumeration.

Copyright 2019 William W. Kimball, Jr. MBA MSIS
"""
from enum import Enum, auto
from typing import Any, List

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
    """
    Supported representation formats for YAML values.  These include:

    `BARE`
        The value is written as-is, when possible, with neither demarcation nor
        reformatting.  The YAML parser may convert the format to something else
        if it deems necessary.

    `BOOLEAN`
        The value is written as a bare True or False.

    `DEFAULT`
        The value is written in whatever format is deemed most appropriate.

    `DQUOTE`
        The value is demarcated via quotation-marks (").

    `FLOAT`
        The value is written as a bare floating-point decimal.

    `FOLDED`
        An otherwise long single-line string is written as a multi-line value
        which YAML data parsers can read back as the original single-line
        string.

    `INT`
        The value is written as a bare integer number with no fractional
        component.

    `LITERAL`
        A multi-line string is written as-is, preserving newline characters and
        any other white-space.

    `SQUOTE`
        The value is demarcated via apostrophes (').
    """
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
    def get_names() -> List[str]:
        """
        Returns all entry names for this enumeration.

        Parameters:  N/A

        Returns:  (List[str]) Upper-case names from this enumeration

        Raises:  N/A
        """
        return [entry.name.upper() for entry in YAMLValueFormats]

    @staticmethod
    def from_str(name: str) -> "YAMLValueFormats":
        """Converts a string value to a value of this enumeration, if valid.

        Parameters:
            1. name (str) The name to convert

        Returns:  (YAMLValueFormats) the converted enumeration value

        Raises:
            - `NameError` when name doesn't match any enumeration values.
        """
        check: str = str(name).upper()
        if check in YAMLValueFormats.get_names():
            return YAMLValueFormats[check]
        raise NameError(
            "YAMLValueFormats has no such item:  {}"
            .format(name))

    @staticmethod
    def from_node(node: Any) -> "YAMLValueFormats":
        """Identifies the best matching enumeration value from a sample data
        node.  Will return YAMLValueFormats.DEFAULT if the node is None or its
        best match cannot be determined.

        Parameters:
            1. node (Any) The node to type

        Returns:  (YAMLValueFormats) one of the enumerated values

        Raises:  N/A
        """
        best_type: YAMLValueFormats = YAMLValueFormats.DEFAULT
        if node is None:
            return best_type

        node_type: type = type(node)
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
