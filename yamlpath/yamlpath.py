"""YAML Path implementation based on ruamel.yaml.

Copyright 2018, 2019 William W. Kimball, Jr. MBA MSIS
"""
from sys import maxsize
import re
from distutils.util import strtobool

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

from yamlpath.exceptions import YAMLPathException
from yamlpath.enums import (
    YAMLValueFormats,
    PathSegmentTypes,
    PathSearchMethods,
)
from yamlpath.parser import Parser


class YAMLPath:
    """Query and update YAML data via robust YAML Paths."""

    def __init__(self, logger, **kwargs):
        """Init this class.

        Positional Parameters:
          1. logger (ConsoleWriter) Instance of ConsoleWriter or any similar
             wrapper (say, around stdlib logging modules)

        Returns:  N/A

        Raises:  N/A
        """
        self.log = logger

        if "parser" in kwargs:
            self.parser = kwargs.pop("parser")
        else:
            self.parser = Parser(logger, **kwargs)

    def get_nodes(self, data, yaml_path, **kwargs):
        """Retrieves zero or more node at YAML Path in YAML data.

        Positional Parameters:
          1. data (ruamel.yaml data) The parsed YAML data to process
          2. yaml_path (any) The YAML Path to evaluate

        Optional Parameters:
          1. mustexist (Boolean) Indicate whether yaml_path must exist
             in data prior to this query (lest an Exception be raised);
             default=False
          2. default_value (any) The value to set at yaml_path should
             it not already exist in data and mustexist is False;
             default=None

        Returns:  (object) The requested YAML nodes as they are matched or None
          when data or yaml_path are None.

        Raises:
            YAMLPathException when YAML Path is invalid
        """
        mustexist = kwargs.pop("mustexist", False)
        default_value = kwargs.pop("default_value", None)

        if data is None or yaml_path is None:
            return

        path = self.parser.parse_path(yaml_path)
        if mustexist:
            matched_nodes = 0
            for node in self._get_nodes(data, path):
                if node is not None:
                    matched_nodes += 1
                    self.log.debug(
                        "YAMLPath::get_nodes:  Relaying required node:"
                    )
                    yield node

            if matched_nodes < 1:
                raise YAMLPathException(
                    "Required YAML Path does not match any nodes",
                    self.parser.str_path(yaml_path)
                )
        else:
            for node in self._ensure_path(data, path, default_value):
                if node is not None:
                    self.log.debug(
                        "YAMLPath::get_nodes:  Relaying optional node:"
                    )
                    yield node

    def set_value(self, data, yaml_path, value, **kwargs):
        """Sets the value of zero or more nodes at YAML Path in YAML data.

        Positional Parameters:
          1. data (ruamel.yaml data) The parsed YAML data to process
          2. yaml_path (any) The YAML Path to evaluate
          3. value (any) The value to set

        Optional Parameters:
          1. mustexist (Boolean) Indicate whether yaml_path must exist
             in data prior to this query (lest an Exception be raised);
             default=False
          2. value_format (YAMLValueFormats) The demarcation or visual
             representation to use when writing the data;
             default=YAMLValueFormats.DEFAULT

        Returns:  N/A

        Raises:
            YAMLPathException when YAML Path is invalid
        """
        if data is None or yaml_path is None:
            return

        mustexist = kwargs.pop("mustexist", False)
        value_format = kwargs.pop("value_format", YAMLValueFormats.DEFAULT)
        path = self.parser.parse_path(yaml_path)
        if mustexist:
            self.log.debug(
                "YAMLPath::set_value:  Seeking required node at {}."
                .format(self.parser.str_path(path))
            )
            found_nodes = 0
            for node in self._get_nodes(data, path):
                if node is not None:
                    found_nodes += 1
                    self.update_node(data, node, value, value_format)

            if found_nodes < 1:
                raise YAMLPathException(
                    "No nodes matched required YAML Path",
                    self.parser.str_path(path)
                )
        else:
            self.log.debug(
                "YAMLPath::set_value:  Seeking optional node at {}."
                .format(self.parser.str_path(path))
            )
            for node in self._ensure_path(data, path, value):
                if node is not None:
                    self.update_node(data, node, value, value_format)

    def _get_nodes(self, data, yaml_path):
        """Generates zero or more matching, pre-existing nodes from YAML data
        matching a YAML Path.

        Positional Parameters:
          1. data (ruamel.yaml data) The parsed YAML data to process
          2. yaml_path (deque) The pre-parsed YAML Path to follow

        Returns:  (object) The requested YAML nodes as they are matched or None

        Raises:  N/A
        """
        if data is None or yaml_path is None:
            return

        matches = 0
        if yaml_path:
            (curtyp, curele) = curref = yaml_path.popleft()
            unstripped_ele = curele[2]

            self.log.debug(
                ("YAMLPath::_get_nodes:  Seeking element <{}>{} in data of"
                 + " type {}:"
                ).format(curtyp, unstripped_ele, type(data))
            )
            self.log.debug(data)
            self.log.debug("")

            # The next element must already exist
            for node in self._get_elements_by_ref(data, curref):
                if node is not None:
                    matches += 1
                    self.log.debug(
                        ("YAMLPath::_get_nodes:  Found element <{}>{} in the"
                         + " data and recursing into it...")
                        .format(curtyp, unstripped_ele)
                    )
                    for epn in self._get_nodes(node, yaml_path.copy()):
                        if epn is not None:
                            yield epn

            if not matches:
                return

        if not matches:
            self.log.debug(
                "YAMLPath::_get_nodes:  Finally returning data of type {}:"
                .format(type(data))
            )
            self.log.debug(data)
            self.log.debug("")

            yield data

    def _get_elements_by_ref(self, data, ref):
        """Returns zero or more referenced YALM Nodes or None when the given
        reference points nowhere.

        Positional Parameters:
          1. data (ruamel.yaml data) The parsed YAML data to process
          2. ref (tuple(PathSegmentTypes,(str,any,any))) A YAML Path segment
             reference

        Returns:  (object) At least one YAML Node or None

        Raises:
          NotImplementedError when ref indicates an unknown
          PathSegmentTypes value.
        """
        if data is None or ref is None:
            return

        reftyp = ref[0]
        refori = ref[1][0]
        refesc = ref[1][1]
        refune = ref[1][2]
        if reftyp == PathSegmentTypes.KEY:
            if isinstance(data, dict) and refesc in data:
                yield data[refesc]
            elif isinstance(data, list):
                try:
                    # Try using the ref as a bare Array index
                    intele = int(refesc)
                    if len(data) > intele:
                        yield data[intele]
                except ValueError:
                    # Pass-through search against possible Array-of-Hashes
                    for rec in data:
                        for node in self._get_elements_by_ref(rec, ref):
                            if node is not None:
                                yield node
        elif (
            reftyp == PathSegmentTypes.INDEX
            and isinstance(refesc, str)
            and ':' in refesc
        ):
            # Array index or Hash key slice
            refparts = refesc.split(':', 1)
            min_match = refparts[0]
            max_match = refparts[1]
            if isinstance(data, list):
                try:
                    intmin = int(min_match)
                    intmax = int(max_match)
                except ValueError:
                    raise YAMLPathException(
                        "{} is not an integer array slice".format(str(refesc))
                        , refori
                        , refune
                    )

                if intmin == intmax and len(data) > intmin:
                    yield data[intmin]
                else:
                    yield data[intmin:intmax]

            elif isinstance(data, dict):
                for key, val in data.items():
                    if key >= min_match and key <= max_match:
                        yield val
        elif reftyp == PathSegmentTypes.INDEX:
            try:
                intele = int(refesc)
            except ValueError:
                raise YAMLPathException(
                    "{} is not an integer array index".format(str(refesc))
                    , refori
                    , refune
                )

            if isinstance(data, list) and len(data) > intele:
                yield data[intele]
        elif reftyp == PathSegmentTypes.ANCHOR:
            if isinstance(data, list):
                for ele in data:
                    if hasattr(ele, "anchor") and refesc == ele.anchor.value:
                        yield ele
            elif isinstance(data, dict):
                for _, val in data.items():
                    if hasattr(val, "anchor") and refesc == val.anchor.value:
                        yield val
        elif reftyp == PathSegmentTypes.SEARCH:
            for match in self._search(data, refesc):
                if match is not None:
                    yield match
        else:
            raise NotImplementedError

    def _search(self, data, terms):
        """Searches the top level of given YAML data for all matching dictionary
        entries.

        Positional Parameters:
          1. data (ruamel.yaml data) The parsed YAML data to process
          2. terms (list) A list with these elements:
             0 = invert result (Boolean) true = Return a NON-matching node
             1 = search method (PathSearchMethods) the search
                 method
             2 = attribute name (str) the dictionary key to the value to check
             3 = search phrase (any) the value to match
        """

        def search_matches(method, needle, haystack):
            self.log.debug(
                ("YAMLPath::_search::search_matches:  Searching for {}{}"
                 + " using {} against {}:"
                ).format(type(needle), needle, method, type(haystack))
            )
            self.log.debug(haystack)
            matches = None

            if method is PathSearchMethods.EQUALS:
                if isinstance(haystack, int):
                    try:
                        matches = haystack == int(needle)
                    except ValueError:
                        matches = False
                elif isinstance(haystack, float):
                    try:
                        matches = haystack == float(needle)
                    except ValueError:
                        matches = False
                else:
                    matches = haystack == needle
            elif method is PathSearchMethods.STARTS_WITH:
                matches = str(haystack).startswith(needle)
            elif method is PathSearchMethods.ENDS_WITH:
                matches = str(haystack).endswith(needle)
            elif method is PathSearchMethods.CONTAINS:
                matches = needle in str(haystack)
            elif method is PathSearchMethods.GREATER_THAN:
                if isinstance(haystack, int):
                    try:
                        matches = haystack > int(needle)
                    except ValueError:
                        matches = False
                elif isinstance(haystack, float):
                    try:
                        matches = haystack > float(needle)
                    except ValueError:
                        matches = False
                else:
                    matches = haystack > needle
            elif method is PathSearchMethods.LESS_THAN:
                if isinstance(haystack, int):
                    try:
                        matches = haystack < int(needle)
                    except ValueError:
                        matches = False
                elif isinstance(haystack, float):
                    try:
                        matches = haystack < float(needle)
                    except ValueError:
                        matches = False
                else:
                    matches = haystack < needle
            elif method is PathSearchMethods.GREATER_THAN_OR_EQUAL:
                if isinstance(haystack, int):
                    try:
                        matches = haystack >= int(needle)
                    except ValueError:
                        matches = False
                elif isinstance(haystack, float):
                    try:
                        matches = haystack >= float(needle)
                    except ValueError:
                        matches = False
                else:
                    matches = haystack >= needle
            elif method is PathSearchMethods.LESS_THAN_OR_EQUAL:
                if isinstance(haystack, int):
                    try:
                        matches = haystack <= int(needle)
                    except ValueError:
                        matches = False
                elif isinstance(haystack, float):
                    try:
                        matches = haystack <= float(needle)
                    except ValueError:
                        matches = False
                else:
                    matches = haystack <= needle
            elif method == PathSearchMethods.REGEX:
                matcher = re.compile(needle)
                matches = matcher.search(str(haystack)) is not None
            else:
                raise NotImplementedError

            return matches

        invert, method, attr, term = terms
        if isinstance(data, list):
            for ele in data:
                if attr == '.':
                    matches = search_matches(method, term, ele)
                elif isinstance(ele, dict) and attr in ele:
                    matches = search_matches(method, term, ele[attr])

                if (matches and not invert) or (invert and not matches):
                    yield ele

        elif isinstance(data, dict):
            # Allow . to mean "each key's name"
            if attr == '.':
                for key, val in data.items():
                    matches = search_matches(method, term, key)
                    if (matches and not invert) or (invert and not matches):
                        yield val

            elif attr in data:
                value = data[attr]
                matches = search_matches(method, term, value)
                if (matches and not invert) or (invert and not matches):
                    yield value

        else:
            # Check the passed data itself for a match
            matches = search_matches(method, term, data)
            if (matches and not invert) or (invert and not matches):
                yield data

    def _ensure_path(self, data, path, value=None):
        """Returns zero or more pre-existing nodes matching a YAML Path, or
        exactly one new node at the end of the YAML Path if it had to be
        created.

        Positional Parameters:
          1. data (ruamel.yaml data) The parsed YAML data to process
          2. path (deque) The pre-parsed YAML Path to follow
          3. value (any) The value to assign to the element

        Returns:  (object) The specified node(s)

        Raises:
          YAMLPathException when the YAML Path is invalid.
          NotImplementedError when a segment of the YAML Path indicates
            an element that does not exist in data and this code isn't
            yet prepared to add it.
        """
        if data is None or path is None:
            self.log.debug(
                "YAMLPath::_ensure_path:  Bailing out on None data/path!"
            )
            return

        if path:
            (curtyp, curele) = curref = path.popleft()
            original_path = curele[0]
            stripped_ele = curele[1]
            unstripped_ele = curele[2]

            self.log.debug(
                ("YAMLPath::_ensure_path:  Seeking element <{}>{} in data of"
                 + " type {}:"
                ).format(curtyp, unstripped_ele, type(data))
            )
            self.log.debug(data)
            self.log.debug("")

            # The next element may not exist; this method ensures that it does
            matched_nodes = 0
            for node in self._get_elements_by_ref(data, curref):
                if node is not None:
                    matched_nodes += 1
                    self.log.debug(
                        ("YAMLPath::_ensure_path:  Found element <{}>{} in the"
                            + " data; recursing into it..."
                        ).format(curtyp, unstripped_ele)
                    )
                    for epn in self._ensure_path(node, path.copy(), value):
                        if epn is not None:
                            yield epn

            if (
                matched_nodes < 1
                and curtyp is not PathSegmentTypes.SEARCH
            ):
                # Add the missing element
                self.log.debug(
                    ("YAMLPath::_ensure_path:  Element <{}>{} is unknown in"
                     + " the data!"
                    ).format(curtyp, unstripped_ele)
                )
                if isinstance(data, list):
                    self.log.debug(
                        "YAMLPath::_ensure_path:  Dealing with a list"
                    )
                    if curtyp is PathSegmentTypes.ANCHOR:
                        new_val = self.default_for_child(path, value)
                        new_ele = self.append_list_element(
                            data, new_val, stripped_ele
                        )
                        for node in self._ensure_path(new_ele, path, value):
                            if node is not None:
                                matched_nodes += 1
                                yield node
                    elif (
                        curtyp is PathSegmentTypes.INDEX
                        and isinstance(stripped_ele, int)
                    ):
                        for _ in range(len(data) - 1, stripped_ele):
                            new_val = self.default_for_child(path, value)
                            self.append_list_element(data, new_val)
                        for node in self._ensure_path(
                            data[stripped_ele], path, value
                        ):
                            if node is not None:
                                matched_nodes += 1
                                yield node
                    else:
                        raise YAMLPathException(
                            "Cannot add {} subreference to lists"
                            .format(str(curtyp))
                            , original_path
                            , unstripped_ele
                        )
                elif isinstance(data, dict):
                    self.log.debug(
                        "YAMLPath::_ensure_path:  Dealing with a dictionary"
                    )
                    if curtyp is PathSegmentTypes.ANCHOR:
                        raise NotImplementedError

                    if curtyp is PathSegmentTypes.KEY:
                        data[stripped_ele] = self.default_for_child(
                            path, value
                        )
                        for node in self._ensure_path(
                            data[stripped_ele], path, value
                        ):
                            if node is not None:
                                matched_nodes += 1
                                yield node
                    else:
                        raise YAMLPathException(
                            "Cannot add {} subreference to dictionaries"
                            .format(str(curtyp)),
                            original_path,
                            unstripped_ele
                        )
                else:
                    raise YAMLPathException(
                        "Cannot add {} subreference to scalars".format(
                            str(curtyp)
                        ),
                        original_path,
                        unstripped_ele
                    )

        else:
            self.log.debug(
                ("YAMLPath::_ensure_path:  Finally returning data of type"
                 + " {}:"
                ).format(type(data))
            )
            self.log.debug(data)

            yield data

    @staticmethod
    def default_for_child(yaml_path, value=None):
        """Identifies and returns the most appropriate default value for the
        next entry in a YAML Path, should it not already exist.

        Positional Parameters:
          1. yaml_path (deque) The pre-parsed YAML Path to follow
          2. value (any) The final expected value for the final YAML Path entry

        Returns:  (any) The most appropriate default value

        Raises:  N/A
        """
        if yaml_path is None or not yaml_path:
            return value

        default_value = value
        (typ, _) = yaml_path[0]
        if typ == PathSegmentTypes.INDEX:
            default_value = CommentedSeq()
        elif typ == PathSegmentTypes.KEY:
            default_value = CommentedMap()
        elif isinstance(value, str):
            default_value = PlainScalarString("")
        elif isinstance(value, bool):
            default_value = ScalarBoolean(False)
        elif isinstance(value, int):
            default_value = ScalarInt(maxsize)
        elif isinstance(value, float):
            default_value = ScalarFloat("inf")

        return default_value

    @staticmethod
    def append_list_element(data, value=None, anchor=None):
        """Appends a new element to an ruamel.yaml presented list, preserving
        any tailing comment for the former last element of the same list.

        Positional Parameters:
          1. data (ruamel.yaml data) The parsed YAML data to process
          2. value (any) The value of the element to append
          3. anchor (str) An Anchor or Alias name for the new element

        Returns:  (object) The newly appended element node

        Raises:  N/A
        """

        if anchor is not None and value is not None:
            value = YAMLPath.wrap_type(value)
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

    @staticmethod
    def wrap_type(value):
        """Wraps a value in one of the ruamel.yaml wrapper types.

        Positional Parameters:
          1. value (any) The value to wrap.

        Returns: (any) The wrapped value or the original value when a better
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

    @staticmethod
    def clone_node(node):
        """Duplicates a YAML Data node.

        Positional Parameters:
          1. node (object) The node to clone.

        Returns: (object) Clone of the given node
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

    @staticmethod
    def make_new_node(source_node, value, value_format):
        """Creates a new data node given a value and its presumed format.
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
                    "The requested value format is {}, but '{}' cannot be cast\
                     to a floating-point number.".format(valform, value)
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
                    "The requested value format is {}, but '{}' cannot be cast\
                     to an integer number.".format(valform, value)
                )
        else:
            # Punt to whatever the best type may be
            new_type = type(YAMLPath.wrap_type(value))

        if new_node is None:
            if hasattr(source_node, "anchor"):
                new_node = new_type(new_value, anchor=source_node.anchor.value)
            else:
                new_node = new_type(new_value)

        return new_node

    @staticmethod
    def update_node(data, source_node, value, value_format):
        """Recursively updates the value of a YAML Node and any references to it
        within the entire YAML data structure (Anchors and Aliases, if any).

        Positional Parameters:
          1. data (ruamel.yaml data) The parsed YAML data to process
          2. source_node (object) The YAML Node to update
          3. value (any) The new value to assign to the source_node and
             its references
          4. value_format (YAMLValueFormats) the YAML representation of the
             value

        Returns: N/A

        Raises:
          No Exception but it will terminate the program after printing
          a console error when value_format is illegal for the given value or
          is unknown.
        """
        # Change val has already been made to obj in data.  When obj is either
        # an Anchor or an Alias, all other references to it must also receive
        # an identical update so they are kept in synchronization.  In addition,
        # if obj is a child of a parent that is an Anchor or Alias, all
        # references to that parent must also be updated.
        def update_refs(data, reference_node, replacement_node):
            if isinstance(data, dict):
                for i, k in [
                    (idx, key) for idx, key in
                        enumerate(data.keys()) if key is reference_node
                ]:
                    data.insert(i, replacement_node, data.pop(k))
                for k, val in data.non_merged_items():
                    if val is reference_node:
                        data[k] = replacement_node
                    else:
                        update_refs(val, reference_node, replacement_node)
            elif isinstance(data, list):
                for idx, item in enumerate(data):
                    if item is reference_node:
                        data[idx] = replacement_node
                    else:
                        update_refs(item, reference_node, replacement_node)

        new_node = YAMLPath.make_new_node(source_node, value, value_format)
        update_refs(data, source_node, new_node)
