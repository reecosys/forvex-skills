# CFO lane — MCP data sources

> **Governed by:** `reecosystem-core/docs/SKILL_SYSTEM_CONTRACT.md`

Production MCP: `https://control.forvex.app/api/mcp`

## forvex_emit_event

**Write.** `lane` is always `cfo`. Default `entity_type: workspace` with
`source_uri: "routine://cfo/<verb>/<YYYY-Www>"`.

**Output:** `{ event_id, idempotency_key, status, deduped, entity_type, property_id, deal_id }`
