# LifeLedger Correction Actions (Judge-Readiness)

Use this as the implementation checklist before final submission.

## A) Reliability and Completeness (Highest Priority)

- [x] Ensure p01 consistently produces non-trivial stress/spend signal (target `|r| >= 0.3` when variance exists).
- [x] Ensure at least 1-3 spike weeks render with evidence in normal demo runs.
- [x] Add explicit low-variance fallback in correlation output:
  - `insufficient_variance: true`
  - human-readable fallback interpretation
  - actionable suggestion instead of empty state.
- [x] Prevent demo dead-ends: every core card should show either evidence or a meaningful fallback message.

## B) Contract Lock (Data + Insight Schema)

- [x] Freeze final loader contract (`profile`, `consent`, source keys, `year_week` format).
- [x] Freeze final insight schema and enforce it in `compute_insights`:
  - `id`, `title`, `finding`, `evidence`, `dollar_impact`, plus feature-specific fields.
- [x] Add schema validation before save (`save_insights`) and fail fast on contract mismatch.
- [x] Remove temporary UI fallback parsing once schema is locked.

## C) Stronger Evidence (Innovation + Explainability)

- [x] For each spike week include:
  - top 3 discretionary transactions (`date`, `merchant/text`, `amount`, `tags`)
  - up to 3 calendar events (`date`, `title/text`, `tags`)
  - threshold math (`week_spend`, `mean`, `std`, `threshold`, `prior_week_stress`).
- [x] Show evidence inline in expanders and summary cards.
- [x] Ensure evidence ties directly to a decision/action.

## D) Track 3 Story and Consent Clarity

- [x] Add in-app "Data Story" section:
  - where data comes from,
  - who owns it,
  - what is computed,
  - why multi-source insight is valuable.
- [x] Add in-app consent/privacy card:
  - local processing,
  - synthetic/demo mode,
  - no raw data sent to LLM,
  - only structured insights used for chat.

## E) UX Upgrades (Quick Wins)

- [x] Add plain-English "What this means" under each major metric.
- [x] Add "Recommended next action" bullets for each persona.
- [x] Improve empty-state language so non-technical judges still understand outcome.

## F) Demo Hardening

- [x] Pre-generate and freeze `outputs/insights_p01.json` and `outputs/insights_p05.json` immediately before demo.
- [x] Validate app startup + both persona paths on a fresh shell.
- [x] Run a 2-minute timed dry run script with exact clicks and chat prompt.
- [x] Prepare one backup screenshot per critical panel in case of runtime issues.

## G) Optional LLM Deployment Strategy

- [ ] Support provider modes:
  - hosted key (default),
  - BYOK OpenAI,
  - BYOK OpenRouter.
- [ ] Keep BYOK keys session-only (never persisted).
- [ ] Keep chat grounded strictly in cached insight JSON.

## H) Final QA Gates

- [ ] `python3 -m py_compile` passes for all modules.
- [ ] `cd web && npm run dev` starts API + frontend without runtime errors.
- [ ] p01: meaningful stress/spend narrative visible.
- [ ] p05: undercharging signal visible (or explicit not-found explanation).
- [ ] At least 5 benchmark chat questions return grounded answers.
