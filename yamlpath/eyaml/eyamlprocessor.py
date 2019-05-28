"""
Implements an EYAML-capable version of YAML Path.

Copyright 2018, 2019 William W. Kimball, Jr. MBA MSIS
"""
import re
from subprocess import run, PIPE, CalledProcessError
from os import access, sep, X_OK
from shutil import which
from typing import Any, Generator, List, Optional

from ruamel.yaml.comments import CommentedSeq, CommentedMap

from yamlpath import YAMLPath
from yamlpath.eyaml.enums import EYAMLOutputFormats
from yamlpath.enums import YAMLValueFormats
from yamlpath.eyaml.exceptions import EYAMLCommandException
from yamlpath.wrappers import ConsolePrinter
from yamlpath import Processor


class EYAMLProcessor(Processor):
    """
    Extend Processor to understand EYAML values.

    Note that due to a bug in the eyaml command at the time of this writing,
    either both or neither of the public and private keys must be set.  So,
    even though you would normally need only the public key to encrypt values,
    you must also supply the private key, anyway.

    Parameters:
        1. logger (ConsolePrinter) Instance of ConsolePrinter or subclass
        2. data (Any) Parsed YAML data
        3. **kwargs (Optional[str]) can contain the following keyword
           parameters:
           * binary (str) The external eyaml command to use when performing
             data encryption or decryption; if no path is provided, the command
             will be sought on the system PATH.  Defaut="eyaml"
           * publickey (Optional[str]) Fully-qualified path to the public key
             for use with data encryption
           * privatekey (Optional[str]) Fully-qualified path to the public key
             for use with data decryption

    Returns:  N/A

    Raises:  N/A
    """

    def __init__(self, logger: ConsolePrinter, data: Any,
                 **kwargs: Optional[str]) -> None:
        self.eyaml: Optional[str] = kwargs.pop("binary", "eyaml")
        self.publickey: Optional[str] = kwargs.pop("publickey", None)
        self.privatekey: Optional[str] = kwargs.pop("privatekey", None)
        super().__init__(logger, data)

    # pylint: disable=locally-disabled,too-many-branches
    def _find_eyaml_paths(
            self, data: Any, build_path: str = ""
    ) -> Generator[YAMLPath, None, None]:
        """
        Recursively generates a set of stringified YAML Paths, each entry
        leading to an EYAML value within the evaluated YAML data.

        Parameters:
            1. data (Any) The parsed YAML data to process
            2. build_path (str) A YAML Path under construction

        Returns:  (Generator[Path, None, None]) each YAML Path entry as they
            are discovered

        Raises:  N/A
        """
        if isinstance(data, CommentedSeq):
            build_path += "["
            for idx, ele in enumerate(data):
                if hasattr(ele, "anchor") and ele.anchor.value is not None:
                    tmp_path = build_path + "&" + ele.anchor.value + "]"
                else:
                    tmp_path = build_path + str(idx) + "]"

                if self.is_eyaml_value(ele):
                    yield YAMLPath(tmp_path)
                else:
                    for subpath in self._find_eyaml_paths(ele, tmp_path):
                        yield subpath

        elif isinstance(data, CommentedMap):
            if build_path:
                build_path += "."

            for key, val in data.non_merged_items():
                tmp_path = build_path + str(key)
                if self.is_eyaml_value(val):
                    yield YAMLPath(tmp_path)
                else:
                    for subpath in self._find_eyaml_paths(val, tmp_path):
                        yield subpath

    def find_eyaml_paths(self) -> Generator[YAMLPath, None, None]:
        """
        Recursively generates a set of stringified YAML Paths, each entry
        leading to an EYAML value within the evaluated YAML data.

        Parameters:  N/A

        Returns:  (Generator[Path, None, None]) each YAML Path entry as they
            are discovered

        Raises:  N/A
        """
        # Initiate the scan from the data root
        for path in self._find_eyaml_paths(self.data):
            yield path

    def decrypt_eyaml(self, value: str) -> str:
        """
        Decrypts an EYAML value.

        Parameters:
            1. value (str) The EYAML value to decrypt

        Returns:  (str) The decrypted value or the original value if it was not
        actually encrypted.

        Raises:
            - `EYAMLCommandException` when the eyaml binary cannot be utilized
        """
        if not self.is_eyaml_value(value):
            return value

        if not self._can_run_eyaml():
            raise EYAMLCommandException("No accessible eyaml command.")

        cmdstr: str = "{} decrypt --quiet --stdin".format(self.eyaml)
        if self.publickey:
            cmdstr += " --pkcs7-public-key={}".format(self.publickey)
        if self.privatekey:
            cmdstr += " --pkcs7-private-key={}".format(self.privatekey)

        cmd: List[str] = cmdstr.split()
        cleanval: str = str(value).replace("\n", "").replace(" ", "").rstrip()
        bval: bytes = (cleanval + "\n").encode("ascii")
        self.logger.debug(
            "EYAMLPath::decrypt_eyaml:  About to execute {} against:\n{}"
            .format(cmdstr, cleanval)
        )

        try:
            retval: str = run(
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

    def encrypt_eyaml(self, value: str,
                      output: EYAMLOutputFormats = EYAMLOutputFormats.STRING
                     ) -> str:
        """
        Encrypts a value via EYAML.

        Parameters:
            1. value (str) the value to encrypt
            2. output (EYAMLOutputFormats) the output format of the encryption

        Returns:  (str) The encrypted result or the original value if it was
        already an EYAML encryption.

        Raises:
            - `EYAMLCommandException` when the eyaml binary cannot be utilized.
        """
        if self.is_eyaml_value(value):
            return value

        if not self._can_run_eyaml():
            raise EYAMLCommandException(
                "The eyaml binary is not executable at {}.".format(self.eyaml)
            )

        cmdstr: str = ("{} encrypt --quiet --stdin --output={}"
                       .format(self.eyaml, output))
        if self.publickey:
            cmdstr += " --pkcs7-public-key={}".format(self.publickey)
        if self.privatekey:
            cmdstr += " --pkcs7-private-key={}".format(self.privatekey)

        cmd: List[str] = cmdstr.split()
        self.logger.debug(
            "EYAMLPath::encrypt_eyaml:  About to execute:  {}"
            .format(" ".join(cmd))
        )
        bval: bytes = (value + "\n").encode("ascii")

        try:
            retval: str = (
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

        if output is EYAMLOutputFormats.BLOCK:
            retval = re.sub(r" +", "", retval) + "\n"

        self.logger.debug(
            "EYAMLPath::encrypt_eyaml:  Encrypted result:\n{}".format(retval)
        )
        return retval

    def set_eyaml_value(self, yaml_path: YAMLPath, value: str,
                        output: EYAMLOutputFormats = EYAMLOutputFormats.STRING,
                        mustexist: bool = False) -> None:
        """
        Encrypts a value and stores the result to zero or more nodes specified
        via YAML Path.

        Parameters:
            1. yaml_path (Path) The YAML Path specifying which nodes are to
               receive the encrypted value
            2. value (any) The value to encrypt
            3. output (EYAMLOutputFormats) the output format of the encryption
            4. mustexist (bool) Indicates whether YAML Path must
                specify a pre-existing node

        Returns:  N/A

        Raises:
            - `YAMLPathException` when YAML Path is invalid
        """
        self.logger.verbose(
            "Encrypting value(s) for {}."
            .format(yaml_path)
        )
        encval: str = self.encrypt_eyaml(value, output)
        emit_format: YAMLValueFormats = YAMLValueFormats.FOLDED
        if output is EYAMLOutputFormats.STRING:
            emit_format = YAMLValueFormats.DEFAULT

        self.set_value(
            yaml_path,
            encval,
            mustexist=mustexist,
            value_format=emit_format
        )

    def get_eyaml_values(self, yaml_path: YAMLPath, mustexist: bool = False,
                         default_value: str = ""
                        ) -> Generator[str, None, None]:
        """
        Retrieves and decrypts zero or more EYAML nodes from YAML data at a
        YAML Path.

        Parameters:
            1. yaml_path (Path) The YAML Path specifying which nodes to decrypt
            2. mustexist (bool) Indicates whether YAML Path must specify a
               pre-existing node; when False, the node will be created when
               missing
            3. default_value (str) The default value to add to the YAML data
               when `mustexist=False` and yaml_path points to a non-existent
               node

        Returns:  (str) The decrypted value or `default_value` when YAML Path
            specifies a non-existant node

        Raises:
            - `YAMLPathException` when YAML Path is invalid
        """
        self.logger.verbose(
            "Decrypting value(s) at {}.".format(yaml_path)
        )
        for node in self.get_nodes(yaml_path, mustexist=mustexist,
                                   default_value=default_value):
            plain_text: str = self.decrypt_eyaml(node)
            yield plain_text

    def _can_run_eyaml(self) -> bool:
        """
        Indicates whether this instance is capable of running the eyaml binary
        as specified via its eyaml property.

        Parameters:  N/A

        Returns:  (bool) True when the present eyaml property indicates an
        executable; False, otherwise

        Raises:  N/A
        """
        binary: Optional[str] = EYAMLProcessor.get_eyaml_executable(self.eyaml)
        if binary is None:
            return False
        self.eyaml = binary
        return True

    @staticmethod
    def get_eyaml_executable(binary: Optional[str] = "eyaml") -> Optional[str]:
        """
        Returns the full executable path to an eyaml binary or None when it
        cannot be found or is not executable.

        Parameters:
            1. binary (str) The executable to test; if an absolute or relative
               path is not provided, the system PATH will be searched for a
               match to test

        Returns: (str) None or the executable eyaml binary path

        Raises:  N/A
        """
        if binary is None or not binary:
            return None

        if binary.find(sep) < 0:
            binary = which(binary)
            if binary is None:
                return None
            binary = str(binary)

        if access(binary, X_OK):
            return binary
        return None

    @staticmethod
    def is_eyaml_value(value: str) -> bool:
        """
        Indicates whether a value is EYAML-encrypted.

        Parameters:
            1. value (any) The value to check

        Returns:  (bool) True when the value is encrypted; False, otherwise

        Raises:  N/A
        """
        if not isinstance(value, str):
            return False
        return value.replace("\n", "").replace(" ", "").startswith("ENC[")
