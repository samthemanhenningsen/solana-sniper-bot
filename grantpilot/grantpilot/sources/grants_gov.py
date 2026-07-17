"""Grants.gov connector — the free public API covering all US federal grant opportunities.

Uses the Search2 endpoint (no API key required):
  POST https://api.grants.gov/v1/api/search2       — keyword search over opportunities
  POST https://api.grants.gov/v1/api/fetchOpportunity — full detail for one opportunity
"""

from __future__ import annotations

import html
import logging
import re

import requests

from .base import Opportunity

log = logging.getLogger(__name__)

API_BASE = "https://api.grants.gov/v1/api"
OPP_URL = "https://www.grants.gov/search-results-detail/{id}"


def _strip_html(text: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", " ", text or "")).strip()


class GrantsGovSource:
    name = "grants.gov"

    def __init__(self, session: requests.Session | None = None, timeout: int = 30):
        self.session = session or requests.Session()
        self.timeout = timeout

    def search(self, keyword: str, statuses: str = "posted|forecasted", rows: int = 50) -> list[Opportunity]:
        """Search open and forecasted opportunities for a keyword."""
        payload = {
            "keyword": keyword,
            "oppStatuses": statuses,
            "rows": rows,
            "startRecordNum": 0,
        }
        try:
            resp = self.session.post(f"{API_BASE}/search2", json=payload, timeout=self.timeout)
            resp.raise_for_status()
            hits = (resp.json().get("data") or {}).get("oppHits") or []
        except (requests.RequestException, ValueError) as e:
            log.warning("grants.gov search failed for %r: %s", keyword, e)
            return []

        results = []
        for hit in hits:
            opp_id = str(hit.get("id", ""))
            results.append(
                Opportunity(
                    source=self.name,
                    opportunity_id=opp_id,
                    number=hit.get("number", "") or "",
                    title=hit.get("title", "") or "",
                    agency=hit.get("agencyName", hit.get("agency", "")) or "",
                    status=hit.get("oppStatus", "") or "",
                    open_date=hit.get("openDate", "") or "",
                    close_date=hit.get("closeDate", "") or "",
                    url=OPP_URL.format(id=opp_id),
                    raw=hit,
                )
            )
        return results

    def enrich(self, opp: Opportunity) -> Opportunity:
        """Fetch full detail (synopsis, eligibility, award amounts) for an opportunity."""
        try:
            resp = self.session.post(
                f"{API_BASE}/fetchOpportunity",
                json={"opportunityId": int(opp.opportunity_id)},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json().get("data") or {}
        except (requests.RequestException, ValueError) as e:
            log.warning("grants.gov detail fetch failed for %s: %s", opp.opportunity_id, e)
            return opp

        syn = data.get("synopsis") or data.get("forecast") or {}
        opp.synopsis = _strip_html(syn.get("synopsisDesc", "")) or opp.synopsis
        opp.award_ceiling = str(syn.get("awardCeiling", "") or "")
        opp.award_floor = str(syn.get("awardFloor", "") or "")
        elig_desc = _strip_html(syn.get("applicantEligibilityDesc", ""))
        elig_types = ", ".join(
            t.get("description", "") for t in (syn.get("applicantTypes") or []) if t.get("description")
        )
        opp.eligibility_summary = "; ".join(p for p in [elig_types, elig_desc] if p)
        return opp
