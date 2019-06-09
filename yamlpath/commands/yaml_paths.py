"""
Returns zero or more YAML Paths indicating where in given YAML/Compatible data
a search expression matches.  Values and/or keys can be searched.  EYAML can be
employed to search encrypted values.

Copyright 2019 William W. Kimball, Jr. MBA MSIS
"""
import argparse
from os import access, R_OK
from os.path import isfile
from typing import Any, Generator, List, Optional, Tuple

from ruamel.yaml.comments import CommentedSeq, CommentedMap

from yamlpath.func import (
    create_searchterms_from_pathattributes,
    escape_path_section,
    get_yaml_data,
    get_yaml_editor,
    search_matches,
    search_anchor,
)
from yamlpath.exceptions import YAMLPathException
from yamlpath.enums import (
    AnchorMatches,
    IncludeAliases,
    PathSeperators,
    PathSearchMethods
)
from yamlpath.path import SearchTerms
from yamlpath import YAMLPath
from yamlpath.wrappers import ConsolePrinter
from yamlpath.eyaml import EYAMLProcessor

# Implied Constants
MY_VERSION = "0.1.0"

def processcli():
    """Process command-line arguments."""
    search_ops = ", ".join(PathSearchMethods.get_operators()) + ", or !"
    parser = argparse.ArgumentParser(
        description="Returns zero or more YAML Paths indicating where in given\
            YAML/Compatible data one or more search expressions match.\
            Values, keys, and/or anchors can be searched.  EYAML can be\
            employed to search encrypted values.",
        epilog="A search or exception EXPRESSION takes the form of a YAML Path\
            search operator -- {} -- followed by the search term, omitting the\
            left-hand operand.  For more information about YAML Paths, please\
            visit https://github.com/wwkimball/yamlpath.".format(search_ops)
    )
    parser.add_argument("-V", "--version", action="version",
                        version="%(prog)s " + MY_VERSION)

    required_group = parser.add_argument_group("required settings")
    required_group.add_argument(
        "-s", "--search",
        required=True,
        metavar="EXPRESSION", action="append",
        help="the search expression; can be set more than once")

    parser.add_argument(
        "-c", "--except",
        metavar="EXPRESSION", action="append", dest="except_expression",
        help="except results matching this search expression; can be set more\
            than once")

    noise_group = parser.add_mutually_exclusive_group()
    noise_group.add_argument(
        "-d", "--debug",
        action="store_true",
        help="output debugging details")
    noise_group.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="increase output verbosity")
    noise_group.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="suppress all non-result output except errors")

    parser.add_argument(
        "-p", "--pathonly",
        action="store_true",
        help="print results without any search expression decorators")

    parser.add_argument(
        "-m", "--expand",
        action="store_true",
        help="expand matching parent nodes to list all permissible child leaf\
              nodes (see \"Reference handling options\" for restrictions)")

    parser.add_argument(
        "-t", "--pathsep",
        default="dot",
        choices=PathSeperators,
        metavar=PathSeperators.get_choices(),
        type=PathSeperators.from_str,
        help="indicate which YAML Path seperator to use when rendering\
              results; default=dot")

    keyname_group_ex = parser.add_argument_group("Key name searching options")
    keyname_group = keyname_group_ex.add_mutually_exclusive_group()
    keyname_group.add_argument(
        "-i", "--ignorekeynames",
        action="store_true",
        help="(default) do not search key names")
    keyname_group.add_argument(
        "-k", "--keynames",
        action="store_true",
        help="search key names in addition to values and array elements")
    keyname_group.add_argument(
        "-K", "--onlykeynames",
        action="store_true",
        help="only search key names (ignore all values and array elements)")

    parser.add_argument(
        "-a", "--refnames",
        action="store_true",
        help="also search the names of &anchor and *alias references")

    dedup_group_ex = parser.add_argument_group(
        "Reference handling options",
        "Indicate how to treat anchor and alias references.  An anchor is an\
         original, reusable key or value.  All aliases become replaced by the\
         anchors they reference when YAML data is read.  These options specify\
         how to handle this duplication of keys and values.  Note that the\
         default behavior includes all aliased keys but not aliased values.")
    dedup_group = dedup_group_ex.add_mutually_exclusive_group()
    dedup_group.add_argument(
        "-A", "--anchorsonly",
        action="store_const",
        dest="include_aliases",
        const=IncludeAliases.ANCHORS_ONLY,
        help="include only original matching key and value anchors in results,\
              discarding all aliased keys and values (including child nodes)")
    dedup_group.add_argument(
        "-Y", "--allowkeyaliases",
        action="store_const",
        dest="include_aliases",
        const=IncludeAliases.INCLUDE_KEY_ALIASES,
        help="(default) include matching key aliases, permitting search\
              traversal into their child nodes")
    dedup_group.add_argument(
        "-y", "--allowvaluealiases",
        action="store_const",
        dest="include_aliases",
        const=IncludeAliases.INCLUDE_VALUE_ALIASES,
        help="include matching value aliases (does not permit search traversal\
              into aliased keys)")
    dedup_group.add_argument(
        "-l", "--allowaliases",
        action="store_const",
        dest="include_aliases",
        const=IncludeAliases.INCLUDE_ALL_ALIASES,
        help="include all matching key and value aliases")

    eyaml_group = parser.add_argument_group(
        "EYAML options", "Left unset, the EYAML keys will default to your\
         system or user defaults.  Both keys must be set either here or in\
         your system or user EYAML configuration file when using EYAML.")
    eyaml_group.add_argument(
        "-e", "--decrypt",
        action="store_true",
        help="decrypt EYAML values in order to search them (otherwise, search\
            the encrypted blob)"
    )
    eyaml_group.add_argument(
        "-x", "--eyaml",
        default="eyaml",
        help="the eyaml binary to use when it isn't on the PATH")
    eyaml_group.add_argument("-r", "--privatekey", help="EYAML private key")
    eyaml_group.add_argument("-u", "--publickey", help="EYAML public key")

    parser.add_argument("yaml_files", metavar="YAML_FILE", nargs="+",
                        help="one or more YAML files to search")

    parser.set_defaults(include_aliases=IncludeAliases.INCLUDE_KEY_ALIASES)

    return parser.parse_args()

