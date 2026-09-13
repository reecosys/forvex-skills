# Ops lane — MCP data sources

> **Governed by:** `reecosystem-core/docs/SKILL_SYSTEM_CONTRACT.md`

Production MCP: `https://control.forvex.app/api/mcp`

## forvex_emit_event

**Write.** `lane` is always `ops`. Default `entity_type: workspace`.
`source_uri: "session://ops/<verb>/<YYYY-MM-DD>"` or `routine://ops/sync_completed/<YYYY-MM-DD>`.

**Output:** `{ event_id, idempotency_key, status, deduped, entity_type, property_id, deal_id }`

Do not call `forvex_save_deal` or `readvise_append_pulse_today` from this skill.
