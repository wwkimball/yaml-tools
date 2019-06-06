"""Defines a custom type for YAML Path segments."""
from typing import Tuple

from yamlpath.enums import PathSegmentTypes
from yamlpath.types import PathAttributes

PathSegment = Tuple[PathSegmentTypes, PathAttributes]
