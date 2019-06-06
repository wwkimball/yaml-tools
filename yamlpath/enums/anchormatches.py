"""
Implements the AnchorMatches enumeration.

Copyright 2019 William W. Kimball, Jr. MBA MSIS
"""
from enum import Enum, auto


class AnchorMatches(Enum):
    """
    When performing a search, YAML Anchors and Aliases can be evaluated.  When
    they are, these are the possible match results:

    `ALIAS_EXCLUDED`
        The Anchor is a duplicate that has already matched.

    `ALIAS_INCLUDED`
        The Anchor is a duplicate alias and the search parameters permit
        duplicates.

    `MATCH`
        This original Anchor is a match.

    `NO_ANCHOR`
        The given node has no Anchor.

    `NO_MATCH`
        This original Anchor is not a match.

    `UNSEARCHABLE_ALIAS`
        The node references an Anchor via an Alias that has already been seen,
        but the search parameters prohibit searching Anchor names.

    `UNSEARCHABLE_ANCHOR`
        The node has an Anchor that is so-far unique, but the search parameters
        prohibit searching Anchor names.
    """
    ALIAS_EXCLUDED = auto()
    ALIAS_INCLUDED = auto()
    MATCH = auto()
    NO_ANCHOR = auto()
    NO_MATCH = auto()
    UNSEARCHABLE_ALIAS = auto()
    UNSEARCHABLE_ANCHOR = auto()
