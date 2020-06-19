"""
YAML Path processor based on ruamel.yaml.

Copyright 2018, 2019, 2020 William W. Kimball, Jr. MBA MSIS
"""
from typing import Any, Generator, List, Union

from yamlpath.func import (
    append_list_element,
    build_next_node,
    make_new_node,
    search_matches,
    unwrap_node_coords,
)
from yamlpath import YAMLPath
from yamlpath.path import SearchTerms, CollectorTerms
from yamlpath.wrappers import ConsolePrinter, NodeCoords
from yamlpath.exceptions import YAMLPathException
from yamlpath.enums import (
    YAMLValueFormats,
    PathSegmentTypes,
    CollectorOperators,
    PathSeperators,
)


class Processor:
    """Query and update YAML data via robust YAML Paths."""

    def __init__(self, logger: ConsolePrinter, data: Any) -> None:
        """
        Instantiate this class into an object.

        Parameters:
        1. logger (ConsolePrinter) Instance of ConsoleWriter or subclass
        2. data (Any) Parsed YAML data

        Returns:  N/A

        Raises:  N/A
        """
        self.logger: ConsolePrinter = logger
        self.data: Any = data

    def get_nodes(self, yaml_path: Union[YAMLPath, str],
                  **kwargs: Any) -> Generator[Any, None, None]:
        """
        Get nodes at YAML Path in data.

        Parameters:
        1. yaml_path (Union[YAMLPath, str]) The YAML Path to evaluate

        Keyword Parameters:
        * mustexist (bool) Indicate whether yaml_path must exist
          in data prior to this query (lest an Exception be raised);
          default=False
        * default_value (Any) The value to set at yaml_path should
          it not already exist in data and mustexist is False;
          default=None
        * pathsep (PathSeperators) Forced YAML Path segment seperator; set
          only when automatic inference fails;
          default = PathSeperators.AUTO

        Returns:  (Generator) The requested YAML nodes as they are matched

        Raises:
            - `YAMLPathException` when YAML Path is invalid
        """
        mustexist: bool = kwargs.pop("mustexist", False)
        default_value: Any = kwargs.pop("default_value", None)
        pathsep: PathSeperators = kwargs.pop("pathsep", PathSeperators.AUTO)

        if self.data is None:
            return

        if isinstance(yaml_path, str):
            yaml_path = YAMLPath(yaml_path, pathsep)
        elif pathsep is not PathSeperators.AUTO:
            yaml_path.seperator = pathsep

        if mustexist:
            matched_nodes: int = 0
            for node_coords in self._get_required_nodes(self.data, yaml_path):
                matched_nodes += 1
                self.logger.debug(
                    "Processor::get_nodes:  Relaying required node {}:"
                    .format(type(node_coords))
                )
                self.logger.debug(node_coords)
                yield node_coords

            if matched_nodes < 1:
                raise YAMLPathException(
                    "Required YAML Path does not match any nodes",
                    str(yaml_path)
                )
        else:
            for opt_node in self._get_optional_nodes(
                    self.data, yaml_path, default_value
            ):
                self.logger.debug(
                    "Processor::get_nodes:  Relaying optional node <{}>:"
                    .format(type(opt_node.node))
                )
                self.logger.debug(opt_node.node)
                yield opt_node

    def set_value(self, yaml_path: Union[YAMLPath, str],
                  value: Any, **kwargs) -> None:
        """
        Set the value of zero or more nodes at YAML Path in YAML data.

        Parameters:
        1. yaml_path (Union[Path, str]) The YAML Path to evaluate
        2. value (Any) The value to set

        Keyword Parameters:
        * mustexist (bool) Indicate whether yaml_path must exist
          in data prior to this query (lest an Exception be raised);
          default=False
        * value_format (YAMLValueFormats) The demarcation or visual
          representation to use when writing the data;
          default=YAMLValueFormats.DEFAULT
        * pathsep (PathSeperators) Forced YAML Path segment seperator; set
          only when automatic inference fails;
          default = PathSeperators.AUTO

        Returns:  N/A

        Raises:
            - `YAMLPathException` when YAML Path is invalid
        """
        if self.data is None:
            return

        mustexist: bool = kwargs.pop("mustexist", False)
        value_format: YAMLValueFormats = kwargs.pop("value_format",
                                                    YAMLValueFormats.DEFAULT)
        pathsep: PathSeperators = kwargs.pop("pathsep", PathSeperators.AUTO)
        encoding: str = kwargs.pop("encoding", None)

        if isinstance(yaml_path, str):
            yaml_path = YAMLPath(yaml_path, pathsep)
        elif pathsep is not PathSeperators.AUTO:
            yaml_path.seperator = pathsep

        if mustexist:
            self.logger.debug(
                "Processor::set_value:  Seeking required node at {}."
                .format(yaml_path)
            )
            found_nodes: int = 0
            for req_node in self._get_required_nodes(
                    self.data, yaml_path
            ):
                found_nodes += 1
                self._update_node(
                    req_node.parent, req_node.parentref, value, value_format,
                    encoding)

            if found_nodes < 1:
                raise YAMLPathException(
                    "No nodes matched required YAML Path",
                    str(yaml_path)
                )
        else:
            self.logger.debug(
                "Processor::set_value:  Seeking optional node at {}."
                .format(yaml_path)
            )
            for node_coord in self._get_optional_nodes(
                    self.data, yaml_path, value
            ):
                self.logger.debug(
                    "Processor::set_value:  Matched optional node coord, {}."
                    .format(node_coord)
                )
                self._update_node(
                    node_coord.parent, node_coord.parentref, value,
                    value_format, encoding)

    # pylint: disable=locally-disabled,too-many-branches,too-many-arguments
    def _get_nodes_by_path_segment(self, data: Any,
                                   yaml_path: YAMLPath, segment_index: int,
                                   parent: Any = None, parentref: Any = None
                                  ) -> Generator[Any, None, None]:
        """
        Get nodes identified by their YAML Path segment.

        Returns zero or more NodeCoords *or* List[NodeCoords] identified by one
        segment of a YAML Path within the present data context.

        Parameters:
        1. data (ruamel.yaml data) The parsed YAML data to process
        2. yaml_path (yamlpath.Path) The YAML Path being processed
        3. segment_index (int) Segment index of the YAML Path to process
        4. parent (ruamel.yaml node) The parent node from which this query
           originates
        5. parentref (Any) The Index or Key of data within parent

        Returns:  (Generator[Any, None, None]) Each node coordinate or list of
        node coordinates as they are matched.  You must check with isinstance()
        to determine whether you have received a NodeCoords or a
        List[NodeCoords].

        Raises:
            - `NotImplementedError` when the segment indicates an unknown
              PathSegmentTypes value.
        """
        if data is None:
            return

        segments = yaml_path.escaped
        if not (segments and len(segments) > segment_index):
            return

        (segment_type, stripped_attrs) = segments[segment_index]

        node_coords: Any = None
        if segment_type == PathSegmentTypes.KEY:
            node_coords = self._get_nodes_by_key(
                data, yaml_path, segment_index)
        elif segment_type == PathSegmentTypes.INDEX:
            node_coords = self._get_nodes_by_index(
                data, yaml_path, segment_index)
        elif segment_type == PathSegmentTypes.ANCHOR:
            node_coords = self._get_nodes_by_anchor(
                data, yaml_path, segment_index)
        elif (
                segment_type == PathSegmentTypes.SEARCH
                and isinstance(stripped_attrs, SearchTerms)
        ):
            node_coords = self._get_nodes_by_search(
                data, stripped_attrs, parent, parentref)
        elif (
                segment_type == PathSegmentTypes.COLLECTOR
                and isinstance(stripped_attrs, CollectorTerms)
        ):
            node_coords = self._get_nodes_by_collector(
                data, yaml_path, segment_index, stripped_attrs,
                parent, parentref)
        else:
            raise NotImplementedError

        for node_coord in node_coords:
            yield node_coord

    def _get_nodes_by_key(
            self, data: Any, yaml_path: YAMLPath, segment_index: int
    ) -> Generator[NodeCoords, None, None]:
        """
        Get nodes from a Hash by their unique key name.

        Returns zero or more NodeCoords identified by a dict key found at a
        specific segment of a YAML Path within the present data context.

        Parameters:
        1. data (ruamel.yaml data) The parsed YAML data to process
        2. yaml_path (yamlpath.Path) The YAML Path being processed
        3. segment_index (int) Segment index of the YAML Path to process

        Returns:  (Generator[NodeCoords, None, None]) Each NodeCoords as they
        are matched

        Raises:  N/A
        """
        (_, stripped_attrs) = yaml_path.escaped[segment_index]
        str_stripped = str(stripped_attrs)

        self.logger.debug(
            "Processor::_get_nodes_by_key:  Seeking KEY node at {}."
            .format(str_stripped)
        )

        if isinstance(data, dict):
            if stripped_attrs in data:
                yield NodeCoords(data[stripped_attrs], data, stripped_attrs)
            else:
                # Check for a string/int type mismatch
                try:
                    intkey = int(str(stripped_attrs))
                    if intkey in data:
                        yield NodeCoords(data[intkey], data, intkey)
                except ValueError:
                    pass
        elif isinstance(data, list):
            try:
                # Try using the ref as a bare Array index
                idx = int(str_stripped)
                if len(data) > idx:
                    yield NodeCoords(data[idx], data, idx)
            except ValueError:
                # Pass-through search against possible Array-of-Hashes
                for eleidx, element in enumerate(data):
                    for node_coord in self._get_nodes_by_path_segment(
                            element, yaml_path, segment_index, data, eleidx):
                        yield node_coord

    # pylint: disable=locally-disabled,too-many-locals
    def _get_nodes_by_index(
            self, data: Any, yaml_path: YAMLPath, segment_index: int
    ) -> Generator[NodeCoords, None, None]:
        """
        Get nodes from a List by their index.

        Returns zero or more NodeCoords identified by a list element index
        found at a specific segment of a YAML Path within the present data
        context.

        Parameters:
        1. data (Any) The parsed YAML data to process
        2. yaml_path (Path) The YAML Path being processed
        3. segment_index (int) Segment index of the YAML Path to process

        Returns:  (Generator[NodeCoords, None, None]) Each NodeCoords as they
        are matched

        Raises:  N/A
        """
        (_, stripped_attrs) = yaml_path.escaped[segment_index]
        (_, unstripped_attrs) = yaml_path.unescaped[segment_index]
        str_stripped = str(stripped_attrs)

        self.logger.debug(
            "Processor::_get_nodes_by_index:  Seeking INDEX node at {}."
            .format(str_stripped)
        )

        if ':' in str_stripped:
            # Array index or Hash key slice
            slice_parts: List[str] = str_stripped.split(':', 1)
            min_match: str = slice_parts[0]
            max_match: str = slice_parts[1]
            if isinstance(data, list):
                try:
                    intmin: int = int(min_match)
                    intmax: int = int(max_match)
                except ValueError:
                    raise YAMLPathException(
                        "{} is not an integer array slice"
                        .format(str_stripped),
                        str(yaml_path),
                        str(unstripped_attrs)
                    )

                if intmin == intmax and len(data) > intmin:
                    yield NodeCoords([data[intmin]], data, intmin)
                else:
                    yield NodeCoords(data[intmin:intmax], data, intmin)

            elif isinstance(data, dict):
                for key, val in data.items():
                    if min_match <= key <= max_match:
                        yield NodeCoords(val, data, key)
        else:
            try:
                idx: int = int(str_stripped)
            except ValueError:
                raise YAMLPathException(
                    "{} is not an integer array index"
                    .format(str_stripped),
                    str(yaml_path),
                    str(unstripped_attrs)
                )

            if isinstance(data, list) and len(data) > idx:
                yield NodeCoords(data[idx], data, idx)

    def _get_nodes_by_anchor(
            self, data: Any, yaml_path: YAMLPath, segment_index: int
    ) -> Generator[NodeCoords, None, None]:
        """
        Get nodes matching an Anchor name.

        Returns zero or more NodeCoords identified by an Anchor name found at a
        specific segment of a YAML Path within the present data context.

        Parameters:
        1. data (Any) The parsed YAML data to process
        2. yaml_path (Path) The YAML Path being processed
        3. segment_index (int) Segment index of the YAML Path to process

        Returns:  (Generator[NodeCoords, None, None]) Each NodeCoords as they
        are matched

        Raises:  N/A
        """
        (_, stripped_attrs) = yaml_path.escaped[segment_index]

        self.logger.debug(
            "Processor::_get_nodes_by_anchor:  Seeking ANCHOR node at {}."
            .format(stripped_attrs)
        )

        if isinstance(data, list):
            for lstidx, ele in enumerate(data):
                if (hasattr(ele, "anchor")
                        and stripped_attrs == ele.anchor.value):
                    yield NodeCoords(ele, data, lstidx)
        elif isinstance(data, dict):
            for key, val in data.items():
                if (hasattr(key, "anchor")
                        and stripped_attrs == key.anchor.value):
                    yield NodeCoords(val, data, key)
                elif (hasattr(val, "anchor")
                      and stripped_attrs == val.anchor.value):
                    yield NodeCoords(val, data, key)

    def _get_nodes_by_search(
            self, data: Any, terms: SearchTerms, parent: Any, parentref: Any
    ) -> Generator[NodeCoords, None, None]:
        """
        Get nodes matching a search expression.

        Searches the the current data context for all NodeCoords matching a
        search expression.

        Parameters:
        1. data (Any) The parsed YAML data to process
        2. terms (SearchTerms) The search terms
        3. parent (ruamel.yaml node) The parent node from which this query
           originates
        4. parentref (Any) The Index or Key of data within parent

        Returns:  (Generator[NodeCoords, None, None]) Each NodeCoords as they
        are matched

        Raises:  N/A
        """
        self.logger.debug(
            ("Processor::_get_nodes_by_search:  Seeking SEARCH nodes matching"
             + " {}.")
            .format(terms)
        )

        invert = terms.inverted
        method = terms.method
        attr = terms.attribute
        term = terms.term
        if isinstance(data, list):
            for lstidx, ele in enumerate(data):
                if attr == '.':
                    matches = search_matches(method, term, ele)
                elif isinstance(ele, dict) and attr in ele:
                    matches = search_matches(method, term, ele[attr])

                if (matches and not invert) or (invert and not matches):
                    yield NodeCoords(ele, data, lstidx)

        elif isinstance(data, dict):
            # Allow . to mean "each key's name"
            if attr == '.':
                for key, val in data.items():
                    matches = search_matches(method, term, key)
                    if (matches and not invert) or (invert and not matches):
                        yield NodeCoords(val, data, key)

            elif attr in data:
                value = data[attr]
                matches = search_matches(method, term, value)
                if (matches and not invert) or (invert and not matches):
                    yield NodeCoords(value, data, attr)

        else:
            # Check the passed data itself for a match
            matches = search_matches(method, term, data)
            if (matches and not invert) or (invert and not matches):
                yield NodeCoords(data, parent, parentref)

    # pylint: disable=locally-disabled,too-many-arguments
    def _get_nodes_by_collector(
            self, data: Any, yaml_path: YAMLPath, segment_index: int,
            terms: CollectorTerms, parent: Any, parentref: Any
    ) -> Generator[List[NodeCoords], None, None]:
        """
        Generate List of nodes gathered via a Collector.

        Returns a list of zero or more NodeCoords within a given data context
        that match an inner YAML Path found at a specific segment of an outer
        YAML Path.

        Parameters:
        1. data (ruamel.yaml data) The parsed YAML data to process
        2. yaml_path (Path) The YAML Path being processed
        3. segment_index (int) Segment index of the YAML Path to process
        4. terms (CollectorTerms) The collector terms
        5. parent (ruamel.yaml node) The parent node from which this query
           originates
        6. parentref (Any) The Index or Key of data within parent

        Returns:  (Generator[List[NodeCoords], None, None]) Each list of
        NodeCoords as they are matched (the result is always a list)

        Raises:  N/A
        """
        if not terms.operation is CollectorOperators.NONE:
            yield data
            return

        node_coords = []    # A list of NodeCoords
        for node_coord in self._get_required_nodes(
                data, YAMLPath(terms.expression), 0, parent, parentref):
            node_coords.append(node_coord)

        # This may end up being a bad idea for some cases, but this method will
        # unwrap all lists that look like `[[value]]` into just `[value]`.
        # When this isn't done, Collector syntax gets burdensome because
        # `(...)[0]` becomes necessary in too many use-cases.  This will be an
        # issue when the user actually expects a list-of-lists as output,
        # though I haven't yet come up with any use-case where a
        # list-of-only-one-list-result is what I really wanted to get from the
        # query.
        if (len(node_coords) == 1
                and isinstance(node_coords[0], NodeCoords)
                and isinstance(node_coords[0].node, list)):
            # Give each element the same parent and its relative index
            node_coord = node_coords[0]
            flat_nodes = []
            for flatten_idx, flatten_node in enumerate(node_coord.node):
                flat_nodes.append(
                    NodeCoords(flatten_node, node_coord.parent, flatten_idx))
            node_coords = flat_nodes

        # As long as each next segment is an ADDITION or SUBTRACTION
        # COLLECTOR, keep combining the results.
        segments = yaml_path.escaped
        next_segment_idx = segment_index + 1

        # pylint: disable=too-many-nested-blocks
        while next_segment_idx < len(segments):
            (peek_type, peek_attrs) = segments[next_segment_idx]
            if (
                    peek_type is PathSegmentTypes.COLLECTOR
                    and isinstance(peek_attrs, CollectorTerms)
            ):
                peek_path: YAMLPath = YAMLPath(peek_attrs.expression)
                if peek_attrs.operation == CollectorOperators.ADDITION:
                    for node_coord in self._get_required_nodes(
                            data, peek_path, 0, parent, parentref):
                        if (isinstance(node_coord, NodeCoords)
                                and isinstance(node_coord.node, list)):
                            for coord_idx, coord in enumerate(node_coord.node):
                                if not isinstance(coord, NodeCoords):
                                    coord = NodeCoords(
                                        coord, node_coord.node, coord_idx)
                                node_coords.append(coord)
                        else:
                            node_coords.append(node_coord)
                elif peek_attrs.operation == CollectorOperators.SUBTRACTION:
                    rem_data = []
                    for node_coord in self._get_required_nodes(
                            data, peek_path, 0, parent, parentref):
                        unwrapped_data = unwrap_node_coords(node_coord)
                        if isinstance(unwrapped_data, list):
                            for unwrapped_datum in unwrapped_data:
                                rem_data.append(unwrapped_datum)
                        else:
                            rem_data.append(unwrapped_data)

                    node_coords = [e for e in node_coords
                                   if unwrap_node_coords(e) not in rem_data]
                else:
                    raise YAMLPathException(
                        "Adjoining Collectors without an operator has no"
                        + " meaning; try + or - between them",
                        str(yaml_path),
                        str(peek_path)
                    )
            else:
                break  # pragma: no cover

            next_segment_idx += 1

        # yield only when there are results
        if node_coords:
            yield node_coords

    def _get_required_nodes(self, data: Any, yaml_path: YAMLPath,
                            depth: int = 0, parent: Any = None,
                            parentref: Any = None
                            ) -> Generator[NodeCoords, None, None]:
        """
        Generate pre-existing NodeCoords from YAML data matching a YAML Path.

        Parameters:
        1. data (Any) The parsed YAML data to process
        2. yaml_path (Path) The pre-parsed YAML Path to follow
        3. depth (int) Index within yaml_path to process; default=0
        4. parent (ruamel.yaml node) The parent node from which this query
           originates
        5. parentref (Any) Key or Index of data within parent

        Returns:  (Generator[NodeCoords, None, None]) The requested NodeCoords
        as they are matched

        Raises:  N/A
        """
        if data is None:
            return

        segments = yaml_path.escaped
        if segments and len(segments) > depth:
            (segment_type, unstripped_attrs) = yaml_path.unescaped[depth]
            except_segment = str(unstripped_attrs)
            self.logger.debug(
                ("Processor::_get_required_nodes:  "
                 + "Seeking segment <{}>{} in"
                 + " data of type {}:")
                .format(segment_type, except_segment, type(data))
            )
            self.logger.debug(data)
            self.logger.debug("")

            for segment_node_coords in self._get_nodes_by_path_segment(
                    data, yaml_path, depth, parent, parentref):
                self.logger.debug(
                    ("Processor::_get_required_nodes:  "
                     + "Found node of type {} at <{}>{} in"
                     + " the data and recursing into it...")
                    .format(type(segment_node_coords), segment_type,
                            except_segment)
                )
                self.logger.debug(segment_node_coords)

                if isinstance(segment_node_coords, list):
                    # Most likely the output of a Collector, this list will be
                    # of NodeCoords rather than an actual DOM reference.  As
                    # such, it must be treated as a virtual DOM element that
                    # cannot itself be parented to the real DOM, though each
                    # of its elements has a real parent.
                    for subnode_coord in self._get_required_nodes(
                            segment_node_coords, yaml_path, depth + 1,
                            None, None):
                        yield subnode_coord
                else:
                    for subnode_coord in self._get_required_nodes(
                            segment_node_coords.node, yaml_path, depth + 1,
                            segment_node_coords.parent,
                            segment_node_coords.parentref):
                        yield subnode_coord
        else:
            self.logger.debug(
                ("Processor::_get_required_nodes:  "
                 + "Finally returning data of"
                 + " type {} at parentref {}:")
                .format(type(data), parentref)
            )
            self.logger.debug(data)
            self.logger.debug("")

            yield NodeCoords(data, parent, parentref)

    # pylint: disable=locally-disabled,too-many-statements,too-many-arguments
    def _get_optional_nodes(
            self, data: Any, yaml_path: YAMLPath, value: Any = None,
            depth: int = 0, parent: Any = None, parentref: Any = None
    ) -> Generator[NodeCoords, None, None]:
        """
        Return zero or more pre-existing NodeCoords matching a YAML Path.

        Will create nodes that are missing, as long as any missing segments are
        deterministic (SEARCH and COLLECTOR segments are non-deterministic).

        Parameters:
        1. data (Any) The parsed YAML data to process
        2. yaml_path (Path) The pre-parsed YAML Path to follow
        3. value (Any) The value to assign to the element
        4. depth (int) For recursion, this identifies which segment of
           yaml_path to evaluate; default=0
        5. parent (ruamel.yaml node) The parent node from which this query
           originates
        6. parentref (Any) Index or Key of data within parent

        Returns:  (Generator[NodeCoords, None, None]) The requested NodeCoords
        as they are matched

        Raises:
        - `YAMLPathException` when the YAML Path is invalid.
        - `NotImplementedError` when a segment of the YAML Path indicates
          an element that does not exist in data and this code isn't
          yet prepared to add it.
        """
        if data is None:
            self.logger.debug(
                "Processor::_get_optional_nodes:  Bailing out on None"
                + " data/path!"
            )
            return

        segments = yaml_path.escaped
        # pylint: disable=locally-disabled,too-many-nested-blocks
        if segments and len(segments) > depth:
            (segment_type, unstripped_attrs) = yaml_path.unescaped[depth]
            stripped_attrs: Union[
                str,
                int,
                SearchTerms,
                CollectorTerms
            ] = segments[depth][1]
            except_segment = str(unstripped_attrs)

            self.logger.debug(
                ("Processor::_get_optional_nodes:  Seeking element <{}>{} in"
                 + " data of type {}:"
                ).format(segment_type, except_segment, type(data))
            )
            self.logger.debug(data)
            self.logger.debug("")

            # The next element may not exist; this method ensures that it does
            matched_nodes = 0
            for next_coord in self._get_nodes_by_path_segment(
                    data, yaml_path, depth, parent, parentref
            ):
                matched_nodes += 1
                self.logger.debug(
                    ("Processor::_get_optional_nodes:  Found element <{}>{} in"
                     + " the data; recursing into it..."
                    ).format(segment_type, except_segment)
                )
                for node_coord in self._get_optional_nodes(
                        next_coord.node, yaml_path, value, depth + 1,
                        next_coord.parent, next_coord.parentref
                ):
                    yield node_coord

            if (
                    matched_nodes < 1
                    and segment_type is not PathSegmentTypes.SEARCH
            ):
                # Add the missing element
                self.logger.debug(
                    ("Processor::_get_optional_nodes:  Element <{}>{} is"
                     + " unknown in the data!  Applying default, <{}>{}."
                    ).format(segment_type, except_segment, type(value), value)
                )
                if isinstance(data, list):
                    self.logger.debug(
                        "Processor::_get_optional_nodes:  Dealing with a list"
                    )
                    if (
                            segment_type is PathSegmentTypes.ANCHOR
                            and isinstance(stripped_attrs, str)
                    ):
                        next_node = build_next_node(
                            yaml_path, depth + 1, value
                        )
                        new_ele = append_list_element(
                            data, next_node, stripped_attrs
                        )
                        for node_coord in self._get_optional_nodes(
                                new_ele, yaml_path, value, depth + 1,
                                data, len(data) - 1
                        ):
                            matched_nodes += 1
                            yield node_coord
                    elif (
                            segment_type in [
                                PathSegmentTypes.INDEX,
                                PathSegmentTypes.KEY]
                    ):
                        if isinstance(stripped_attrs, int):
                            newidx = stripped_attrs
                        else:
                            try:
                                newidx = int(str(stripped_attrs))
                            except ValueError:
                                raise YAMLPathException(
                                    ("Cannot add non-integer {} subreference"
                                     + " to lists")
                                    .format(str(segment_type)),
                                    str(yaml_path),
                                    except_segment
                                )
                        for _ in range(len(data) - 1, newidx):
                            next_node = build_next_node(
                                yaml_path, depth + 1, value
                            )
                            append_list_element(data, next_node)
                        for node_coord in self._get_optional_nodes(
                                data[newidx], yaml_path, value,
                                depth + 1, data, newidx
                        ):
                            matched_nodes += 1
                            yield node_coord
                    else:
                        raise YAMLPathException(
                            "Cannot add {} subreference to lists"
                            .format(str(segment_type)),
                            str(yaml_path),
                            except_segment
                        )
                elif isinstance(data, dict):
                    self.logger.debug(
                        "Processor::_get_optional_nodes:  Dealing with a"
                        + " dictionary"
                    )
                    if segment_type is PathSegmentTypes.ANCHOR:
                        raise YAMLPathException(
                            "Cannot add ANCHOR keys",
                            str(yaml_path),
                            str(unstripped_attrs)
                        )
                    if segment_type is PathSegmentTypes.KEY:
                        data[stripped_attrs] = build_next_node(
                            yaml_path, depth + 1, value
                        )
                        for node_coord in self._get_optional_nodes(
                                data[stripped_attrs], yaml_path, value,
                                depth + 1, data, stripped_attrs
                        ):
                            matched_nodes += 1
                            yield node_coord
                    else:
                        raise YAMLPathException(
                            "Cannot add {} subreference to dictionaries"
                            .format(str(segment_type)),
                            str(yaml_path),
                            except_segment
                        )
                else:
                    raise YAMLPathException(
                        "Cannot add {} subreference to scalars".format(
                            str(segment_type)
                        ),
                        str(yaml_path),
                        except_segment
                    )

        else:
            self.logger.debug(
                ("Processor::_get_optional_nodes:  Finally returning data of"
                 + " type {}:"
                ).format(type(data))
            )
            self.logger.debug(data)

            yield NodeCoords(data, parent, parentref)

    def _update_node(self, parent: Any, parentref: Any, value: Any,
                     value_format: YAMLValueFormats, encoding: str) -> None:
        """
        Set the value of a data node.

        Recursively updates the value of a YAML Node and any references to it
        within the entire YAML data structure (Anchors and Aliases, if any).

        Parameters:
        1. parent (ruamel.yaml data) The parent of the node to change
        2. parent_ref (Any) Index or Key of the value within parent_node to
           change
        3. value (any) The new value to assign to the source_node and
           its references
        4. value_format (YAMLValueFormats) the YAML representation of the
           value

        Returns: N/A

        Raises: N/A
        """
        # This update_refs function was contributed by Anthon van der Neut, the
        # author of ruamel.yaml, to resolve how to update all references to an
        # Anchor throughout the parsed data structure.
        def recurse(data, parent, parentref, reference_node, replacement_node):
            if isinstance(data, dict):
                for i, k in [
                        (idx, key) for idx, key in
                        enumerate(data.keys()) if key is reference_node
                ]:
                    data.insert(i, replacement_node, data.pop(k))
                for k, val in data.non_merged_items():
                    if val is reference_node:
                        if (hasattr(val, "anchor") or
                                (data is parent and k == parentref)):
                            data[k] = replacement_node
                    else:
                        recurse(val, parent, parentref, reference_node,
                                replacement_node)
            elif isinstance(data, list):
                for idx, item in enumerate(data):
                    if item is reference_node:
                        data[idx] = replacement_node
                    else:
                        recurse(item, parent, parentref, reference_node,
                                replacement_node)

        change_node = parent[parentref]
        new_node = make_new_node(change_node, value, value_format, encoding)
        recurse(self.data, parent, parentref, change_node, new_node)
