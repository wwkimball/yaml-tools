"""
Express an issue with a YAML Path.

Copyright 2019 William W. Kimball, Jr. MBA MSIS
"""
from typing import Optional


class YAMLPathException(Exception):
    """
    Occurs when a YAML Path is improperly formed or fails to lead to a required
    YAML node.

    Parameters:
        - user_message (str) The message to convey to the user
        - yaml_path (str) The stringified YAML Path which lead to the exception
        - segment (Optional[str]) The segment of the YAML Path which triggered
          the exception, if available

    Returns:  N/A

    Raises:  N/A
    """

    def __init__(self, user_message: str, yaml_path: str,
                 segment: Optional[str] = None) -> None:
        self.user_message: str = user_message
        self.yaml_path: str = yaml_path
        self.segment: Optional[str] = segment

        super(YAMLPathException, self).__init__(
            "user_message: {}, yaml_path: {}, segment: {}"
            .format(user_message, yaml_path, segment))

    # Should Pickling ever be necessary:
    # def __reduce__(self):
    #     return YAMLPathException, (
    #         self.user_message,
    #         self.yaml_path,
    #         self.segment
    #     )

    def __str__(self) -> str:
        message: str = ""
        if self.segment is None:
            message = "{}, '{}'.".format(
                self.user_message,
                self.yaml_path)
        else:
            message = "{} at '{}' in '{}'.".format(
                self.user_message,
                self.segment,
                self.yaml_path)
        return message
