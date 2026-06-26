---
name: cmo-lane
description: The CMO (marketing) Cowork lane. Produces marketing artifacts for a property or deal AND emits a structured event to the forVEX activity ledger at the moment of action, so Readvise can reason over cross-lane activity. Use when working the marketing lane — drafting social posts, flyers, listing campaigns, or email blasts tied to a specific property/deal. Requires the forVEX Control MCP connector.
---

> **Contract:** `reecosystem-core/docs/SKILL_SYSTEM_CONTRACT.md` · shared refs: `references/platform/` (vendored at package time) · MCP data: `references/data-sources.md`

# CMO Lane

You work the marketing lane and **emit** structured events into the forVEX activity ledger
(`core.lane_events`) at the moment you do something. Readvise reasons over that ledger; forVEX
Control stores it. The artifact (the post, flyer, email) stays in your Drive folder — the event is
the small structured signal alongside it.

## The rule: emission is definition-of-done

**No task is complete until its event has landed.** After producing any marketing artifact tied to
a specific property or deal, call `forvex_emit_event` and confirm it returned an `event_id`. Skip
it and the work is invisible to the rest of the business — the one failure mode this exists to
avoid.

## Resolve the entity first (non-negotiable)

Every event attaches to a **canonical** property or deal. Never put a raw address where an id
belongs:
1. Pass `address` (property events) — the tool resolves it to the canonical `property_id`.
2. Or pass a known `property_id` / `deal_id`.

If the address won't resolve, fix it — don't force it. (`raw_mention` is debug-only, never a key.)

## Verbs (initial CMO set)

snake_case, past-tense. Propose additions if a real action isn't covered.

| verb | when | payload |
|------|------|---------|
| `listing_marketed` | property put into active marketing | `{ channels: [], headline? }` |
| `post_published` | social post about a property | `{ platform, post_count, url? }` |
| `content_published` | blog/article/video about a property | `{ format, url? }` |
| `flyer_created` | collateral for a property | `{ format, channel? }` |
| `email_campaign_sent` | email featuring a property | `{ recipients, subject }` |
| `buyer_lead_captured` | inbound buyer lead on a property | `{ channel, contact_name? }` |
| `campaign_launched` | multi-channel campaign for a property/deal | `{ channels: [], objective? }` |

## source_uri & idempotency

- **`source_uri`** — link to the Drive artifact you made. Always include it when an artifact
  exists; it doubles as the dedup identity (re-emitting the same artifact returns `deduped: true`).
- **`idempotency_key`** — only for rare artifact-less events; generate one stable UUID so retries
  dedup. With a `source_uri`, you don't need it.

## Definition-of-done checklist

1. Produce the artifact, save to Drive.
2. Resolve the entity (`address` or known id).
3. `forvex_emit_event` with the right `verb`, `payload`, `source_uri`.
4. Confirm an `event_id` came back. Only then is the task done.

## What NOT to emit (yet)

- **Brand-level marketing not tied to a property/deal** — the ledger only accepts `property` and
  `deal` entities (no `campaign` spine yet). Leave these un-emitted; don't force them onto a
  property. Flag the volume to the operator.
- **The artifacts themselves** — those live in Drive; the event links to them.
- **Anything you can't tie to a canonical entity.**

## If emission fails

Keep the artifact, note the failure in your output so it's visible, and retry. A periodic
reconciler sweep is the backstop — not a substitute for emitting at the source.
