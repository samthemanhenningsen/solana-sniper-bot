"""FastAPI application — dashboard, profiles, runs, drafts, billing, admin."""

from __future__ import annotations

import io
import json
import logging
import zipfile
from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..profile import ApplicantProfile, Contact
from . import billing
from .auth import SESSION_COOKIE, current_user, hash_password, make_session_token, verify_password
from .db import get_db, init_db
from .jobs import enqueue_run, start_scheduler
from .models import Decision, Draft, Profile, Run, User
from .settings import settings

log = logging.getLogger(__name__)

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def create_app(scheduler: bool | None = None) -> FastAPI:
    app = FastAPI(title="GrantPilot")
    init_db()
    if scheduler if scheduler is not None else settings.scheduler_enabled:
        start_scheduler()

    def render(request: Request, template: str, **ctx) -> HTMLResponse:
        ctx.setdefault("billing_enabled", billing.available())
        return templates.TemplateResponse(request, template, ctx)

    def require_user(user: User | None = Depends(current_user)) -> User:
        if user is None:
            raise HTTPException(status_code=303, headers={"Location": "/login"})
        return user

    def owned_profile(profile_id: int, user: User, db: Session) -> Profile:
        profile = db.get(Profile, profile_id)
        if profile is None or (profile.user_id != user.id and not user.is_admin):
            raise HTTPException(status_code=404)
        return profile

    def owned_run(run_id: int, user: User, db: Session) -> Run:
        run = db.get(Run, run_id)
        if run is None or (run.profile.user_id != user.id and not user.is_admin):
            raise HTTPException(status_code=404)
        return run

    def owned_draft(draft_id: int, user: User, db: Session) -> Draft:
        draft = db.get(Draft, draft_id)
        if draft is None or (draft.decision.run.profile.user_id != user.id and not user.is_admin):
            raise HTTPException(status_code=404)
        return draft

    # ---------- auth ----------

    @app.get("/register", response_class=HTMLResponse)
    def register_page(request: Request):
        return render(request, "auth.html", mode="register", error=None)

    @app.post("/register")
    def register(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
        email = email.strip().lower()
        if len(password) < 8:
            return render(request, "auth.html", mode="register", error="Password must be at least 8 characters.")
        if db.query(User).filter(User.email == email).first():
            return render(request, "auth.html", mode="register", error="An account with that email already exists.")
        is_first = db.query(User).count() == 0  # first account becomes the operator/admin
        user = User(email=email, password_hash=hash_password(password), is_admin=is_first)
        db.add(user)
        db.commit()
        resp = RedirectResponse("/", status_code=303)
        resp.set_cookie(SESSION_COOKIE, make_session_token(user.id), httponly=True, samesite="lax")
        return resp

    @app.get("/login", response_class=HTMLResponse)
    def login_page(request: Request):
        return render(request, "auth.html", mode="login", error=None)

    @app.post("/login")
    def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
        user = db.query(User).filter(User.email == email.strip().lower()).first()
        if user is None or not verify_password(password, user.password_hash):
            return render(request, "auth.html", mode="login", error="Invalid email or password.")
        resp = RedirectResponse("/", status_code=303)
        resp.set_cookie(SESSION_COOKIE, make_session_token(user.id), httponly=True, samesite="lax")
        return resp

    @app.post("/logout")
    def logout():
        resp = RedirectResponse("/login", status_code=303)
        resp.delete_cookie(SESSION_COOKIE)
        return resp

    # ---------- dashboard ----------

    @app.get("/", response_class=HTMLResponse)
    def dashboard(request: Request, user: User | None = Depends(current_user), db: Session = Depends(get_db)):
        if user is None:
            return RedirectResponse("/login", status_code=303)
        profiles = db.scalars(select(Profile).where(Profile.user_id == user.id)).all()
        runs = (
            db.query(Run)
            .join(Profile)
            .filter(Profile.user_id == user.id)
            .order_by(Run.created_at.desc())
            .limit(15)
            .all()
        )
        return render(request, "dashboard.html", user=user, profiles=profiles, runs=runs)

    # ---------- profiles ----------

    def _profile_from_form(form: dict) -> ApplicantProfile:
        def csv_list(key: str) -> list[str]:
            return [x.strip() for x in form.get(key, "").split(",") if x.strip()]

        def maybe_int(key: str) -> int | None:
            raw = form.get(key, "").strip()
            return int(raw) if raw.isdigit() else None

        return ApplicantProfile(
            legal_name=form.get("legal_name", "").strip(),
            entity_type=form.get("entity_type", "").strip(),
            description=form.get("description", "").strip(),
            mission=form.get("mission", "").strip(),
            city=form.get("city", "").strip(),
            state=form.get("state", "").strip(),
            founded_year=maybe_int("founded_year"),
            employee_count=maybe_int("employee_count"),
            annual_revenue_usd=maybe_int("annual_revenue_usd"),
            naics_codes=csv_list("naics_codes"),
            certifications=csv_list("certifications"),
            focus_areas=csv_list("focus_areas"),
            funding_needs=form.get("funding_needs", "").strip(),
            past_projects=csv_list("past_projects"),
            has_sam_registration=form.get("has_sam_registration") == "on",
            uei=form.get("uei", "").strip(),
            contact=Contact(
                name=form.get("contact_name", "").strip(),
                email=form.get("contact_email", "").strip(),
                phone=form.get("contact_phone", "").strip(),
            ),
        )

    @app.get("/profiles/new", response_class=HTMLResponse)
    def profile_new(request: Request, user: User = Depends(require_user)):
        return render(request, "profile_form.html", user=user, profile=None, data={}, error=None)

    @app.post("/profiles/new")
    async def profile_create(request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
        form = dict(await request.form())
        try:
            applicant = _profile_from_form(form)
        except Exception as e:
            return render(request, "profile_form.html", user=user, profile=None, data=form, error=str(e))
        profile = Profile(
            user_id=user.id,
            name=applicant.legal_name or "Unnamed",
            data=applicant.model_dump_json(),
            auto_run=form.get("auto_run") == "on",
            min_score=int(form.get("min_score", 60) or 60),
            max_grants=int(form.get("max_grants", 50) or 50),
        )
        db.add(profile)
        db.commit()
        return RedirectResponse("/", status_code=303)

    @app.get("/profiles/{profile_id}", response_class=HTMLResponse)
    def profile_edit(profile_id: int, request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
        profile = owned_profile(profile_id, user, db)
        return render(
            request, "profile_form.html", user=user, profile=profile, data=profile.applicant_data(), error=None
        )

    @app.post("/profiles/{profile_id}")
    async def profile_update(profile_id: int, request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
        profile = owned_profile(profile_id, user, db)
        form = dict(await request.form())
        try:
            applicant = _profile_from_form(form)
        except Exception as e:
            return render(request, "profile_form.html", user=user, profile=profile, data=form, error=str(e))
        profile.name = applicant.legal_name or profile.name
        profile.data = applicant.model_dump_json()
        profile.auto_run = form.get("auto_run") == "on"
        profile.min_score = int(form.get("min_score", 60) or 60)
        profile.max_grants = int(form.get("max_grants", 50) or 50)
        db.commit()
        return RedirectResponse("/", status_code=303)

    # ---------- runs ----------

    @app.post("/profiles/{profile_id}/run")
    def launch_run(profile_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
        profile = owned_profile(profile_id, user, db)
        run_id = enqueue_run(profile.id)
        return RedirectResponse(f"/runs/{run_id}", status_code=303)

    @app.get("/runs/{run_id}", response_class=HTMLResponse)
    def run_detail(run_id: int, request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
        run = owned_run(run_id, user, db)
        decisions = sorted(run.decisions, key=lambda d: d.fit_score, reverse=True)
        return render(request, "run_detail.html", user=user, run=run, decisions=decisions, stats=run.stats_dict())

    @app.get("/api/runs/{run_id}/status")
    def run_status(run_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
        run = owned_run(run_id, user, db)
        return {"status": run.status, "decisions": len(run.decisions), "stats": run.stats_dict()}

    @app.get("/runs/{run_id}/export.zip")
    def run_export(run_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
        run = owned_run(run_id, user, db)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            decision_log = []
            for d in run.decisions:
                opp = d.opportunity_dict()
                decision_log.append(
                    {
                        "opportunity": opp.get("number") or opp.get("opportunity_id"),
                        "title": opp.get("title"),
                        "eligible": d.eligible,
                        "fit_score": d.fit_score,
                        "rationale": d.rationale,
                        "missing_requirements": d.missing_list(),
                    }
                )
                if d.draft:
                    slug = "".join(c if c.isalnum() or c in "-_" else "-" for c in (opp.get("number") or str(d.id)))[:80]
                    zf.writestr(f"{slug}/application_draft.md", d.draft.content)
                    zf.writestr(f"{slug}/review_checklist.md", d.draft.checklist)
            zf.writestr("decision_log.json", json.dumps(decision_log, indent=2))
        return Response(
            buf.getvalue(),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=grantpilot-run-{run.id}.zip"},
        )

    # ---------- drafts ----------

    @app.get("/drafts/{draft_id}", response_class=HTMLResponse)
    def draft_view(draft_id: int, request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
        draft = owned_draft(draft_id, user, db)
        return render(
            request, "draft_view.html", user=user, draft=draft, opp=draft.decision.opportunity_dict()
        )

    @app.post("/drafts/{draft_id}")
    def draft_save(
        draft_id: int,
        content: str = Form(...),
        status: str = Form("draft"),
        user: User = Depends(require_user),
        db: Session = Depends(get_db),
    ):
        draft = owned_draft(draft_id, user, db)
        draft.content = content
        if status in ("draft", "approved", "submitted"):
            draft.status = status
        db.commit()
        return RedirectResponse(f"/drafts/{draft_id}", status_code=303)

    # ---------- billing ----------

    @app.get("/billing", response_class=HTMLResponse)
    def billing_page(request: Request, user: User = Depends(require_user)):
        return render(request, "billing.html", user=user)

    @app.post("/billing/checkout")
    def billing_checkout(user: User = Depends(require_user), db: Session = Depends(get_db)):
        url = billing.create_checkout_url(user, db)
        if url is None:
            raise HTTPException(status_code=400, detail="Billing is not configured on this server.")
        return RedirectResponse(url, status_code=303)

    @app.post("/billing/webhook")
    async def billing_webhook(request: Request, db: Session = Depends(get_db)):
        payload = await request.body()
        signature = request.headers.get("stripe-signature", "")
        try:
            billing.handle_webhook(payload, signature, db)
        except Exception as e:
            log.warning("stripe webhook rejected: %s", e)
            raise HTTPException(status_code=400, detail="invalid webhook")
        return {"ok": True}

    # ---------- admin ----------

    @app.get("/admin", response_class=HTMLResponse)
    def admin_page(request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
        if not user.is_admin:
            raise HTTPException(status_code=404)
        users = db.query(User).order_by(User.created_at.desc()).all()
        runs = db.query(Run).order_by(Run.created_at.desc()).limit(50).all()
        return render(request, "admin.html", user=user, users=users, runs=runs)

    return app

