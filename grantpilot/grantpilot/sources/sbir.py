"""SBIR/STTR connector — federal R&D funding for small businesses (api.www.sbir.gov).

Public API, no key required:
  GET https://api.www.sbir.gov/public/api/solicitations?keyword=...
"""

from __future__ import annotations

import logging

import requests

from .base import Opportunity

log = logging.getLogger(__name__)

API_URL = "https://api.www.sbir.gov/public/api/solicitations"


class SbirSource:
    name = "sbir.gov"

    def __init__(self, session: requests.Session | None = None, timeout: int = 30):
        self.session = session or requests.Session()
        self.timeout = timeout

    def search(self, keyword: str, rows: int = 50) -> list[Opportunity]:
        try:
            resp = self.session.get(
                API_URL, params={"keyword": keyword, "rows": rows}, timeout=self.timeout
            )
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError) as e:
            log.warning("sbir.gov search failed for %r: %s", keyword, e)
            return []

        items = data if isinstance(data, list) else []
        results = []
        for item in items:
            number = item.get("solicitation_number", "") or ""
            topics = item.get("solicitation_topics") or []
            synopsis = " ".join(
                t.get("topic_description", "") or "" for t in topics if isinstance(t, dict)
            ).strip()
            results.append(
                Opportunity(
                    source=self.name,
                    opportunity_id=str(item.get("solicitation_id", number)),
                    number=number,
                    title=item.get("solicitation_title", "") or "",
                    agency=item.get("agency", "") or "",
                    status=item.get("current_status", "") or "",
                    open_date=item.get("open_date", "") or "",
                    close_date=item.get("close_date", "") or "",
                    eligibility_summary=(
                        f"{item.get('program', '')} {item.get('phase', '')} — US small businesses "
                        "(<500 employees, majority US-owned); STTR requires a research institution partner"
                    ).strip(),
                    synopsis=synopsis[:4000],
                    url=item.get("solicitation_agency_url", "") or "",
                    raw=item,
                )
            )
        return results

    def enrich(self, opp: Opportunity) -> Opportunity:
        return opp  # search results already carry full detail
