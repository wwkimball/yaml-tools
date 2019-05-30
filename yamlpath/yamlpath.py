"""
Implements YAML Path.

Copyright 2019 William W. Kimball, Jr. MBA MSIS
"""
from collections import deque
from typing import Deque, List, Optional, Union

from yamlpath.enums import (
    PathSegmentTypes,
    PathSearchMethods,
    PathSeperators,
    CollectorOperators,
)
from yamlpath.path import SearchTerms, CollectorTerms
from yamlpath.types import PathSegment


class YAMLPath:
    """
    Encapsulate a YAML Path and its parsing logic.

    This will keep track of:
      * the original, unparsed, and unmodified YAML Path;
      * its segment seperator (inferred or manually specified);
      * the unescaped, parsed representation of the YAML Path; and
      * the escaped, parsed representation of the YAML Path.

    Parsing operations are lazy and property setting smartly tiggers re-parsing
    only when necessary.

    Parameters:
        1. yaml_path (Union["YAMLPath", str]) The YAML Path to parse or copy
        2. pathsep (PathSeperators) Forced YAML Path segment seperator; set
            only when automatic inference fails

    Returns:  N/A

    Raises:  N/A
    """

    def __init__(self, yaml_path: Union["YAMLPath", str] = "",
                 pathsep: PathSeperators = PathSeperators.AUTO) -> None:
        self._seperator: PathSeperators = pathsep
        self._original: str = ""
        self._unescaped: deque = deque()
        self._escaped: deque = deque()
        self._stringified: str = ""

        if isinstance(yaml_path, YAMLPath):
            self.original = yaml_path.original
        else:
            self.original = yaml_path

    def __str__(self) -> str:
        if self._stringified:
            return self._stringified

        segments = self.unescaped
        pathsep: str = str(self.seperator)
        add_sep: bool = False
        ppath: str = ""

        # FSLASH seperator requires a path starting with a /
        if self.seperator is PathSeperators.FSLASH:
            ppath = "/"

        for (segment_type, segment_attrs) in segments:
            if segment_type == PathSegmentTypes.KEY:
                if add_sep:
                    ppath += pathsep

                ppath += (
                    str(segment_attrs)
                    .replace(pathsep, "\\{}".format(pathsep))
                    .replace("&", r"\&")
                    .replace("[", r"\[")
                    .replace("]", r"\]")
                )
            elif segment_type == PathSegmentTypes.INDEX:
                ppath += "[{}]".format(segment_attrs)
            elif segment_type == PathSegmentTypes.ANCHOR:
                if add_sep:
                    ppath += "[&{}]".format(segment_attrs)
                else:
                    ppath += "&{}".format(segment_attrs)
            elif segment_type == PathSegmentTypes.SEARCH:
                ppath += str(segment_attrs)
            elif segment_type == PathSegmentTypes.COLLECTOR:
                ppath += str(segment_attrs)

            add_sep = True

        self._stringified = ppath
        return ppath

    def __repr__(self) -> str:
        """Generates an eval()-safe representation of this object."""
        return ("{}('{}', '{}')".format(self.__class__.__name__,
                                        self.original, self.seperator))

    @property
    def original(self) -> str:
        """
        Original YAML Path accessor.

        Positional Parameters:  N/A

        Returns:  (str) The original, unparsed, unmodified YAML Path

        Raises:  N/A
        """
        return self._original

    @original.setter
    def original(self, value: str) -> None:
        """
        Original YAML Path mutator.

        Parameters:
            1. value (str) A YAML Path in string form

        Returns:  N/A

        Raises:  N/A
        """
        # Check for empty paths
        if not str(value).strip():
            value = ""

        self._original = value
        self._seperator = PathSeperators.AUTO
        self._unescaped = deque()
        self._escaped = deque()
        self._stringified = ""

    @property
    def seperator(self) -> PathSeperators:
        """
        Accessor for the seperator used to demarcate YAML Path segments.

        Parameters:  N/A

        Returns:  (PathSeperators) The segment demarcation symbol

        Raises:  N/A
        """
        if self._seperator is PathSeperators.AUTO:
            self._seperator = PathSeperators.infer_seperator(self._original)

        return self._seperator

    @seperator.setter
    def seperator(self, value: PathSeperators) -> None:
        """
        Mutator for the seperator used to demarcate YAML Path segments.  This
        only affects __str__ and only when the new value differs from the
        seperator already inferred from the original YAML Path.

        Parameters:
            1. value (PathSeperators) The segment demarcation symbol

        Returns:  N/A

        Raises:  N/A
        """
        old_value: PathSeperators = self._seperator

        # This changes only the stringified representation
        if not value == old_value:
            self._seperator = value
            self._stringified = ""
            self._stringified = str(self)

    @property
    def escaped(self) -> Deque[PathSegment]:
        r"""
        Accessor for the escaped, parsed version of this YAML Path.

        Any leading \ symbols are stripped out.  This is the parsed YAML Path
        used for processing YAML data.

        Parameters:  N/A

        Returns:  (deque) The escaped, parsed version of this YAML Path

        Raises:  N/A
        """
        if not self._escaped:
            self._escaped = self._parse_path(True)

        return self._escaped.copy()

    @property
    def unescaped(self) -> Deque[PathSegment]:
        r"""
        Accessor for the unescaped, parsed version of this YAML Path.  Any
        leading \ symbols are preserved.  This is the print and log friendly
        version of the parsed YAML Path.

        Parameters:  N/A

        Returns:  (deque) The unescaped, parsed version of this YAML Path

        Raises:  N/A
        """
        if not self._unescaped:
            self._unescaped = self._parse_path(False)

        return self._unescaped.copy()

    # pylint: disable=locally-disabled,too-many-locals,too-many-branches,too-many-statements
    def _parse_path(self,
                    strip_escapes: bool = True
                   ) -> Deque[PathSegment]:
        r"""
        Breaks apart a stringified YAML Path into component segments, each
        identified by its type.  See README.md for sample YAML Paths.

        Parameters:
            1. strip_escapes (bool) True = Remove leading \ symbols, leaving
               only the "escaped" symbol.  False = Leave all leading \ symbols
               intact.

        Returns:  (deque) an empty queue or a queue of tuples, each identifying
          (PathSegmentTypes, segment_attributes).

        Raises:
            - `YAMLPathException` when the YAML Path is invalid
        """
        from yamlpath.exceptions import YAMLPathException

        yaml_path: str = self.original
        path_segments: deque = deque()
        segment_id: str = ""
        segment_type: Optional[PathSegmentTypes] = None
        demarc_stack: List[str] = []
        escape_next: bool = False
        search_inverted: bool = False
        search_method: Optional[PathSearchMethods] = None
        search_attr: str = ""
        seeking_regex_delim: bool = False
        capturing_regex: bool = False
        pathsep: str = str(self.seperator)
        collector_level: int = 0
        collector_operator: CollectorOperators = CollectorOperators.NONE
        seeking_collector_operator: bool = False

        # Empty paths yield empty queues
        if not yaml_path:
            return path_segments

        # Infer the first possible position for a top-level Anchor mark
        first_anchor_pos = 0
        if self.seperator is PathSeperators.FSLASH and len(yaml_path) > 1:
            first_anchor_pos = 1
        seeking_anchor_mark = yaml_path[first_anchor_pos] == "&"

        # Parse the YAML Path
        # pylint: disable=locally-disabled,too-many-nested-blocks
        for char in yaml_path:
            demarc_count = len(demarc_stack)

            if escape_next:
                # Pass-through; capture this escaped character
                escape_next = False

            elif capturing_regex:
                if char == demarc_stack[-1]:
                    # Stop the RegEx capture
                    capturing_regex = False
                    demarc_stack.pop()
                    continue
                else:
                    # Pass-through; capture everything that isn't the present
                    # RegEx delimiter.  This deliberately means users cannot
                    # escape the RegEx delimiter itself should it occur within
                    # the RegEx; thus, users must select a delimiter that won't
                    # appear within the RegEx (which is exactly why the user
                    # gets to choose the delimiter).
                    pass  # pragma: no cover

            # The escape test MUST come AFTER the RegEx capture test so users
            # won't be forced into "The Backslash Plague".
            # (https://docs.python.org/3/howto/regex.html#the-backslash-plague)
            elif char == "\\":
                # Escape the next character
                escape_next = True
                if strip_escapes:
                    continue

            elif (
                    char == " "
                    and (demarc_count < 1
                         or demarc_stack[-1] not in ["'", '"'])
            ):
                # Ignore unescaped, non-demarcated whitespace
                continue

            elif seeking_regex_delim:
                # This first non-space symbol is now the RegEx delimiter
                seeking_regex_delim = False
                capturing_regex = True
                demarc_stack.append(char)
                demarc_count += 1
                continue

            elif seeking_anchor_mark and char == "&":
                # Found an expected (permissible) ANCHOR mark
                seeking_anchor_mark = False
                segment_type = PathSegmentTypes.ANCHOR
                continue

            elif seeking_collector_operator and char in ['+', '-']:
                seeking_collector_operator = False
                if char == '+':
                    collector_operator = CollectorOperators.ADDITION
                elif char == '-':
                    collector_operator = CollectorOperators.SUBTRACTION
                continue

            elif char in ['"', "'"]:
                # Found a string demarcation mark
                if demarc_count > 0:
                    # Already appending to an ongoing demarcated value
                    if char == demarc_stack[-1]:
                        # Close a matching pair
                        demarc_stack.pop()
                        demarc_count -= 1

                        # Record the element_id when all pairs have closed
                        # unless there is no element_id.
                        if demarc_count < 1:
                            if segment_id:
                                # Unless the element has already been
                                # identified as a special type, assume it is a
                                # KEY.
                                if segment_type is None:
                                    segment_type = PathSegmentTypes.KEY
                                path_segments.append(
                                    (segment_type, segment_id))

                            segment_id = ""
                            segment_type = None
                            continue
                    else:
                        # Embed a nested, demarcated component
                        demarc_stack.append(char)
                        demarc_count += 1
                else:
                    # Fresh demarcated value
                    demarc_stack.append(char)
                    demarc_count += 1
                    continue

            elif char == "(":
                seeking_collector_operator = False
                collector_level += 1
                demarc_stack.append(char)
                demarc_count += 1
                segment_type = PathSegmentTypes.COLLECTOR

                # Preserve nested collectors
                if collector_level == 1:
                    continue

            elif collector_level > 0:
                if (
                        demarc_count > 0
                        and char == ")"
                        and demarc_stack[-1] == "("
                ):
                    collector_level -= 1
                    demarc_count -= 1
                    demarc_stack.pop()

                    if collector_level < 1:
                        path_segments.append(
                            (segment_type,
                             CollectorTerms(segment_id, collector_operator)))
                        segment_id = ""
                        collector_operator = CollectorOperators.NONE
                        seeking_collector_operator = True
                        continue

            elif demarc_count == 0 and char == "[":
                # Array INDEX/SLICE or SEARCH
                if segment_id:
                    # Record its predecessor element; unless it has already
                    # been identified as a special type, assume it is a KEY.
                    if segment_type is None:
                        segment_type = PathSegmentTypes.KEY
                    path_segments.append((segment_type, segment_id))
                    segment_id = ""

                demarc_stack.append(char)
                demarc_count += 1
                segment_type = PathSegmentTypes.INDEX
                seeking_anchor_mark = True
                search_inverted = False
                search_method = None
                search_attr = ""
                continue

            elif (
                    demarc_count > 0
                    and demarc_stack[-1] == "["
                    and char in ["=", "^", "$", "%", "!", ">", "<", "~"]
            ):
                # Hash attribute search
                if char == "!":
                    if search_inverted:
                        raise YAMLPathException(
                            "Double search inversion is meaningless at {}"
                            .format(char)
                            , yaml_path
                        )

                    # Invert the search
                    search_inverted = True
                    continue

                elif char == "=":
                    # Exact value match OR >=|<=
                    segment_type = PathSegmentTypes.SEARCH

                    if search_method is PathSearchMethods.LESS_THAN:
                        search_method = PathSearchMethods.LESS_THAN_OR_EQUAL
                    elif search_method is PathSearchMethods.GREATER_THAN:
                        search_method = PathSearchMethods.GREATER_THAN_OR_EQUAL
                    elif search_method is PathSearchMethods.EQUALS:
                        # Allow ==
                        continue
                    elif search_method is None:
                        search_method = PathSearchMethods.EQUALS

                        if segment_id:
                            search_attr = segment_id
                            segment_id = ""
                        else:
                            raise YAMLPathException(
                                "Missing search operand before operator, {}"
                                .format(char)
                                , yaml_path
                            )
                    else:
                        raise YAMLPathException(
                            "Unsupported search operator combination at {}"
                            .format(char)
                            , yaml_path
                        )

                    continue  # pragma: no cover

                elif char == "~":
                    if search_method == PathSearchMethods.EQUALS:
                        search_method = PathSearchMethods.REGEX
                        seeking_regex_delim = True
                    else:
                        raise YAMLPathException(
                            ("Unexpected use of {} operator.  Please try =~ if"
                             + " you mean to search with a Regular"
                             + " Expression."
                            ).format(char)
                            , yaml_path
                        )

                    continue  # pragma: no cover

                elif not segment_id:
                    # All tests beyond this point require an operand
                    raise YAMLPathException(
                        "Missing search operand before operator, {}"
                        .format(char)
                        , yaml_path
                    )

                elif char == "^":
                    # Value starts with
                    segment_type = PathSegmentTypes.SEARCH
                    search_method = PathSearchMethods.STARTS_WITH
                    if segment_id:
                        search_attr = segment_id
                        segment_id = ""
                    continue

                elif char == "$":
                    # Value ends with
                    segment_type = PathSegmentTypes.SEARCH
                    search_method = PathSearchMethods.ENDS_WITH
                    if segment_id:
                        search_attr = segment_id
                        segment_id = ""
                    continue

                elif char == "%":
                    # Value contains
                    segment_type = PathSegmentTypes.SEARCH
                    search_method = PathSearchMethods.CONTAINS
                    if segment_id:
                        search_attr = segment_id
                        segment_id = ""
                    continue

                elif char == ">":
                    # Value greater than
                    segment_type = PathSegmentTypes.SEARCH
                    search_method = PathSearchMethods.GREATER_THAN
                    if segment_id:
                        search_attr = segment_id
                        segment_id = ""
                    continue

                elif char == "<":
                    # Value less than
                    segment_type = PathSegmentTypes.SEARCH
                    search_method = PathSearchMethods.LESS_THAN
                    if segment_id:
                        search_attr = segment_id
                        segment_id = ""
                    continue

            elif (
                    demarc_count > 0
                    and char == "]"
                    and demarc_stack[-1] == "["
            ):
                # Store the INDEX, SLICE, or SEARCH parameters
                if (
                        segment_type is PathSegmentTypes.INDEX
                        and ':' not in segment_id
                ):
                    try:
                        idx = int(segment_id)
                    except ValueError:
                        raise YAMLPathException(
                            "Not an integer index:  {}".format(segment_id)
                            , yaml_path
                        )
                    path_segments.append((segment_type, idx))
                elif (
                        segment_type is PathSegmentTypes.SEARCH
                        and search_method is not None
                ):
                    # Undemarcate the search term, if it is so
                    if segment_id and segment_id[0] in ["'", '"']:
                        leading_mark = segment_id[0]
                        if segment_id[-1] == leading_mark:
                            segment_id = segment_id[1:-1]

                    path_segments.append((
                        segment_type,
                        SearchTerms(search_inverted, search_method,
                                    search_attr, segment_id)
                    ))
                else:
                    path_segments.append((segment_type, segment_id))

                segment_id = ""
                segment_type = None
                demarc_stack.pop()
                demarc_count -= 1
                search_method = None
                continue

            elif demarc_count < 1 and char == pathsep:
                # Do not store empty elements
                if segment_id:
                    # Unless its type has already been identified as a special
                    # type, assume it is a KEY.
                    if segment_type is None:
                        segment_type = PathSegmentTypes.KEY
                    path_segments.append((segment_type, segment_id))
                    segment_id = ""

                segment_type = None
                continue

            segment_id += char
            seeking_anchor_mark = False
            seeking_collector_operator = False

        # Check for unmatched subpath demarcations
        if collector_level > 0:
            raise YAMLPathException(
                "YAML Path contains an unmatched () collector pair",
                yaml_path
            )

        # Check for unterminated RegExes
        if capturing_regex:
            raise YAMLPathException(
                "YAML Path contains an unterminated Regular Expression",
                yaml_path
            )

        # Check for mismatched demarcations
        if demarc_count > 0:
            raise YAMLPathException(
                "YAML Path contains at least one unmatched demarcation mark",
                yaml_path
            )

        # Store the final element_id, which must have been a KEY
        if segment_id:
            # Unless its type has already been identified as a special
            # type, assume it is a KEY.
            if segment_type is None:
                segment_type = PathSegmentTypes.KEY
            path_segments.append((segment_type, segment_id))

        return path_segments
