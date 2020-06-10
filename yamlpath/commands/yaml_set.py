"""
Enable users to change YAML/Compatible files using YAML Paths.

Changes one or more values in a YAML file at a specified YAML Path.  Matched
values can be checked before they are replaced to mitigate accidental change.
When matching singular results, the value can be archived to another key
before it is replaced.  Further, EYAML can be employed to encrypt the new
values and/or decrypt old values before checking them.

Copyright 2018, 2019, 2020 William W. Kimball, Jr. MBA MSIS
"""
import sys
import tempfile
import argparse
import secrets
import string
import re
import codecs
from os import remove, access, R_OK
from os.path import isfile, exists
from shutil import copy2, copyfileobj

from yamlpath.func import clone_node, get_yaml_data, get_yaml_editor
from yamlpath import YAMLPath
from yamlpath.exceptions import YAMLPathException
from yamlpath.enums import YAMLValueFormats, PathSeperators
from yamlpath.eyaml.exceptions import EYAMLCommandException
from yamlpath.eyaml.enums import EYAMLOutputFormats
from yamlpath.eyaml import EYAMLProcessor

# pylint: disable=locally-disabled,unused-import
import yamlpath.patches
from yamlpath.wrappers import ConsolePrinter

# Implied Constants
MY_VERSION = "1.1.0"
ESCAPE_SEQUENCE_RE = re.compile(r'''
    ( \\U........      # 8-digit hex escapes
    | \\u....          # 4-digit hex escapes
    | \\x..            # 2-digit hex escapes
    | \\[0-7]{1,3}     # Octal escapes
    | \\N\{[^}]+\}     # Unicode characters by name
    | \\[\\'"abfnrtv]  # Single-character escapes
    )''', re.UNICODE | re.VERBOSE)

