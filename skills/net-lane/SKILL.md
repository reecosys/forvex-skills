---
name: net-lane
description: Networking / BNI Cowork lane. Emit when a chapter watch, member sweep, monthly presentation, or leadership report finishes so Readvise records the relationship work. Not marketing (that is cmo-lane). Requires the forVEX Control MCP connector.
---

> **Contract:** `reecosystem-core/docs/SKILL_SYSTEM_CONTRACT.md` · shared refs: `references/platform/` (vendored at package time) · MCP data: `references/data-sources.md`

# Net Lane (BNI / relationships)

You work chapter and relationship ops — BNI chapter watch, member sweeps, monthly presentations,
leadership reporting, contact lists — and **emit** when a run finishes. This is not CMO.

## Emission is definition-of-done

Scheduled chapter watch / member sweep: emit then stop.

```
forvex_emit_event({
  lane: "net",
  verb: "chapter_watched" | "presentation_delivered" | "leadership_reported" | "network_updated",
  entity_type: "workspace",
  payload: { period: "<YYYY-Www>", count?: <members or slides>, highlights?: [] },
  source_uri: "routine://net/<verb>/<YYYY-Www>"
})
```

Do **not** pass `property_id`, `deal_id`, or `address`.

## Verbs

| verb | when |
|------|------|
| `chapter_watched` | weekly member sweep / chapter watch |
| `presentation_delivered` | BNI monthly presentation given or finalized |
| `leadership_reported` | leadership reporting / coordination |
| `network_updated` | member contact list / power-team update (BNI/community, not product) |

A BNI *deck* you rendered via `forvex-presentation` should still emit here as
`presentation_delivered` (net) in addition to CMO `presentations_produced` only if the deck was
also a marketing artifact. Default: **net only** for BNI decks.

## What NOT to emit

- CMO social/newsletter/competitor work.
- Personal non-chapter chats.
- forVEX product/community-app work (Forge, Gale) unless the operator tags it as BNI.

Confirm `event_id` before declaring the run done.
