# Skill Routing — Who Owns What

> Registry source of truth: `skills/SKILL_REGISTRY.json`

Use this when a user action could map to multiple skills. **Hand off** — do not duplicate another skill's write path.

## Acquisition → analyze

| User intent | Skill | Key writes |
|---|---|---|
| Set up buy-box / first-time setup | `forvex-onboarding` | `forvex_save_buy_box` |
| Analyze a deal / MAO / what-if | `forvex-underwriting` | `forvex_save_deal`, `forvex_capture_deal_brief` (8.5) |
| Prep for seller meeting | `forvex-appointment-prep` | none (hands off saves to underwriting) |
| Render dashboard / PDF / deck / debrief / rehab scope | `forvex-presentation` | `forvex_emit_event` (workspace rollup + per-property when addressed) |

## Pipeline (REdeal)

| User intent | Skill | Key writes |
|---|---|---|
| Morning pipeline triage | `forvex-pipeline-standup` | none (read-only) |
| Log call / drive-by / counter note | `forvex-activity-log` | `forvex_log_activity` |
| Move deal status (OFFER → SOLD) | `forvex-deal-disposition` | `forvex_update_deal_disposition`, `forvex_record_deal_outcome` (terminal) |
| Missing / refresh close actuals | `forvex-deal-outcomes` | `forvex_list_deal_outcomes`, `forvex_record_deal_outcome`, `forvex_update_deal_outcome` |
| Post-meeting updates | `forvex-appointment-prep` → routes to disposition / activity / underwriting |

## Execution (REbuild)

| User intent | Skill | Key writes |
|---|---|---|
| New rehab estimate | `forvex-rehab-estimator` | `forvex_save_draft_estimate` |
| Scope / dollar change | `forvex-change-order` | `forvex_update_estimate` |
| Progress note (no $ change) | `forvex-project-update` | timeline via REbuild MCP |
| Check project status | `forvex-project-status` | none |

## Cowork lanes (emit to `core.lane_events`)

| User intent | Skill | Key writes |
|---|---|---|
| Triage / hand work to specialist Bots, company week brief | `cos-lane` | Grok `@`/DM + `forvex_emit_event` (`work_dispatched` / `week_briefed`) |
| Weekly accountability check-in | `cos-lane` (or alias `weekly-accountability`) | `readvise_create_accountability_debrief` |
| Listing marketing, social audit, newsletter, competitor intel, mail targeting | `cmo-lane` | `forvex_emit_event` |
| Weekly COO / PM reconcile (flips + Holdings rentals) | `pm-lane` | `forvex_emit_event` (+ CapEx/ops upserts) |
| KPI / cash / payables review | `cfo-lane` | `forvex_emit_event` |
| Holdings loan ↔ property / payoff update | `cfo-lane` | `readvise_upsert_rental_debt` (then emit `position_reviewed`) |
| CapEx watch add / statement month log | `pm-lane` | `readvise_upsert_property_capex` / `readvise_upsert_rental_ops` |
| BNI chapter watch, monthly presentation, leadership report | `net-lane` | `forvex_emit_event` |
| Session closeout, daily sync, meeting prep (not CMO) | `ops-lane` | `forvex_emit_event` |

Scheduled jobs invoke the matching lane skill at the end ("emit then stop"). One lane skill per
domain — not one skill per cron title. CMO/CFO **reads** (pipeline, market brief, outcomes)
are allowlisted in those skills. Writes stay `forvex_emit_event` except CFO's
Holdings capital map (`readvise_upsert_rental_debt`) and COO's CapEx watch + rental ops
snapshots. **CoS (`cos-lane`) orchestrates in Grok** — `@` or async-DM the owner Bot,
then emit `work_dispatched` for the ledger. Paul is not the courier. Domain skills
accept CoS handoff messages and reply to CoS when done. COO (`pm-lane`) may **read**
the capital map and the flip pipeline; it does not write debt or underwrite.

## Operate (Readvise)

| User intent | Skill | Key writes |
|---|---|---|
| Notes, tasks, pulse, advisor lane | `readvise-capture` | `readvise_*` |
| Weekly accountability check-in (alias) | `weekly-accountability` | `readvise_create_accountability_debrief` (prefer `cos-lane` on the CoS bot) |

## Demo (no MCP)

| User intent | Skill |
|---|---|
| Quick MAO | `forvex-mao` |
| Light rehab ballpark | `forvex-rehab-light` |
| Finish package | `forvex-finish` |
| Closed-deal math recap | `forvex-postmortem` |
| Weekly accountability, no account | `accountability-partner` — superseded by `weekly-accountability` when the Control MCP is connected |

## Learning loop (cross-cutting)

1. **Underwriting save** — `forvex_save_deal` + `context.session_summary` (Operate memo).
2. **Same close-out** — `forvex_capture_deal_brief` with triaged `corrections[]` (step 8.5).
3. **Deal close** — `forvex_record_deal_outcome` at `SOLD` / `LOST` (disposition or appointment-prep handoff). Weekly / missing actuals: `forvex-deal-outcomes`.

Without step 3, captured adjustments never confirm in `/learning`.
