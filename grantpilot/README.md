# GrantPilot

A full-stack AI product that finds every grant a person or business could plausibly win,
screens each one for eligibility, and drafts a complete application packet for every
match — automatically, nightly, per customer. Run it for yourself and sell it: each
customer is an account with one or more applicant profiles, and the whole thing runs as
a multi-tenant web app with billing hooks.

## Architecture

```
                        ┌──────────────────────────────────────────────┐
 customer browser ────▶ │  FastAPI web app (auth, dashboard, review)   │
                        │    profiles · runs · drafts · billing · admin│
                        └───────┬──────────────────────────────────────┘
                                │ enqueue                    SQLite/Postgres
                        ┌───────▼──────────┐               (users, profiles,
                        │ background worker │──────────────▶ runs, decisions,
                        │ + nightly cron    │                drafts)
                        └───────┬──────────┘
                ┌───────────────┼────────────────┐
        DISCOVER│         SCREEN│           DRAFT│
   Grants.gov + SBIR    Claude eligibility   Claude writes the
   (pluggable sources)  + fit scoring        application packet
```

- **Discover** — pluggable sources; ships with [Grants.gov](https://grants.gov)
  (all US federal grants) and [SBIR/STTR](https://www.sbir.gov) (federal R&D for small
  businesses). Both are free public APIs, no keys.
- **Screen** — Claude scores every opportunity against the profile: eligible or not,
  0–100 fit score, rationale, and fixable gaps ("needs SAM.gov registration").
  The profile sits under a prompt-cache breakpoint so screening 100 grants per
  customer stays cheap.
- **Draft** — for every eligible grant above the profile's fit threshold, Claude writes
  a full packet: executive summary, statement of need, project narrative, budget
  narrative, capability statement. Unknown facts become inline `[VERIFY: …]` markers,
  never fabrications.
- **Review** — customers open each draft in the dashboard, edit it, resolve the
  checklist, and mark it approved/submitted. Everything exports as a zip.
- **Schedule** — profiles with auto-run enabled get a fresh run every night (new
  federal opportunities post daily).

## Run the web app

```bash
cd grantpilot
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python serve.py            # http://localhost:8000
```

The **first account registered becomes the admin/operator** (you). Every account after
that is a customer. Docker:

```bash
docker build -t grantpilot . && docker run -p 8000:8000 -v grantpilot-data:/data \
  -e ANTHROPIC_API_KEY=sk-ant-... grantpilot
```

## Charge customers (optional)

Without Stripe configured, everything is free/unlocked. To monetize, set:

```bash
export STRIPE_SECRET_KEY=sk_live_...
export STRIPE_PRICE_ID=price_...        # a recurring subscription price
export STRIPE_WEBHOOK_SECRET=whsec_...  # webhook endpoint: POST /billing/webhook
pip install stripe
```

The gate is: **screening free, drafting is Pro**. Free users see every grant and score
(the hook); Pro users get the drafted packets (the value). Webhooks flip `user.plan`
automatically on subscribe/cancel.

## CLI (single-profile mode, no server)

```bash
python -m grantpilot init --out my_profile.json   # intake template
python -m grantpilot run --profile my_profile.json --min-score 60
python -m grantpilot discover --profile my_profile.json
```

## Configuration

| Env var | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Required. Claude API key. |
| `GRANTPILOT_MODEL` | `claude-opus-4-8` | Model for screening and drafting. |
| `GRANTPILOT_DB` | `sqlite:///grantpilot.db` | SQLAlchemy URL; point at Postgres in prod. |
| `GRANTPILOT_SECRET` | random per boot | Session-signing secret. Set it in prod or logins reset on restart. |
| `GRANTPILOT_SCHEDULER` | `1` | Set `0` to disable the nightly auto-run loop. |
| `GRANTPILOT_BASE_URL` | `http://localhost:8000` | Public URL, used for Stripe redirects. |
| `STRIPE_*` | — | See billing above. |

## Why drafts, not auto-submission

The pipeline deliberately stops at a review-ready draft. Federal applications
(Grants.gov, SF-424) end in certifications signed under penalty of perjury
(18 U.S.C. § 1001), submission requires the applicant's own SAM.gov/Grants.gov
credentials, and funders reject and blacklist boilerplate mass submissions.
"Apply to everything" as a product means *draft* everything eligible and make
submission a one-click human review — that's the version you can legally sell and
that actually wins money. Screening filters ineligible grants instead of spamming
them for the same reason. Each packet ships with a pre-submission checklist covering
exactly what the human must confirm before submitting through the official portal.

## Production notes

- Put it behind HTTPS (the session cookie is HttpOnly/SameSite=Lax but not
  Secure-flagged until you terminate TLS).
- Set `GRANTPILOT_SECRET` and move `GRANTPILOT_DB` to Postgres for real traffic.
- Forms use same-site cookies as CSRF mitigation; add token-based CSRF before taking
  untrusted traffic at scale.
- Add sources by implementing `search(keyword) -> list[Opportunity]` +
  `enrich(opp)` and appending to `DEFAULT_SOURCES` — state portals, foundation
  databases, and Candid are natural next connectors.

## Tests

```bash
python -m pytest tests/ -q   # offline: fakes for the model, HTTP sources, and Stripe
```
