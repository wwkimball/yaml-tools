"""Defines a custom type for YAML Path segments."""
from typing import Tuple, Union

from yamlpath.path import SearchTerms, CollectorTerms
from yamlpath.enums import PathSegmentTypes


PathSegment = Tuple[PathSegmentTypes, Union[str, CollectorTerms, SearchTerms]]