def validateargs(args, log):
    """Validate command-line arguments."""
    has_errors = False

    # Enforce sanity
    # * When set, --privatekey must be a readable file
    if args.privatekey and not (
            isfile(args.privatekey) and access(args.privatekey, R_OK)
    ):
        has_errors = True
        log.error(
            "EYAML private key is not a readable file:  " + args.privatekey
        )

    # * When set, --publickey must be a readable file
    if args.publickey and not (
            isfile(args.publickey) and access(args.publickey, R_OK)
    ):
        has_errors = True
        log.error(
            "EYAML public key is not a readable file:  " + args.publickey
        )

    # * When either --publickey or --privatekey are set, the other must also
    #   be.  This is because the `eyaml` command requires them both when
    #   decrypting values.
    if (
            (args.publickey and not args.privatekey)
            or (args.privatekey and not args.publickey)
    ):
        has_errors = True
        log.error("Both private and public EYAML keys must be set.")

    if has_errors:
        exit(1)

# pylint: disable=locally-disabled,too-many-arguments,too-many-locals,too-many-branches
def yield_children(logger: ConsolePrinter, data: Any,
                   terms: SearchTerms, pathsep: PathSeperators,
                   build_path: str, seen_anchors: List[str],
                   **kwargs: bool) -> Generator[YAMLPath, None, None]:
    """
    Except for unwanted aliases, unconditionally dump the YAML Path of every
    child node beneath a given parent node, if there are any.
    """
    include_key_aliases: bool = kwargs.pop("include_key_aliases", True)
    include_value_aliases: bool = kwargs.pop("include_value_aliases", False)
    search_anchors: bool = kwargs.pop("search_anchors", False)
    logger.debug(
        ("yaml_paths::yield_children:  "
         + "dumping all children in data of type, {}:")
        .format(type(data)))
    logger.debug(data)

    exclude_alias_matchers = [AnchorMatches.UNSEARCHABLE_ALIAS,
                              AnchorMatches.ALIAS_EXCLUDED]

    if isinstance(data, CommentedSeq):
        if not build_path and pathsep is PathSeperators.FSLASH:
            build_path = str(pathsep)
        build_path += "["

        for idx, ele in enumerate(data):
            anchor_matched = search_anchor(
                ele, terms, seen_anchors, search_anchors=search_anchors,
                include_aliases=include_value_aliases)
            logger.debug(
                ("yaml_paths::yield_children<list>:  "
                 + "element[{}] has anchor search => {}.")
                .format(idx, anchor_matched))

            # Build the temporary YAML Path using either Anchor or Index
            if anchor_matched is AnchorMatches.NO_ANCHOR:
                # Not an anchor/alias, so ref this node by its index
                tmp_path = build_path + str(idx) + "]"
            else:
                tmp_path = "{}&{}]".format(
                    build_path,
                    escape_path_section(ele.anchor.value, pathsep)
                )

            if (not include_value_aliases
                    and anchor_matched in exclude_alias_matchers):
                continue

            if isinstance(ele, (CommentedMap, CommentedSeq)):
                for path in yield_children(
                        logger, ele, terms, pathsep, tmp_path, seen_anchors,
                        search_anchors=search_anchors,
                        include_key_aliases=include_key_aliases,
                        include_value_aliases=include_value_aliases):
                    yield path
            else:
                yield YAMLPath(tmp_path)

    elif isinstance(data, CommentedMap):
        if build_path:
            build_path += str(pathsep)
        elif pathsep is PathSeperators.FSLASH:
            build_path = str(pathsep)

        pool = data.non_merged_items()
        if include_key_aliases or include_value_aliases:
            pool = data.items()

        for key, val in pool:
            tmp_path = build_path + escape_path_section(key, pathsep)

            key_anchor_matched = search_anchor(
                key, terms, seen_anchors, search_anchors=search_anchors,
                include_aliases=include_key_aliases)
            val_anchor_matched = search_anchor(
                val, terms, seen_anchors, search_anchors=search_anchors,
                include_aliases=include_value_aliases)
            logger.debug(
                ("yaml_paths::yield_children<dict>:  "
                 + "key[{}]:value have value anchor search => {}:{}.")
                .format(key, key_anchor_matched, val_anchor_matched))

            if (
                    (not include_key_aliases
                     and key_anchor_matched in exclude_alias_matchers)
                    or (not include_value_aliases
                        and val_anchor_matched in exclude_alias_matchers)
            ):
                continue

            if isinstance(val, (CommentedSeq, CommentedMap)):
                for path in yield_children(
                        logger, val, terms, pathsep, tmp_path, seen_anchors,
                        search_anchors=search_anchors,
                        include_key_aliases=include_key_aliases,
                        include_value_aliases=include_value_aliases):
                    yield path
            else:
                yield YAMLPath(tmp_path)

    else:
        if not build_path and pathsep is PathSeperators.FSLASH:
            build_path = str(pathsep)
        yield YAMLPath(build_path)

