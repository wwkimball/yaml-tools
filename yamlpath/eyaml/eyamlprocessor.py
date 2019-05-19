"""Implements an EYAML-capable version of YAMLPath.

Copyright 2018, 2019 William W. Kimball, Jr. MBA MSIS
"""
import re
from subprocess import run, PIPE, CalledProcessError
from os import access, sep, X_OK
from shutil import which
from typing import Any, Generator, Optional

from ruamel.yaml.comments import CommentedSeq, CommentedMap

from yamlpath.enums import YAMLValueFormats
from yamlpath.exceptions import EYAMLCommandException
from yamlpath.wrappers import ConsolePrinter
from yamlpath import Processor, Path


class EYAMLProcessor(Processor):
    """Extend Processor to understand EYAML values."""

    def __init__(self, logger: ConsolePrinter, data: Any, **kwargs):
        """Init this class.

        Positional Parameters:
          1. logger (ConsoleWriter) Instance of ConsoleWriter

        Optional Keyword Parameters:
          1. eyaml (str) The eyaml executable to use
          2. publickey (str) An EYAML public key file; when used,
             privatekey must also be set
          3. privatekey (str) An EYAML private key file; when used,
             publickey must also be set

        Returns:  N/A

        Raises:  N/A
        """
        self.eyaml: str = kwargs.pop("eyaml", "eyaml")
        self.publickey: str = kwargs.pop("publickey", None)
        self.privatekey: str = kwargs.pop("privatekey", None)
        super().__init__(logger, data)

    def _find_eyaml_paths(self, data: Any,
                          build_path: str = "") -> Generator[Path, None, None]:
        """Recursively generates a set of stringified YAML Paths, each entry
        leading to an EYAML value within the evaluated YAML data.

        Positional Parameters:
          1. data (ruamel.yaml data) The parsed YAML data to process
          2. yaml_path (any) The YAML Path under construction

        Returns:  (str or None) each YAML Path entry as they are discovered

        Raises:  N/A
        """
        if isinstance(data, CommentedSeq):
            build_path += "["
            for i, ele in enumerate(data):
                if hasattr(ele, "anchor") and ele.anchor.value is not None:
                    tmp_path = build_path + "&" + ele.anchor.value + "]"
                else:
                    tmp_path = build_path + str(i) + "]"

                if self.is_eyaml_value(ele):
                    yield Path(tmp_path)

                for eyp in self._find_eyaml_paths(ele, tmp_path):
                    yield Path(eyp)

        elif isinstance(data, CommentedMap):
            if build_path:
                build_path += "."

            for k, val in data.non_merged_items():
                tmp_path = build_path + str(k)
                if self.is_eyaml_value(val):
                    yield Path(tmp_path)

                for eyp in self._find_eyaml_paths(val, tmp_path):
                    yield Path(eyp)

    def find_eyaml_paths(self) -> Generator[Path, None, None]:
        """Recursively generates a set of stringified YAML Paths, each entry
        leading to an EYAML value within the evaluated YAML data.

        Positional Parameters:
          1. data (ruamel.yaml data) The parsed YAML data to process
          2. yaml_path (any) The YAML Path under construction

        Returns:  (str or None) each YAML Path entry as they are discovered

        Raises:  N/A
        """
        for node in self._find_eyaml_paths(self.data):
            yield node

    def decrypt_eyaml(self, value: str) -> str:
        """Decrypts an EYAML value.

        Positional Parameters:
          1. value (any) The EYAML value to decrypt

        Returns:  (str) The decrypted value or the original value if it was not
        actually encrypted.

        Raises:
          EYAMLCommandException when the eyaml binary cannot be utilized.
        """
        if not self.is_eyaml_value(value):
            return value

        if not self._can_run_eyaml():
            raise EYAMLCommandException("No accessible eyaml command.")

        cmdstr = self.eyaml + " decrypt --quiet --stdin"
        if self.publickey:
            cmdstr += " --pkcs7-public-key={}".format(self.publickey)
        if self.privatekey:
            cmdstr += " --pkcs7-private-key={}".format(self.privatekey)

        cmd = cmdstr.split()
        cleanval = str(value).replace("\n", "").replace(" ", "").rstrip()
        bval = (cleanval + "\n").encode("ascii")
        self.logger.debug(
            "EYAMLPath::decrypt_eyaml:  About to execute {} against:\n{}"
            .format(cmdstr, cleanval)
        )

        try:
            retval = run(
                cmd,
                stdout=PIPE,
                input=bval
            ).stdout.decode('ascii').rstrip()
        except CalledProcessError as ex:
            raise EYAMLCommandException(
                "The {} command cannot be run due to exit code:  {}"
                .format(self.eyaml, ex.returncode)
            )

        # Check for bad decryptions
        self.logger.debug(
            "EYAMLPath::decrypt_eyaml:  Decrypted result:  {}".format(retval)
        )
        if not retval or retval == cleanval:
            raise EYAMLCommandException(
                "Unable to decrypt value!  Please verify you are using the"
                + " correct old EYAML keys and the value is not corrupt:  {}"
                .format(cleanval)
            )

        return retval

    def encrypt_eyaml(self, value: str, output: str = "string") -> str:
        """Encrypts a value via EYAML.

        Positional Parameters:
          1. value (any) the value to encrypt
          2. output (string) one of "string" or "block"; "string" causes
             the EYAML representation to be one single line while
             "block" results in a folded-string variant

        Returns:  (str) The encrypted result or the original value if it was
        already an EYAML encryption.

        Raises:
          EYAMLCommandException when the eyaml binary cannot be utilized.
        """
        if self.is_eyaml_value(value):
            return value

        if not self._can_run_eyaml():
            raise EYAMLCommandException(
                "The eyaml binary is not executable at {}.".format(self.eyaml)
            )

        cmdstr = self.eyaml + " encrypt --quiet --stdin --output=" + output
        if self.publickey:
            cmdstr += " --pkcs7-public-key={}".format(self.publickey)
        if self.privatekey:
            cmdstr += " --pkcs7-private-key={}".format(self.privatekey)

        cmd = cmdstr.split()
        self.logger.debug(
            "EYAMLPath::encrypt_eyaml:  About to execute:  {}"
            .format(" ".join(cmd))
        )
        bval = (value + "\n").encode("ascii")

        try:
            retval = (
                run(cmd, stdout=PIPE, input=bval, check=True)
                .stdout
                .decode('ascii')
                .rstrip()
            )
        except CalledProcessError as ex:
            raise EYAMLCommandException(
                "The {} command cannot be run due to exit code:  {}"
                .format(self.eyaml, ex.returncode)
            )

        if not retval:
            raise EYAMLCommandException(
                ("The {} command was unable to encrypt your value.  Please"
                 + " verify this process can run that command and read your"
                 + " EYAML keys.").format(self.eyaml)
            )

        if output == "block":
            retval = re.sub(r" +", "", retval) + "\n"

        self.logger.debug(
            "EYAMLPath::encrypt_eyaml:  Encrypted result:\n{}".format(retval)
        )
        return retval

    def set_eyaml_value(self, yaml_path: Path, value: Any, **kwargs) -> None:
        """Encrypts a value and stores the result to zero or more nodes
        specified via YAML Path.

        Positional Parameters:
          1. data (ruamel.yaml data) The parsed YAML data to process
          2. yaml_path (any) The YAML Path specifying which node to
             encrypt
          3. value (any) The value to encrypt

        Optional Parameters:
          1. output (string) one of "string" or "block"; "string" causes
             the EYAML representation to be one single line while
             "block" results in a folded-string variant
          2. mustexist (Boolean) Indicates whether YAML Path must
             specify a pre-existing node

        Returns:  N/A

        Raises:
            YAMLPathException when YAML Path is invalid
        """
        self.logger.verbose(
            "Encrypting value(s) for {}."
            .format(yaml_path)
        )
        output = kwargs.pop("output", "string")
        mustexist = kwargs.pop("mustexist", False)
        encval = self.encrypt_eyaml(value, output)
        emit_format = YAMLValueFormats.FOLDED
        if output == "string":
            emit_format = YAMLValueFormats.DEFAULT

        self.set_value(
            yaml_path,
            encval,
            mustexist=mustexist,
            value_format=emit_format
        )

    def get_eyaml_values(self, yaml_path: Path,
                         **kwargs) -> Generator[str, None, None]:
        """Retrieves and decrypts zero or more EYAML nodes from YAML data at a
        YAML Path.

        Positional Parameters:
          1. data (ruamel.yaml data) The parsed YAML data to process
          2. yaml_path (any) The YAML Path specifying which node to
             decrypt

        Optional Parameters:
          1. mustexist (Boolean) Indicates whether YAML Path must
             specify a pre-existing node
          2. default_value (any) The default value to add to the YAML data when
             mustexist=False and yaml_path points to a non-existent node

        Returns:  (str) The decrypted value or None when YAML Path specifies a
        non-existant node.

        Raises:
            YAMLPathException when YAML Path is invalid
        """
        self.logger.verbose(
            "Decrypting value(s) at {}.".format(yaml_path)
        )
        mustexist = kwargs.pop("mustexist", False)
        default_value = kwargs.pop("default_value", None)
        for node in self.get_nodes(yaml_path, mustexist=mustexist,
                default_value=default_value):
            plain_text = self.decrypt_eyaml(node)
            yield plain_text

    def _can_run_eyaml(self) -> bool:
        """Indicates whether this instance is capable of running the eyaml
        binary as specified via its eyaml property.

        Positional Parameters:  N/A

        Returns:  (Boolean) true when the present eyaml property indicates an
        executable; false, otherwise

        Raises:  N/A
        """
        binary = EYAMLProcessor.get_eyaml_executable(self.eyaml)
        if binary is None:
            return False
        self.eyaml = binary
        return True

    @staticmethod
    def get_eyaml_executable(binary: str = "eyaml") -> Optional[str]:
        """Returns the full executable path to an eyaml binary or None when it
        cannot be found or is not executable.

        Positional Parameters:
          1. binary (str) The executable to test.  If an absolute or relative
             path is not provided, the system PATH will be searched for a match
             to test.

        Returns: (str) None or the executable eyaml binary path.

        Raises:  N/A
        """
        if not binary:
            return None

        if binary.find(sep) < 0:
            binary = str(which(binary))
            if not binary:
                return None

        if access(binary, X_OK):
            return binary
        return None

    @staticmethod
    def is_eyaml_value(value: str) -> bool:
        """Indicates whether a value is EYAML-encrypted.

        Positional Parameters:
          1. value (any) The value to check

        Returns:  (Boolean) true when the value is encrypted; false, otherwise

        Raises:  N/A
        """
        if not isinstance(value, str):
            return False
        return value.replace("\n", "").replace(" ", "").startswith("ENC[")
