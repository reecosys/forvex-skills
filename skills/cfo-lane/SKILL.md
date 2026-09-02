---
name: cfo-lane
description: Finance Cowork lane. Close out a KPI review, cash-position discussion, or payables pass by emitting a workspace event to the forVEX ledger. Use for Louisville KPI analysis, rental cash strategy, position reviews. Requires the forVEX Control MCP connector.
---

> **Contract:** `reecosystem-core/docs/SKILL_SYSTEM_CONTRACT.md` · shared refs: `references/platform/` (vendored at package time) · MCP data: `references/data-sources.md`

# CFO Lane

You work the finance lane and **emit** when a review finishes. Emit the act (KPI reviewed, cash
position reviewed) — not the spreadsheet or the conversation transcript.

## Emission is definition-of-done

```
forvex_emit_event({
  lane: "cfo",
  verb: "kpi_reviewed" | "position_reviewed" | "payables_reviewed",
  entity_type: "workspace",
  payload: { period: "<YYYY-Www>", highlights?: [<short themes>] },
  source_uri: "routine://cfo/<verb>/<YYYY-Www>"
})
```

Do **not** pass `property_id`, `deal_id`, or `address`. If the discussion is actually about one
deal's numbers, that is a deal event (`entity_type: "deal"`, `deal_id` required) — only when you
have the id.

## Verbs

| verb | when |
|------|------|
| `kpi_reviewed` | market/office KPI pass (e.g. Louisville monthly/quarterly) |
| `position_reviewed` | cash / rental cash / capital position |
| `payables_reviewed` | AP / bills pass |

## What NOT to emit

- Transcripts, model files, or tax returns — `source_uri` points at them.
- Product-build finance (platform burn) unless the operator explicitly tags it as franchise ops.
- CMO spend recaps that are really marketing — hand off to `cmo-lane` (`analytics_reviewed`).

Confirm `event_id` before declaring the review done.
