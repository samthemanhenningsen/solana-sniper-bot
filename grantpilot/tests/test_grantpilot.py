"""Offline tests — mock the Grants.gov HTTP layer and the Claude client."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from grantpilot.drafter import Drafter
from grantpilot.matcher import MatchResult
from grantpilot.profile import PROFILE_TEMPLATE, ApplicantProfile
from grantpilot.sources.grants_gov import GrantsGovSource

SEARCH_RESPONSE = {
    "data": {
        "hitCount": 1,
        "oppHits": [
            {
                "id": 358500,
                "number": "USDA-RD-2026-01",
                "title": "Rural Business Development Grants",
                "agencyName": "Rural Business-Cooperative Service",
                "oppStatus": "posted",
                "openDate": "01/15/2026",
                "closeDate": "08/30/2026",
            }
        ],
    }
}

DETAIL_RESPONSE = {
    "data": {
        "synopsis": {
            "synopsisDesc": "<p>Supports targeted technical assistance for small rural businesses.</p>",
            "awardCeiling": "500000",
            "awardFloor": "10000",
            "applicantEligibilityDesc": "Small businesses in rural areas with fewer than 50 employees.",
            "applicantTypes": [{"description": "Small businesses"}],
        }
    }
}


def _session(payload):
    resp = MagicMock()
    resp.json.return_value = payload
    resp.raise_for_status.return_value = None
    session = MagicMock()
    session.post.return_value = resp
    return session


def test_search_parses_hits():
    src = GrantsGovSource(session=_session(SEARCH_RESPONSE))
    opps = src.search("rural")
    assert len(opps) == 1
    opp = opps[0]
    assert opp.number == "USDA-RD-2026-01"
    assert opp.agency == "Rural Business-Cooperative Service"
    assert "358500" in opp.url
    assert opp.slug() == "USDA-RD-2026-01"


def test_enrich_strips_html_and_fills_fields():
    src = GrantsGovSource(session=_session(SEARCH_RESPONSE))
    opp = src.search("rural")[0]
    src.session = _session(DETAIL_RESPONSE)
    src.enrich(opp)
    assert "technical assistance" in opp.synopsis
    assert "<p>" not in opp.synopsis
    assert opp.award_ceiling == "500000"
    assert "Small businesses" in opp.eligibility_summary


def test_search_failure_returns_empty():
    import requests

    session = MagicMock()
    session.post.side_effect = requests.ConnectionError("boom")
    src = GrantsGovSource(session=session)
    assert src.search("anything") == []


def test_profile_roundtrip(tmp_path):
    p = tmp_path / "profile.json"
    p.write_text(PROFILE_TEMPLATE.model_dump_json())
    loaded = ApplicantProfile.load(p)
    assert loaded.legal_name == PROFILE_TEMPLATE.legal_name
    # deterministic serialization matters for prompt caching
    assert loaded.to_prompt_block() == json.dumps(
        loaded.model_dump(exclude_none=True), indent=2, sort_keys=True
    )


def test_checklist_includes_missing_requirements():
    src = GrantsGovSource(session=_session(SEARCH_RESPONSE))
    opp = src.search("rural")[0]
    match = MatchResult(
        eligible=True,
        fit_score=80,
        rationale="Strong fit.",
        missing_requirements=["SAM.gov registration"],
    )
    text = Drafter.checklist(opp, match)
    assert "Obtain: SAM.gov registration" in text
    assert "never submits" in text
    assert "USDA-RD-2026-01" in text
