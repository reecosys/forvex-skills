# CMO lane — MCP data sources

> **Governed by:** `reecosystem-core/docs/SKILL_SYSTEM_CONTRACT.md`

Production MCP: `https://control.forvex.app/api/mcp`

Standard recontrol envelope: success → `structuredContent`; errors → `isError: true`.

Write tool is **`forvex_emit_event` only.** Reads below are allowlisted. Do not call
`forvex_underwrite` or `forvex_save_deal` from this lane.

## forvex_list_deals

**Read.** Pipeline to market. Filter `status` to `LISTED`, `REHAB`, or `INVENTORY` unless the
operator asks for another slice. Paginated (default 25).

## forvex_get_property

**Read.** Resolve an address to a canonical `property_id` before emitting a property event.

| Input | Type | Required |
|-------|------|----------|
| `address` | string | yes (or `id`) |
| `id` | uuid | no |
| `workspace_id` | uuid | no |

**Output:** `{ property_id, address, ... }`

## forvex_get_deal

**Read.** Saved analysis snapshot for listing-tied work. Required before
`forvex_render_presentation` modes that need a saved deal.

## forvex_get_market_brief

**Read.** Market-wide Sense brief (metro pricing/liquidity, ZIP movers, tract scores).
**Data only** — write the Local Market Intel narrative in CMO voice. Caveat `data_month` vs
`scored_month` (scores lag).

## forvex_get_market_intelligence

**Read.** Property-tied tract/momentum. Use for a named house, not the weekly brand audit.

## forvex_render_presentation

**Read.** Operator HTML for a **saved** analysis (`dashboard` / `deck` / `pdf`). Does not
re-run math. If there is no saved analysis, refuse and hand off — do not invent numbers.

## readvise_list_competitor_work

**Read.** Call **first** on a competitor sweep. Returns work queues (ripened listings without
outcome, stale operator sizing, quiet feeds). Read `collector_status` before treating feeds
as dead.

## forvex_emit_event

**Write.** Drop a structured event into the cross-lane ledger (`core.lane_events`). Idempotent via
`idempotency_key`, or `source_uri` (artifact or `routine://cmo/<verb>/<period>`) as the default
dedup identity.

| Input | Type | Required |
|-------|------|----------|
| `lane` | `cmo` | yes — this skill always sends `cmo` |
| `verb` | string (snake_case) | yes |
| `entity_type` | `property` \| `deal` \| `workspace` | yes |
| `property_id` / `deal_id` | uuid | required for property/deal (or `address` for property) |
| `address` | string | property events — resolved to canonical id. **Forbidden on workspace.** |
| `payload` | object | no — verb-specific detail (`count`, `areas`, `period`, `highlights`) |
| `source_uri` | string | no — Drive/session link or `routine://cmo/<verb>/YYYY-Www` |
| `idempotency_key` | uuid | no — explicit dedup for artifact-less events |
| `occurred_at` | datetime | no — backdating |
| `workspace_id` | uuid | no |

**Output:** `{ event_id, idempotency_key, status, deduped, entity_type, property_id, deal_id }`

Workspace events return `property_id: null` and `deal_id: null`.
