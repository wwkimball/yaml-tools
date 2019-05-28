"""
YAML path Search segment terms.

Copyright 2019 William W. Kimball, Jr. MBA MSIS
"""
from yamlpath.enums import PathSearchMethods


class SearchTerms:
    """YAML path Search segment terms."""

    def __init__(self, inverted: bool, method: PathSearchMethods,
                 attribute: str, term: str) -> None:
        self._inverted: bool = inverted
        self._method: PathSearchMethods = method
        self._attribute: str = attribute
        self._term: str = term

    def __str__(self) -> str:
        if self.method == PathSearchMethods.REGEX:
            safe_term = "/{}/".format(self.term.replace("/", r"\/"))
        else:
            # Replace unescaped spaces with escaped spaces
            safe_term = r"\ ".join(
                list(map(
                    lambda ele: ele.replace(" ", r"\ ")
                    , self.term.split(r"\ ")
                ))
            )

        return (
            "["
            + str(self.attribute)
            + ("!" if self.inverted else "")
            + str(self.method)
            + safe_term
            + "]"
        )

    @property
    def inverted(self) -> bool:
        """
        Accesses the inversion flag for this Search, indicating whether the
        results are to be inverted.
        """
        return self._inverted

    @property
    def method(self) -> PathSearchMethods:
        """
        Accesses the search method, indicating what kind of search is to be
        performed.
        """
        return self._method

    @property
    def attribute(self) -> str:
        """
        Accessor for the attribute being searched.  This is the "haystack" and
        may reference a particular dictionary key, all values of a dictionary,
        or the elements of a list.
        """
        return self._attribute

    @property
    def term(self) -> str:
        """
        Accessor for the search term.  This is the "needle" to search for
        within the attribute ("haystack").
        """
        return self._term
