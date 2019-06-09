"""
Implements the IncludeAliases enumeration.

Copyright 2019 William W. Kimball, Jr. MBA MSIS
"""
from enum import Enum, auto


class IncludeAliases(Enum):
    """
    When performing a search, YAML Anchors and Aliases can be evaluated.
    Whether either are is dictated by these options:

    `ANCHORS_ONLY`
        Only anchors are evaluated.

    `INCLUDE_KEY_ALIASES`
        Anchors and key aliases are evaluated.

    `INCLUDE_VALUE_ALIASES`
        Anchors and value aliases are evaluated.

    `INCLUDE_ALL_ALIASES`
        Anchors and all aliases are evaluated.
    """
    ANCHORS_ONLY = auto()
    INCLUDE_KEY_ALIASES = auto()
    INCLUDE_VALUE_ALIASES = auto()
    INCLUDE_ALL_ALIASES = auto()