# pylint: disable=locally-disabled,too-many-arguments,too-many-locals,too-many-branches,too-many-statements
def search_for_paths(logger: ConsolePrinter, processor: EYAMLProcessor,
                     data: Any, terms: SearchTerms,
                     pathsep: PathSeperators = PathSeperators.DOT,
                     build_path: str = "",
                     seen_anchors: Optional[List[str]] = None,
                     **kwargs: bool) -> Generator[YAMLPath, None, None]:
    """
    Recursively searches a data structure for nodes matching a search
    expression.  The nodes can be keys, values, and/or elements.  When dealing
    with anchors and their aliases, the caller indicates whether to include
    only the original anchor or the anchor and all of its (duplicate) aliases.
    """
    search_values: bool = kwargs.pop("search_values", True)
    search_keys: bool = kwargs.pop("search_keys", False)
    search_anchors: bool = kwargs.pop("search_anchors", False)
    include_key_aliases: bool = kwargs.pop("include_key_aliases", True)
    include_value_aliases: bool = kwargs.pop("include_value_aliases", False)
    decrypt_eyaml: bool = kwargs.pop("decrypt_eyaml", False)
    expand_children: bool = kwargs.pop("expand_children", False)
    strsep = str(pathsep)
    invert = terms.inverted
    method = terms.method
    term = terms.term

    if seen_anchors is None:
        seen_anchors = []

    if isinstance(data, CommentedSeq):
        # Build the path
        if not build_path and pathsep is PathSeperators.FSLASH:
            build_path = strsep
        build_path += "["

        for idx, ele in enumerate(data):
            # Any element may or may not have an Anchor/Alias
            anchor_matched = search_anchor(
                ele, terms, seen_anchors, search_anchors=search_anchors,
                include_aliases=include_value_aliases)
            logger.debug(
                ("yaml_paths::search_for_paths<list>:"
                 + "anchor search => {}.")
                .format(anchor_matched)
            )

            # Build the temporary YAML Path using either Anchor or Index
            if anchor_matched is AnchorMatches.NO_ANCHOR:
                # Not an anchor/alias, so ref this node by its index
                tmp_path = build_path + str(idx) + "]"
            else:
                tmp_path = "{}&{}]".format(
                    build_path,
                    escape_path_section(ele.anchor.value, pathsep)
                )

            if anchor_matched is AnchorMatches.ALIAS_EXCLUDED:
                continue

            if anchor_matched in [AnchorMatches.MATCH,
                                  AnchorMatches.ALIAS_INCLUDED]:
                logger.debug(
                    ("yaml_paths::search_for_paths<list>:"
                     + "yielding an Anchor/Alias match, {}.")
                    .format(tmp_path)
                )
                if expand_children:
                    for path in yield_children(
                            logger, ele, terms, pathsep, tmp_path,
                            seen_anchors, search_anchors=search_anchors,
                            include_key_aliases=include_key_aliases,
                            include_value_aliases=include_value_aliases):
                        yield path
                else:
                    yield YAMLPath(tmp_path)
                continue

            if isinstance(ele, (CommentedSeq, CommentedMap)):
                logger.debug(
                    "yaml_paths::search_for_paths<list>:"
                    + "recursing into complex data:"
                )
                logger.debug(ele)
                logger.debug(">>>> >>>> >>>> >>>> >>>> >>>> >>>>")
                for subpath in search_for_paths(
                        logger, processor, ele, terms, pathsep, tmp_path,
                        seen_anchors, search_values=search_values,
                        search_keys=search_keys, search_anchors=search_anchors,
                        include_key_aliases=include_key_aliases,
                        include_value_aliases=include_value_aliases,
                        decrypt_eyaml=decrypt_eyaml,
                        expand_children=expand_children
                ):
                    logger.debug(
                        ("yaml_paths::search_for_paths<list>:"
                         + "yielding RECURSED match, {}."
                        ).format(subpath)
                    )
                    logger.debug("<<<< <<<< <<<< <<<< <<<< <<<< <<<<")
                    yield subpath
            elif search_values:
                if (anchor_matched is AnchorMatches.UNSEARCHABLE_ALIAS
                        and not include_value_aliases):
                    continue

                check_value = ele
                if decrypt_eyaml and processor.is_eyaml_value(ele):
                    check_value = processor.decrypt_eyaml(ele)

                matches = search_matches(method, term, check_value)
                if (matches and not invert) or (invert and not matches):
                    logger.debug(
                        ("yaml_paths::search_for_paths<list>:"
                         + "yielding VALUE match, {}:  {}."
                        ).format(check_value, tmp_path)
                    )
                    yield YAMLPath(tmp_path)

    # pylint: disable=too-many-nested-blocks
    elif isinstance(data, CommentedMap):
        if build_path:
            build_path += strsep
        elif pathsep is PathSeperators.FSLASH:
            build_path = strsep

        pool = data.non_merged_items()
        if include_key_aliases or include_value_aliases:
            pool = data.items()

        for key, val in pool:
            tmp_path = build_path + escape_path_section(key, pathsep)

            # Search the value anchor to have it on record, in case the key
            # anchor match would otherwise block the value anchor from
            # appearing in seen_anchors (which is important).
            val_anchor_matched = search_anchor(
                val, terms, seen_anchors, search_anchors=search_anchors,
                include_aliases=include_value_aliases)
            logger.debug(
                ("yaml_paths::search_for_paths<dict>:"
                 + "VALUE anchor search => {}.")
                .format(val_anchor_matched)
            )

            # Search the key when the caller wishes it.
            if search_keys:
                # The key itself may be an Anchor or Alias.  Search it when the
                # caller wishes.
                key_anchor_matched = search_anchor(
                    key, terms, seen_anchors, search_anchors=search_anchors,
                    include_aliases=include_key_aliases)
                logger.debug(
                    ("yaml_paths::search_for_paths<dict>:"
                     + "KEY anchor search, {}:  {}.")
                    .format(key, key_anchor_matched)
                )

                if key_anchor_matched in [AnchorMatches.MATCH,
                                          AnchorMatches.ALIAS_INCLUDED]:
                    logger.debug(
                        ("yaml_paths::search_for_paths<dict>:"
                         + "yielding a KEY-ANCHOR match, {}."
                        ).format(key, tmp_path)
                    )
                    if expand_children:
                        for path in yield_children(
                                logger, val, terms, pathsep, tmp_path,
                                seen_anchors, search_anchors=search_anchors,
                                include_key_aliases=include_key_aliases,
                                include_value_aliases=include_value_aliases):
                            yield path
                    else:
                        yield YAMLPath(tmp_path)
                    continue

                # Search the name of the key, itself
                matches = search_matches(method, term, key)
                if (matches and not invert) or (invert and not matches):
                    logger.debug(
                        ("yaml_paths::search_for_paths<dict>:"
                         + "yielding KEY name match, {}:  {}."
                        ).format(key, tmp_path)
                    )
                    if expand_children:
                        # Include every non-excluded child node under this
                        # matched parent node.
                        for path in yield_children(
                                logger, val, terms, pathsep, tmp_path,
                                seen_anchors, search_anchors=search_anchors,
                                include_key_aliases=include_key_aliases,
                                include_value_aliases=include_value_aliases):
                            yield path
                    else:
                        # No other matches within this node matter because they
                        # are already in the result.
                        yield YAMLPath(tmp_path)
                    continue

            # The value may itself be anchored; search it if requested
            if val_anchor_matched is AnchorMatches.ALIAS_EXCLUDED:
                continue

            if val_anchor_matched in [AnchorMatches.MATCH,
                                      AnchorMatches.ALIAS_INCLUDED]:
                logger.debug(
                    ("yaml_paths::search_for_paths<dict>:"
                     + "yielding a VALUE-ANCHOR match, {}.")
                    .format(tmp_path)
                )
                if expand_children:
                    for path in yield_children(
                            logger, val, terms, pathsep, tmp_path,
                            seen_anchors, search_anchors=search_anchors,
                            include_key_aliases=include_key_aliases,
                            include_value_aliases=include_value_aliases):
                        yield path
                else:
                    yield tmp_path
                continue

            if isinstance(val, (CommentedSeq, CommentedMap)):
                logger.debug(
                    "yaml_paths::search_for_paths<dict>:"
                    + "recursing into complex data:"
                )
                logger.debug(val)
                logger.debug(">>>> >>>> >>>> >>>> >>>> >>>> >>>>")
                for subpath in search_for_paths(
                        logger, processor, val, terms, pathsep, tmp_path,
                        seen_anchors, search_values=search_values,
                        search_keys=search_keys, search_anchors=search_anchors,
                        include_key_aliases=include_key_aliases,
                        include_value_aliases=include_value_aliases,
                        decrypt_eyaml=decrypt_eyaml,
                        expand_children=expand_children
                ):
                    logger.debug(
                        ("yaml_paths::search_for_paths<dict>:"
                         + "yielding RECURSED match, {}."
                        ).format(subpath)
                    )
                    logger.debug("<<<< <<<< <<<< <<<< <<<< <<<< <<<<")
                    yield subpath
            elif search_values:
                if (val_anchor_matched is AnchorMatches.UNSEARCHABLE_ALIAS
                        and not include_value_aliases):
                    continue

                check_value = val
                if decrypt_eyaml and processor.is_eyaml_value(val):
                    check_value = processor.decrypt_eyaml(val)

                matches = search_matches(method, term, check_value)
                if (matches and not invert) or (invert and not matches):
                    logger.debug(
                        ("yaml_paths::search_for_paths<dict>:"
                         + "yielding VALUE match, {}:  {}."
                        ).format(check_value, tmp_path)
                    )
                    yield YAMLPath(tmp_path)

