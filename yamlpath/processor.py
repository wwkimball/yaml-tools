#pylint: disable=too-many-lines
"""
YAML Path processor based on ruamel.yaml.

Copyright 2018, 2019, 2020 William W. Kimball, Jr. MBA MSIS
"""
from typing import Any, Generator, List, Union

from yamlpath.common import Nodes, Searches
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
            self.logger.debug(
                "Refusing to get nodes from a null document!",
                prefix="Processor::get_nodes:  ", data=self.data)
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
                    "Relaying required node:",
                    prefix="Processor::get_nodes:  ", data=node_coords)
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
                    "Relaying optional node:",
                    prefix="Processor::get_nodes:  ", data=opt_node)
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
        * tag (str) Custom data-type tag to assign

        Returns:  N/A

        Raises:
            - `YAMLPathException` when YAML Path is invalid
        """
        if self.data is None:
            self.logger.debug(
                "Refusing to set nodes of a null document!",
                prefix="Processor::set_nodes:  ", data=self.data)
            return

        mustexist: bool = kwargs.pop("mustexist", False)
        value_format: YAMLValueFormats = kwargs.pop("value_format",
                                                    YAMLValueFormats.DEFAULT)
        pathsep: PathSeperators = kwargs.pop("pathsep", PathSeperators.AUTO)
        tag: str = kwargs.pop("tag", None)

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
            for req_node in self._get_required_nodes(self.data, yaml_path):
                found_nodes += 1
                if isinstance(req_node.node, list):
                    for req_ele in req_node.node:
                        self.logger.debug(
                            "Submitting required node element for change:",
                            prefix="Processor::set_value:  ", data=req_ele)
                        try:
                            if isinstance(req_ele.node, NodeCoords):
                                self._update_node(
                                    req_ele.node.parent,
                                    req_ele.node.parentref,
                                    value, value_format, tag)
                            else:
                                self._update_node(
                                    req_ele.parent, req_ele.parentref, value,
                                    value_format, tag)
                        except ValueError as vex:
                            raise YAMLPathException(
                                "Impossible to write '{}' as {}.  The error"
                                " was:  {}".format(
                                    value, value_format, str(vex))
                                , str(yaml_path)) from vex
                else:
                    self.logger.debug(
                        "Submitting required node for change:",
                        prefix="Processor::set_value:  ", data=req_node)
                    try:
                        if isinstance(req_node.node, NodeCoords):
                            self._update_node(
                                req_node.node.parent, req_node.node.parentref,
                                value, value_format, tag)
                        else:
                            self._update_node(
                                req_node.parent, req_node.parentref, value,
                                value_format, tag)
                    except ValueError as vex:
                        raise YAMLPathException(
                            "Impossible to write '{}' as {}.  The error was:  {}"
                            .format(value, value_format, str(vex))
                            , str(yaml_path)) from vex

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
                    "Matched optional node coordinate:"
                    , data=node_coord
                    , prefix="Processor::set_value:  ")
                self.logger.debug(
                    "Setting its value with format {} to:".format(value_format)
                    , data=value
                    , prefix="Processor::set_value:  ")
                try:
                    if isinstance(node_coord.node, NodeCoords):
                        self._update_node(
                            node_coord.node.parent, node_coord.node.parentref,
                            value, value_format, tag)
                    else:
                        self._update_node(
                            node_coord.parent, node_coord.parentref, value,
                            value_format, tag)
                except ValueError as vex:
                    raise YAMLPathException(
                        "Impossible to write '{}' as {}.  The error was:  {}"
                        .format(value, value_format, str(vex))
                        , str(yaml_path)) from vex

    # pylint: disable=locally-disabled,too-many-branches,too-many-locals
    def _get_nodes_by_path_segment(self, data: Any,
                                   yaml_path: YAMLPath, segment_index: int,
                                   **kwargs: Any
                                  ) -> Generator[Any, None, None]:
        """
        Get nodes identified by their YAML Path segment.

        Returns zero or more NodeCoords *or* List[NodeCoords] identified by one
        segment of a YAML Path within the present data context.

        Parameters:
        1. data (ruamel.yaml data) The parsed YAML data to process
        2. yaml_path (yamlpath.Path) The YAML Path being processed
        3. segment_index (int) Segment index of the YAML Path to process

        Keyword Arguments:
        * parent (ruamel.yaml node) The parent node from which this query
          originates
        * parentref (Any) The Index or Key of data within parent
        * traverse_lists (Boolean) Indicate whether KEY searches against lists
          are permitted to automatically traverse into the list; Default=True

        Returns:  (Generator[Any, None, None]) Each node coordinate or list of
        node coordinates as they are matched.  You must check with isinstance()
        to determine whether you have received a NodeCoords or a
        List[NodeCoords].

        Raises:
            - `NotImplementedError` when the segment indicates an unknown
              PathSegmentTypes value.
        """
        parent = kwargs.pop("parent", None)
        parentref = kwargs.pop("parentref", None)
        traverse_lists = kwargs.pop("traverse_lists", True)
        translated_path = kwargs.pop("translated_path", YAMLPath(""))
        if data is None:
            self.logger.debug(
                "Bailing out on None data at parentref, {}, of parent:"
                .format(parentref),
                prefix="Processor::_get_nodes_by_path_segment:  ",
                data=parent)
            return

        segments = yaml_path.escaped
        if not (segments and len(segments) > segment_index):
            self.logger.debug(
                "Bailing out because there are not {} segments in:"
                .format(segment_index),
                prefix="Processor::_get_nodes_by_path_segment:  ",
                data=segments)
            return

        (segment_type, stripped_attrs) = segments[segment_index]
        (unesc_type, unesc_attrs) = yaml_path.unescaped[segment_index]

        # Disallow traversal recursion (because it creates a denial-of-service)
        if segment_index > 0 and segment_type == PathSegmentTypes.TRAVERSE:
            (prior_segment_type, _) = segments[segment_index - 1]
            if prior_segment_type == PathSegmentTypes.TRAVERSE:
                raise YAMLPathException(
                    "Repeating traversals are not allowed because they cause"
                    " recursion which leads to excessive CPU and RAM"
                    " consumption while yielding no additional useful data",
                    str(yaml_path), "**")

        node_coords: Any = None
        if segment_type == PathSegmentTypes.KEY:
            node_coords = self._get_nodes_by_key(
                data, yaml_path, segment_index, traverse_lists=traverse_lists,
                translated_path=translated_path)
        elif segment_type == PathSegmentTypes.INDEX:
            node_coords = self._get_nodes_by_index(
                data, yaml_path, segment_index,
                translated_path=translated_path)
        elif segment_type == PathSegmentTypes.ANCHOR:
            node_coords = self._get_nodes_by_anchor(
                data, yaml_path, segment_index,
                translated_path=translated_path)
        elif (
                segment_type == PathSegmentTypes.SEARCH
                and isinstance(stripped_attrs, SearchTerms)
        ):
            node_coords = self._get_nodes_by_search(
                data, stripped_attrs, parent=parent, parentref=parentref,
                traverse_lists=traverse_lists, translated_path=translated_path)
        elif (
                unesc_type == PathSegmentTypes.COLLECTOR
                and isinstance(unesc_attrs, CollectorTerms)
        ):
            node_coords = self._get_nodes_by_collector(
                data, yaml_path, segment_index, unesc_attrs, parent=parent,
                parentref=parentref, translated_path=translated_path)
        elif segment_type == PathSegmentTypes.TRAVERSE:
            node_coords = self._get_nodes_by_traversal(
                data, yaml_path, segment_index, parent=parent,
                parentref=parentref, translated_path=translated_path)
        else:
            raise NotImplementedError

        for node_coord in node_coords:
            yield node_coord

    def _get_nodes_by_key(
            self, data: Any, yaml_path: YAMLPath, segment_index: int,
            **kwargs: Any
    ) -> Generator[NodeCoords, None, None]:
        """
        Get nodes from a Hash by their unique key name.

        Returns zero or more NodeCoords identified by a dict key found at a
        specific segment of a YAML Path within the present data context.

        Parameters:
        1. data (ruamel.yaml data) The parsed YAML data to process
        2. yaml_path (yamlpath.Path) The YAML Path being processed
        3. segment_index (int) Segment index of the YAML Path to process

        Keyword Arguments:
        * traverse_lists (Boolean) Indicate whether KEY searches against lists
          are permitted to automatically traverse into the list; Default=True

        Returns:  (Generator[NodeCoords, None, None]) Each NodeCoords as they
        are matched

        Raises:  N/A
        """
        traverse_lists = kwargs.pop("traverse_lists", True)
        translated_path = kwargs.pop("translated_path", YAMLPath(""))

        (_, stripped_attrs) = yaml_path.escaped[segment_index]
        str_stripped = str(stripped_attrs)

        self.logger.debug(
            "Processor::_get_nodes_by_key:  Seeking KEY node at {}."
            .format(str_stripped))

        if isinstance(data, dict):
            next_translated_path = (translated_path +
                YAMLPath.escape_path_section(
                    str_stripped, translated_path.seperator))
            if stripped_attrs in data:
                yield NodeCoords(
                    data[stripped_attrs], data, stripped_attrs,
                    next_translated_path)
            else:
                # Check for a string/int type mismatch
                try:
                    intkey = int(str_stripped)
                    if intkey in data:
                        yield NodeCoords(
                            data[intkey], data, intkey, next_translated_path)
                except ValueError:
                    pass
        elif isinstance(data, list):
            try:
                # Try using the ref as a bare Array index
                idx = int(str_stripped)
                if len(data) > idx:
                    yield NodeCoords(
                        data[idx], data, idx,
                        translated_path + "[{}]".format(idx))
            except ValueError:
                # Pass-through search against possible Array-of-Hashes, if
                # allowed.
                if not traverse_lists:
                    self.logger.debug(
                        "Processor::_get_nodes_by_key:  Refusing to traverse a"
                        " list.")
                    return

                for eleidx, element in enumerate(data):
                    next_translated_path = translated_path + "[{}]".format(
                        eleidx)
                    for node_coord in self._get_nodes_by_path_segment(
                            element, yaml_path, segment_index, parent=data,
                            parentref=eleidx, traverse_lists=traverse_lists,
                            translated_path=next_translated_path):
                        yield node_coord

    # pylint: disable=locally-disabled,too-many-locals
    def _get_nodes_by_index(
            self, data: Any, yaml_path: YAMLPath, segment_index: int, **kwargs
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
        translated_path = kwargs.pop("translated_path", YAMLPath(""))

        self.logger.debug(
            "Processor::_get_nodes_by_index:  Seeking INDEX node at {}."
            .format(str_stripped))

        if ':' in str_stripped:
            # Array index or Hash key slice
            slice_parts: List[str] = str_stripped.split(':', 1)
            min_match: str = slice_parts[0]
            max_match: str = slice_parts[1]
            if isinstance(data, list):
                try:
                    intmin: int = int(min_match)
                    intmax: int = int(max_match)
                except ValueError as wrap_ex:
                    raise YAMLPathException(
                        "{} is not an integer array slice"
                        .format(str_stripped),
                        str(yaml_path),
                        str(unstripped_attrs)
                    ) from wrap_ex

                if intmin == intmax and len(data) > intmin:
                    yield NodeCoords(
                        [data[intmin]], data, intmin,
                        translated_path + "[{}]".format(intmin))
                else:
                    sliced_elements = []
                    for slice_index in range(intmin, intmax):
                        sliced_elements.append(NodeCoords(
                            data[slice_index], data, intmin,
                            translated_path + "[{}]".format(slice_index)))
                    yield NodeCoords(
                        sliced_elements, data, intmin,
                        translated_path + "[{}:{}]".format(intmin, intmax))

            elif isinstance(data, dict):
                for key, val in data.items():
                    if min_match <= key <= max_match:
                        yield NodeCoords(
                            val, data, key,
                            translated_path + YAMLPath.escape_path_section(
                                key, translated_path.seperator))
        else:
            try:
                idx: int = int(str_stripped)
            except ValueError as wrap_ex:
                raise YAMLPathException(
                    "{} is not an integer array index"
                    .format(str_stripped),
                    str(yaml_path),
                    str(unstripped_attrs)
                ) from wrap_ex

            if isinstance(data, list) and len(data) > idx:
                yield NodeCoords(
                    data[idx], data, idx, translated_path + "[{}]".format(idx))

    def _get_nodes_by_anchor(
            self, data: Any, yaml_path: YAMLPath, segment_index: int, **kwargs
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
        translated_path = kwargs.pop("translated_path", YAMLPath(""))
        next_translated_path = translated_path + "[&{}]".format(
            YAMLPath.escape_path_section(
                str(stripped_attrs), translated_path.seperator))

        self.logger.debug(
            "Processor::_get_nodes_by_anchor:  Seeking ANCHOR node at {}."
            .format(stripped_attrs))

        if isinstance(data, list):
            for lstidx, ele in enumerate(data):
                if (hasattr(ele, "anchor")
                        and stripped_attrs == ele.anchor.value):
                    yield NodeCoords(ele, data, lstidx, next_translated_path)
        elif isinstance(data, dict):
            for key, val in data.items():
                if (hasattr(key, "anchor")
                        and stripped_attrs == key.anchor.value):
                    yield NodeCoords(val, data, key, next_translated_path)
                elif (hasattr(val, "anchor")
                      and stripped_attrs == val.anchor.value):
                    yield NodeCoords(val, data, key, next_translated_path)

    # pylint: disable=too-many-statements
    def _get_nodes_by_search(
            self, data: Any, terms: SearchTerms, **kwargs: Any
    ) -> Generator[NodeCoords, None, None]:
        """
        Get nodes matching a search expression.

        Searches the the current data context for all NodeCoords matching a
        search expression.

        Parameters:
        1. data (Any) The parsed YAML data to process
        2. terms (SearchTerms) The search terms

        Keyword Arguments:
        * parent (ruamel.yaml node) The parent node from which this query
          originates
        * parentref (Any) The Index or Key of data within parent
        * traverse_lists (Boolean) Indicate whether searches against lists are
          permitted to automatically traverse into the list; Default=True

        Returns:  (Generator[NodeCoords, None, None]) Each NodeCoords as they
        are matched

        Raises:  N/A
        """
        self.logger.debug(
            "Seeking SEARCH nodes matching {} in data:".format(terms),
            data=data,
            prefix="Processor::_get_nodes_by_search:  ")

        parent = kwargs.pop("parent", None)
        parentref = kwargs.pop("parentref", None)
        traverse_lists = kwargs.pop("traverse_lists", True)
        translated_path = kwargs.pop("translated_path", YAMLPath(""))
        invert = terms.inverted
        method = terms.method
        attr = terms.attribute
        term = terms.term
        matches = False
        desc_path = YAMLPath(attr)
        if isinstance(data, list):
            if not traverse_lists:
                self.logger.debug(
                    "Processor::_get_nodes_by_search:  Refusing to traverse a"
                    " list.")
                return

            for lstidx, ele in enumerate(data):
                if attr == '.':
                    matches = Searches.search_matches(method, term, ele)
                elif isinstance(ele, dict) and attr in ele:
                    matches = Searches.search_matches(method, term, ele[attr])
                else:
                    # Attempt a descendant search
                    next_translated_path = translated_path + "[{}]".format(
                        lstidx)
                    for desc_node in self._get_required_nodes(
                        ele, desc_path, 0, translated_path=next_translated_path
                    ):
                        matches = Searches.search_matches(
                            method, term, desc_node.node)
                        break

                if (matches and not invert) or (invert and not matches):
                    self.logger.debug(
                        "Yielding list match at index {}:".format(lstidx),
                        data=ele,
                        prefix="Processor::_get_nodes_by_search:  ")
                    yield NodeCoords(
                        ele, data, lstidx,
                        translated_path + "[{}]".format(lstidx))

        elif isinstance(data, dict):
            # Allow . to mean "each key's name"
            if attr == '.':
                for key, val in data.items():
                    matches = Searches.search_matches(method, term, key)
                    if (matches and not invert) or (invert and not matches):
                        self.logger.debug(
                            "Yielding dictionary key name match against '{}':"
                            .format(key),
                            data=val,
                            prefix="Processor::_get_nodes_by_search:  ")
                        yield NodeCoords(
                            val, data, key,
                            translated_path + YAMLPath.escape_path_section(
                                key, translated_path.seperator))

            elif attr in data:
                value = data[attr]
                matches = Searches.search_matches(method, term, value)
                if (matches and not invert) or (invert and not matches):
                    self.logger.debug(
                        "Yielding dictionary attribute match against '{}':"
                        .format(attr),
                        data=value,
                        prefix="Processor::_get_nodes_by_search:  ")
                    yield NodeCoords(
                        value, data, attr,
                        translated_path + YAMLPath.escape_path_section(
                            attr, translated_path.seperator))

            else:
                # Attempt a descendant search
                for desc_node in self._get_required_nodes(
                    data, desc_path, 0, parent=parent, parentref=parentref,
                    translated_path=translated_path
                ):
                    matches = Searches.search_matches(
                        method, term, desc_node.node)
                    break

                if (matches and not invert) or (invert and not matches):
                    yield NodeCoords(data, parent, parentref, translated_path)

        else:
            # Check the passed data itself for a match
            matches = Searches.search_matches(method, term, data)
            if (matches and not invert) or (invert and not matches):
                self.logger.debug(
                    "Yielding the queried data itself because it matches.",
                    prefix="Processor::_get_nodes_by_search:  ")
                yield NodeCoords(data, parent, parentref, translated_path)

    # pylint: disable=locally-disabled
    def _get_nodes_by_collector(
            self, data: Any, yaml_path: YAMLPath, segment_index: int,
            terms: CollectorTerms, **kwargs: Any
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

        Keyword Arguments:
        * parent (ruamel.yaml node) The parent node from which this query
          originates
        * parentref (Any) The Index or Key of data within parent

        Returns:  (Generator[List[NodeCoords], None, None]) Each list of
        NodeCoords as they are matched (the result is always a list)

        Raises:  N/A
        """
        if not terms.operation is CollectorOperators.NONE:
            yield data
            return

        parent = kwargs.pop("parent", None)
        parentref = kwargs.pop("parentref", None)
        translated_path = kwargs.pop("translated_path", YAMLPath(""))
        node_coords = []    # A list of NodeCoords
        self.logger.debug(
            "Processor::_get_nodes_by_collector:  Getting required nodes"
            " matching search expression:  {}".format(terms.expression))
        for node_coord in self._get_required_nodes(
                data, YAMLPath(terms.expression), 0, parent=parent,
                parentref=parentref, translated_path=translated_path):
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
                    NodeCoords(
                        flatten_node, node_coord.parent, flatten_idx,
                        node_coord.path))
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
                            data, peek_path, 0, parent=parent,
                            parentref=parentref,
                            translated_path=translated_path):
                        if (isinstance(node_coord, NodeCoords)
                                and isinstance(node_coord.node, list)):
                            for coord_idx, coord in enumerate(node_coord.node):
                                if not isinstance(coord, NodeCoords):
                                    next_translated_path = node_coord.path
                                    if next_translated_path is not None:
                                        next_translated_path = (
                                            next_translated_path +
                                            "[{}]".format(coord_idx))
                                    coord = NodeCoords(
                                        coord, node_coord.node, coord_idx,
                                        next_translated_path)
                                node_coords.append(coord)
                        else:
                            node_coords.append(node_coord)
                elif peek_attrs.operation == CollectorOperators.SUBTRACTION:
                    rem_data = []
                    for node_coord in self._get_required_nodes(
                            data, peek_path, 0, parent=parent,
                            parentref=parentref,
                            translated_path=translated_path):
                        unwrapped_data = NodeCoords.unwrap_node_coords(
                            node_coord)
                        if isinstance(unwrapped_data, list):
                            for unwrapped_datum in unwrapped_data:
                                rem_data.append(unwrapped_datum)
                        else:
                            rem_data.append(unwrapped_data)

                    node_coords = [e for e in node_coords
                                   if NodeCoords.unwrap_node_coords(e)
                                   not in rem_data]
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

    # pylint: disable=locally-disabled,too-many-branches
    def _get_nodes_by_traversal(self, data: Any, yaml_path: YAMLPath,
                                segment_index: int, **kwargs: Any
                                ) -> Generator[Any, None, None]:
        """
        Deeply traverse the document tree, returning all or filtered nodes.

        Parameters:
        1. data (ruamel.yaml data) The parsed YAML data to process
        2. yaml_path (yamlpath.Path) The YAML Path being processed
        3. segment_index (int) Segment index of the YAML Path to process

        Keyword Parameters:
        * parent (ruamel.yaml node) The parent node from which this query
          originates
        * parentref (Any) The Index or Key of data within parent

        Returns:  (Generator[Any, None, None]) Each node coordinate as they are
        matched.
        """
        parent = kwargs.pop("parent", None)
        parentref = kwargs.pop("parentref", None)
        translated_path = kwargs.pop("translated_path", YAMLPath(""))

        self.logger.debug(
            "TRAVERSING the tree at parentref:",
            prefix="Processor::_get_nodes_by_traversal:  ", data=parentref)

        if data is None:
            self.logger.debug(
                "Processor::_get_nodes_by_traversal:  Yielding a None node.")
            yield NodeCoords(None, parent, parentref)
            return

        # Is there a next segment?
        segments = yaml_path.escaped
        if segment_index + 1 == len(segments):
            # This traversal is gathering every leaf node
            if isinstance(data, dict):
                for key, val in data.items():
                    next_translated_path = (
                        translated_path + YAMLPath.escape_path_section(
                            key, translated_path.seperator))
                    for node_coord in self._get_nodes_by_traversal(
                        val, yaml_path, segment_index,
                        parent=data, parentref=key,
                        translated_path=next_translated_path
                    ):
                        self.logger.debug(
                            "Yielding unfiltered Hash value:",
                            prefix="Processor::_get_nodes_by_traversal:  ",
                            data=node_coord)
                        yield node_coord
            elif isinstance(data, list):
                for idx, ele in enumerate(data):
                    next_translated_path = translated_path + "[{}]".format(idx)
                    for node_coord in self._get_nodes_by_traversal(
                        ele, yaml_path, segment_index,
                        parent=data, parentref=idx,
                        translated_path=next_translated_path
                    ):
                        self.logger.debug(
                            "Yielding unfiltered Array value:",
                            prefix="Processor::_get_nodes_by_traversal:  ",
                            data=node_coord)
                        yield node_coord
            else:
                self.logger.debug(
                    "Yielding unfiltered Scalar value:",
                    prefix="Processor::_get_nodes_by_traversal:  ", data=data)
                yield NodeCoords(data, parent, parentref, translated_path)
        else:
            # There is a filter in the next segment; recurse data, comparing
            # every child against the following segment until there are no more
            # nodes.  For each match, resume normal path function against the
            # matching node(s).

            # Because the calling code will continue to process the remainder
            # of the YAML Path, only the parent of the matched node(s) can be
            # yielded.
            self.logger.debug(
                "Processor::_get_nodes_by_traversal:  Checking the DIRECT node"
                " for a next-segment match at {}...".format(parentref))
            for node_coord in self._get_nodes_by_path_segment(
                data, yaml_path, segment_index + 1, parent=parent,
                parentref=parentref, traverse_lists=False,
                translated_path=translated_path
            ):
                self.logger.debug(
                    "Yielding filtered DIRECT node at parentref {} of coord:"
                    .format(parentref),
                    prefix="Processor::_get_nodes_by_traversal:  ",
                    data=node_coord)
                yield NodeCoords(data, parent, parentref, translated_path)

            # Then, recurse into each child to perform the same test.
            if isinstance(data, dict):
                for key, val in data.items():
                    self.logger.debug(
                        "Processor::_get_nodes_by_traversal:  Recursing into"
                        " KEY '{}' at ref '{}' for next-segment matches..."
                        .format(key, parentref))
                    next_translated_path = (
                        translated_path + YAMLPath.escape_path_section(
                            key, translated_path.seperator))
                    for node_coord in self._get_nodes_by_traversal(
                        val, yaml_path, segment_index,
                        parent=data, parentref=key,
                        translated_path=next_translated_path
                    ):
                        self.logger.debug(
                            "Yielding filtered indirect Hash value from KEY"
                            " '{}' at ref '{}':".format(key, parentref),
                            prefix="Processor::_get_nodes_by_traversal:  ",
                            data=node_coord.node)
                        yield node_coord
            elif isinstance(data, list):
                for idx, ele in enumerate(data):
                    self.logger.debug(
                        "Processor::_get_nodes_by_traversal:  Recursing into"
                        " INDEX '{}' at ref '{}' for next-segment matches..."
                        .format(idx, parentref))
                    next_translated_path = translated_path + "[{}]".format(idx)
                    for node_coord in self._get_nodes_by_traversal(
                        ele, yaml_path, segment_index,
                        parent=data, parentref=idx,
                        translated_path=next_translated_path
                    ):
                        self.logger.debug(
                            "Yielding filtered indirect Array value from INDEX"
                            " {} at {}:".format(idx, parentref),
                            prefix="Processor::_get_nodes_by_traversal:  ",
                            data=node_coord)
                        yield node_coord

    def _get_required_nodes(self, data: Any, yaml_path: YAMLPath,
                            depth: int = 0, **kwargs: Any
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
        parent = kwargs.pop("parent", None)
        parentref = kwargs.pop("parentref", None)
        translated_path = kwargs.pop("translated_path", YAMLPath(""))

        if data is None:
            self.logger.debug(
                "Bailing out on None data at parentref, {}, of parent:"
                .format(parentref),
                prefix="Processor::_get_required_nodes:  ",
                data=parent)
            return

        segments = yaml_path.escaped
        if segments and len(segments) > depth:
            (segment_type, unstripped_attrs) = yaml_path.unescaped[depth]
            except_segment = str(unstripped_attrs)
            self.logger.debug(
                "Seeking segment <{}>{} in data of type {}:"
                .format(segment_type, except_segment, type(data)),
                prefix="Processor::_get_required_nodes:  ",
                data=data, footer=" ")

            for segment_node_coords in self._get_nodes_by_path_segment(
                data, yaml_path, depth, parent=parent, parentref=parentref,
                translated_path=translated_path
            ):
                self.logger.debug(
                    "Found node of type {} at <{}>{} in the data and recursing"
                    " into it..."
                    .format(
                        type(segment_node_coords.node
                             if hasattr(segment_node_coords, "node")
                             else segment_node_coords),
                        segment_type,
                        except_segment),
                    prefix="Processor::_get_required_nodes:  ",
                    data=segment_node_coords)

                if (segment_node_coords is None
                    or (hasattr(segment_node_coords, "node")
                        and segment_node_coords.node is None)
                ):
                    self.logger.debug(
                        "Processor::_get_required_nodes:  Yielding null.")
                    yield segment_node_coords
                elif isinstance(segment_node_coords, list):
                    # Most likely the output of a Collector, this list will be
                    # of NodeCoords rather than an actual DOM reference.  As
                    # such, it must be treated as a virtual DOM element that
                    # cannot itself be parented to the real DOM, though each
                    # of its elements has a real parent.
                    for subnode_coord in self._get_required_nodes(
                            segment_node_coords, yaml_path, depth + 1,
                            translated_path=translated_path):
                        yield subnode_coord
                else:
                    for subnode_coord in self._get_required_nodes(
                            segment_node_coords.node, yaml_path, depth + 1,
                            parent=segment_node_coords.parent,
                            parentref=segment_node_coords.parentref,
                            translated_path=segment_node_coords.path):
                        self.logger.debug(
                            "Finally returning segment data of type {} at"
                            " parentref {}:"
                            .format(type(subnode_coord.node),
                                    subnode_coord.parentref),
                            prefix="Processor::_get_required_nodes:  ",
                            data=subnode_coord, footer=" ")
                        yield subnode_coord
        else:
            self.logger.debug(
                "Finally returning data of type {} at parentref {}:"
                .format(type(data), parentref),
                prefix="Processor::_get_required_nodes:  ",
                data=data, footer=" ")
            yield NodeCoords(data, parent, parentref, translated_path)

    def _get_collected_nodes(
        self, data: Any
    ) -> Generator[NodeCoords, None, None]:
        """Yield all nodes -- however nested -- from a Collector result."""
        if isinstance(data, list):
            for ele in data:
                for node in self._get_collected_nodes(ele):
                    self.logger.debug(
                        "Yielding a list element:",
                        prefix="Processor::_get_collected_nodes:  ",
                        data=node)
                    yield node
        elif (isinstance(data, NodeCoords)
              and isinstance(data.node, NodeCoords)
        ):
            for node in self._get_collected_nodes(data.node):
                self.logger.debug(
                    "Yielding a nested NodeCoords:",
                    prefix="Processor::_get_collected_nodes:  ",
                    data=node)
                yield node
        else:
            self.logger.debug(
                "Yielding the given data:",
                prefix="Processor::_get_collected_nodes:  ",
                data=data)
            yield data

    # pylint: disable=locally-disabled,too-many-statements
    def _get_optional_nodes(
            self, data: Any, yaml_path: YAMLPath, value: Any = None,
            depth: int = 0, **kwargs: Any
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
        parent = kwargs.pop("parent", None)
        parentref = kwargs.pop("parentref", None)
        translated_path = kwargs.pop("translated_path", YAMLPath(""))
        if data is None:
            self.logger.debug(
                "Bailing out on None data at parentref, {}, of parent:"
                .format(parentref),
                prefix="Processor::_get_optional_nodes:  ", data=parent)
            return

        segments = yaml_path.escaped
        # pylint: disable=locally-disabled,too-many-nested-blocks
        if segments and len(segments) > depth:
            segment_type: PathSegmentTypes
            (segment_type, unstripped_attrs) = yaml_path.unescaped[depth]
            stripped_attrs: Union[
                str,
                int,
                SearchTerms,
                CollectorTerms
            ] = segments[depth][1]
            except_segment = str(unstripped_attrs)

            self.logger.debug(
                "Seeking element <{}>{} in data of type {}:"
                .format(segment_type, except_segment, type(data)),
                prefix="Processor::_get_optional_nodes:  ",
                data=data, footer=" ")

            # The next element may not exist; this method ensures that it does
            matched_nodes = 0
            for next_coord in self._get_nodes_by_path_segment(
                data, yaml_path, depth, parent=parent, parentref=parentref,
                translated_path=translated_path
            ):
                if segment_type is PathSegmentTypes.COLLECTOR:
                    # The next_coord will be a list, not a NodeCoords
                    self.logger.debug(
                        "Received Collector results; sub-processing each:",
                        prefix="Processor::_get_optional_nodes:  ",
                        data=next_coord)
                    matched_nodes += 1
                    for col_node in self._get_collected_nodes(next_coord):
                        for subnode_coord in self._get_optional_nodes(
                                col_node, yaml_path, value, depth + 1,
                                translated_path=translated_path):
                            self.logger.debug(
                                "Yielding Collector sub-node coordinate from"
                                " {} segment:".format(segment_type),
                                prefix="Processor::_get_optional_nodes:  ",
                                data=subnode_coord)
                            yield subnode_coord
                else:
                    matched_nodes += 1
                    self.logger.debug(
                        "Processor::_get_optional_nodes:  Found element <{}>{}"
                        " in the data; recursing into it..."
                        .format(segment_type, except_segment))
                    for node_coord in self._get_optional_nodes(
                            next_coord.node, yaml_path, value, depth + 1,
                            parent=next_coord.parent,
                            parentref=next_coord.parentref,
                            translated_path=next_coord.path
                    ):
                        self.logger.debug(
                            "Yielding recursed node coordinate from {}"
                            " segment:".format(segment_type),
                            prefix="Processor::_get_optional_nodes:  ",
                            data=node_coord)
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
                        next_node = Nodes.build_next_node(
                            yaml_path, depth + 1, value
                        )
                        new_ele = Nodes.append_list_element(
                            data, next_node, stripped_attrs
                        )
                        new_idx = len(data) - 1
                        next_translated_path = translated_path + "[{}]".format(
                            new_idx)
                        for node_coord in self._get_optional_nodes(
                                new_ele, yaml_path, value, depth + 1,
                                parent=data, parentref=new_idx,
                                translated_path=next_translated_path
                        ):
                            matched_nodes += 1
                            self.logger.debug(
                                "Yielding generic list node coordinate from {}"
                                " segment:".format(segment_type),
                                prefix="Processor::_get_optional_nodes:  ",
                                data=node_coord)
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
                            except ValueError as wrap_ex:
                                raise YAMLPathException(
                                    ("Cannot add non-integer {} subreference"
                                     + " to lists")
                                    .format(str(segment_type)),
                                    str(yaml_path),
                                    except_segment
                                ) from wrap_ex
                        for _ in range(len(data) - 1, newidx):
                            next_node = Nodes.build_next_node(
                                yaml_path, depth + 1, value
                            )
                            Nodes.append_list_element(data, next_node)
                        next_translated_path = translated_path + "[{}]".format(
                            newidx)
                        for node_coord in self._get_optional_nodes(
                                data[newidx], yaml_path, value,
                                depth + 1, parent=data, parentref=newidx,
                                translated_path=next_translated_path
                        ):
                            matched_nodes += 1
                            self.logger.debug(
                                "Yielding indexed node coordinate from {}"
                                " segment:".format(segment_type),
                                prefix="Processor::_get_optional_nodes:  ",
                                data=node_coord)
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
                        data[stripped_attrs] = Nodes.build_next_node(
                            yaml_path, depth + 1, value
                        )
                        next_translated_path = (
                            translated_path + YAMLPath.escape_path_section(
                                str(stripped_attrs),
                                translated_path.seperator))
                        for node_coord in self._get_optional_nodes(
                                data[stripped_attrs], yaml_path, value,
                                depth + 1, parent=data,
                                parentref=stripped_attrs,
                                translated_path=next_translated_path
                        ):
                            matched_nodes += 1
                            self.logger.debug(
                                "Yielding keyed node coordinate from {}"
                                " segment:".format(segment_type),
                                prefix="Processor::_get_optional_nodes:  ",
                                data=node_coord)
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
                "Finally returning data of type {}:"
                .format(type(data)),
                prefix="Processor::_get_optional_nodes:  ", data=data)
            yield NodeCoords(data, parent, parentref, translated_path)

    # pylint: disable=too-many-arguments
    def _update_node(
        self, parent: Any, parentref: Any, value: Any,
        value_format: YAMLValueFormats, value_tag: str = None
    ) -> None:
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
        5. value_tag (str) the custom YAML data-type tag of the value

        Returns: N/A

        Raises: N/A
        """
        if parent is None:
            # Empty document or the document root
            self.logger.debug(
                "Ignoring node with no parent:",
                prefix="Processor::_update_node:  ",
                data=value)
            return

        # This recurse function was contributed by Anthon van der Neut, the
        # author of ruamel.yaml, to resolve how to update all references to an
        # Anchor throughout the parsed data structure.
        def recurse(data, parent, parentref, reference_node, replacement_node):
            if isinstance(data, dict):
                for i, k in [
                        (idx, key) for idx, key in enumerate(data.keys())
                        if key is reference_node
                ]:
                    data.insert(i, replacement_node, data.pop(k))
                for k, val in data.items():
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
        new_node = Nodes.make_new_node(
            change_node, value, value_format, tag=value_tag)

        self.logger.debug(
            "Changing the following <{}> formatted node:".format(value_format),
            prefix="Processor::_update_node:  ",
            data={ "__FROM__": change_node, "___TO___": new_node })

        recurse(self.data, parent, parentref, change_node, new_node)

        self.logger.debug(
            "Parent after change:", prefix="Processor::_update_node:  ",
            data=parent)