def processcli():
    """Process command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Changes one or more values in a YAML file at a specified\
            YAML Path.  Matched values can be checked before they are replaced\
            to mitigate accidental change. When matching singular results, the\
            value can be archived to another key before it is replaced.\
            Further, EYAML can be employed to encrypt the new values and/or\
            decrypt an old value before checking them.",
        epilog="When no changes are made, no backup is created, even when\
            -b/--backup is specified.  For more information about YAML Paths,\
            please visit https://github.com/wwkimball/yamlpath."
    )
    parser.add_argument("-V", "--version", action="version",
                        version="%(prog)s " + MY_VERSION)

    required_group = parser.add_argument_group("required settings")
    required_group.add_argument(
        "-g", "--change",
        required=True,
        metavar="YAML_PATH",
        help="YAML Path where the target value is found")

    inputex_group = parser.add_argument_group("input options")
    input_group = inputex_group.add_mutually_exclusive_group()
    input_group.add_argument(
        "-a", "--value",
        help="set the new value from the command-line instead of STDIN")
    input_group.add_argument(
        "-f", "--file",
        help="read the new value from file (discarding any trailing\
              new-lines)")
    input_group.add_argument(
        "-i", "--stdin", action="store_true",
        help="accept the new value from STDIN (best for sensitive data)")
    input_group.add_argument(
        "-R", "--random",
        type=int,
        metavar="LENGTH",
        help="randomly generate a replacement value of a set length")

    parser.add_argument(
        "-F", "--format",
        default="default",
        choices=[l.lower() for l in YAMLValueFormats.get_names()],
        type=str.lower,
        help="override automatic formatting of the new value")
    parser.add_argument(
        "-C", "--codec",
        type=str.lower,
        help="when set, decode character escape sequences within the new value\
              into their actual characters (convert \\n into new-lines,\
              \\xNN into their hexadecimal values, \\uNNNN into their Unicode\
              characers, and so on); in most cases, you probably want\
              unicode-escape")
    parser.add_argument(
        "-c", "--check",
        help="check the value before replacing it")
    parser.add_argument(
        "-s", "--saveto", metavar="YAML_PATH",
        help="save the old value to YAML_PATH before replacing it; implies\
              --mustexist")
    parser.add_argument(
        "-m", "--mustexist", action="store_true",
        help="require that the --change YAML_PATH already exist in YAML_FILE")
    parser.add_argument(
        "-b", "--backup", action="store_true",
        help="save a backup YAML_FILE with an extra .bak file-extension")
    parser.add_argument(
        "-t", "--pathsep",
        default="dot",
        choices=PathSeperators,
        metavar=PathSeperators.get_choices(),
        type=PathSeperators.from_str,
        help="indicate which YAML Path seperator to use when rendering\
              results; default=dot")

    eyaml_group = parser.add_argument_group(
        "EYAML options", "Left unset, the EYAML keys will default to your\
         system or user defaults.  You do not need to supply a private key\
         unless you enable --check and the old value is encrypted.")
    eyaml_group.add_argument(
        "-e", "--eyamlcrypt", action="store_true",
        help="encrypt the new value using EYAML")
    eyaml_group.add_argument(
        "-x", "--eyaml", default="eyaml",
        help="the eyaml binary to use when it isn't on the PATH")
    eyaml_group.add_argument("-r", "--privatekey", help="EYAML private key")
    eyaml_group.add_argument("-u", "--publickey", help="EYAML public key")

    noise_group = parser.add_mutually_exclusive_group()
    noise_group.add_argument(
        "-d", "--debug", action="store_true",
        help="output debugging details")
    noise_group.add_argument(
        "-v", "--verbose", action="store_true",
        help="increase output verbosity")
    noise_group.add_argument(
        "-q", "--quiet", action="store_true",
        help="suppress all output except errors")

    parser.add_argument(
        "yaml_file", metavar="YAML_FILE",
        help="the YAML file to update")
    return parser.parse_args()

def validateargs(args, log):
    """Validate command-line arguments."""
    has_errors = False

    # Enforce sanity
    # * At least one of --value, --file, --stdin, or --random must be set
    if not (
            args.value
            or args.file
            or args.stdin
            or args.random
    ):
        has_errors = True
        log.error(
            "Exactly one of the following must be set:  --value, --file,"
            + " --stdin, or --random")

    # * When set, --saveto cannot be identical to --change
    if args.saveto and args.saveto == args.change:
        has_errors = True
        log.error(
            "Impossible to save the old value to the same YAML Path as the new"
            + " value!")

    # * When set, --privatekey must be a readable file
    if args.privatekey and not (
            isfile(args.privatekey)
            and access(args.privatekey, R_OK)
    ):
        has_errors = True
        log.error(
            "EYAML private key is not a readable file:  " + args.privatekey)

    # * When set, --publickey must be a readable file
    if args.publickey and not (
            isfile(args.publickey)
            and access(args.publickey, R_OK)
    ):
        has_errors = True
        log.error(
            "EYAML public key is not a readable file:  " + args.publickey)

    if has_errors:
        sys.exit(1)

# Credit: https://stackoverflow.com/a/24519338/5880190
def decode_escapes(value, codec):
    def decode_match(match):
        return codecs.decode(match.group(0), codec)

    return ESCAPE_SEQUENCE_RE.sub(decode_match, value)

# pylint: disable=locally-disabled,too-many-locals,too-many-branches,too-many-statements
def main():
    """Main code."""
    args = processcli()
    log = ConsolePrinter(args)
    validateargs(args, log)
    change_path = YAMLPath(args.change, pathsep=args.pathsep)
    backup_file = args.yaml_file + ".bak"

    # Obtain the replacement value
    if args.value:
        new_value = args.value
    elif args.stdin:
        new_value = ''.join(sys.stdin.readlines())
    elif args.file:
        with open(args.file, 'r') as fhnd:
            new_value = fhnd.read().rstrip()
    elif args.random is not None:
        new_value = ''.join(
            secrets.choice(
                string.ascii_uppercase + string.ascii_lowercase + string.digits
            ) for _ in range(args.random)
        )

    # Decode the new value whenever a codec has been supplied
    if args.codec:
        try:
            new_value = decode_escapes(new_value, args.codec)
        except UnicodeDecodeError as ude:
            log.critical("Specified codec is unable to decode your value due"
                         + " to error: {}.".format(ude), 1)

    # Prep the YAML parser
    yaml = get_yaml_editor()

    # Attempt to open the YAML file; check for parsing errors
    yaml_data = get_yaml_data(yaml, log, args.yaml_file)
    if yaml_data is None:
        # An error message has already been logged
        sys.exit(1)

    # Load the present value at the specified YAML Path
    change_node_coordinates = []
    old_format = YAMLValueFormats.DEFAULT
    processor = EYAMLProcessor(
        log, yaml_data, binary=args.eyaml,
        publickey=args.publickey, privatekey=args.privatekey)
    try:
        for node_coordinate in processor.get_nodes(
                change_path, mustexist=(args.mustexist or args.saveto),
                default_value=("" if new_value else " ")):
            log.debug('Got "{}" from {}.'.format(node_coordinate, change_path))
            change_node_coordinates.append(node_coordinate)
    except YAMLPathException as ex:
        log.critical(ex, 1)

    if len(change_node_coordinates) == 1:
        # When there is exactly one result, its old format can be known.  This
        # is necessary to retain whether the replacement value should be
        # represented later as a multi-line string when the new value is to be
        # encrypted.
        old_format = YAMLValueFormats.from_node(
            change_node_coordinates[0].node)

    log.debug("Collected nodes:")
    log.debug(change_node_coordinates)

    # Check the value(s), if desired
    if args.check:
        for node_coordinate in change_node_coordinates:
            if processor.is_eyaml_value(node_coordinate.node):
                # Sanity check:  If either --publickey or --privatekey were set
                # then they must both be set in order to decrypt this value.
                # This is enforced only when the value must be decrypted due to
                # a --check request.
                if (
                        (args.publickey and not args.privatekey)
                        or (args.privatekey and not args.publickey)
                ):
                    log.error(
                        "Neither or both private and public EYAML keys must be"
                        + " set when --check is required to decrypt the old"
                        + " value.")
                    sys.exit(1)

                try:
                    check_value = processor.decrypt_eyaml(node_coordinate.node)
                except EYAMLCommandException as ex:
                    log.critical(ex, 1)
            else:
                check_value = node_coordinate.node

            if not args.check == check_value:
                log.critical(
                    '"{}" does not match the check value.'
                    .format(args.check),
                    20
                )

    # Save the old value, if desired and possible
    if args.saveto:
        # Only one can be saved; otherwise it is impossible to meaningfully
        # convey to the end-user from exactly which other YAML node each saved
        # value came.
        if len(change_node_coordinates) > 1:
            log.critical(
                "It is impossible to meaningly save more than one matched"
                + " value.  Please omit --saveto or set --change to affect"
                + " exactly one value.", 1)

        saveto_path = YAMLPath(args.saveto, pathsep=args.pathsep)
        log.verbose("Saving the old value to {}.".format(saveto_path))

        # Folded EYAML values have their embedded newlines converted to spaces
        # when read.  As such, writing them back out breaks their original
        # format, despite being properly typed.  To restore the original
        # written form, reverse the conversion, here.
        old_value = change_node_coordinates[0].node
        if (
                (old_format is YAMLValueFormats.FOLDED
                 or old_format is YAMLValueFormats.LITERAL
                )
                and EYAMLProcessor.is_eyaml_value(old_value)
        ):
            old_value = old_value.replace(" ", "\n")

        try:
            processor.set_value(
                saveto_path, clone_node(old_value),
                value_format=old_format)
        except YAMLPathException as ex:
            log.critical(ex, 1)

    # Set the requested value
    log.verbose("Setting the new value for {}.".format(change_path))
    if args.eyamlcrypt:
        # If the user hasn't specified a format, use the same format as the
        # value being replaced, if known.
        format_type = YAMLValueFormats.from_str(args.format)
        if format_type is YAMLValueFormats.DEFAULT:
            format_type = old_format

        output_type = EYAMLOutputFormats.STRING
        if format_type in [YAMLValueFormats.FOLDED, YAMLValueFormats.LITERAL]:
            output_type = EYAMLOutputFormats.BLOCK

        try:
            processor.set_eyaml_value(
                change_path, new_value
                , output=output_type
                , mustexist=False
            )
        except EYAMLCommandException as ex:
            log.critical(ex, 2)
    else:
        processor.set_value(change_path, new_value, value_format=args.format)

    # Save a backup of the original file, if requested
    if args.backup:
        log.verbose(
            "Saving a backup of {} to {}."
            .format(args.yaml_file, backup_file))
        if exists(backup_file):
            remove(backup_file)
        copy2(args.yaml_file, backup_file)

    # Save the changed file
    log.verbose("Writing changed data to {}.".format(args.yaml_file))
    with tempfile.TemporaryFile() as tmphnd:
        with open(args.yaml_file, 'rb') as inhnd:
            copyfileobj(inhnd, tmphnd)

        with open(args.yaml_file, 'w') as yaml_dump:
            try:
                yaml.dump(yaml_data, yaml_dump)
            except UnicodeEncodeError as ex:
                rollback_changes(yaml_dump, tmphnd, args, backup_file)
                log.debug("Assertion error: {}".format(ex))
                log.critical((
                    "Unicode encoding error encountered while attempting to"
                    + " write updated data to {}.  You may need to specify a"
                    + " codec, a different codec, or compatible values for the"
                    + " specified codec.  The original file content was"
                    + " restored.  The Unicode error was as follows: {}"
                ).format(args.yaml_file, ex), 3)
            except AssertionError as ex:
                rollback_changes(yaml_dump, tmphnd, args, backup_file)
                log.debug("Assertion error: {}".format(ex))
                log.critical((
                    "Indeterminate assertion error encountered while"
                    + " attempting to write updated data to {}.  The original"
                    + " file content was restored.").format(args.yaml_file), 3)

def rollback_changes(outhnd, tmphnd, args, backup_file):
    """Rollback changes to the target output file."""
    outhnd.close()
    tmphnd.seek(0)
    with open(args.yaml_file, 'wb') as rollbackhnd:
        copyfileobj(tmphnd, rollbackhnd)

    # No sense in preserving a backup file with no changes
    if args.backup:
        remove(backup_file)

if __name__ == "__main__":
    main()  # pragma: no cover
