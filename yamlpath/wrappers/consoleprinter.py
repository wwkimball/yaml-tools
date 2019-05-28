"""
Implements a reusable console print facility for simple command-line scripts.
Other implementations can easily wrap Python's standard logger/warning modules,
but this one does not because those are overkill for *simple* STDOUT/STDERR
printing (that must support squelching).

Requires an object on init which has the following properties:
  quiet:  <Boolean> suppresses all output except ConsolePrinter::error() and
          ::critical().
  verbose:  <Boolean> allows output from ConsolePrinter::verbose().
  debug:  <Boolean> allows output from ConsolePrinter::debug().

Copyright 2018, 2019 William W. Kimball, Jr. MBA MSIS
"""
import sys


class ConsolePrinter:
    """
    Generally-useful console messager, writing INFO, VERBOSE, WARN, and DEBUG
    messages to STDOUT as well as ERROR messages to STDERR with multi-lne
    formatting.

    Positional Parameters:
        1. args (object) An object representing log level settings with these
           properties:
            - debug (Boolean) true = write debugging informational messages
            - verbose (Boolean) true = write verbose informational messages
            - quiet (Boolean) true = write only error messages

    Returns:  N/A

    Raises:  N/A
    """

    def __init__(self, args):
        self.args = args

    def info(self, message):
        """
        Writes an informational message to STDOUT unless quiet mode is active.

        Positional Parameters:
            1. message (str) The message to print

        Returns:  N/A

        Raises:  N/A
        """
        if not self.args.quiet:
            print(message)

    def verbose(self, message):
        """
        Writes a verbose message to STDOUT when verbose mode is active unless
        quiet mode is active.

        Positional Parameters:
            1. message (str) The message to print

        Returns:  N/A

        Raises:  N/A
        """
        if not self.args.quiet and (self.args.verbose or self.args.debug):
            print(message)

    def warning(self, message):
        """
        Writes a warning message to STDOUT unless quiet mode is active.

        Positional Parameters:
            1. message (str) The message to print

        Returns:  N/A

        Raises:  N/A
        """
        if not self.args.quiet:
            print("WARNING:  " + str(message).replace("\n", "\nWARNING:  "))

    def error(self, message, exit_code=None):
        """
        Writes a recoverable error message to STDERR and optionally terminates
        the program, exiting with a specific error code.

        Positional Parameters:
            1. message (str) The message to print
            2. exit_code (int) The exit code to terminate the program
               with; default=None

        Returns:  N/A

        Raises:  N/A
        """
        print(
            "ERROR:  " + str(message).replace("\n", "\nERROR:  "),
            file=sys.stderr
        )
        print("Please try --help for more information.")
        sys.stdout.flush()

        # Optionally terminate program execution with a specified exit code
        if exit_code is not None:
            self.debug("Terminating with exit code, {}.".format(exit_code))
            exit(exit_code)

    def critical(self, message, exit_code=1):
        """
        Writes a critical, nonrecoverable failure message to STDERR and
        terminates the program, exiting with a specific error code.

        Positional Parameters:
            1. message (str) The message to print
            2. exit_code (int) The exit code to terminate the program
               with; default=1

        Returns:  N/A

        Raises:  N/A
        """
        print(
            "CRITICAL:  " + str(message).replace("\n", "\nCRITICAL:  "),
            file=sys.stderr
        )
        sys.stdout.flush()

        # Terminate program execution with a specified exit code
        self.debug("Terminating with exit code, {}.".format(exit_code))
        exit(exit_code)

    def debug(self, message):
        """
        Writes a debug message to STDOUT unless quiet mode is active, dumping
        all key-value pairs of a dictionary or all elements of a list, when the
        message is either.

        Positional Parameters:
            1. message (str) The message to print

        Returns:  N/A

        Raises:  N/A
        """
        if self.args.debug and not self.args.quiet:
            if isinstance(message, list):
                for i, ele in enumerate(message):
                    attr = ""
                    if hasattr(ele, "anchor") and ele.anchor.value is not None:
                        attr = "; &" + ele.anchor.value
                    eattr = (str(ele) + attr).replace("\n", "\nDEBUG:  ")
                    print("DEBUG:  [" + str(i) + "]=" + str(eattr))
            elif isinstance(message, dict):
                for k, val in message.items():
                    attr = ""
                    if hasattr(val, "anchor") and val.anchor.value is not None:
                        attr = "; &" + val.anchor.value
                    vattr = (str(val) + attr).replace("\n", "\nDEBUG:  ")
                    print("DEBUG:  [" + str(k) + "]=>" + str(vattr))
            else:
                attr = ""
                if (
                        hasattr(message, "anchor")
                        and message.anchor.value is not None
                ):
                    attr = "; &" + message.anchor.value
                mattr = (str(message) + attr).replace("\n", "\nDEBUG:  ")
                print("DEBUG:  " + str(mattr))
