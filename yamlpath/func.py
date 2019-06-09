"""
Collection of general helper functions.

Copyright 2018, 2019 William W. Kimball, Jr. MBA MSIS
"""
import re
from sys import maxsize
from distutils.util import strtobool
from typing import Any, List, Optional

from ruamel.yaml import YAML
from ruamel.yaml.parser import ParserError
from ruamel.yaml.composer import ComposerError, ReusedAnchorWarning
from ruamel.yaml.constructor import ConstructorError, DuplicateKeyError
from ruamel.yaml.scanner import ScannerError
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

from yamlpath.enums import (
    AnchorMatches,
    PathSearchMethods,
    PathSegmentTypes,
    PathSeperators,
    YAMLValueFormats,
)
from yamlpath.wrappers import ConsolePrinter
from yamlpath.types import PathAttributes
from yamlpath.path import SearchTerms
from yamlpath import YAMLPath

def get_yaml_editor() -> Any:
    """
    Builds and returns a generic YAML editor based on ruamel.yaml.

    Parameters:  N/A

    Returns (Any) The ready-for-use YAML editor.

    Raises:  N/A
    """
    yaml = YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.explicit_start = True
    yaml.preserve_quotes = True
    yaml.width = maxsize
    return yaml

# pylint: disable=locally-disabled,too-many-branches
def get_yaml_data(parser: Any, logger: ConsolePrinter, source: str) -> Any:
    """
    Attempts to parse YAML/Compatible data and return the ruamel.yaml object
    result.

    All known issues are caught and distinctively logged.  Returns None when
    the data could not be loaded.
    """
    import warnings
    warnings.filterwarnings("error")
    yaml_data = None

    # Try to open the file
    try:
        with open(source, 'r') as fhnd:
            yaml_data = parser.load(fhnd)
    except KeyboardInterrupt:
        logger.error("Aborting data load due to keyboard interrupt!")
        yaml_data = None
    except FileNotFoundError:
        logger.error("File not found:  {}".format(source))
        yaml_data = None
    except ParserError as ex:
        logger.error("YAML parsing error {}:  {}"
                     .format(str(ex.problem_mark).lstrip(), ex.problem))
        yaml_data = None
    except ComposerError as ex:
        logger.error("YAML composition error {}:  {}"
                     .format(str(ex.problem_mark).lstrip(), ex.problem))
        yaml_data = None
    except ConstructorError as ex:
        logger.error("YAML construction error {}:  {}"
                     .format(str(ex.problem_mark).lstrip(), ex.problem))
        yaml_data = None
    except ScannerError as ex:
        logger.error("YAML syntax error {}:  {}"
                     .format(str(ex.problem_mark).lstrip(), ex.problem))
        yaml_data = None
    except DuplicateKeyError as dke:
        omits = [
            "while constructing", "To suppress this", "readthedocs",
            "future releases", "the new API",
        ]
        message = str(dke).split("\n")
        newmsg = ""
        for line in message:
            line = line.strip()
            if not line:
                continue
            write_line = True
            for omit in omits:
                if omit in line:
                    write_line = False
                    break
            if write_line:
                newmsg += "\n   " + line
        logger.error("Duplicate Hash key detected:  {}"
                     .format(newmsg))
        yaml_data = None
    except ReusedAnchorWarning as raw:
        logger.error("Duplicate YAML Anchor detected:  {}"
                     .format(
                         str(raw)
                         .replace("occurrence   ", "occurrence ")
                         .replace("\n", "\n   ")))
        yaml_data = None

    return yaml_data

def build_next_node(yaml_path: YAMLPath, depth: int,
                    value: Any = None) -> Any:
    """
    Identifies and returns the most appropriate default value for the next
    entry in a YAML Path, should it not already exist.

    Parameters:
        1. yaml_path (deque) The pre-parsed YAML Path to follow
        2. depth (int) Index of the YAML Path segment to evaluate
        3. value (Any) The expected value for the final YAML Path entry

    Returns:  (Any) The most appropriate default value

    Raises:  N/A
    """
    default_value = wrap_type(value)
    segments = yaml_path.escaped
    if not (segments and len(segments) > depth):
        return default_value

    typ = segments[depth][0]
    if typ == PathSegmentTypes.INDEX:
        default_value = CommentedSeq()
    elif typ == PathSegmentTypes.KEY:
        default_value = CommentedMap()

    return default_value

def append_list_element(data: Any, value: Any = None,
                        anchor: str = None) -> Any:
    """
    Appends a new element to an ruamel.yaml presented list, preserving any
    tailing comment for the former last element of the same list.

    Parameters:
        1. data (Any) The parsed YAML data to process
        2. value (Any) The value of the element to append
        3. anchor (str) An Anchor or Alias name for the new element

    Returns:  (Any) The newly appended element node

    Raises:  N/A
    """
    if anchor is not None and value is not None:
        value = wrap_type(value)
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