def get_search_term(logger: ConsolePrinter,
                    expression: str) -> Optional[SearchTerms]:
    """
    Attempts to cast a search expression into a SearchTerms instance.  Returns
    None on failure.
    """
    # The leading character must be a known search operator
    check_operator = expression[0] if expression else ""
    if not (PathSearchMethods.is_operator(check_operator)
            or check_operator == '!'):
        logger.error(
            ("Invalid search expression, '{}'.  The first symbol of"
             + " every search expression must be one of:  {}")
            .format(expression,
                    ", ".join(PathSearchMethods.get_operators())))
        return None

    if not len(expression) > 1:
        # Empty expressions do nothing
        logger.error(
            "An EXPRESSION with only a search operator has no effect, '{}'."
            .format(expression))
        return None

    try:
        exterm = create_searchterms_from_pathattributes(
            YAMLPath("[*{}]".format(expression)).escaped[0][1]
        )
    except YAMLPathException as ex:
        logger.error(
            ("Invalid search expression, '{}', due to:  {}")
            .format(expression, ex)
        )
        return None

    return exterm

def print_results(args: Any, yaml_file: str,
                  yaml_paths: List[Tuple[str, YAMLPath]]) -> None:
    """
    Dumps the search results to STDOUT with optional and dynamic formatting.
    """
    in_file_count = len(args.yaml_files)
    in_expressions = len(args.search)
    suppress_expression = in_expressions < 2 or args.pathonly
    for entry in yaml_paths:
        expression, result = entry
        resline = ""
        if in_file_count > 1:
            if suppress_expression:
                resline += "{}: {}".format(yaml_file, result)
            else:
                resline += "{}[{}]: {}".format(
                    yaml_file, expression, result)
        else:
            if suppress_expression:
                resline += "{}".format(result)
            else:
                resline += "[{}]: {}".format(expression, result)
        print(resline)

