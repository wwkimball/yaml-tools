"""
Implement YAML Path.

Copyright 2019, 2020 William W. Kimball, Jr. MBA MSIS
"""
from collections import deque
from typing import Deque, List, Optional, Union

from yamlpath.types import PathSegment
from yamlpath.exceptions import YAMLPathException
from yamlpath.enums import (
    PathSegmentTypes,
    PathSearchMethods,
    PathSeperators,
    CollectorOperators,
)
from yamlpath.path import SearchTerms, CollectorTerms


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
    """

    def __init__(self, yaml_path: Union["YAMLPath", str] = "",
                 pathsep: PathSeperators = PathSeperators.AUTO) -> None:
        """
        Instantiate this class into an object.

        Parameters:
        1. yaml_path (Union["YAMLPath", str]) The YAML Path to parse or copy
        2. pathsep (PathSeperators) Forced YAML Path segment seperator; set
           only when automatic inference fails

        Returns:  N/A

        Raises:  N/A
        """
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
        """Get a stringified version of this object."""
        if self._stringified:
            return self._stringified

        self._stringified = YAMLPath._stringify_yamlpath_segments(
            self.unescaped, self.seperator)
        return self._stringified

    def __repr__(self) -> str:
        """Generate an eval()-safe representation of this object."""
        return ("{}('{}', '{}')".format(self.__class__.__name__,
                                        self.original, self.seperator))

    def __len__(self) -> int:
        """Indicate how many segments comprise this YAML Path."""
        return len(self.escaped)

    def __eq__(self, other: object) -> bool:
        """
        Indicate equivalence of two YAMLPaths.

        Parameters:
        1. other (object) The other YAMLPath to compare against.

        Returns:  (bool) true = Both are identical; false, otherwise
        """
        if not isinstance(other, (YAMLPath, str)):
            return False

        equiv_this = YAMLPath(self)
        equiv_this.seperator = PathSeperators.FSLASH
        cmp_this = str(equiv_this)

        equiv_that = YAMLPath(other)
        equiv_that.seperator = PathSeperators.FSLASH
        cmp_that = str(equiv_that)

        return cmp_this == cmp_that

    def __ne__(self, other: object) -> bool:
        """Indicate non-equivalence of two YAMLPaths."""
        return not self == other

    def __add__(self, other: object) -> "YAMLPath":
        """Add a nonmutating -- pre-escaped -- path segment."""
        next_segment = str(other) if not isinstance(other, str) else other
        return YAMLPath(self).append(next_segment)

    def append(self, segment: str) -> "YAMLPath":
        """
        Append a new -- pre-escaped -- segment to this YAML Path.

        Parameters:
        1. segment (str) The new -- pre-escaped -- segment to append to this
           YAML Path.  Do NOT include any seperator with this value; it will be
           added for you.

        Returns:  (YAMLPath) The adjusted YAMLPath
        """
        seperator = (
            PathSeperators.FSLASH
            if self.seperator is PathSeperators.AUTO
            else self.seperator)
        if len(self._original) < 1:
            self.original = segment
        else:
            self.original += "{}{}".format(seperator, segment)
        return self

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
        Get the seperator used to demarcate YAML Path segments.

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
        Set the seperator used to demarcate YAML Path segments.

        This only affects __str__ and only when the new value differs from the
        seperator already inferred from the original YAML Path.

        Parameters:
        1. value (PathSeperators) The segment demarcation symbol

        Returns:  N/A

        Raises:  N/A
        """
        old_value: PathSeperators = self._seperator

        # This changes only the stringified representation
        if not value == old_value:
            self._stringified = YAMLPath._stringify_yamlpath_segments(
                self.unescaped, value)
            self._seperator = value

    @property
    def escaped(self) -> Deque[PathSegment]:
        r"""
        Get the escaped, parsed version of this YAML Path.

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
        Get the unescaped, parsed version of this YAML Path.

        Any leading \ symbols are preserved.  This is the print and log
        friendly version of the parsed YAML Path.

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
        Parse the YAML Path into its component segments.

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

                # Pass-through; capture everything that isn't the present
                # RegEx delimiter.  This deliberately means users cannot
                # escape the RegEx delimiter itself should it occur within
                # the RegEx; thus, users must select a delimiter that won't
                # appear within the RegEx (which is exactly why the user
                # gets to choose the delimiter).
                # pylint: disable=unnecessary-pass
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
                    path_segments.append(self._expand_splats(
                        yaml_path, segment_id, segment_type))
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
                # pylint: disable=no-else-continue
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
                    except ValueError as wrap_ex:
                        raise YAMLPathException(
                            "Not an integer index:  {}".format(segment_id)
                            , yaml_path
                            , segment_id
                        ) from wrap_ex
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
                    path_segments.append(self._expand_splats(
                        yaml_path, segment_id, segment_type))
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
            path_segments.append(self._expand_splats(
                yaml_path, segment_id, segment_type))

        return path_segments

    @staticmethod
    def _expand_splats(
        yaml_path: str, segment_id: str,
        segment_type: Optional[PathSegmentTypes] = None
    ) -> tuple:
        """
        Replace segment IDs with search operators when * is present.

        Parameters:
        1. yaml_path (str) The full YAML Path being processed.
        2. segment_id (str) The segment identifier to parse.
        3. segment_type (Optional[PathSegmentTypes]) Pending predetermined type
           of the segment under evaluation.

        Returns:  (tuple) Coallesced YAML Path segment.
        """
        coal_type = segment_type
        coal_value: Union[str, SearchTerms, None] = segment_id

        if '*' in segment_id:
            splat_count = segment_id.count("*")
            splat_pos = segment_id.index("*")
            segment_len = len(segment_id)
            if splat_count == 1:
                if segment_len == 1:
                    # /*/ -> [.=~/.*/]
                    coal_type = PathSegmentTypes.SEARCH
                    coal_value = SearchTerms(
                        False, PathSearchMethods.REGEX, ".", ".*")
                elif splat_pos == 0:
                    # /*text/ -> [.$text]
                    coal_type = PathSegmentTypes.SEARCH
                    coal_value = SearchTerms(
                        False, PathSearchMethods.ENDS_WITH, ".",
                        segment_id[1:])
                elif splat_pos == segment_len - 1:
                    # /text*/ -> [.^text]
                    coal_type = PathSegmentTypes.SEARCH
                    coal_value = SearchTerms(
                        False, PathSearchMethods.STARTS_WITH, ".",
                        segment_id[0:splat_pos])
                else:
                    # /te*xt/ -> [.=~/^te.*xt$/]
                    coal_type = PathSegmentTypes.SEARCH
                    coal_value = SearchTerms(
                        False, PathSearchMethods.REGEX, ".",
                        "^{}.*{}$".format(
                            segment_id[0:splat_pos],
                            segment_id[splat_pos + 1:]))
            elif splat_count == 2 and segment_len == 2:
                # Traversal operator
                coal_type = PathSegmentTypes.TRAVERSE
                coal_value = None
            elif splat_count > 1:
                # Multi-wildcard search
                search_term = "^"
                was_splat = False
                for char in segment_id:
                    if char == "*":
                        if was_splat:
                            raise YAMLPathException(
                                "The ** traversal operator has no meaning when"
                                " combined with other characters", yaml_path,
                                segment_id)
                        was_splat = True
                        search_term += ".*"
                    else:
                        was_splat = False
                        search_term += char
                search_term += "$"

                coal_type = PathSegmentTypes.SEARCH
                coal_value = SearchTerms(
                    False, PathSearchMethods.REGEX, ".", search_term)

        return (coal_type, coal_value)

    @staticmethod
    def _stringify_yamlpath_segments(
        segments: Deque[PathSegment], seperator: PathSeperators
    ) -> str:
        """Stringify segments of a YAMLPath."""
        pathsep: str = str(seperator)
        add_sep: bool = False
        ppath: str = ""

        # FSLASH seperator requires a path starting with a /
        if seperator is PathSeperators.FSLASH:
            ppath = pathsep

        for (segment_type, segment_attrs) in segments:
            if segment_type == PathSegmentTypes.KEY:
                if add_sep:
                    ppath += pathsep

                # Replace a subset of special characters to alert users to
                # potentially unintentional demarcation.
                ppath += YAMLPath.ensure_escaped(
                    str(segment_attrs),
                    pathsep,
                    '(', ')', '[', ']', '^', '$', '%', ' ', "'", '"'
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
            elif segment_type == PathSegmentTypes.TRAVERSE:
                if add_sep:
                    ppath += pathsep
                ppath += "**"

            add_sep = True

        return ppath

    @staticmethod
    def strip_path_prefix(path: "YAMLPath", prefix: "YAMLPath") -> "YAMLPath":
        """
        Remove a prefix from a YAML Path.

        Parameters:
        1. path (YAMLPath) The path from which to remove the prefix.
        2. prefix (YAMLPath) The prefix to remove (except "/").

        Returns:  (YAMLPath) The trimmed YAML Path.
        """
        if prefix is None:
            return path

        prefix.seperator = PathSeperators.FSLASH
        if str(prefix) == "/":
            return path

        prefix.seperator = PathSeperators.FSLASH
        path.seperator = PathSeperators.FSLASH
        prefix_str = str(prefix)
        path_str = str(path)
        if path_str.startswith(prefix_str):
            path_str = path_str[len(prefix_str):]
            return YAMLPath(path_str)

        return path

    @staticmethod
    def ensure_escaped(value: str, *symbols: str) -> str:
        r"""
        Escape all instances of a symbol within a value.

        Ensures all instances of a symbol are escaped (via \) within a value.
        Multiple symbols can be processed at once.
        """
        escaped: str = value
        for symbol in symbols:
            replace_term: str = "\\{}".format(symbol)
            oparts: List[str] = str(escaped).split(replace_term)
            eparts: List[str] = []
            for opart in oparts:
                eparts.append(opart.replace(symbol, replace_term))
            escaped = replace_term.join(eparts)
        return escaped

    @staticmethod
    def escape_path_section(section: str, pathsep: PathSeperators) -> str:
        """
        Escape all special symbols present within a YAML Path segment.

        Renders inert via escaping all symbols within a string which have
        special meaning to YAML Path.  The resulting string can be consumed as
        a YAML Path section without triggering unwanted additional processing.
        """
        return YAMLPath.ensure_escaped(
            section,
            '\\', str(pathsep), '(', ')', '[', ']', '^', '$', '%',
            ' ', "'", '"'
        )
