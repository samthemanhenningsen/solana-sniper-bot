"""Database-backed pipeline execution — the server-side counterpart of grantpilot.pipeline.run."""

from __future__ import annotations

import json
import logging

from ..drafter import Drafter
from ..matcher import Matcher, MatchResult
from ..pipeline import discover
from ..profile import ApplicantProfile
from .db import SessionLocal
from .models import Decision, Draft, Run, utcnow
from .settings import settings

log = logging.getLogger(__name__)


def _drafting_allowed(plan: str) -> bool:
    # When billing is configured, drafting is the paid feature; screening stays free.
    return plan == "pro" or not settings.billing_enabled


def execute_run(run_id: int, matcher: Matcher | None = None, drafter: Drafter | None = None, sources=None) -> None:
    """Execute a queued run to completion. Designed to be called from a worker thread."""
    db = SessionLocal()
    try:
        run = db.get(Run, run_id)
        if run is None or run.status not in ("queued", "running"):
            return
        run.status = "running"
        run.started_at = utcnow()
        db.commit()

        profile_row = run.profile
        applicant = ApplicantProfile.model_validate(profile_row.applicant_data())
        plan = profile_row.user.plan
        matcher = matcher or Matcher()
        drafter = drafter or Drafter()

        opportunities = discover(applicant, max_grants=profile_row.max_grants, sources=sources)
        eligible = drafted = 0

        for opp in opportunities:
            try:
                match = matcher.screen(applicant, opp)
            except Exception as e:
                log.warning("screening error for %s: %s", opp.slug(), e)
                match = MatchResult(eligible=False, fit_score=0, rationale=f"Screening error: {e}")

            decision = Decision(
                run_id=run.id,
                opportunity=opp.model_dump_json(exclude={"raw"}),
                eligible=match.eligible,
                fit_score=match.fit_score,
                rationale=match.rationale,
                missing_requirements=json.dumps(match.missing_requirements),
            )
            db.add(decision)
            db.commit()

            if match.eligible:
                eligible += 1
            if match.eligible and match.fit_score >= profile_row.min_score and _drafting_allowed(plan):
                try:
                    content = drafter.draft(applicant, opp, match)
                    db.add(
                        Draft(
                            decision_id=decision.id,
                            content=content,
                            checklist=Drafter.checklist(opp, match),
                        )
                    )
                    drafted += 1
                    db.commit()
                except Exception as e:
                    log.warning("drafting error for %s: %s", opp.slug(), e)
                    db.rollback()

        run.status = "completed"
        run.finished_at = utcnow()
        run.stats = json.dumps(
            {
                "considered": len(opportunities),
                "eligible": eligible,
                "drafted": drafted,
                "drafting_gated": not _drafting_allowed(plan),
            }
        )
        db.commit()
    except Exception as e:
        log.exception("run %s failed", run_id)
        db.rollback()
        run = db.get(Run, run_id)
        if run is not None:
            run.status = "failed"
            run.finished_at = utcnow()
            run.error = str(e)
            db.commit()
    finally:
        db.close()
