from __future__ import annotations

from pydantic import BaseModel, Field


class Opportunity(BaseModel):
    """A single grant opportunity, normalized across sources."""

    source: str
    opportunity_id: str
    number: str = ""
    title: str
    agency: str = ""
    status: str = ""
    open_date: str = ""
    close_date: str = ""
    award_ceiling: str = ""
    award_floor: str = ""
    eligibility_summary: str = ""
    synopsis: str = ""
    url: str = ""
    raw: dict = Field(default_factory=dict, repr=False)

    def slug(self) -> str:
        base = self.number or self.opportunity_id
        return "".join(c if c.isalnum() or c in "-_" else "-" for c in base)[:80]

    def to_prompt_block(self) -> str:
        parts = [
            f"Title: {self.title}",
            f"Opportunity number: {self.number or self.opportunity_id}",
            f"Agency: {self.agency}",
            f"Status: {self.status}",
            f"Opens: {self.open_date}  Closes: {self.close_date}",
        ]
        if self.award_floor or self.award_ceiling:
            parts.append(f"Award range: {self.award_floor or '?'} – {self.award_ceiling or '?'}")
        if self.eligibility_summary:
            parts.append(f"Eligibility: {self.eligibility_summary}")
        if self.synopsis:
            parts.append(f"Synopsis: {self.synopsis}")
        if self.url:
            parts.append(f"URL: {self.url}")
        return "\n".join(parts)
