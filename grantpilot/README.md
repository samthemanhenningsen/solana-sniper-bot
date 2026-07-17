# GrantPilot

An AI engine that finds every grant a person or business could plausibly win, screens
each one for eligibility, and drafts a complete application packet for every match —
automatically. Built to run for yourself and to sell as a service: each customer is a
profile, and the pipeline runs end-to-end per profile.

## How it works

```
profile.json ──▶ DISCOVER ──▶ SCREEN ──▶ DRAFT ──▶ outputs/<grant>/packet
                (Grants.gov)  (Claude     (Claude    (review-ready draft +
                              eligibility  writes     checklist + decision log)
                              scoring)     the app)
```

1. **Profile** — a structured description of the applicant: entity type, location,
   NAICS codes, certifications (veteran-owned, minority-owned, …), mission, focus
   areas, funding needs. One JSON file per customer.
2. **Discover** — queries funding sources for open and forecasted opportunities.
   Ships with a [Grants.gov](https://grants.gov) connector (free public API, no key
   needed — covers all US federal grants). The source interface is pluggable so
   state, local, and private-foundation sources can be added.
3. **Screen** — Claude scores every opportunity against the profile: eligible or not,
   0–100 fit score, rationale, and a list of missing requirements (e.g. "requires
   SAM.gov registration", "501(c)(3) only"). Ineligible grants are skipped instead of
   spammed — funders blacklist mass applicants, and eligibility is scored, not assumed.
4. **Draft** — for every grant above the fit threshold, Claude writes a full
   application packet: executive summary, statement of need, project narrative,
   budget narrative, and organizational capability statement, tailored to that
   specific opportunity and the applicant's profile.

## Quick start

```bash
cd grantpilot
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...

# 1. Create a profile template and fill it in
python -m grantpilot init --out my_profile.json

# 2. Run the full pipeline
python -m grantpilot run --profile my_profile.json --min-score 60

# Or just see what's out there without drafting anything
python -m grantpilot discover --profile my_profile.json
```

Results land in `outputs/<run timestamp>/`:

- `decision_log.json` — every grant considered, with its score and rationale
- `<opportunity>/application_draft.md` — the drafted packet
- `<opportunity>/review_checklist.md` — what a human must verify before submitting

## Selling it

The unit of work is a profile. To onboard a customer, collect their `profile.json`
(the `init` template doubles as an intake questionnaire) and run the pipeline on a
schedule — new federal opportunities post daily, so a nightly cron per customer keeps
their queue full of fresh drafts. Pricing models that fit: monthly subscription per
profile, or per-drafted-application.

## Why drafts, not auto-submission

The pipeline deliberately stops at a review-ready draft. Federal applications
(Grants.gov, SF-424) end in certifications signed under penalty of perjury
(18 U.S.C. § 1001), submission requires the applicant's own SAM.gov/Grants.gov
credentials, and funders reject and blacklist boilerplate mass submissions.
"Apply to everything" as a product means *draft* everything eligible and make
submission a one-click human review — that's the version you can legally sell and
that actually wins money. Each packet ships with a checklist covering exactly what
the human must confirm (facts, figures, registrations, attachments) before they
submit through the official portal.

## Configuration

| Env var | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Required. Claude API key. |
| `GRANTPILOT_MODEL` | `claude-opus-4-8` | Model used for screening and drafting. |
