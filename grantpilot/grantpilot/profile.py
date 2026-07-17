"""Applicant profile — the unit of onboarding. One profile per person or business."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field


class Contact(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""


class ApplicantProfile(BaseModel):
    """Everything the pipeline knows about who it's applying on behalf of."""

    legal_name: str
    entity_type: str = Field(
        description="e.g. 'LLC', 'S-Corp', 'sole proprietorship', '501(c)(3) nonprofit', 'individual'"
    )
    description: str = Field(description="What the business/person does, in a few sentences")
    mission: str = ""
    city: str = ""
    state: str = ""
    country: str = "US"
    founded_year: int | None = None
    employee_count: int | None = None
    annual_revenue_usd: int | None = None
    naics_codes: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(
        default_factory=list,
        description="e.g. 'veteran-owned', 'minority-owned', 'woman-owned', 'HUBZone', '8(a)'",
    )
    focus_areas: list[str] = Field(
        default_factory=list,
        description="Keywords driving grant discovery, e.g. 'small business technology', 'clean energy', 'rural development'",
    )
    funding_needs: str = Field(
        default="",
        description="What the money would be used for — projects, equipment, hiring, R&D",
    )
    past_projects: list[str] = Field(default_factory=list)
    has_sam_registration: bool = Field(
        default=False, description="Registered in SAM.gov with a UEI (required for federal grants)"
    )
    uei: str = Field(default="", description="SAM.gov Unique Entity ID, if registered")
    contact: Contact = Field(default_factory=Contact)

    @classmethod
    def load(cls, path: str | Path) -> "ApplicantProfile":
        return cls.model_validate_json(Path(path).read_text())

    def to_prompt_block(self) -> str:
        """Render the profile as a stable text block for Claude prompts.

        Serialized deterministically so the block can sit under a prompt-cache
        breakpoint while dozens of grants are screened against it.
        """
        data = self.model_dump(exclude_none=True)
        return json.dumps(data, indent=2, sort_keys=True)


PROFILE_TEMPLATE = ApplicantProfile(
    legal_name="Acme Widgets LLC",
    entity_type="LLC",
    description="A small manufacturer of energy-efficient widgets serving the Midwest.",
    mission="Make sustainable widgets affordable for every household.",
    city="Columbus",
    state="OH",
    founded_year=2021,
    employee_count=4,
    annual_revenue_usd=250000,
    naics_codes=["333999"],
    certifications=["veteran-owned"],
    focus_areas=["small business", "manufacturing", "energy efficiency", "rural development"],
    funding_needs="Purchase CNC equipment and hire two machinists to triple production capacity.",
    past_projects=["Pilot program with 3 local hardware stores"],
    has_sam_registration=False,
    contact=Contact(name="Jane Doe", email="jane@acmewidgets.example", phone="555-0100"),
)
