"""Defines a custom type for YAML Path segment attributes."""
from typing import Union

from yamlpath.path import CollectorTerms
import yamlpath.path.searchterms as searchterms


PathAttributes = Union[str, CollectorTerms, searchterms.SearchTerms]
