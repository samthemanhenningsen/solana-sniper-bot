"""Grant sources. Each source yields Opportunity records for a profile's focus areas."""

from .base import Opportunity
from .grants_gov import GrantsGovSource
from .sbir import SbirSource

DEFAULT_SOURCES = [GrantsGovSource, SbirSource]

__all__ = ["Opportunity", "GrantsGovSource", "SbirSource", "DEFAULT_SOURCES"]
