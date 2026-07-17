"""End-to-end pipeline: discover -> screen -> draft -> write review packets."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from .drafter import Drafter
from .matcher import Matcher, MatchResult
from .profile import ApplicantProfile
from .sources import GrantsGovSource, Opportunity

log = logging.getLogger(__name__)


def discover(profile: ApplicantProfile, max_grants: int = 100) -> list[Opportunity]:
    """Query every source with every focus area, dedupe, and enrich with full detail."""
    source = GrantsGovSource()
    keywords = profile.focus_areas or [profile.description[:80]]

    seen: dict[str, Opportunity] = {}
    for kw in keywords:
        for opp in source.search(kw):
            key = opp.number or opp.opportunity_id
            if key not in seen:
                seen[key] = opp
    opportunities = list(seen.values())[:max_grants]
    log.info("discovered %d unique opportunities from %d keywords", len(opportunities), len(keywords))

    for opp in opportunities:
        source.enrich(opp)
    return opportunities


def run(
    profile: ApplicantProfile,
    out_dir: str | Path = "outputs",
    max_grants: int = 100,
    min_score: int = 60,
    draft: bool = True,
) -> Path:
    """Run the full pipeline for one profile. Returns the run's output directory."""
    run_dir = Path(out_dir) / datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)

    opportunities = discover(profile, max_grants=max_grants)
    matcher = Matcher()
    drafter = Drafter()

    decision_log: list[dict] = []
    drafted = 0

    for i, opp in enumerate(opportunities, 1):
        log.info("[%d/%d] screening: %s", i, len(opportunities), opp.title[:80])
        try:
            match = matcher.screen(profile, opp)
        except Exception as e:  # keep the run alive; one bad grant shouldn't kill the batch
            log.warning("screening error for %s: %s", opp.slug(), e)
            match = MatchResult(eligible=False, fit_score=0, rationale=f"Screening error: {e}")

        decision_log.append(
            {
                "opportunity": opp.number or opp.opportunity_id,
                "title": opp.title,
                "agency": opp.agency,
                "close_date": opp.close_date,
                "url": opp.url,
                "eligible": match.eligible,
                "fit_score": match.fit_score,
                "rationale": match.rationale,
                "missing_requirements": match.missing_requirements,
            }
        )

        if draft and match.eligible and match.fit_score >= min_score:
            log.info("  -> drafting (score %d)", match.fit_score)
            packet_dir = run_dir / opp.slug()
            packet_dir.mkdir(exist_ok=True)
            try:
                (packet_dir / "application_draft.md").write_text(drafter.draft(profile, opp, match))
                (packet_dir / "review_checklist.md").write_text(drafter.checklist(opp, match))
                (packet_dir / "opportunity.json").write_text(opp.model_dump_json(indent=2, exclude={"raw"}))
                drafted += 1
            except Exception as e:
                log.warning("drafting error for %s: %s", opp.slug(), e)

        # persist incrementally so a crash mid-run loses nothing
        (run_dir / "decision_log.json").write_text(json.dumps(decision_log, indent=2))

    log.info(
        "run complete: %d considered, %d eligible, %d drafted -> %s",
        len(decision_log),
        sum(1 for d in decision_log if d["eligible"]),
        drafted,
        run_dir,
    )
    return run_dir