def main():
    """Main code."""
    # Process any command-line arguments
    args = processcli()
    log = ConsolePrinter(args)
    validateargs(args, log)
    search_values = True
    search_keys = False
    include_key_aliases = False
    include_value_aliases = False

    if args.onlykeynames:
        search_values = False
        search_keys = True
    elif args.keynames:
        search_keys = True

    if args.include_aliases is IncludeAliases.INCLUDE_ALL_ALIASES:
        include_key_aliases = True
        include_value_aliases = True
    elif args.include_aliases is IncludeAliases.INCLUDE_KEY_ALIASES:
        include_key_aliases = True
    elif args.include_aliases is IncludeAliases.INCLUDE_VALUE_ALIASES:
        include_value_aliases = True

    # Prepare the YAML processor
    yaml = get_yaml_editor()
    processor = EYAMLProcessor(
        log, None, binary=args.eyaml,
        publickey=args.publickey, privatekey=args.privatekey)

    # Process the input file(s)
    exit_state = 0

    # pylint: disable=too-many-nested-blocks
    for yaml_file in args.yaml_files:
        # Try to open the file
        yaml_data = get_yaml_data(yaml, log, yaml_file)
        if yaml_data is None:
            # An error message has already been logged
            exit_state = 3
            continue

        # Process all searches
        processor.data = yaml_data
        yaml_paths = []
        for expression in args.search:
            exterm = get_search_term(log, expression)
            log.debug(("yaml_paths::main:"
                       + "converting search expression '{}' into '{}'"
                       ).format(expression, exterm))
            if exterm is None:
                exit_state = 1
                continue

            for result in search_for_paths(
                    log, processor, yaml_data, exterm, args.pathsep,
                    search_values=search_values, search_keys=search_keys,
                    search_anchors=args.refnames,
                    include_key_aliases=include_key_aliases,
                    include_value_aliases=include_value_aliases,
                    decrypt_eyaml=args.decrypt, expand_children=args.expand):
                # Record only unique results
                add_entry = True
                for entry in yaml_paths:
                    if str(result) == str(entry[1]):
                        add_entry = False
                        break
                if add_entry:
                    yaml_paths.append((expression, result))

        if not yaml_paths:
            # Nothing further to do when there are no results
            continue

        if args.except_expression:
            for expression in args.except_expression:
                exterm = get_search_term(log, expression)
                log.debug(("yaml_paths::main:"
                           + "converted except expression '{}' into '{}'"
                           ).format(expression, exterm))
                if exterm is None:
                    exit_state = 1
                    continue

                for result in search_for_paths(
                        log, processor, yaml_data, exterm, args.pathsep,
                        search_values=search_values, search_keys=search_keys,
                        search_anchors=args.refnames,
                        include_key_aliases=include_key_aliases,
                        include_value_aliases=include_value_aliases,
                        decrypt_eyaml=args.decrypt,
                        expand_children=args.expand):
                    for entry in yaml_paths:
                        if str(result) == str(entry[1]):
                            yaml_paths.remove(entry)
                            break  # Entries are already unique

        print_results(args, yaml_file, yaml_paths)

    exit(exit_state)

if __name__ == "__main__":
    main()  # pragma: no cover
