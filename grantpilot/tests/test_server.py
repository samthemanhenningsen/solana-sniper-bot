"""Full-stack server tests — real app + real SQLite, fake model and fake grant source."""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_tmpdir = tempfile.mkdtemp(prefix="grantpilot-test-")
os.environ["GRANTPILOT_DB"] = f"sqlite:///{_tmpdir}/test.db"
os.environ["GRANTPILOT_SCHEDULER"] = "0"
os.environ["GRANTPILOT_SECRET"] = "test-secret"

import pytest
from fastapi.testclient import TestClient

import grantpilot.server.app as app_module
from grantpilot.matcher import MatchResult
from grantpilot.server.db import SessionLocal
from grantpilot.server.engine import execute_run
from grantpilot.server.jobs import _profiles_due
from grantpilot.server.models import Profile, Run
from grantpilot.sources.base import Opportunity

FAKE_OPP = Opportunity(
    source="test",
    opportunity_id="1",
    number="TEST-2026-01",
    title="Test Grant for Widget Makers",
    agency="Test Agency",
    close_date="12/31/2026",
    synopsis="Funding for widget innovation.",
    url="https://example.gov/1",
)


class FakeSource:
    def search(self, keyword, **kw):
        return [FAKE_OPP.model_copy(deep=True)]

    def enrich(self, opp):
        return opp


class FakeMatcher:
    def screen(self, profile, opp):
        return MatchResult(
            eligible=True,
            fit_score=88,
            rationale="Great fit for testing.",
            missing_requirements=["SAM.gov registration"],
        )


class FakeDrafter:
    def draft(self, profile, opp, match):
        return f"# Application draft for {opp.title}\n\n[VERIFY: everything]"

    @staticmethod
    def checklist(opp, match):
        from grantpilot.drafter import Drafter

        return Drafter.checklist(opp, match)


def _sync_enqueue(profile_id: int) -> int:
    """Test replacement for jobs.enqueue_run: run synchronously with fakes."""
    db = SessionLocal()
    try:
        run = Run(profile_id=profile_id, status="queued")
        db.add(run)
        db.commit()
        run_id = run.id
    finally:
        db.close()
    execute_run(run_id, matcher=FakeMatcher(), drafter=FakeDrafter(), sources=[FakeSource()])
    return run_id


@pytest.fixture(scope="module")
def client(request):
    app = app_module.create_app(scheduler=False)
    original = app_module.enqueue_run
    app_module.enqueue_run = _sync_enqueue
    request.addfinalizer(lambda: setattr(app_module, "enqueue_run", original))
    with TestClient(app, follow_redirects=False) as c:
        yield c


PROFILE_FORM = {
    "legal_name": "Acme Widgets LLC",
    "entity_type": "LLC",
    "description": "We make widgets.",
    "focus_areas": "widgets, manufacturing",
    "certifications": "veteran-owned",
    "min_score": "60",
    "max_grants": "50",
}


def test_register_first_user_is_admin(client):
    r = client.post("/register", data={"email": "owner@example.com", "password": "hunter22!"})
    assert r.status_code == 303
    assert "gp_session" in r.cookies
    # first user is admin — can see admin page
    assert client.get("/admin").status_code == 200


def test_unauthenticated_redirects(client):
    fresh = TestClient(client.app, follow_redirects=False)
    r = fresh.get("/")
    assert r.status_code == 303 and r.headers["location"] == "/login"


def test_create_profile_and_run_pipeline(client):
    r = client.post("/profiles/new", data=PROFILE_FORM)
    assert r.status_code == 303

    db = SessionLocal()
    profile = db.query(Profile).first()
    assert profile is not None
    assert profile.applicant_data()["focus_areas"] == ["widgets", "manufacturing"]
    profile_id = profile.id
    db.close()

    r = client.post(f"/profiles/{profile_id}/run")
    assert r.status_code == 303
    run_url = r.headers["location"]

    page = client.get(run_url)
    assert page.status_code == 200
    assert "Test Grant for Widget Makers" in page.text
    assert "eligible" in page.text
    assert "88" in page.text


def test_run_status_api_and_export(client):
    db = SessionLocal()
    run = db.query(Run).first()
    run_id = run.id
    db.close()

    status = client.get(f"/api/runs/{run_id}/status").json()
    assert status["status"] == "completed"
    assert status["stats"]["drafted"] == 1

    zip_resp = client.get(f"/runs/{run_id}/export.zip")
    assert zip_resp.status_code == 200
    assert zip_resp.headers["content-type"] == "application/zip"
    import io
    import zipfile

    zf = zipfile.ZipFile(io.BytesIO(zip_resp.content))
    names = zf.namelist()
    assert "decision_log.json" in names
    assert any(n.endswith("application_draft.md") for n in names)


def test_draft_review_and_approve(client):
    db = SessionLocal()
    run = db.query(Run).first()
    draft = run.decisions[0].draft
    draft_id = draft.id
    db.close()

    page = client.get(f"/drafts/{draft_id}")
    assert page.status_code == 200
    assert "Application draft" in page.text
    assert "never submits" in page.text  # checklist rendered

    r = client.post(f"/drafts/{draft_id}", data={"content": "edited by human", "status": "approved"})
    assert r.status_code == 303
    db = SessionLocal()
    from grantpilot.server.models import Draft

    saved = db.get(Draft, draft_id)
    assert saved.content == "edited by human"
    assert saved.status == "approved"
    db.close()


def test_ownership_enforced(client):
    other = TestClient(client.app, follow_redirects=False)
    other.post("/register", data={"email": "intruder@example.com", "password": "password1"})
    db = SessionLocal()
    run_id = db.query(Run).first().id
    profile_id = db.query(Profile).first().id
    db.close()
    assert other.get(f"/runs/{run_id}").status_code == 404
    assert other.get(f"/profiles/{profile_id}").status_code == 404
    assert other.get("/admin").status_code == 404  # second user is not admin


def test_scheduler_due_logic(client):
    db = SessionLocal()
    profile = db.query(Profile).first()
    profile.auto_run = True
    db.commit()
    # latest run just finished -> not due
    assert profile.id not in _profiles_due(db)
    # push the finish time back a day -> due
    from datetime import timedelta

    from grantpilot.server.models import utcnow

    for run in profile.runs:
        run.finished_at = utcnow() - timedelta(hours=30)
    db.commit()
    assert profile.id in _profiles_due(db)
    db.close()
