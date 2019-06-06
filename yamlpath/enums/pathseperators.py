"""
Implements the PathSeperators enumeration.

Copyright 2019 William W. Kimball, Jr. MBA MSIS
"""
from enum import Enum, auto
from typing import List


class PathSeperators(Enum):
    """
    Supported YAML Path segment seperators.  Seperators include:

    `AUTO`
        The seperator must be manually dictated or automatically inferred from
        the YAML Path being evaluated.

    `DOT`
        YAML Path segments are seperated via dots (.).

    `FSLASH`
        YAML Path segments are seperated via forward-slashes (/).
    """
    AUTO = auto()
    DOT = auto()
    FSLASH = auto()

    def __str__(self) -> str:
        seperator = '.'
        if self is PathSeperators.FSLASH:
            seperator = '/'
        return seperator

    @staticmethod
    def get_names() -> List[str]:
        """
        Returns all upper-cased entry names for this enumeration.

        Parameters:  N/A

        Returns:  (List[str]) Upper-case names from this enumeration

        Raises:  N/A
        """
        return [entry.name.upper() for entry in PathSeperators]

    @staticmethod
    def get_choices() -> List[str]:
        """
        Returns all lower-cased entry names with symbolic representatins for
        this enumeration.

        Parameters:  N/A

        Returns:  (List[str]) Lower-case names and symbols from this
            enumeration

        Raises:  N/A
        """
        names = [l.lower() for l in PathSeperators.get_names()]
        symbols = [str(e) for e in PathSeperators]
        choices = list(set(names + symbols))
        choices.sort()
        return choices

    @staticmethod
    def from_str(name: str) -> "PathSeperators":
        """
        Converts a string value to a value of this enumeration, if valid.

        Parameters:
            1. name (str) The name to convert

        Returns:  (PathSeperators) the converted enumeration value

        Raises:
            - `NameError` when name doesn't match any enumeration values
        """
        if isinstance(name, PathSeperators):
            return name

        check: str = str(name).upper()
        if check == '.':
            check = "DOT"
        elif check == '/':
            check = "FSLASH"

        if check in PathSeperators.get_names():
            return PathSeperators[check]
        raise NameError("PathSeperators has no such item, {}.".format(check))

    @staticmethod
    def infer_seperator(yaml_path: str) -> "PathSeperators":
        """
        Infers the seperator used within a sample YAML Path, returning the best
        PathSeperators match.  Will return `PathSeperators.AUTO` when the
        sample is empty.

        Parameters:
            1. yaml_path (str) The sample YAML Path to evaluate

        Returns: (PathSeperators) the inferred PathSeperators value

        Raises:  N/A
        """
        seperator: PathSeperators = PathSeperators.AUTO

        if yaml_path:
            if yaml_path[0] == '/':
                seperator = PathSeperators.FSLASH
            else:
                seperator = PathSeperators.DOT

        return seperator
