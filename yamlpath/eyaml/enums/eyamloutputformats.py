"""
Implements the EYAMLOutputFormats enumeration.

Copyright 2019 William W. Kimball, Jr. MBA MSIS
"""
from enum import Enum, auto
from typing import List

class EYAMLOutputFormats(Enum):
    """
    Supported EYAML command output formats.  Options include:

    `BLOCK`
        A multi-line version of the otherwise very long encrypted value,
        represented in YAML as a folded string.  Special to EYAML, the
        consequent spaces must be removed from the value when it is read
        before it can be decrypted.

    `STRING`
        A single-line version of the encrypted value, usually very long.
    """
    BLOCK = auto()
    STRING = auto()

    def __str__(self) -> str:
        return str(self.name).lower()

    @staticmethod
    def get_names() -> List[str]:
        """
        Returns all entry names for this enumeration.

        Parameters:  N/A

        Returns:  (List[str]) Upper-case names from this enumeration

        Raises:  N/A
        """
        return [entry.name.upper() for entry in EYAMLOutputFormats]

    @staticmethod
    def from_str(name: str) -> "EYAMLOutputFormats":
        """Converts a string value to a value of this enumeration, if valid.

        Parameters:
            1. name (str) The name to convert

        Returns:  (EYAMLOutputFormats) the converted enumeration value

        Raises:
            - `NameError` when name doesn't match any enumeration values.
        """
        check: str = str(name).upper()
        if check in EYAMLOutputFormats.get_names():
            return EYAMLOutputFormats[check]
        raise NameError(
            "EYAMLOutputFormats has no such item:  {}"
            .format(name))
