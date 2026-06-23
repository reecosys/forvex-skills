# Skill Routing — Who Owns What

> Registry source of truth: `skills/SKILL_REGISTRY.json`

Use this when a user action could map to multiple skills. **Hand off** — do not duplicate another skill's write path.

## Acquisition → analyze

| User intent | Skill | Key writes |
|---|---|---|
| Set up buy-box / first-time setup | `forvex-onboarding` | `forvex_save_buy_box` |
| Analyze a deal / MAO / what-if | `forvex-underwriting` | `forvex_save_deal`, `forvex_capture_deal_brief` (8.5) |
| Prep for seller meeting | `forvex-appointment-prep` | none (hands off saves to underwriting) |
| Render dashboard / PDF / deck | `forvex-presentation` | none |

## Pipeline (REdeal)

| User intent | Skill | Key writes |
|---|---|---|
| Morning pipeline triage | `forvex-pipeline-standup` | none (read-only) |
| Log call / drive-by / counter note | `forvex-activity-log` | `forvex_log_activity` |
| Move deal status (OFFER → SOLD) | `forvex-deal-disposition` | `forvex_update_deal_disposition`, `forvex_record_deal_outcome` (terminal) |
| Post-meeting updates | `forvex-appointment-prep` → routes to disposition / activity / underwriting |

## Execution (REbuild)

| User intent | Skill | Key writes |
|---|---|---|
| New rehab estimate | `forvex-rehab-estimator` | `forvex_save_draft_estimate` |
| Scope / dollar change | `forvex-change-order` | `forvex_update_estimate` |
| Progress note (no $ change) | `forvex-project-update` | timeline via REbuild MCP |
| Check project status | `forvex-project-status` | none |

## Operate (Readvise)

| User intent | Skill | Key writes |
|---|---|---|
| Notes, tasks, pulse, advisor lane | `readvise-capture` | `readvise_*` |

## Demo (no MCP)

| User intent | Skill |
|---|---|
| Quick MAO | `forvex-mao` |
| Light rehab ballpark | `forvex-rehab-light` |
| Finish package | `forvex-finish` |
| Closed-deal math recap | `forvex-postmortem` |

## Learning loop (cross-cutting)

1. **Underwriting save** — `forvex_save_deal` + `context.session_summary` (Operate memo).
2. **Same close-out** — `forvex_capture_deal_brief` with triaged `corrections[]` (step 8.5).
3. **Deal close** — `forvex_record_deal_outcome` at `SOLD` / `LOST` (disposition or appointment-prep handoff).

Without step 3, captured adjustments never confirm in `/learning`.