def wrap_type(value: Any) -> Any:
    """
    Wraps a value in one of the ruamel.yaml wrapper types.

    Parameters:
        1. value (Any) The value to wrap.

    Returns: (Any) The wrapped value or the original value when a better
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

def clone_node(node: Any) -> Any:
    """
    Duplicates a YAML Data node.  This is necessary because otherwise,
    Python would treat any copies of a value as references to each other
    such that changes to one automatically affect all copies.  This is not
    desired when an original value must be duplicated elsewhere in the data
    and then the original changed without impacting the copy.

    Parameters:
        1. node (Any) The node to clone.

    Returns: (Any) Clone of the given node

    Raises:  N/A
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

# pylint: disable=locally-disabled,too-many-branches,too-many-statements
def make_new_node(source_node: Any, value: Any,
                  value_format: YAMLValueFormats) -> Any:
    """
    Creates a new data node based on a sample node, effectively duplicaing
    the type and anchor of the node but giving it a different value.

    Parameters:
        1. source_node (Any) The node from which to copy type
        2. value (Any) The value to assign to the new node
        3. value_format (YAMLValueFormats) The YAML presentation format to
            apply to value when it is dumped

    Returns: (Any) The new node

    Raises:
        - `NameError` when value_format is invalid
        - `ValueError' when the new value is not numeric and value_format
            requires it to be so
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
                ("The requested value format is {}, but '{}' cannot be"
                 + " cast to a floating-point number.")
                .format(valform, value)
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
                ("The requested value format is {}, but '{}' cannot be"
                 + " cast to an integer number.")
                .format(valform, value)
            )
    else:
        # Punt to whatever the best type may be
        new_type = type(wrap_type(value))

    if new_node is None:
        if hasattr(source_node, "anchor"):
            new_node = new_type(new_value, anchor=source_node.anchor.value)
        else:
            new_node = new_type(new_value)

    return new_node

def get_node_anchor(node: Any) -> Optional[str]:
    """
    Returns a node's Anchor/Alias name or None wheh there isn't one.
    """
    if (
            not hasattr(node, "anchor")
            or node.anchor is None
            or node.anchor.value is None
            or not node.anchor.value
    ):
        return None
    return str(node.anchor.value)

def search_matches(method: PathSearchMethods, needle: str,
                   haystack: Any) -> bool:
    """
    Performs a search.
    """
    matches: bool = False

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

def search_anchor(node: Any, terms: SearchTerms, seen_anchors: List[str],
                  **kwargs: bool) -> AnchorMatches:
    """
    Indicates whether a node has an Anchor that matches given search terms.
    """
    anchor_name = get_node_anchor(node)
    if anchor_name is None:
        return AnchorMatches.NO_ANCHOR

    is_alias = True
    if anchor_name not in seen_anchors:
        is_alias = False
        seen_anchors.append(anchor_name)

    search_anchors: bool = kwargs.pop("search_anchors", False)
    if not search_anchors:
        retval = AnchorMatches.UNSEARCHABLE_ANCHOR
        if is_alias:
            retval = AnchorMatches.UNSEARCHABLE_ALIAS
        return retval

    include_aliases: bool = kwargs.pop("include_aliases", False)
    if is_alias and not include_aliases:
        return AnchorMatches.ALIAS_EXCLUDED

    retval = AnchorMatches.NO_MATCH
    matches = search_matches(terms.method, terms.term, anchor_name)
    if (matches and not terms.inverted) or (terms.inverted and not matches):
        retval = AnchorMatches.MATCH
        if is_alias:
            retval = AnchorMatches.ALIAS_INCLUDED
    return retval

def ensure_escaped(value: str, *symbols: str) -> str:
    """
    Ensures all instances of a symbol are escaped (via \\) within a value.
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

def escape_path_section(section: str, pathsep: PathSeperators) -> str:
    """
    Renders inert via escaping all symbols within a string which have special
    meaning to YAML Path.  The resulting string can be consumed as a YAML Path
    section without triggering unwanted additional processing.
    """
    return ensure_escaped(
        section,
        '\\', str(pathsep), '(', ')', '[', ']', '^', '$', '%', ' ', "'", '"'
    )

def create_searchterms_from_pathattributes(
        rhs: PathAttributes) -> SearchTerms:
    """
    Generates a new SearchTerms instance by copying SearchTerms
    attributes from a YAML Path segment's attributes.
    """
    if isinstance(rhs, SearchTerms):
        newinst: SearchTerms = SearchTerms(
            rhs.inverted, rhs.method, rhs.attribute, rhs.term
        )
        return newinst
    raise AttributeError
