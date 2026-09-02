---
name: cmo-lane
description: The CMO (marketing) Cowork lane. Produces marketing artifacts AND emits a structured event to the forVEX activity ledger at the moment of action. Use for listing-tied marketing, brand/workspace routines (weekly social audit, newsletter, competitor intel, mail targeting, presentations), and scheduled CMO jobs. Requires the forVEX Control MCP connector. Emission is definition-of-done.
---

> **Contract:** `reecosystem-core/docs/SKILL_SYSTEM_CONTRACT.md` · shared refs: `references/platform/` (vendored at package time) · MCP data: `references/data-sources.md`

# CMO Lane

You work the marketing lane and **emit** structured events into the forVEX activity ledger
(`core.lane_events`) at the moment you do something. Readvise reasons over that ledger. The
artifact stays in Drive (or the Claude session); the event is the small structured signal.

## The rule: emission is definition-of-done

**No CMO task is complete until its event has landed.** Call `forvex_emit_event` and confirm an
`event_id` (or `deduped: true`). Skip it and the work is invisible to the rest of the business.

Scheduled jobs (weekly social audit, newsletter sourcing, competitor sweep/intel, Monday
presentation batch) **emit then stop** after the run's work is done. Do not wait to be asked.

## Two entity kinds

**Property or deal** — listing-tied work. Resolve first: pass `address` (property) or a known
`property_id` / `deal_id`. Never put a raw address where an id belongs.

**Workspace** — brand, routine, and batch work with no single house. Pass
`entity_type: "workspace"`. Do **not** pass `property_id`, `deal_id`, or `address`. Do **not**
fake-attach brand work to an unrelated property.

If a batch includes named properties, emit the **workspace rollup** and **one property event per
address**. Rollup + entity, not one or the other.

## Verbs

snake_case, past-tense. Propose additions if a real action isn't covered.

### Property / deal

| verb | when | payload |
|------|------|---------|
| `listing_marketed` | property put into active marketing | `{ channels: [], headline? }` |
| `post_published` | social post about a property | `{ platform, post_count, url? }` |
| `content_published` | blog/article/video about a property | `{ format, url? }` |
| `flyer_created` | collateral for a property | `{ format, channel? }` |
| `email_campaign_sent` | email featuring a property | `{ recipients, subject }` |
| `buyer_lead_captured` | inbound buyer lead on a property | `{ channel, contact_name? }` |
| `campaign_launched` | multi-channel campaign for a property/deal | `{ channels: [], objective? }` |

### Workspace (routines and brand)

| verb | when | payload |
|------|------|---------|
| `social_audited` | weekly social audit finished | `{ count?, platforms?, period, highlights? }` |
| `newsletter_sourced` | newsletter research/sourcing done | `{ period, topic_count? }` |
| `newsletter_published` | newsletter actually sent | `{ period, url? }` |
| `content_planned` | brand/YouTube/topic selection | `{ count?, areas?, period }` |
| `creative_produced` | postcards, seller email, ads | `{ count?, format?, period }` |
| `intel_gathered` | competitor sweep / market intel | `{ period, sources? }` |
| `audience_targeted` | mail targeting by zip / list | `{ zips?, period }` |
| `presentations_produced` | presentation batch (Monday decks, etc.) | `{ count, areas?, period }` |
| `analytics_reviewed` | Blotato / channel analytics | `{ period }` |

## source_uri and idempotency

- Artifact exists → `source_uri` is the Drive/session link. Re-emitting the same URI dedups.
- Scheduled routine → `source_uri: "routine://cmo/<verb>/<period>"` where `period` is `YYYY-Www`
  (weekly) or `YYYY-MM-DD` (daily). Re-running the same week collapses to one row.
- `idempotency_key` — only if there is no artifact and no routine URI; one stable UUID per event.

## Definition-of-done checklist

1. Do the work (artifact, audit, sourcing, batch).
2. Choose entity: workspace, or resolve property/deal.
3. `forvex_emit_event` with `lane: "cmo"`, verb, payload, `source_uri`.
4. Confirm `event_id`. Only then is the task done.

## What NOT to emit

- The artifacts themselves — those live in Drive; the event links to them.
- Personal / non-franchise activity.
- BNI chapter work — hand off to `net-lane`.
- PM portfolio reconcile — hand off to `pm-lane`.
- Guessed property ids. If you cannot resolve an address, emit workspace-only for the batch.

## If emission fails

Keep the artifact, note the failure in your output, and retry. A reconciler sweep is the
backstop — not a substitute for emitting at the source.
