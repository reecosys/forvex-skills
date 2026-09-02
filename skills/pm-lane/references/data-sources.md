# PM lane — MCP data sources

> **Governed by:** `reecosystem-core/docs/SKILL_SYSTEM_CONTRACT.md`

Production MCP: `https://control.forvex.app/api/mcp`

## forvex_emit_event

**Write.** `lane` is always `pm`. Workspace rollups use `entity_type: workspace` and
`source_uri: "routine://pm/<verb>/<YYYY-Www>"`. Property follow-ups pass `address` or `property_id`.

**Output:** `{ event_id, idempotency_key, status, deduped, entity_type, property_id, deal_id }`

## forvex_get_property

**Read.** Only when emitting a per-property follow-up and you have an address but not an id.
