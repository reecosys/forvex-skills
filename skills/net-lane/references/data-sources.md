# Net lane — MCP data sources

> **Governed by:** `reecosystem-core/docs/SKILL_SYSTEM_CONTRACT.md`

Production MCP: `https://control.forvex.app/api/mcp`

## forvex_emit_event

**Write.** `lane` is always `net`. `entity_type: workspace`.
`source_uri: "routine://net/<verb>/<YYYY-Www>"`.

**Output:** `{ event_id, idempotency_key, status, deduped, entity_type, property_id, deal_id }`
