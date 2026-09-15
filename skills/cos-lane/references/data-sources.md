# Chief of Staff lane — MCP data sources

> **Governed by:** `reecosystem-core/docs/SKILL_SYSTEM_CONTRACT.md`

Production MCP: `https://control.forvex.app/api/mcp`

**Coordination transport is Grok** (group `@` / async Bot DM), not MCP and not
Paul-as-courier. MCP writes below are the durable ledger for Readvise.

Writes: **`readvise_create_accountability_debrief`**, **`forvex_emit_event`**
(`lane: cos`).

## Accountability

### readvise_get_prior_context

**Read.** First call on weekly check-in.

### readvise_create_accountability_debrief

**Write.** Store check-in. Idempotent per workspace + user + week. Prefer
`create_tasks: true`.

### readvise_get_today_summary

**Read (optional).** Open tasks / pulse before triage or brief.

## Thin reads (triage / brief only)

`forvex_list_deals`, `forvex_get_deal`, `readvise_list_rental_debt`,
`readvise_list_rental_ops`, `readvise_list_property_capex`,
`readvise_resolve_property` — read only. Domain writes stay on the owner Bot.

## forvex_emit_event (`lane: cos`)

| verb | when |
|------|------|
| `work_dispatched` | After you hand off in Grok to a specialist |
| `week_briefed` | Weekly company rollup |
| `decision_recorded` | Paul named a real decision |
| `cadence_reminded` | Ritual due nudge |

`work_dispatched` payload: `assign_to`, `ask`, `done_when` (required).

`source_uri`: `routine://cos/<verb>/<YYYY-Www>[/<slug>]`.

## Optional later

`forvex_list_lane_events` — pull open `work_dispatched` if a Grok message was
missed. Complements Grok handoffs; does not replace them.
