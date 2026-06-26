# CMO lane — MCP data sources

> **Governed by:** `reecosystem-core/docs/SKILL_SYSTEM_CONTRACT.md`

Production MCP: `https://control.forvex.app/api/mcp`

Standard recontrol envelope: success → `structuredContent`; errors → `isError: true`.

## forvex_get_property

**Read.** Resolve an address to a canonical `property_id` before emitting.

| Input | Type | Required |
|-------|------|----------|
| `address` | string | yes (or `id`) |
| `id` | uuid | no |
| `workspace_id` | uuid | no |

**Output:** `{ property_id, address, ... }`

## forvex_emit_event

**Write.** Drop a structured event into the cross-lane ledger (`core.lane_events`). Resolve the
entity to a canonical id first; a free-text address is never an entity key. Idempotent via
`idempotency_key`, or `source_uri` (the artifact) as the default dedup identity.

| Input | Type | Required |
|-------|------|----------|
| `lane` | `cmo\|cfo\|pm` | yes |
| `verb` | string (snake_case) | yes |
| `entity_type` | `property\|deal` | yes |
| `property_id` / `deal_id` | uuid | one required (or `address` for property) |
| `address` | string | property events — resolved to canonical id |
| `payload` | object | no — verb-specific detail |
| `source_uri` | string | no — Drive artifact link + default dedup identity |
| `idempotency_key` | uuid | no — explicit dedup for artifact-less events |
| `occurred_at` | datetime | no — backdating |
| `workspace_id` | uuid | no |

**Output:** `{ event_id, idempotency_key, status, deduped, entity_type, property_id, deal_id }`
