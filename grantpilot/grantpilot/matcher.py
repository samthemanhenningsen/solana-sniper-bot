"""Eligibility screening — Claude scores each opportunity against the applicant profile."""

from __future__ import annotations

import logging
import os

import anthropic
from pydantic import BaseModel, Field

from .profile import ApplicantProfile
from .sources.base import Opportunity

log = logging.getLogger(__name__)

MODEL = os.environ.get("GRANTPILOT_MODEL", "claude-opus-4-8")

SCREEN_INSTRUCTIONS = """\
You are an expert grant eligibility analyst. You are given an applicant profile and a \
grant opportunity. Determine honestly whether this applicant is eligible and how strong \
a fit the grant is.

Rules:
- Be strict about hard eligibility requirements (entity type, geography, certifications, \
registrations like SAM.gov). If the opportunity is restricted to entity types the \
applicant is not (e.g. state governments, universities, 501(c)(3)s only), mark ineligible.
- Missing-but-fixable requirements (e.g. SAM.gov registration not yet done) do NOT make \
the applicant ineligible — list them in missing_requirements instead.
- The fit score reflects how competitive a well-written application would realistically \
be: alignment of the applicant's work with the funder's purpose, award size vs. the \
applicant's needs, and applicant qualifications.
- Never invent facts about the applicant. If the opportunity text is too thin to judge, \
say so in the rationale and score conservatively."""


class MatchResult(BaseModel):
    eligible: bool
    fit_score: int = Field(description="0-100; how competitive a strong application would be")
    rationale: str = Field(description="2-4 sentences explaining the verdict")
    missing_requirements: list[str] = Field(
        default_factory=list,
        description="Registrations, documents, or statuses the applicant must obtain before applying",
    )


class Matcher:
    def __init__(self, client: anthropic.Anthropic | None = None, model: str = MODEL):
        self.client = client or anthropic.Anthropic()
        self.model = model

    def screen(self, profile: ApplicantProfile, opp: Opportunity) -> MatchResult:
        # The instructions + profile are identical across every grant screened in a
        # run, so they live in system under a cache breakpoint; only the grant varies.
        response = self.client.messages.parse(
            model=self.model,
            max_tokens=16000,
            thinking={"type": "adaptive"},
            system=[
                {"type": "text", "text": SCREEN_INSTRUCTIONS},
                {
                    "type": "text",
                    "text": f"APPLICANT PROFILE:\n{profile.to_prompt_block()}",
                    "cache_control": {"type": "ephemeral"},
                },
            ],
            messages=[
                {
                    "role": "user",
                    "content": f"GRANT OPPORTUNITY:\n{opp.to_prompt_block()}\n\nScreen this opportunity.",
                }
            ],
            output_format=MatchResult,
        )
        if response.stop_reason == "refusal":
            log.warning("screening refused for %s", opp.slug())
            return MatchResult(eligible=False, fit_score=0, rationale="Screening was declined by the model.")
        return response.parsed_output
