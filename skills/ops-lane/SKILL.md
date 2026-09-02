---
name: ops-lane
description: Operator session closeout and daily-sync lane. At the end of a Cursor/Claude conversation that produced franchise operating acts or decisions, extract those acts (not the transcript) and emit workspace events. Also used for OTF daily sync and meeting prep. Skips personal and forVEX-product threads unless the operator explicitly tags them. Requires the forVEX Control MCP connector.
---

> **Contract:** `reecosystem-core/docs/SKILL_SYSTEM_CONTRACT.md` · shared refs: `references/platform/` (vendored at package time) · MCP data: `references/data-sources.md`

# Ops Lane (session closeout)

You close out operator sessions. You emit **acts and decisions**, never a chat dump. Pulse remains
for how the day felt (`readvise-capture` / `weekly-accountability`).

## When to invoke

- End of a work conversation: "close this out", "emit what we did", "session closeout"
- Scheduled OTF daily sync finishing
- Meeting prep (Cobbs Corner) that is not clearly CMO

Do **not** invoke yourself on every chat. Wait for the closeout ask or a scheduled sync prompt
that tells you to emit then stop.

## Skip list (do not emit unless explicitly tagged)

- Personal noise (shopping, whiskey, family logistics)
- forVEX **product** build (Forge app, Gale models, MCP architecture articles, design-system
  vision) — that is building the platform, not operating the franchise
- Threads that already emitted via `cmo-lane` / `pm-lane` / `cfo-lane` / `net-lane` /
  `forvex-presentation` — do not double-emit the same act
- Underwriting that was saved via `forvex_save_deal` — Readvise **joins** saves; do not shadow-emit

If the whole session is skip-list, say so and emit nothing.

## What to extract

From this conversation only, list 1–5 real acts or decisions. Preview them. Then emit (unless
the operator said "just save it", still preview one line).

Each act is one event:

```
forvex_emit_event({
  lane: "ops",
  verb: "session_closed" | "decision_recorded" | "sync_completed" | "meeting_prepped",
  entity_type: "workspace",
  payload: {
    period: "<YYYY-Www or YYYY-MM-DD>",
    highlights: [<one line per act>],
    count: <N>
  },
  source_uri: "session://ops/<verb>/<YYYY-MM-DD>" 
})
```

Prefer **one** `session_closed` (or `sync_completed` for daily sync) with `highlights[]` over
five tiny events. Use `decision_recorded` only for an explicit decision the operator made
(not a suggestion you floated).

Do **not** pass `property_id`, `deal_id`, or `address` on workspace events. If an act is
property-tied and was not already logged, hand off to `forvex-activity-log` rather than stuffing
the address into ops.

## Verbs

| verb | when |
|------|------|
| `sync_completed` | OTF / daily ops sync finished |
| `meeting_prepped` | meeting prep that is not CMO |
| `session_closed` | end-of-conversation act rollup |
| `decision_recorded` | a real operator decision, named in highlights |

## Confirm

Report `event_id` and the highlights you emitted. If you skipped, say why (personal / product /
already emitted / nothing happened).
