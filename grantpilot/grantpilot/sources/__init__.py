"""Grant sources. Each source yields Opportunity records for a profile's focus areas."""

from .base import Opportunity
from .grants_gov import GrantsGovSource

__all__ = ["Opportunity", "GrantsGovSource"]
