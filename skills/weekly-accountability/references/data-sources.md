# Weekly accountability — MCP data sources

> **Governed by:** `reecosystem-core/docs/SKILL_SYSTEM_CONTRACT.md`

Production MCP: `https://control.forvex.app/api/mcp`

Standard recontrol envelope: success → `structuredContent`; errors → `isError: true`.

## readvise_get_prior_context

**Read.** Load the operator's recent accountability context to open the session. Call first.

| Input | Type | Required |
|-------|------|----------|
| `lookback` | int (1–4) | no — how many prior accountability debriefs (default 1) |
| `include_open_tasks` | boolean | no — default true |
| `workspace_id` | uuid | no |

**Output:** `{ prior_debriefs: [{ debrief_id, week, created_at, short_summary, commitments[], wins[], blockers[], decisions[], last_week_review }], open_tasks: [{ task_id, label, status, property_id }] }`

## readvise_create_accountability_debrief

**Write.** Store the session as a Readvise debrief (`source_type='accountability'`). Idempotent per
(workspace, user, week) — re-running the same week updates the row. Emits a Readvise timeline event
(in-app activity), and optionally suggested tasks. Call at the END of the chat.

| Input | Type | Required |
|-------|------|----------|
| `short_summary` | string (≤320) | yes |
| `summary` | string | yes |
| `commitments` | string[] | no — this week's commitments → next_steps (+ tasks if create_tasks) |
| `last_week_review` | string | no |
| `wins` / `blockers` / `decisions` | string[] | no |
| `momentum` | `high\|medium\|low\|stalled` | no |
| `mood` | `energized\|steady\|stressed` | no |
| `energy_score` | number 0–10 | no |
| `create_tasks` | boolean | no — emit commitments as suggested tasks (first insert only) |
| `week` | string (e.g. `2026-W26`) | no — defaults to current week |
| `workspace_id` | uuid | no |

**Output:** `{ debrief_id, week, mode: 'inserted' | 'updated', tasks_created }`
