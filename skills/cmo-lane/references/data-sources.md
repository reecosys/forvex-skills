# CMO lane — MCP data sources

> **Governed by:** `reecosystem-core/docs/SKILL_SYSTEM_CONTRACT.md`

Production MCP: `https://control.forvex.app/api/mcp`

Standard recontrol envelope: success → `structuredContent`; errors → `isError: true`.

## forvex_get_property

**Read.** Resolve an address to a canonical `property_id` before emitting a property event.

| Input | Type | Required |
|-------|------|----------|
| `address` | string | yes (or `id`) |
| `id` | uuid | no |
| `workspace_id` | uuid | no |

**Output:** `{ property_id, address, ... }`

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
