"""
YAML Path Collector segment terms.

Copyright 2019 William W. Kimball, Jr. MBA MSIS
"""
from yamlpath.enums import CollectorOperators


class CollectorTerms:
    """YAML Path Collector segment terms."""

    def __init__(self, expression: str,
                 operation: CollectorOperators = CollectorOperators.NONE
                ) -> None:
        self._expression: str = expression
        self._operation: CollectorOperators = operation

    def __str__(self) -> str:
        operator: str = str(self.operation)
        return "{}({})".format(operator, self.expression)

    @property
    def operation(self) -> CollectorOperators:
        """
        Gets the operation for this Collector, indicating whether its results
        are independent, added to the prior Collector, or removed from the
        prior Collector.
        """
        return self._operation

    @property
    def expression(self) -> str:
        """Gets the Collector expression, which is a stringified YAML Path."""
        return self._expression
