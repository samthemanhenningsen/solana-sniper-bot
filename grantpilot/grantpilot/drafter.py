"""Application drafting — Claude writes a full, tailored application packet per grant."""

from __future__ import annotations

import os

import anthropic

from .matcher import MatchResult
from .profile import ApplicantProfile
from .sources.base import Opportunity

MODEL = os.environ.get("GRANTPILOT_MODEL", "claude-opus-4-8")

DRAFT_INSTRUCTIONS = """\
You are a professional grant writer producing a submission-ready application draft. \
Write in the applicant's voice, tailored to this specific funder and opportunity — \
never generic boilerplate.

Produce a markdown document with these sections:
1. **Executive Summary** — the ask, the amount (aligned to the award range), and why \
this applicant.
2. **Statement of Need** — the problem this funding addresses, grounded in the \
applicant's actual situation and market.
3. **Project Narrative** — what will be done with the funds, timeline, and milestones. \
Align explicitly with the funder's stated purpose.
4. **Budget Narrative** — a realistic line-item breakdown summing to the requested \
amount, with one-line justifications.
5. **Organizational Capability** — why this applicant can execute: history, team, \
certifications, past projects.

Hard rules:
- Use ONLY facts from the applicant profile. Where a specific figure, date, or document \
is needed but not in the profile, write [VERIFY: what's needed] inline instead of \
inventing it.
- Do not overstate capabilities or fabricate history, partnerships, or metrics — \
applications carry legal certifications of accuracy.
- Mirror the funder's terminology from the opportunity text where it helps alignment."""

CHECKLIST_TEMPLATE = """\
# Pre-submission review checklist — {title}

**Opportunity:** {number} ({agency})
**Deadline:** {close_date}
**Portal:** {url}

A human must complete every item below before this application is submitted.
GrantPilot drafts; it never submits.

- [ ] Read the full Notice of Funding Opportunity on the portal (the draft was written
      from a summary — the NOFO controls)
- [ ] Verify every fact and figure in the draft; resolve every `[VERIFY: ...]` marker
- [ ] Confirm eligibility requirements listed by the funder are actually met
{missing_items}- [ ] Confirm SAM.gov registration is active and the UEI is current (federal grants)
- [ ] Prepare required attachments (SF-424 forms, budget forms, letters of support)
- [ ] Have an authorized representative review the certifications page — these are
      signed under penalty of perjury
- [ ] Submit through the official portal with the applicant's own credentials
"""


class Drafter:
    def __init__(self, client: anthropic.Anthropic | None = None, model: str = MODEL):
        self.client = client or anthropic.Anthropic()
        self.model = model

    def draft(self, profile: ApplicantProfile, opp: Opportunity, match: MatchResult) -> str:
        """Return the full application packet as markdown."""
        user_prompt = (
            f"APPLICANT PROFILE:\n{profile.to_prompt_block()}\n\n"
            f"GRANT OPPORTUNITY:\n{opp.to_prompt_block()}\n\n"
            f"ELIGIBILITY ANALYSIS (from screening):\n{match.rationale}\n"
            f"Missing requirements to flag: {', '.join(match.missing_requirements) or 'none'}\n\n"
            "Write the application draft now."
        )
        with self.client.messages.stream(
            model=self.model,
            max_tokens=64000,
            thinking={"type": "adaptive"},
            system=DRAFT_INSTRUCTIONS,
            messages=[{"role": "user", "content": user_prompt}],
        ) as stream:
            message = stream.get_final_message()

        if message.stop_reason == "refusal":
            return "> Drafting was declined by the model for this opportunity.\n"
        return "".join(b.text for b in message.content if b.type == "text")

    @staticmethod
    def checklist(opp: Opportunity, match: MatchResult) -> str:
        missing = "".join(f"- [ ] Obtain: {req}\n" for req in match.missing_requirements)
        return CHECKLIST_TEMPLATE.format(
            title=opp.title,
            number=opp.number or opp.opportunity_id,
            agency=opp.agency,
            close_date=opp.close_date or "see portal",
            url=opp.url,
            missing_items=missing,
        )
